import logging

from crispy_forms.layout import Layout, HTML

from django.conf import settings
from django.urls import reverse_lazy
from django import forms

# import django_htmx

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
            attrs={
                'hx-get': reverse_lazy('observing-run-folders'),  # send GET request to this URL
                # (the view for this endpoint returns folder names for the selected observing run)
                'hx-trigger': 'change, load',  # when this happens
                'hx-target': '#div_id_p2_folder_name',  # replace p2_folder_name div
            })
    )

    p2_folder_name = forms.ChoiceField(
        label='Folder Name',
        required=False,
        # these choices will be updated when the p2_observing_run field is changed
        # as specified by the htmx attributes on the p2_observing_run's <select> element
        choices=[(0, 'Please select an Observing Run')],
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
        # TODO: upon loading, initialize the folders to whatever is present in the observing run
        self['p2_observing_run'].initial = (60929601, '60.A-9296(B) - VISTA - QMOST')

    # 3. now the layout

    def layout(self):
        layout = Layout(
            'p2_observing_run',
            'p2_folder_name',
            HTML('<hr><p>More Field widgets here</p><hr>'),
        )
        return layout

    # 4. implement other Form methods


class ESOFacility(BaseRoboticObservationFacility):
    name = 'ESO'

    # key is the observation type, value is the form class
    observation_forms = {
        'XSHOOTER': ESOObservationForm
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.eso = ESOAPI()

    def get_facility_context_data(self, **kwargs):
        facility_context_data = super().get_facility_context_data(**kwargs)

        new_context_data = {
            'version': __version__,  # from tom_eso/__init__.py
            'username': settings.FACILITIES['ESO']['username'],
        }

        facility_context_data.update(new_context_data)
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

    def submit_observation(self):
        pass

    def validate_observation(self):
        pass
