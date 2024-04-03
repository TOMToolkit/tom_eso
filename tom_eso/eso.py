import logging

from crispy_forms.layout import Layout, Div, Field
from crispy_forms.bootstrap import Accordion, AccordionGroup
from django.conf import settings
from django import forms
from django.utils.safestring import mark_safe

from tom_observations.facility import BaseRoboticObservationForm, BaseRoboticObservationFacility, get_service_class
from tom_targets.models import Target

from tom_eso import __version__

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ESOObservationForm(BaseRoboticObservationForm):
    pass
    p1_observing_run = forms.ChoiceField(
        label='Observing Run',
        # TODO: populate from ESO API
        choices=[('choice_value_1', 'choice_label_1'),
                 ('choice_value_2', 'choice_label_2')],
        required=False,
    )

    def layout(self):
        layout = Layout(
            'p1_observing_run'
        )
        return layout


class ESOFacility(BaseRoboticObservationFacility):
    name = 'ESO'

    # TODO: try this, too: observation_form = ESOObservationForm
    observation_forms = {
        'XSHOOTER': ESOObservationForm
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_facility_context_data(self, **kwargs):
        facility_context_data = super().get_facility_context_data(**kwargs)

        new_context_data = {
            'version': __version__,  # from tom_eso/__init__.py
            'username': settings.FACILITIES['ESO']['username'],
        }

        facility_context_data.update(new_context_data)
        return facility_context_data

    def get_form(self, observation_type):
        logger.debug(f'ESOFacility.get_form() called for observation_type={observation_type}')
        return ESOObservationForm
        #return self.observation_forms.get(observation_type, ESOObservationForm)

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