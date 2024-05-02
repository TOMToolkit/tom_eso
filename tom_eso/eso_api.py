import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

import p1api
import p2api  # these are the ESO APIs for phase1 and phase2

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ESOAPI(object):
    """Lazily instanciated singleton to hold ESO p1 and p2 ApiConnections.

    Background reading about the implementation of this singleton:
    https://python-3-patterns-idioms-test.readthedocs.io/en/latest/Singleton.html#the-singleton
    """
    class __ESOAPI:
        """This is the access-restricted inner class where everything happens.

        The outer class below handles lazy instanciation and delegates everything
        else to this inner class via __{get,set}attr__ methods.
        """
        def __init__(self):
            try:
                self.environment = settings.FACILITIES['ESO']['environment']
                self.username = settings.FACILITIES['ESO']['username'],
                self.password = settings.FACILITIES['ESO']['password']
            except KeyError as e:
                raise ImproperlyConfigured(f'ESO not found in settings.FACILITIES: {e}')

            self.api1 = p1api.ApiConnection(self.environment, self.username, self.password)
            self.api2 = p2api.ApiConnection(self.environment, self.username, self.password)

        def observing_run_choices(self):
            """Return a list of tuples for the ESO Phase 2 observing runs available to the user.

            Uses ESO Phase2 API method `getRuns()` to get the observing runs, and creates
            the list of form.ChoiceField tuples from the result.
            """
            # TODO: this and other methods should be cached
            observing_runs, _ = self.api2.getRuns()
            return [(run['runId'], f"{run['progId']} - {run['telescope']} - {run['instrument']}")
                    for run in observing_runs]

        def folder_name_choices(self, observing_run_id):
            """Return a list of tuples for the ESO Phase 2 folder names available to the user.

            Uses ESO Phase2 API method `getItems()` for the ObservingRun's continer_id
            to get the items and filters on itemType to select Folders.
            Creates the list of form.ChoiceField tuples from the result.
            """
            observing_run, _ = self.api2.getRun(observing_run_id)
            # logger.debug(f'observing_run: {observing_run}')
            container_id = observing_run['containerId']

            items_in_run_container, _ = self.api2.getItems(container_id)
            # logger.debug(f'items: {items_in_run_container}')

            folder_name_choices = [(folder['containerId'], folder['name'])
                                   for folder in items_in_run_container if folder['itemType'] == 'Folder']
            # logger.debug(f'folder_choices: {folder_name_choices}')
            return folder_name_choices

    # Don't do anything else below here: it should all be handled by the inner class above.
    # Everything below just handles lazy instanciation and delegation to the inner class.
    _instance = None

    def __new__(cls):
        if not ESOAPI._instance:
            # there's no instance yet so make the singleton instance
            ESOAPI._instance = ESOAPI.__ESOAPI()
        return ESOAPI._instance

    def __getattr__(self, name):
        return getattr(self._instance, name)

    def __setattr__(self, name):
        return setattr(self._instance, name)
