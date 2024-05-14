import logging
# from django.shortcuts import render
from django.http import HttpResponse

from crispy_forms.templatetags.crispy_forms_filters import as_crispy_field

from tom_eso.eso_api import ESOAPI
from tom_eso.eso import ESOObservationForm

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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
    # extract the observing run id from the request.GET QueryDict
    observing_run_id = int(request.GET['p2_observing_run'])
    # logger.debug(f'observing_run_id: {observing_run_id}')

    # Get the folder name choices for the selected observing run
    # NOTE: this is a potentially slow API call
    # TODO: considing caching the results
    folder_name_choices = ESOAPI().folder_name_choices(observing_run_id)

    # Update the choices for the p2_folder_name field
    form = ESOObservationForm(request.GET)  # populate the form with the request data
    field = form['p2_folder_name']
    field.field.choices = folder_name_choices

    # get the HTML for the updated ChoiceField that will update the p2_folder_name in the DOM
    field_html = as_crispy_field(form['p2_folder_name'])
    return HttpResponse(field_html)


def items_for_folder(request):
    """Return an HTTPResponse which updates the Folder Items choices for the selected Folder.

    Calls to this View are triggered by a change of the ``p2_folder_name`` ChoiceField,
    as specified by the htmx attributes on its <select> element. See the ESOFacility,
    where that ChoiceField is defined.

    The ``folder_items`` MultipleChoiceField's ``choices`` are updated with the folder items
    for the selected Folder, and the <select> element is returned as an <select> HTML element.
    """
    # extract the folder id from the request.GET QueryDict
    try:
        folder_id = int(request.GET['p2_folder_name'])
    except ValueError as e:
        logger.error(f'folder_id is not an integer: {request.GET["p2_folder_name"]}')
        for key, value in request.GET.items():
            logger.error(f'{key}: {value}')
        folder_id = 0
        raise e  # re-raise the exception
    # logger.debug(f'folder_id: {folder_id}')

    # Get the folder items for the selected folder
    item_choices = ESOAPI().folder_item_choices(folder_id)

    form = ESOObservationForm(request.GET)  # populate the form with the request data
    field = form['folder_items']
    field.field.choices = item_choices

    field_html = as_crispy_field(form['folder_items'])
    return HttpResponse(field_html)