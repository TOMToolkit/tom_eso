from django.urls import path, include

from . import views

# by convention, URL patterns and names have dashes, while function names
# (as python identifiers) have underscores.
urlpatterns = [
    path('observing-run/', views.observing_run, name='observing-run'),
]
