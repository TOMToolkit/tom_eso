import logging

from astropy.coordinates import Angle
from astropy import units as u

import p1api
import p2api  # these are the ESO APIs for phase1 and phase2

logger = logging.getLogger(__name__)


class ESOAPI:
    """A class to hold ESO p1 and p2 ApiConnections."""

    def __init__(self, environment, username, password):
        """
        Initializes the ESOAPI object.

        Args:
            environment (str): The ESO environment to use ('production', 'demo', etc.).
            username (str): The ESO username.
            password (str): The ESO password.
        """
        self.environment = environment
        self.username = username
        self.password = password

        try:
            self.api1 = p1api.ApiConnection(self.environment, self.username, self.password)
            self.api2 = p2api.ApiConnection(self.environment, self.username, self.password)
        except Exception as e:
            logger.error(f"ESOAPI.__init__: Error creating API connections: {e}")
            raise

    def create_observation_block(self, folder_id, ob_name, target=None):
        """Create a new Observation Block in the specified folder. Return the new OB's id.
        If a Target is specified, add it to the OB.

        """
        new_OB, ob_version = self.api2.createOB(folder_id, ob_name)

        if target:
            # add the target data to the new OB by modifying the OB JSON
            new_OB['target']['name'] = target.name

            # For ESO P2 API, the RA and Dec have specific formats:
            # RA: Valid format is HH:MM:SS.sss, with 0 <= HH <= 23, 0 <= MM < 60 and 0 <= SS < 60.]
            # Dec: Valid format is [+|-]DD:MM:SS.sss, with -90 <= DD <= 90, 0 <= MM < 60 and 0 <= SS < 60.]
            new_OB['target']['ra'] = Angle(target.ra, unit=u.deg).to_string(unit=u.hourangle, sep=':', precision=3)
            new_OB['target']['dec'] = Angle(target.dec, unit=u.deg).to_string(unit=u.deg, sep=':', precision=3,
                                                                              alwayssign=True)
            # save the updated observation block
            saved_observation_block, ob_version = self.api2.saveOB(new_OB, ob_version)

        return saved_observation_block

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
            logger.error(f'observing_run_choices: KeyError: {e}')
            return [(0, 'Are there any observing runs?')]
        except Exception as e:
            logger.error(f'observing_run_choices: Unexpected error: {e}')
            return [(0, f'Error fetching runs: {str(e)}')]

        choices = [(int(run['runId']), f"{run['progId']} - {run['telescope']} - {run['instrument']}")
                   for run in observing_runs if not int(run['runId']) in OBS_RUN_BLACK_LIST]
        return choices

    def folder_name_choices(self, observing_run_id):
        """Return a list of tuples for the ESO Phase 2 folder names available to the user.
        (These are the folders in the selected Observing Run).

        Uses ESO Phase2 API method `getItems()` for the ObservingRun's continer_id
        to get the items and filters on itemType to select Folders.
        Creates the list of form.ChoiceField tuples from the result.
        """
        observing_run, _ = self.api2.getRun(observing_run_id)
        container_id = observing_run['containerId']

        items_in_run_container, _ = self.api2.getItems(container_id)

        # NOTE: here we know id is containerId, b/c we filter on itemType == 'Folder'
        # see TODO in folder_item_choices() about get_item_id() method
        folder_name_choices = [(int(folder['containerId']), folder['name'])
                               for folder in items_in_run_container if folder['itemType'] == 'Folder']
        return folder_name_choices

    # TODO: consider renaming this to folder_content_choices
    def folder_item_choices(self, folder_id):
        """Return a list of tuples for the ESO Phase 2 folder items available to the user.
        (These are the items in the selected Folder).

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
                folder_item_choices.append((int(item['obId']), f"{item['name']} : {item['itemType']}"))
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

        # TODO: we might need a get_item_id() method that uses the itemType to determing the
        # dict key of the id: OB -> obId, Folder -> containerId, etc.
        # folder_item_choices = [(item['obId'], f"{item['name']} : {item['itemType']} : {item['obStatus']}")
        #                        for item in items_in_folder]

        # or this loop where we try obID and fall back to containerId on KeyError
        folder_ob_choices = []
        for item in items_in_folder:
            try:
                folder_ob_choices.append((int(item['obId']), f"{item['name']} : {item['itemType']}"))
            except KeyError:  # as e:
                pass
                # logger.debug(f'{__name__}: folder_ob_choices: KeyError: {e} for item: {item}')
                # the item doesn't have an obId, so ignore it (unlike folder_item_choices, above)

        return folder_ob_choices

    def getOB(self, ob_id):
        """Return the observation block corresponding to the ob_id.

        This is a straight passthrough (wrapper) to the ESO Phase2 API method `getOB()`.
        """
        ob, _ = self.api2.getOB(ob_id)
        return ob
