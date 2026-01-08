from django.urls import path

from tom_eso.views import (
    folders_for_observing_run,
    observation_blocks_for_folder,
    show_observation_block,
    ProfileUpdateView
)

app_name = 'tom_eso'

# by convention, URL patterns and names have dashes, while function names
# (as python identifiers) have underscores.
urlpatterns = [
    path('observing-run-folders/', folders_for_observing_run, name='observing-run-folders'),
    path('folder-observation-blocks/', observation_blocks_for_folder, name='folder-observation-blocks'),
    path('show-observation-block/', show_observation_block, name='show-observation-block'),

    path('users/<int:pk>/update/', ProfileUpdateView.as_view(), name='eso-profile-update'),
]
