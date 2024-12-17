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
