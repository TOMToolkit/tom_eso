import logging

from crispy_forms.layout import Layout, HTML, Fieldset, Submit, ButtonHolder, Div

from django.conf import settings
from django.urls import reverse_lazy
from django import forms

from tom_observations.facility import BaseRoboticObservationForm, BaseRoboticObservationFacility
from tom_eso import __version__
from tom_eso.eso_api import ESOAPI


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ESOObservationForm(BaseRoboticObservationForm):

    # 1. define the form fields,
    # 2. the define the __init__ below
    # 3. then the layout
    # 4. implement other Fomrm methods

    # 1. Form fields

    p2_observing_run = forms.ChoiceField(
        label='Observing Run',
        choices=ESOAPI().observing_run_choices,  # callable to populate choices
        required=True,
        # Select is the default widget for a ChoiceField, but we need to set htmx attributes.
        widget=forms.Select(
            # set up attributes to trigger folder dropdown update when this field changes
            attrs={
                'hx-get': reverse_lazy('observing-run-folders'),  # send GET request to this URL
                # (the view for this endpoint returns folder names for the selected observing run)
                'hx-trigger': 'change, load',  # when this happens
                'hx-target': '#div_id_p2_folder_name',  # replace p2_folder_name div
                'hx-indicator': '#spinner',  # show spinner while waiting for response
                # 'hx-indicator': '#div_id_p2_folder_name',  # show spinner while waiting for response
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
                'hx-get': reverse_lazy('folder-observation-blocks'),  # send GET request to this URL
                # (the view for this endpoint returns items for the selected folder)
                'hx-trigger': 'change, load',  # when this happens
                'hx-target': '#div_id_observation_blocks',  # replace HTML element with this id
                'hx-indicator': '#spinner',  # show spinner while waiting for response
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
                # iframe is updated with the ESO P2 Tool page for that observation block
                'hx-get': reverse_lazy('show-observation-block'),  # send GET request to this URL
                # (the view for this endpoint returns folder items for the selected folder)
                'hx-trigger': 'change, load',  # when this happens
                'hx-indicator': '#spinner',  # show spinner while waiting for response
                'hx-target': '#div_id_eso_p2_tool_iframe',  # replace this div
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
        super().__init__(*args, **kwargs)
        self.eso = ESOAPI()

        # This form has a self.helper: crispy_forms.helper.FormHelper attribute.
        # It is set in the BaseRoboticObservationForm class.
        # We can use it to set attributes on the <form> tag (like htmx attributes, if necessary).
        # For the field htmx, see the widget attrs in the field definitions above.

        # for testing purposes, set the initial values for the observing run
        self['p2_observing_run'].initial = (60925315, '60.A-9253(P) - UT2 - XSHOOTER')
        # intialize to this so we can switch to the XSHOOTER observing run (for now)
        self['p2_observing_run'].initial = (60929601, '60.A-9296(B) - VISTA - QMOST')

    # 3. now the layout
    def _get_spinner_image(self):
        image = 'bluespinner.gif'
        return f'{{% static "tom_common/img/{image}" %}}'

    def layout(self):
        """Define the ESO-specific layout for the form.

        This method is called by the BaseObservationForm class's __init__() method as it sets up
        the crispy_forms helper.layout attribute. See the layout() stub in the BaseObservationForm class.
        """
        spinner_size = 20
        layout = Layout(
            # the spinner is displayed only while waiting for the response from the ESO P2 API
            # TODO: make the spinner more obvious
            HTML((f"{{% load static %}} <img id='spinner' class='htmx-indicator'"
                  f"width='{spinner_size}' height='{spinner_size}'"
                  f"src={self._get_spinner_image()}></img>")),
            Div(
                Div('p2_observing_run', css_class='col'),
                Div('p2_folder_name', css_class='col'),
                Div('observation_blocks', css_class='col'),
                css_class='form-row',
            ),

            # Add the "Create Observation Block" button
            Div(
                Div('observation_block_name', css_class='col-8'),
                Div(  # this col Div structure mirrors the Div structure of the obervation_block_name Div
                      # so that they can be on the same row and vertically aligned (by their centers)
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
        logger.debug(f'ESOObservationForm.button_layout() target_id: {target_id}')
        return ButtonHolder(
            HTML(f'''<a class="btn btn-outline-primary"
             href="{{% url 'tom_targets:detail' {target_id} %}}?tab=observe">Back</a>''')
        )
        return

    def is_valid(self):
        valid = super().is_valid()

        observation_blocks_choice_field = self.fields['observation_blocks']
        logger.debug(f'ESOObservationForm.is_valid() choices: {observation_blocks_choice_field.choices}')

        logger.debug(f'ESOObservationForm.is_valid() valid: {valid}')

        return valid


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
        super().__init__(*args, **kwargs)
        self.eso = ESOAPI()

    @classmethod
    def get_p2_tool_url(self,
                        observation_run_id=None,
                        container_id=None,
                        observation_block_id=None):
        """Return the URL for the ESO P2 Tool.

        The URL is constructed using the ESO_ENVIRONMENT from settings.
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
        # construct the base p2_tool_url using the ESO_ENVIRONMENT from settings
        if settings.FACILITIES['ESO']['environment'] == 'production':
            eso_env = ''  # url is https://www.eso.org/p2/home
        elif settings.FACILITIES['ESO']['environment'] == 'demo':
            eso_env = 'demo'  # url is https://www.eso.org/p2demo/home
        else:
            eso_env = 'demo'  # safest default
        p2_tool_url = f'https://www.eso.org/p2{eso_env}/home'

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
        logger.debug(f'ESOFacility.get_facility_context_data kwargs: {kwargs}')
        facility_context_data = super().get_facility_context_data(**kwargs)

        p2_tool_url = self.get_p2_tool_url()

        logger.debug(f'ESOFacility.get_facility_context_data facility_context_data: {facility_context_data}')
        new_context_data = {
            'version': __version__,  # from tom_eso/__init__.py
            'username': settings.FACILITIES['ESO']['username'],
            'iframe_url': p2_tool_url,
            'observation_form': ESOObservationForm,
        }
        logger.debug(f'eso new_context_data: {new_context_data}')

        facility_context_data.update(new_context_data)
        logger.debug(f'eso facility_context_data: {facility_context_data}')
        return facility_context_data

    def get_form(self, observation_type):
        """Return the form class for the given observation type.

        Uses the observation_forms class varialble dictionary to map observation types to form classes.
        If the obsevation type is not found, return the ESOboservationForm class
        """
        # use get() to return the default form class if the observation type is not found
        return self.observation_forms.get(observation_type, ESOObservationForm)

    def data_products(self):
        pass

    def get_observation_status():
        pass

    def get_observation_url(self):
        pass

    def get_observing_sites(self):
        # see https://www.eso.org/sci/facilities/paranal/astroclimate/site.html#GeoInfo
        # I don't see an API for this info, so it's hardcoded
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
        """
        logger.debug(f'ESOFacility.submit_new_observation_block observation_payload: {observation_payload}')

    def submit_observation(self, observation_payload):
        """For the ESO Facility we're limited to creating new observation blocks for
        the User to then go to the ESO Phase2 Tool to modify and submit from there

        For now, the Create Observation Block button routes to here and we call the
        ESOAPI.create_observation_block() method to create the new observation block.
        """
        logger.debug(f'ESOFacility.submit_observation observation_payload: {observation_payload}')

        self.submit_new_observation_block(observation_payload)

        created_observation_ids = []
        return created_observation_ids

    def validate_observation(self):
        pass
