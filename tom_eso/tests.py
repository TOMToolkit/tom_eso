import django
from django.test import TestCase  # subclass of unittest.TestCase
from django.conf import settings

# This configuration is necessary for running tests for a reusable Django app.
# It sets up a minimal Django environment so that tests can be run without a
# full Django project.
if not settings.configured:
    settings.configure(
        SECRET_KEY='a-secret-key-for-testing-only',
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        # The INSTALLED_APPS needs to include the app itself ('tom_eso') and any
        # dependencies required for its models or tests to be loaded.
        INSTALLED_APPS=(
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',  # for UserSession's ForeignKey to Session model
            'tom_common',  # For EncryptableModelMixin
            'tom_eso',
        ),
    )
    django.setup()


class TestESO(TestCase):
    def test_eso(self):
        self.assertTrue(True)
