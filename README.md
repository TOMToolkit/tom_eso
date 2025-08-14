# tom_eso
European Southern Obervatory Facility module for TOM Toolkit

NOTE: This TOM Toolkit facility module is in the prototype stage. Any type of feedback is greatly appreciated. Please feel free to create an Issue.

## Installation

Install the module into your TOM environment:

```shell
pip install tom-eso
```

1. In your project `settings.py`, add `tom_eso` to your `INSTALLED_APPS` setting:

    ```python
    INSTALLED_APPS = [
        ...
        'tom_eso',
    ]
    ```

2. Add `tom_eso.eso.ESOFacility` to the `TOM_FACILITY_CLASSES` in your TOM's
`settings.py`:
   ```python
    TOM_FACILITY_CLASSES = [
        'tom_observations.facilities.lco.LCOFacility',
        ...
        'tom_eso.eso.ESOFacility',
    ]
   ```   

## Configuration

Include the following settings inside the `FACILITIES` dictionary inside `settings.py`:

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
