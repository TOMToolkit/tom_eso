import logging

# from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy

from crispy_forms.templatetags.crispy_forms_filters import as_crispy_field

from tom_eso.eso import ESOObservationForm, ESOFacility
from tom_eso.models import ESOProfile
from tom_eso.forms import ESOProfileForm


logger = logging.getLogger(__name__)


def folders_for_observing_run(request):
    """
    HTMX endpoint that updates folder choices when an observing run is selected.

    HTMX PATTERN EXPLANATION:
    ========================
    This is an HTMX "partial view" that returns HTML fragments, not full pages.

    1. USER INTERACTION: User selects an observing run from dropdown
    2. HTMX TRIGGER: Form field has hx-get="/eso/observing-run-folders/" attribute
    3. THIS VIEW: Processes the request and returns updated HTML for folder dropdown
    4. HTMX SWAP: Replaces the folder dropdown in the DOM with the returned HTML

    DJANGO FORM RENDERING:
    =====================
    We create an unbound Django form solely for field rendering purposes:
    - Form validation is NOT needed (this is just for display)
    - We manually populate the choices based on external API data
    - as_crispy_field() renders the field as Bootstrap-styled HTML
    - The HTML fragment is returned and inserted into the DOM by HTMX

    FACILITY PATTERN:
    ================
    Instead of duplicating credential logic, we use the facility to handle
    business concerns (API setup, credential management) while the view
    handles only presentation concerns (form rendering, HTTP responses).

    :param request: HTTP request with p2_observing_run parameter
    :return: HTTPResponse containing HTML for updated folder dropdown
    """
    # Validate required GET parameter
    if 'p2_observing_run' not in request.GET:
        logger.error(f'Missing p2_observing_run parameter in request: {request.GET}')
        # Return empty choices with facility context
        facility = ESOFacility()
        facility.set_user(request.user)
        form = ESOObservationForm(facility=facility)
        field_html = as_crispy_field(form['p2_folder_name'])
        return HttpResponse(field_html)

    try:
        # Extract and validate observing run ID
        observing_run_id = int(request.GET['p2_observing_run'])
        # Skip processing if it's the default "Please select" value
        if observing_run_id == 0:
            facility = ESOFacility()
            facility.set_user(request.user)
            form = ESOObservationForm(facility=facility)
            field_html = as_crispy_field(form['p2_folder_name'])
            return HttpResponse(field_html)
    except (ValueError, TypeError):
        logger.error(f'Invalid p2_observing_run value: {request.GET.get("p2_observing_run")}')
        facility = ESOFacility()
        facility.set_user(request.user)
        form = ESOObservationForm(facility=facility)
        field_html = as_crispy_field(form['p2_folder_name'])
        return HttpResponse(field_html)

    # Use facility to get folder choices (eliminates credential duplication)
    facility = ESOFacility()
    facility.set_user(request.user)
    folder_name_choices = facility.get_folder_name_choices(observing_run_id)

    # Create form with facility context and update choices
    form = ESOObservationForm(facility=facility)
    form.fields['p2_folder_name'].choices = folder_name_choices

    # Render field as HTML fragment for HTMX swap
    field_html = as_crispy_field(form['p2_folder_name'])
    return HttpResponse(field_html)


def observation_blocks_for_folder(request):
    """
    HTMX endpoint that updates observation block choices when a folder is selected.

    This follows the same pattern as folders_for_observing_run():
    1. User selects a folder from the p2_folder_name dropdown
    2. HTMX sends GET request with folder ID to this endpoint
    3. View uses facility to get observation blocks for that folder
    4. Returns HTML fragment for the observation_blocks dropdown
    5. HTMX replaces the observation blocks dropdown in the DOM

    The facility pattern eliminates credential duplication - all ESO API setup
    and authentication is handled by ESOFacility.set_user().

    :param request: HTTP request with p2_folder_name parameter
    :return: HTTPResponse containing HTML for updated observation blocks dropdown
    """
    # Validate required GET parameter
    if 'p2_folder_name' not in request.GET:
        logger.error(f'Missing p2_folder_name parameter in request: {request.GET}')
        facility = ESOFacility()
        facility.set_user(request.user)
        form = ESOObservationForm(facility=facility)
        field_html = as_crispy_field(form['observation_blocks'])
        return HttpResponse(field_html)

    try:
        # Extract and validate folder ID
        folder_id = int(request.GET['p2_folder_name'])
    except (ValueError, TypeError):
        logger.error(f'folder_id is not an integer: {request.GET["p2_folder_name"]}')
        for key, value in request.GET.items():
            logger.error(f'{key}: {value}')
        facility = ESOFacility()
        facility.set_user(request.user)
        form = ESOObservationForm(facility=facility)
        field_html = as_crispy_field(form['observation_blocks'])
        return HttpResponse(field_html)

    # Use facility to get observation block choices
    facility = ESOFacility()
    facility.set_user(request.user)
    observation_block_choices = facility.get_observation_block_choices(folder_id)

    # Create form with facility context and update choices
    form = ESOObservationForm(facility=facility)
    form.fields['observation_blocks'].choices = observation_block_choices

    # Render field as HTML fragment for HTMX swap
    field_html = as_crispy_field(form['observation_blocks'])
    return HttpResponse(field_html)


def show_observation_block(request):
    """
    HTMX endpoint that updates the ESO P2 Tool iframe when an observation block is selected.

    This is a third type of HTMX interaction - instead of updating form fields,
    it updates an iframe's src attribute to show the selected observation block
    in the ESO Phase 2 Tool.

    HTMX IFRAME PATTERN:
    ===================
    1. User selects an observation block from dropdown
    2. HTMX sends GET request with observation block ID
    3. View constructs ESO P2 Tool URL for that observation block
    4. Returns complete <iframe> element with new src URL
    5. HTMX replaces the entire iframe element (hx-swap="outerHTML")

    This demonstrates facility usage for business logic (URL construction)
    while keeping the view focused on presentation (HTML generation).

    :param request: HTTP request with observation_blocks parameter
    :return: HTTPResponse containing iframe HTML element
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
