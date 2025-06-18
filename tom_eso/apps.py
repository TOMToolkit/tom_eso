
import logging

from django.apps import AppConfig
from django.urls import path, include

from tom_common.app_config_utils import auto_reencrypt_model_instances_for_user

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class TomEsoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tom_eso'

    def __init__(self, app_name, app_module):
        logger.debug(f'Initializing {app_name} AppConfig - module: {app_module}')
        super().__init__(app_name, app_module)

    # TOMToolkit Integration Points

    def include_url_paths(self):
        """
        Integration point for adding URL patterns to the Tom Common URL configuration.
        This method should return a list of URL patterns to be included in the main URL configuration.
        """
        urlpatterns = [
            path('eso/', include('tom_eso.urls')),
        ]
        return urlpatterns

    def profile_details(self):
        """
        Integration point for adding items to the user profile page.

        This method should return a list of dictionaries that include a `partial` key pointing to the path of the html
        profile partial. The `context` key should point to the dot separated string path to the templatetag that will
        return a dictionary containing new context for the accompanying partial.
        Typically, this partial will be a bootstrap card displaying some app specific user data.
        """
        profile_config = [
            {
                'partial': f'{self.name}/partials/eso_user_profile.html',
                'context': f'{self.name}.templatetags.eso_extras.eso_profile_data',
            }
        ]
        return profile_config

    # User-specfic TOMToolkit Integration Points

    def reencrypt_app_fields(self, user, decoding_cipher, encoding_cipher):
        """Integration point for re-encrypting any encrypted fields any of this
        app's models. This method is called when the user changes their password.

        parameters:
        - user: User - The user whose profile fields need to be re-encrypted.
        - decoding_cipher: Fernet - The Fernet cipher used to decrypt the existing values.
        - encoding_cipher: Fernet - The Fernet cipher used to encrypt the new values.

        This implementation uses the centralized helper in tom_common.app_config_utils.py.
        """
        auto_reencrypt_model_instances_for_user(
            app_config=self,
            user=user,
            decoding_cipher=decoding_cipher,
            encoding_cipher=encoding_cipher,
            user_relation_field_name='user'  # name of the Model field link to the User model
        )
