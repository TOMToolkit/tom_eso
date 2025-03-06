from django import template
from django.forms.models import model_to_dict
from django.contrib.auth.models import User

from tom_eso.models import ESOProfile

register = template.Library()


@register.inclusion_tag('tom_eso/partials/eso_user_profile.html')
def eso_profile_data(user):
    """
    Returns the app specific user information as a dictionary to be used in the context of the above partial.
    """

    exclude_fields = ['user', 'id']
    try:
        eso_profile_data = model_to_dict(user.esoprofile, exclude=exclude_fields)
        context = {
            'user': user,
            'eso_profile': user.esoprofile,
            'eso_profile_data': eso_profile_data,
        }
    except ESOProfile.DoesNotExist:
        ESOProfile.objects.create(user=user)
        context = {
            'user': user,
            'eso_profile': user.esoprofile,
            'eso_profile_data': {}
        }
    return context
