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
