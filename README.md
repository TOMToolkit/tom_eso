# tom_eso
European Southern Obervatory Facility module for TOM Toolkit

NOTE: This TOM Toolkit facility module is in the prototype stage. Any type of feedback is greatly appreciated. Please feel free to create an Issue.

This module is designed mainly to facilitate getting Target and Observation data
from your TOM to the ESO P2 Tool (without having to re-enter it). Submitting
observations is still expected to be done through the P2 Tool itself.

This facility is still in prototype stage and feature requests are welcome.
Please let us know your use cases.

## Installation

1. Install the module into your TOM environment:

    ```shell
    pip install tom-eso
    ```

You'll want to update your `pyproject.toml` or `requirements.txt` file as well.

2. In your project `settings.py`, add `tom_eso` to your `INSTALLED_APPS` setting:

    ```python
    INSTALLED_APPS = [
        ...
        'tom_eso',
    ]
    ```

3. Add `tom_eso.eso.ESOFacility` to the `TOM_FACILITY_CLASSES` in your TOM's
`settings.py`:
   ```python
    TOM_FACILITY_CLASSES = [
        'tom_observations.facilities.lco.LCOFacility',
        ...
        'tom_eso.eso.ESOFacility',
    ]
   ```   

4. Create the ESOProfile tables in your database:

    ```bash
    $ ./manage.py migrate
    ```


## Configuration Options

After installation, each user will have an `ESOProfile` card in their TOM user profile where they can
enter their ESO P2 Tool `username` and `password` and set the ESO environment to `Demo`, `Production`,
or `Production La Silla`.

If a TOM admin wants to have a single default set of ESO credentials accessible by all of their TOM's users, they can 
include the following to thier `settings.py`:

```python
FACILITIES = {
        ...
        # defaults set from ESO p2 API Tutorial
        # https://www.eso.org/sci/observing/phase2/p2intro/Phase2API/api--python-programming-tutorial.html
        # You should have your own credentials.
        'ESO': {
            'environment': os.getenv('ESO_ENVIRONMENT', 'demo'),
            'username': os.getenv('ESO_USERNAME', '52052'),
            'password': os.getenv('ESO_PASSWORD', 'tutorial'),
        },
    }
```
Note: The user specific credentials will always take precendence over these TOM-wide defaults.