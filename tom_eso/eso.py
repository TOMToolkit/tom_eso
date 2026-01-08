"""
ESO Facility Plugin for TOMToolkit

This module demonstrates the pattern for user-specific credentials in TOMToolkit facilities.

The forms need dynamic data (like dropdown choices) that comes from external APIs
which require user-specific credentials. This calls for a Separation of Concerns:

- **Facility**: Handles business logic (credentials, API clients, external data)
- **Form**: Handles presentation logic (display, validation, layout)

Workflow:
1. ObservationCreateView calls facility.set_user(request.user) in dispatch()
2. Facility.set_user() queries user credentials and sets up API clients
3. Form receives facility instance (not user) and asks facility for data
4. Form uses facility-provided data to populate choice fields

At the moment, this pattern is followed by both tom_eso and tom_swift plugins.
"""
import logging

from crispy_forms.layout import Layout, HTML, Submit, ButtonHolder, Div

from django.urls import reverse_lazy
from django import forms

from tom_observations.facility import (
    BaseRoboticObservationForm,
    BaseRoboticObservationFacility,
    CredentialStatus
)
from tom_eso import __version__
from tom_eso.eso_api import ESOAPI
from tom_eso.models import ESOProfile
from tom_targets.models import Target
from tom_common.session_utils import get_encrypted_field


logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


