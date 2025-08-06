import logging

# from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy

from crispy_forms.templatetags.crispy_forms_filters import as_crispy_field

from tom_eso.eso_api import ESOAPI
from tom_eso.eso import ESOObservationForm, ESOFacility
from tom_eso.models import ESOProfile
from tom_eso.forms import ESOProfileForm
from tom_common.session_utils import get_encrypted_field


logger = logging.getLogger(__name__)


def folders_for_observing_run(request):
    """Return an HTTPResponse which updates the Folder choices for the selected Observing Run.

    Calls to this View are triggered by a change of the ``p2_observing_run`` ChoiceField,
    as specified by the htmx attributes on its <select> element. See the ESOFacility,
    where that ChoiceField is defined.

    The ``p2_folder_name`` ChoiceField's ``choices`` are updated with the folder names
    for the selected Observing Run.  and the <select> element is returned as an
    <select> HTML element. Function view for the htmx GET request to update the observing run field.

    The ``observing_run_id`` of the selected ``p2_observing_run`` is passed as a URL
    parameter and is thus available from the request.GET QueryDict.
    """
    # Validate that we have the required GET parameter
    if 'p2_observing_run' not in request.GET:
        logger.error(f'Missing p2_observing_run parameter in request: {request.GET}')
        # Return empty choices if parameter is missing
        form = ESOObservationForm(user=request.user)  # use request.user instead of None
        field_html = as_crispy_field(form['p2_folder_name'])
        return HttpResponse(field_html)

    try:
        # extract the observing run id from the request.GET QueryDict
        observing_run_id = int(request.GET['p2_observing_run'])
        # Skip processing if it's the default "Please select" value
        if observing_run_id == 0:
            form = ESOObservationForm(user=request.user)
            field_html = as_crispy_field(form['p2_folder_name'])
            return HttpResponse(field_html)
    except (ValueError, TypeError):
        logger.error(f'Invalid p2_observing_run value: {request.GET.get("p2_observing_run")}')
        # Return empty choices if parameter is invalid
        form = ESOObservationForm(user=request.user)
        field_html = as_crispy_field(form['p2_folder_name'])
        return HttpResponse(field_html)

    # Get user-specific ESOAPI instance
    try:
        eso_profile = ESOProfile.objects.get(user=request.user)
        p2_environment = eso_profile.p2_environment
        p2_username = eso_profile.p2_username
        p2_password = get_encrypted_field(request.user, eso_profile, 'p2_password')

        eso_api = ESOAPI(p2_environment, p2_username, p2_password)

        # Get the folder name choices for the selected observing run
        # NOTE: this is a potentially slow API call
        # TODO: consider caching the results
        folder_name_choices = eso_api.folder_name_choices(observing_run_id)

    except ESOProfile.DoesNotExist:
        logger.error(f'User {request.user} has no ESOProfile')
        folder_name_choices = [(0, 'ESO credentials not configured')]
    except Exception as ex:
        logger.error(f'Error getting folder choices: {ex}')
        folder_name_choices = [(0, 'Error loading folders')]

    form = ESOObservationForm(user=request.user)  # instantiate the UNBOUND form with user context
    form.fields['p2_folder_name'].choices = folder_name_choices  # update the choices of the UNBOUND form

    # get the HTML for the updated ChoiceField that will update the p2_folder_name in the DOM
    field_html = as_crispy_field(form['p2_folder_name'])
    return HttpResponse(field_html)


