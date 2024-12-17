import logging

from astropy.coordinates import Angle
from astropy import units as u

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

        def create_observation_block(self, folder_id, ob_name, target=None):
            """Create a new Observation Block in the specified folder. Return the new OB's id.
            If a Target is specified, add it to the OB.

            """
            logger.debug(f'create_observation_block: folder_id: {folder_id}, ob_name: {ob_name}, target: {target}')

            new_ob_id = self.api2.createOB(folder_id, ob_name)
            logger.debug(f'create_observation_block: new_ob_id: {new_ob_id}')

            if target:
                # add the target data to the new OB by modifying the OB JSON
                new_OB['target']['name'] = target.name

                # For ESO P2 API, the RA and Dec have specific formats:
                # RA: Valid format is HH:MM:SS.sss, with 0 <= HH <= 23, 0 <= MM < 60 and 0 <= SS < 60.]
                # Dec: Valid format is [+|-]DD:MM:SS.sss, with -90 <= DD <= 90, 0 <= MM < 60 and 0 <= SS < 60.]
                new_OB['target']['ra'] = Angle(target.ra, unit=u.deg).to_string(unit=u.hourangle, sep=':', precision=3)
                new_OB['target']['dec'] = Angle(target.dec, unit=u.deg).to_string(unit=u.deg, sep=':', precision=3,
                                                                                  alwayssign=True)


                logger.debug(f'Saving {target} to new observation_block: ob: {ob}')

                self.api2.saveOB(new_ob_id, ob, ob_version)

            return new_ob_id

        def observing_run_choices(self):
            """Return a list of tuples for the ESO Phase 2 observing runs available to the user.

            Uses ESO Phase2 API method `getRuns()` to get the observing runs, and creates
            the list of form.ChoiceField tuples from the result.
            """
            # TODO: this and other methods should be cached

            OBS_RUN_BLACK_LIST = [60925302, 60925303]
            try:
                observing_runs, _ = self.api2.getRuns()
            except KeyError as e:
                logger.debug(f'observing_run_choices: api2.getRuns(): oberseving_runs: {observing_runs}')
                logger.error(f'API Error: {e}')
                return [(0, 'Are there any observing runs?')]

            # logger.debug(f'for example, observing_runs[0]: {observing_runs[0]}')
            return [(run['runId'], f"{run['progId']} - {run['telescope']} - {run['instrument']}")
                    for run in observing_runs if not int(run['runId']) in OBS_RUN_BLACK_LIST]

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

            # NOTE: here we know id is containerId, b/c we filter on itemType == 'Folder'
            # see TODO in folder_item_choices() about get_item_id() method
            folder_name_choices = [(str(folder['containerId']), folder['name'])
                                   for folder in items_in_run_container if folder['itemType'] == 'Folder']
            # logger.debug(f'folder_choices: {folder_name_choices}')
            return folder_name_choices

        def folder_item_choices(self, folder_id):
            """Return a list of tuples for the ESO Phase 2 folder items available to the user.

            Uses ESO Phase2 API method `getItems()` for the Folder's continer_id
            to get the items and filters on itemType to select Items.
            Creates the list of form.ChoiceField tuples from the result.
            """
            try:
                items_in_folder, _ = self.api2.getItems(folder_id)
            except p2api.p2api.P2Error as e:
                logger.error(f'API Error: {e}')
                return [(0, 'Are there any items in this folder?')]
            # logger.debug(f'items: {items_in_folder}')

            # TODO: we might need a get_item_id() method that uses the itemType to determing the
            # dict key of the id: OB -> obId, Folder -> containerId, etc.
            # folder_item_choices = [(item['obId'], f"{item['name']} : {item['itemType']} : {item['obStatus']}")
            #                        for item in items_in_folder]

            # or this loop where we try obID and fall back to containerId on KeyError
            folder_item_choices = []
            for item in items_in_folder:
                try:
                    folder_item_choices.append((item['obId'], f"{item['name']} : {item['itemType']}"))
                except KeyError as e:
                    logger.debug(f'{__name__}: folder_item_choices: KeyError: {e} for item: {item}')

                    # the item doesn't have an obId, so fallback and assume it has a containerId to use
                    folder_item_choices.append((item['containerId'], f"{item['name']} : {item['itemType']}"))
            # logger.debug(f'folder_item_choices: {folder_item_choices}')
            return folder_item_choices

        def folder_ob_choices(self, folder_id):
            """Return a list of tuples for the ESO Phase 2 folder observation blocks.
            Only Observation Blocks are returned; other folder items are filtered out.

            Uses ESO Phase2 API method `getItems()` for the Folder's continer_id
            to get the items and filters on itemType to select Items.
            Creates the list of form.ChoiceField tuples from the result.
            """
            try:
                items_in_folder, _ = self.api2.getItems(folder_id)
            except p2api.p2api.P2Error as e:
                logger.error(f'API Error: {e}')
                return [(0, 'Are there any items in this folder?')]
            # logger.debug(f'items: {items_in_folder}')

            # TODO: we might need a get_item_id() method that uses the itemType to determing the
            # dict key of the id: OB -> obId, Folder -> containerId, etc.
            # folder_item_choices = [(item['obId'], f"{item['name']} : {item['itemType']} : {item['obStatus']}")
            #                        for item in items_in_folder]

            # or this loop where we try obID and fall back to containerId on KeyError
            folder_ob_choices = []
            for item in items_in_folder:
                try:
                    folder_ob_choices.append((str(item['obId']), f"{item['name']} : {item['itemType']}"))
                except KeyError as e:
                    logger.debug(f'{__name__}: folder_ob_choices: KeyError: {e} for item: {item}')
                    # the item doesn't have an obId, so ignore it (unlike folder_item_choices, above

            # finally, add a choice for a new observation block
            # folder_ob_choices.append((-1, 'New Observation Block'))

            # logger.debug(f'folder_ob_choices: {folder_ob_choices}')
            return folder_ob_choices

        def getOB(self, ob_id):
            """Return the observation block corresponding to the ob_id.

            This is a straight passthrough (wrapper) to the ESO Phase2 API method `getOB()`.
            """
            ob, _ = self.api2.getOB(ob_id)
            return ob

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
