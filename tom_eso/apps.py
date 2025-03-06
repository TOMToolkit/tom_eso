from django.apps import AppConfig
from django.urls import path, include


class TomEsoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tom_eso'

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
