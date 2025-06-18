
import logging

from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured
from django.urls import path, include

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

        As currently implemented, this method must know which of the app's models
        have encrypted and call that models `reencrypt_model_fields` method.

        parameters:
        - user: User - The user whose profile fields need to be re-encrypted.
        - decoding_cipher: Fernet - The Fernet cipher used to decrypt the existing values.
        - encoding_cipher: Fernet - The Fernet cipher used to encrypt the new values.

        """

        encrypted_field_containing_models = ['ESOProfile']  # List of app-specific models with encrypted fields

        for encrypted_field_containing_model in encrypted_field_containing_models:
            model_class = self.get_model(encrypted_field_containing_model)  # app-specific Profile model class
            try:
                model_instance = model_class.objects.get(user=user)  # CAUTION: Profile specific (assumes a user field)
            except model_class.DoesNotExist:
                logger.error(f'No {encrypted_field_containing_model} found for user {user.username}')
                return  # early return

            model_instance.reencrypt_model_fields(decoding_cipher=decoding_cipher, encoding_cipher=encoding_cipher)

    # TODO: move this information in to the ESOProfile model
    def encrypted_profile_fields(self, *args, **kwargs):
        """
        Integration point for adding fields to be encrypted in the user profile.

        Find the encrypted fields by examining the model and returning a list of the
        names of the setters and getters for the fields with encrypted=True. These
        fields must have a property_name attribute that matches the name of the
        setter and getter.

        See the ESOProfile model in `tom_eso.models` for an example.
        """
        encrypted_fields = []

        # this method knows about the app-specific Profile model
        model = self.get_model('ESOProfile')  # app-specific Profile model
        for field in model._meta.fields:
            if getattr(field, 'encrypted', False):
                try:
                    encrypted_fields.append(field)
                except AttributeError:
                    raise ImproperlyConfigured(
                        f'ESOProfile field {field.name} is encrypted, but does not have a property_name attribute.')
        return encrypted_fields  # List of model.Field subclass instances
