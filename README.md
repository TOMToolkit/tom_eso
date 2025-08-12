# tom_eso
European Southern Obervatory Facility modules for TOM Toolkit

This module mainly designed to facilitate getting Target and Observation data
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

## Configuration

After installation, each user will have an `ESOProfile` card in their TOM user profile where they can
enter their ESO P2 Tool `username` and `password` and set the ESO environment to `Demo`, `Production`,
or `Production La Silla`.
