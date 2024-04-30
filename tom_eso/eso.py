import logging

from crispy_forms.layout import Layout, HTML  # Div, Field

from django.conf import settings
from django.urls import reverse_lazy
from django import forms
import django_htmx

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

    htmx_test = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                'hx-get': reverse_lazy('home'),  # send GET request to this URL
                'hx-trigger': 'keyup',  # when this happens
            }))

    p2_observing_run = forms.ChoiceField(
        label='Observing Run',
        choices=ESOAPI().observing_run_choices,  # callable to populate choices
        required=True,
        #initial=(60925315, '60.A-9253(P) - UT2 - XSHOOTER'),

        # Select is the default widget for a ChoiceField, but we need to set htmx attributes.
        widget=forms.Select(
            attrs={
                'hx-get': reverse_lazy('observing-run'),  # send GET request to this URL
                'hx-trigger': 'change',  # when this happens
                'hx-target': '#div_id_p2_observing_run',  # update this field
            })
    )

    p2_folder_name = forms.ChoiceField(
        label='Folder Name',
        required=True,
        widget=forms.Select(
            attrs={
                'hx-get': reverse_lazy('home'),  # send GET request to this URL
                'hx-trigger': 'change',  # when this happens
            })
    )

    # 2. __init__()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.eso = ESOAPI()

        # This form has a self.helper: crispy_forms.helper.FormHelper attribute.
        # It is set in the BaseRoboticObservationForm class.
        # We can use it to set attributes on the <form> tag.
        # This is how we specify the forms htmx hx-XXXX attributes.
        # (For the form fields, see the widget attrs in the field definitions above).

        # for testing purposes, set the initial values for the observing run
        self['p2_observing_run'].initial = (60925315, '60.A-9253(P) - UT2 - XSHOOTER')
        #self['p2_observing_run'].initial = (60929601, '60.A-9296(B) - VISTA - QMOST')

    # 3. now the layout

    def layout(self):
        layout = Layout(
            'htmx_test',  # this is a test field to see if htmx is working
            'p2_observing_run',
            'p2_folder_name',
            HTML('<hr><p>More Field wigdets here</p><hr>'),
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