class ESOObservationForm(BaseRoboticObservationForm):

    # 1. define the form fields,
    # 2. the define the __init__ below
    # 3. then the layout
    # 4. implement other Fomrm methods

    # 1. Form fields

    p2_observing_run = forms.TypedChoiceField(
        label='Observing Run',
        coerce=int,
        choices=[(0, 'Please set your ESO Credentials')],  # populated in __init__ with user credentials
        required=True,
        # Select is the default widget for a ChoiceField, but we need to set htmx attributes.
        widget=forms.Select(
            # set up attributes to trigger folder dropdown update when this field changes
            attrs={
                'hx-get': reverse_lazy('tom_eso:observing-run-folders'),  # send GET request to this URL
                # (the view for this endpoint returns folder names for the selected observing run)
                'hx-trigger': 'change',  # only on change - on load would be too much
                'hx-target': '#div_id_p2_folder_name',  # replace p2_folder_name div
                # Set loading state immediately when request starts
                'hx-on::before-request': '''
                    let folder_select = document.querySelector("#id_p2_folder_name");
                    let spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];
                    let spinner_index = 0;

                    function updateSpinner() {
                        if (folder_select.innerHTML.includes("Loading ESO P2 folders")) {
                            folder_select.innerHTML =
                            `<option value="">${spinner_chars[spinner_index]} Loading ESO P2 folders...</option>`;
                            spinner_index = (spinner_index + 1) % spinner_chars.length;
                        }
                    }

                    folder_select.innerHTML =
                    '<option value="">⠋ Loading ESO P2 folders...</option>';
                    folder_select.spinner_interval = setInterval(updateSpinner, 150);

                    document.querySelector("#id_observation_blocks").innerHTML =
                    '<option value="">Please select a Folder</option>';
                ''',
                # Clear the spinner animation when request completes
                'hx-on::after-swap': '''
                    let folder_select = document.querySelector("#id_p2_folder_name");
                    if (folder_select.spinner_interval) {
                        clearInterval(folder_select.spinner_interval);
                        folder_select.spinner_interval = null;
                    }
                ''',
            })
    )

    p2_folder_name = forms.TypedChoiceField(
        # The folder name is a ChoiceField that is updated when the observing run is selected.
        # Choices are are of the form (folder_id, folder_name) where folder_id is an integer.
        # Because the folder_id is an integer, we use a TypedChoiceField and set coerce=int.
        label='Folder Name',
        required=False,
        coerce=int,
        # these choices will be updated when the p2_observing_run field is changed
        # as specified by the htmx attributes on the p2_observing_run's <select> element
        choices=[(0, 'Please select an Observing Run')],  # overwritten by when observing run is selected
        # when this ChoiceField is changed, the Observation Blocks for the newly selected folder
        # are updated in the by the htmx attributes on this field's <select> element (below, see widget attrs)
        widget=forms.Select(
            attrs={
                'hx-get': reverse_lazy('tom_eso:folder-observation-blocks'),  # send GET request to this URL
                # (the view for this endpoint returns items for the selected folder)
                'hx-trigger': 'change',  # only on change - load would be too aggressive here
                'hx-target': '#div_id_observation_blocks',  # replace HTML element with this id
                # Set loading state for observation blocks when folder is selected
                'hx-on::before-request': '''
                    let obs_select = document.querySelector("#id_observation_blocks");
                    let spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];
                    let spinner_index = 0;

                    function updateObsSpinner() {
                        if (obs_select.innerHTML.includes("Loading observation blocks")) {
                            obs_select.innerHTML =
                            `<option value="">${spinner_chars[spinner_index]} Loading observation blocks...</option>`;
                            // don't count too high; loop back to the beginning via the modulo operator
                            spinner_index = (spinner_index + 1) % spinner_chars.length;
                        }
                    }

                    // this creates the ob_select element so updateObsSpinner function can update it
                    obs_select.innerHTML = '<option value="">⠋ Loading observation blocks...</option>';

                    // now loop through the spinner_chars
                    obs_select.spinner_interval = setInterval(updateObsSpinner, 150);
                ''',
                # Clear the spinner animation when request completes
                'hx-on::after-swap': '''
                    let obs_select = document.querySelector("#id_observation_blocks");
                    if (obs_select.spinner_interval) {
                        clearInterval(obs_select.spinner_interval);
                        obs_select.spinner_interval = null;
                    }
                ''',
            })
    )

    observation_blocks = forms.TypedChoiceField(
        label='Observation Blocks',
        required=False,
        coerce=int,
        choices=[(0, 'Please select a Folder')],
        widget=forms.Select(
            attrs={
                # these htmx attributes make it such that when you select an observation block, the
                # iframe src is updated to show the selected observation block in the ESO P2 Tool
                'hx-get': reverse_lazy('tom_eso:show-observation-block'),  # send GET request to this URL
                'hx-trigger': 'change',  # only on change - load would be too aggressive here
                'hx-target': '#id_eso_p2_tool_iframe',  # target the iframe directly

                'hx-swap': 'outerHTML',  # replace the entire iframe element

                # This script creates and displays a spinner overlay before the request starts.
                'hx-on::before-request': '''
                    let iframeContainer = document.querySelector("#div_id_eso_p2_tool_iframe");

                    // Create the overlay div
                    let overlay = document.createElement('div');
                    overlay.id = 'iframe-overlay';
                    overlay.style.position = 'absolute';
                    overlay.style.top = '0';
                    overlay.style.left = '0';
                    overlay.style.width = '100%';
                    overlay.style.height = '100%';
                    overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
                    overlay.style.zIndex = '10';
                    overlay.style.display = 'flex';
                    overlay.style.justifyContent = 'center';
                    overlay.style.alignItems = 'center';
                    overlay.style.color = 'white';
                    overlay.style.fontSize = '3rem';

                    // Create the spinner text element and add it to the overlay
                    let spinnerText = document.createElement('span');
                    overlay.appendChild(spinnerText);

                    // Add the overlay to the iframe container
                    iframeContainer.appendChild(overlay);

                    // Animate the spinner
                    let spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];
                    let spinner_index = 0;
                    overlay.spinner_interval = setInterval(() => {
                        spinnerText.textContent = spinner_chars[spinner_index];
                        spinner_index = (spinner_index + 1) % spinner_chars.length;
                    }, 150);

                    // The overlay will be removed after 4 seconds.
                    setTimeout(() => {
                        clearInterval(overlay.spinner_interval);
                        overlay.remove();
                    }, 4000);
                ''',
                })
    )

    # for new observation blocks, the user will enter the observation block name
    observation_block_name = forms.CharField(
        label='Observation Block Name',
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter Observation Block Name'})
    )

    # 2. __init__()

    def __init__(self, *args, **kwargs):
        facility = kwargs.pop('facility', None)

        # add settings instance to Form
        if 'facility_settings' not in kwargs:
            kwargs['facility_settings'] = ESOSettings()
        self.facility_settings = kwargs.pop('facility_settings')

        super().__init__(*args, **kwargs)

        if facility is None:
            logger.warning('ESOObservationForm.__init__ called without facility context!')
            self.fields['p2_observing_run'].choices = [(0, 'No facility context - please reload page')]
            return

        # Store facility reference for use in validation
        self.facility = facility

        if facility.credential_status in [CredentialStatus.USING_USER_CREDS, CredentialStatus.USING_DEFAULTS]:
            # Get choices from facility (business logic handled there)
            observing_run_choices = facility.get_observing_run_choices()
            self.fields['p2_observing_run'].choices = observing_run_choices
        else:
            # Disable form fields until credentials are added
            for field in self.fields:
                self.fields[field].disabled = True

        # This form has a self.helper: crispy_forms.helper.FormHelper attribute.
        # It is set in the BaseRoboticObservationForm class.
        # We can use it to set attributes on the <form> tag (like htmx attributes, if necessary).
        # For the field htmx, see the widget attrs in the field definitions above.

    # 3. now the layout
    def layout(self):
        """Define the ESO-specific layout for the form.

        This method is called by the BaseObservationForm class's __init__() method as it sets up
        the crispy_forms helper.layout attribute. See the layout() stub in the BaseObservationForm class.
        """
        layout = Layout(
            # Add CSS animation for rotating spinner (keeping for any future use)
            HTML('<style>'
                 '@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }'
                 '.spinner-icon { display: inline-block; animation: spin 1s linear infinite; }'
                 '</style>'),
            Div(
                Div('p2_observing_run', css_class='col'),
                Div('p2_folder_name', css_class='col'),
                Div('observation_blocks', css_class='col'),
                css_class='form-row',
            ),

            # Add the "Create Observation Block" button
            Div(
                Div('observation_block_name', css_class='col-8'),
                Div(  # This col Div structure mirrors the Div structure of the obervation_block_name Div
                      # so that they can be on the same row and vertically aligned (by their centers)
                      # That observation_block_name Div structure is defined by crispy_forms.
                    Div(
                        HTML('<label style="visibility:hidden">I am just a vertical space holder!</label>'),
                        Div(Submit('create_observation_block', 'Create Observation Block')),
                        css_class='form-group',  # Bootstrap classes for vertical centering
                        id="div_id_observation_block_name"  # must match id of observation_block_name field Div
                    ),
                    css_class='col-4',
                ),
                css_class='form-row',
            ),

            # tom_eso/observation_form.html will add the ESO Phase2 Tool iframe here
        )
        return layout

    # 4. implement other Form methods

    def button_layout(self):
        """We override the button_layout() method in this (ESOObservationForm) class
        because Users will use the ESO P2 Tool to submit their observations requests.
        By overriding this method (and not calling super()), we remove the "Submit",
        "Validate", and "Back" buttons from the form.
        """
        target_id = self.initial.get('target_id')
        if not target_id:
            pass
            # logger.error(f'ESOObservationForm.button_layout() target_id ({target_id}) not found in initial data')
            return
        else:
            return ButtonHolder(
                HTML(f'''<a class="btn btn-outline-primary"
                 href="{{% url 'tom_targets:detail' {target_id} %}}?tab=observe">Back</a>''')
            )

    def is_valid(self):
        """Update the ChoiceField choices before validating the form. This must be done on the
        form instance that is to be validated. (The form instances in views.py is a different instance
        and it is sufficient to update it's choices for rendering the form, but not for validation.
        That must be done on the instance that is to be validated.)
        """
        # early return (of False) for things that could go wrong
        if (not hasattr(self, "facility")
            or not self.facility
            or self.facility.credential_status not in
                [CredentialStatus.USING_USER_CREDS, CredentialStatus.USING_DEFAULTS]):
            return False

        # extract values from the BoundFields (and use them to update the ChoiceField choices)
        p2_observing_run_id = int(self["p2_observing_run"].value())
        p2_folder_id = int(self["p2_folder_name"].value())
        # observation_block = int(self["observation_blocks"].value())

        # update the ChoiceField choices from the facility (no direct API calls here)
        # TODO: these should be cached and updated in the htmx views
        self["p2_folder_name"].field.choices = self.facility.get_folder_name_choices(p2_observing_run_id)
        self["observation_blocks"].field.choices = self.facility.get_observation_block_choices(p2_folder_id)

        # now that the choices are updated, we are ready to validate the form
        valid = super().is_valid()
        return valid


