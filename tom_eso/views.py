import logging
# from django.shortcuts import render
from django.http import HttpResponse

from crispy_forms.templatetags.crispy_forms_filters import as_crispy_field

from tom_eso.eso import ESOObservationForm

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def observing_run(request):
    """Function view for the htmx GET request to update the observing run field.

    When the observing run is chosen, this should probabaly
    replace the hx-target #div_id_p2_folder_name with a ChoiceField
    populated with the folder names for the selected observing run.

    The 'p2_observing_run' is passed as a URL parameter and is thus
    available from the request.GET QueryDict.
    """
    logger.debug(f"observing_run: {request.GET['p2_observing_run']}")

    form = ESOObservationForm(request.GET)
    # the hx-target is the id of the div containing the field
    # so replace it with the field itself to maintain the <select> element <options>
    field = as_crispy_field(form['p2_observing_run'])

    # also should return the folder names for the selected observing run
    # so that the user can choose a folder name
    # TODO: not sure how to do this yet...
    return HttpResponse(field)
