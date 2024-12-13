from django.urls import path

from . import views

# by convention, URL patterns and names have dashes, while function names
# (as python identifiers) have underscores.
urlpatterns = [
    path('observing-run-folders/', views.folders_for_observing_run, name='observing-run-folders'),
    path('folder-observation-blocks/', views.observation_blocks_for_folder, name='folder-observation-blocks'),
    path('show-observation-block/', views.show_observation_block, name='show-observation-block'),
]