class ESOSettings:
    def __init__(self):
        logger.debug('ESOSettings.__init__')
        self.required_credentials = ['p2_username', 'p2_password', 'p2_environment']
        # these are the credentials that we have found via ESOFacility._configure_credentials
        self.profile_credentials = {k: None for k in self.required_credentials}

    def get_unconfigured_settings(self):
        """
        Check that the settings for this facility are present, and return list of any required settings that are blank.
        """
        # create a list of the keys that are truthy-false. (i.e. eval to False)
        unconfigured_creds = [key for key in self.profile_credentials.keys() if not self.profile_credentials[key]]

        logger.debug(f'self.configured_credentials: {self.profile_credentials}')
        logger.debug(f'self.required_credentails: {self.required_credentials}')
        logger.debug(f'unconfigured_creds: {unconfigured_creds}')

        return unconfigured_creds


class ESOFacility(BaseRoboticObservationFacility):
    name = 'ESO'

    # don't use the default template in the BaseRoboticObservationFacility b/c we want to
    # add an iframe point to the ESO P2 Tool
    template_name = 'tom_eso/observation_form.html'

    # key is the observation type, value is the form class
    observation_forms = {
        'ESO': ESOObservationForm
    }

    def __init__(self, *args, **kwargs):
        self.facility_settings = ESOSettings()
        super().__init__(*args, **kwargs)
        self.eso_api = None

    def set_user(self, user):
        """Set the user and configure ESO-specific credentials."""
        super().set_user(user)
        self._configure_credentials()

    def _configure_credentials(self):
        """
        Configure ESO-specific credentials and API client.

        This method implements the credential management use case:
        - If no ESOProfile exists, try to use settings defaults
        - If ESOProfile exists, use its credentials (even if incomplete)
        - Set configured_credentials accurately to reflect what was found

        The credential_status property tracks the current state.
        """
        logger.debug('ESOFacility._configure_credentials called...')
        if self.user is None:
            logger.warning('ESOFacility._configure_credentials called with None user!')
            self.eso_api = None
            self.credential_status = CredentialStatus.NOT_INITIALIZED  # set_user() hasn't been called yet
            return

        try:
            # Try to get user's ESOProfile
            try:
                eso_profile = ESOProfile.objects.get(user=self.user)
                # Profile exists - use its credentials (but not if incomplete)
                p2_environment = eso_profile.p2_environment
                p2_username = eso_profile.p2_username
                p2_password = get_encrypted_field(self.user, eso_profile, 'p2_password')

                # set configured_credentials to reflect what we found in ESOProfile
                self.facility_settings.profile_credentials = {
                    'p2_environment': p2_environment,
                    'p2_username': p2_username,
                    'p2_password': p2_password,
                }

                # check for missing creds in ESOProfile
                if not self.facility_settings.get_unconfigured_settings():
                    credential_status = CredentialStatus.USING_USER_CREDS
                    logger.info(f'Using ESOProfile credentials for user {self.user.username}')
                else:
                    # if there are missing creds, act like the ESOProfile doesn't exist
                    raise ESOProfile.DoesNotExist

            except ESOProfile.DoesNotExist:
                # No profile exists - try to use settings defaults
                logger.warning(f'No ESOProfile found for user {self.user.username}, trying settings defaults')
                try:
                    creds_from_settings = self._get_setting_credentials(
                        'ESO',
                        self.facility_settings.required_credentials
                    )
                    p2_environment = creds_from_settings['p2_environment']
                    p2_username = creds_from_settings['p2_username']
                    p2_password = creds_from_settings['p2_password']
                    credential_status = CredentialStatus.USING_DEFAULTS
                    logger.warning(
                        f'Using default ESO credentials from settings.FACILITIES for user {self.user.username}. '
                        f'Create/Update ESOProfile to enable user-specific credentials.'
                    )
                except Exception as ex:
                    logger.warning(f'No defaults available: {ex}')
                    self.eso_api = None
                    self.credential_status = CredentialStatus.NOT_INITIALIZED
                    return

            # Initialize API and update configured credentials
            try:
                # now, all creds should be present from ESOProfile or settings (might not be valid)
                self.eso_api = ESOAPI(p2_environment, p2_username, p2_password)
                self.credential_status = credential_status
                logger.debug(f'Successfully configured ESO API with credentials: {p2_environment}, {p2_username}')
            except Exception as api_ex:
                # Handle invalid credentials or API connection errors
                logger.error(f'Failed to initialize ESO API for user {self.user.username}: {api_ex}')
                self.eso_api = None
                self.credential_status = CredentialStatus.VALIDATION_FAILED_AUTH
                return

        except Exception as ex:
            # Unexpected errors
            logger.error(f'Unexpected exception setting up ESO API for user {self.user.username}: {ex}')
            self.eso_api = None
            self.credential_status = CredentialStatus.NOT_INITIALIZED
            raise

    def get_observing_run_choices(self):
        """Get observing run choices for the current user."""
        if (
            self.credential_status
            not in [CredentialStatus.USING_USER_CREDS, CredentialStatus.USING_DEFAULTS]
            or not self.eso_api
        ):
            return [(0, "No ESO credentials configured")]

        try:
            observing_run_choices = self.eso_api.observing_run_choices()
            if not observing_run_choices:
                return [(0, 'No observing runs available')]
            return [('', 'Please select an Observing Run')] + observing_run_choices
        except Exception as ex:
            logger.error(f'Error getting observing runs: {ex}')
            return [(0, f'Error loading observing runs: {str(ex)}')]

    def get_folder_name_choices(self, observing_run_id):
        """Get folder name choices for the given observing run."""
        if (
            self.credential_status
            not in [CredentialStatus.USING_USER_CREDS, CredentialStatus.USING_DEFAULTS]
            or not self.eso_api
        ):
            return [(0, "No ESO credentials configured")]

        try:
            return self.eso_api.folder_name_choices(observing_run_id=observing_run_id)
        except Exception as ex:
            logger.error(f'Error getting folder names: {ex}')
            return [(0, f'Error loading folders: {str(ex)}')]

    def get_observation_block_choices(self, folder_id):
        """Get observation block choices for the given folder."""
        if (
            self.credential_status
            not in [CredentialStatus.USING_USER_CREDS, CredentialStatus.USING_DEFAULTS]
            or not self.eso_api
        ):
            return [(0, "No ESO credentials configured")]

        try:
            return self.eso_api.folder_ob_choices(folder_id)
        except Exception as ex:
            logger.error(f'Error getting observation blocks: {ex}')
            return [(0, f'Error loading observation blocks: {str(ex)}')]

    def get_p2_tool_url(self,
                        observation_run_id=None,
                        container_id=None,
                        observation_block_id=None):
        """Return the URL for the ESO P2 Tool.

        The URL is constructed using the p2_environment attribute from the user's ESOProfile.
        If an observation run ID is provided, the URL will include the observing run ID.
        If an observation block ID is provided, the URL will include the observation block ID.

        ESO P2 Tool URLs look like this:
        Show Observation Run:   https://www.eso.org/p2/home/runId/<runId>
        Show Container:         https://www.eso.org/p2/home/containerId/<containerId>
        Show Observation Block: https://www.eso.org/p2/home/obId/<obID>
        Show OBlock Target tab: https://www.eso.org/p2/home/obId/<obID>/obs-description/target

        Observation Blocks take precedence over containers,
        which take precedence over an observing run.
        """
        try:
            eso_profile = ESOProfile.objects.get(user=self.user)
            if eso_profile.p2_environment == 'production':
                eso_env = ''  # url is https://www.eso.org/p2/home
            elif eso_profile.p2_environment == 'demo':
                eso_env = 'demo'  # url is https://www.eso.org/p2demo/home
            else:
                eso_env = 'demo'  # safest default
            p2_tool_url = f'https://www.eso.org/p2{eso_env}/home'
        except ESOProfile.DoesNotExist:
            p2_tool_url = ''

        # if an object ID is provided, add it to the URL
        if observation_block_id:
            p2_tool_url = f'{p2_tool_url}/ob/{observation_block_id}'
        elif container_id:
            p2_tool_url = f'{p2_tool_url}/container/{container_id}'
        elif observation_run_id:
            p2_tool_url = f'{p2_tool_url}/run/{observation_run_id}'

        return p2_tool_url

    def get_facility_context_data(self, **kwargs):
        """Allow the facility to add additional context data to the template.

        This method is called by `tom_observations.views.ObservationCreateView.get_context_data()`.
        """
        # logger.debug(f'ESOFacility.get_facility_context_data kwargs: {kwargs}')
        facility_context_data = super().get_facility_context_data(**kwargs)

        p2_tool_url = self.get_p2_tool_url()

        # logger.debug(f'ESOFacility.get_facility_context_data facility_context_data: {facility_context_data}')

        # Get ESO username from ESOProfile instead of Django username
        eso_username = 'None. Please check ESO credentials.'
        if self.user:
            if self.credential_status == CredentialStatus.USING_USER_CREDS:
                eso_profile = ESOProfile.objects.get(user=self.user)
                eso_username = eso_profile.p2_username
            elif self.credential_status == CredentialStatus.USING_DEFAULTS:
                creds_from_settings = self._get_setting_credentials(
                    'ESO',
                    self.facility_settings.required_credentials
                )
                eso_username = creds_from_settings['p2_username']

        new_context_data = {
            'version': __version__,  # from tom_eso/__init__.py
            'username': eso_username,
            'iframe_url': p2_tool_url,
            'observation_form': self.get_form(kwargs.get('observation_type')),
            'credential_status': self.credential_status,
        }
        # logger.debug(f'eso new_context_data: {new_context_data}')

        facility_context_data.update(new_context_data)
        # logger.debug(f'eso facility_context_data: {facility_context_data}')
        return facility_context_data

    def get_form(self, observation_type):
        """Return the form class for the given observation type.

        Uses the observation_forms class variable dictionary to map observation types to form classes.
        If the observation type is not found, return the ESOObservationForm class.
        """
        # use get() to return the default form class if the observation type is not found
        return self.observation_forms.get(observation_type, ESOObservationForm)

    def data_products(self, observation_id, product_id=None):
        raise NotImplementedError

    def get_observation_status(self, observation_id):
        raise NotImplementedError

    def get_observation_url(self, observation_id):
        raise NotImplementedError

    def get_observing_sites(self):  # type: ignore - base class method return None, which it should not
        # see https://www.eso.org/sci/facilities/paranal/astroclimate/site.html#GeoInfo
        # I don't see an API for this info, so it's hardcoded
        # TODO: get data for all the ESO sites for production
        return {
            'PARANAL': {
                'sitecode': 'paranal',
                'latitude': -24.62733,   # 24 degrees 40' S
                'longitude': -70.40417,  # 70 degrees 25' W
                'elevation': 2635.43,    # meters
            },
            'LA_SILLA': {
                'sitecode': 'lasilla',
                'latitude': -29.25667,
                'longitude': -70.73194,
                'elevation': 2400.0,  # meters
            },
        }

    def get_terminal_observing_states(self):
        pass

    def submit_new_observation_block(self, observation_payload):
        """
        This is called when the user clicks the Create Observation Block button.

        TODO: this fuction needs error checking.
        """
        logger.debug(f'ESOFacility.submit_new_observation_block observation_payload: {observation_payload}')
        target_id = observation_payload['target_id']
        target = Target.objects.get(pk=target_id)

        # without the user and their creds in the ESOProfile we cannot access to the p2api
        if self.user is None:
            logger.error('Cannot submist new observation block without user: {self.user}')
            return  # so early return

        try:
            eso_profile = ESOProfile.objects.get(user=self.user)
            decrypted_p2_password = get_encrypted_field(self.user, eso_profile, 'p2_password')
            eso = ESOAPI(eso_profile.p2_environment, eso_profile.p2_username, decrypted_p2_password)
            new_observation_block = eso.create_observation_block(
                folder_id=observation_payload['params']['p2_folder_name'],
                ob_name=observation_payload['params']['observation_block_name'],
                target=target
            )
            # TODO: redirect with new observation block id in the ESO P2 Tool iframe
            logger.debug(f'ESOFacility.submit_new_observation_block new_observation_block: {new_observation_block}')
        except ESOProfile.DoesNotExist:
            # Handle the case where the user has no ESOProfile
            logger.error(f'User {self.user} has no ESOProfile')

    def submit_observation(self, observation_payload):
        """For the ESO Facility we're limited to creating new observation blocks for
        the User to then go to the ESO Phase2 Tool to modify and submit from there.

        For now, the Create Observation Block button routes to here and we call the
        ESOAPI.create_observation_block() method to create the new observation block.

        TODO: we should probably not be overriding this method to accomplish this!!!
        """
        # this method is really just an adaptor to call submit_new_observation_block()
        self.submit_new_observation_block(observation_payload)

        created_observation_ids = []
        return created_observation_ids

    def validate_observation(self):
        pass
