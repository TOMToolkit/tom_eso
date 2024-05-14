from django.urls import path

from . import views

# by convention, URL patterns and names have dashes, while function names
# (as python identifiers) have underscores.
urlpatterns = [
    path('observing-run-folders/', views.folders_for_observing_run, name='observing-run-folders'),
    path('folders-items/', views.items_for_folder, name='folder-items'),
]