def observation_blocks_for_folder(request):
    """Return an HTTPResponse which updates the Observation Blocks choices for the selected Folder.

    Calls to this View are triggered by a change of the ``p2_folder_name`` ChoiceField,
    as specified by the htmx attributes on its <select> element. See the ESOFacility,
    where that ChoiceField is defined.

    The ``folder_items`` MultipleChoiceField's ``choices`` are updated with the folder items
    for the selected Folder, and the <select> element is returned as an <select> HTML element.
    """
    # Validate that we have the required GET parameter
    if 'p2_folder_name' not in request.GET:
        logger.error(f'Missing p2_folder_name parameter in request: {request.GET}')
        # Return empty choices if parameter is missing
        form = ESOObservationForm(user=request.user)
        field_html = as_crispy_field(form['observation_blocks'])
        return HttpResponse(field_html)

    # extract the folder id from the request.GET QueryDict
    try:
        folder_id = int(request.GET['p2_folder_name'])
    except (ValueError, TypeError):
        logger.error(f'folder_id is not an integer: {request.GET["p2_folder_name"]}')
        for key, value in request.GET.items():
            logger.error(f'{key}: {value}')
        # Return empty choices if parameter is invalid
        form = ESOObservationForm(user=request.user)
        field_html = as_crispy_field(form['observation_blocks'])
        return HttpResponse(field_html)

    # Get user-specific ESOAPI instance
    try:
        eso_profile = ESOProfile.objects.get(user=request.user)
        p2_environment = eso_profile.p2_environment
        p2_username = eso_profile.p2_username
        p2_password = get_encrypted_field(request.user, eso_profile, 'p2_password')
        eso_api = ESOAPI(p2_environment, p2_username, p2_password)

        # Get the observation_blocks in the selected folder
        observation_block_choices = eso_api.folder_ob_choices(folder_id)

    except ESOProfile.DoesNotExist:
        logger.error(f'User {request.user} has no ESOProfile')
        observation_block_choices = [(0, 'ESO credentials not configured')]
    except Exception as ex:
        logger.error(f'Error getting observation block choices: {ex}')
        observation_block_choices = [(0, 'Error loading observation blocks')]

    form = ESOObservationForm(user=request.user)  # instantiate the UNBOUND form with user context
    form.fields['observation_blocks'].choices = observation_block_choices  # update the choices of the UNBOUND form

    # now render the field as HTML and return it in the HTTPResponse
    field_html = as_crispy_field(form['observation_blocks'])
    return HttpResponse(field_html)


def show_observation_block(request):
    """When an observation block is selected, this View updates the ESO P2 tool iframe
    to show the selected observation block.
    """
    # Validate that we have the required GET parameter
    if 'observation_blocks' not in request.GET:
        logger.error(f'Missing observation_blocks parameter in request: {request.GET}')
        # Return empty iframe if parameter is missing
        html = '<iframe id="id_eso_p2_tool_iframe" height="100%" width="100%" src="about:blank"></iframe>'
        return HttpResponse(html)

    # 1. extract the observation block id from the request.GET QueryDict
    # (this is the value associated with the choice in the MultipleChoiceField.choices)
    try:
        observation_block_id = int(request.GET['observation_blocks'])
    except (ValueError, TypeError):
        logger.error(f'ob_id is not an integer: {request.GET["observation_blocks"]}')
        for key, value in request.GET.items():
            logger.error(f'{key}: {value}')
        # Return error iframe if parameter is invalid
        html = '<iframe id="id_eso_p2_tool_iframe" height="100%" width="100%" src="about:blank"></iframe>'
        return HttpResponse(html)

    # get the ESO P2 tool URL for this observation block
    # Create facility instance with user context
    facility = ESOFacility()
    facility.set_user(request.user)
    iframe_url = facility.get_p2_tool_url(observation_block_id=observation_block_id)

    # return just the iframe element with the new URL
    html = f'<iframe id="id_eso_p2_tool_iframe" height="100%" width="100%" src="{iframe_url}"></iframe>'
    return HttpResponse(html)


class ProfileUpdateView(UpdateView):
    """
    View that handles updating of a user's ``ESOProfile``.

    The ESO Facility has an ``ESOProfile`` model (see ``models.py``). This view updates
    the properties of that model.

    The ``ESOProfile`` properties are displayed by the ``eso_user_profile.html`` template.
    This typically happens on the on the User Profile page via the ``show_app_profiles``
    inclusion tag (see ``tom_base/tom_common/templates/tom_common/user_profile.html`` and
    ``tom_base/tom_common/templatetags/user_extras.py::show_app_profiles``).
    """
    model = ESOProfile
    template_name = 'tom_eso/eso_update_user_profile.html'

    # we need a custom form class to handle the encrypted field
    form_class = ESOProfileForm

    def get_form_kwargs(self):
        """Extend the UpdateView.get_form_kwargs to pass the logged-in User to the form
        """
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse_lazy('user-profile')
