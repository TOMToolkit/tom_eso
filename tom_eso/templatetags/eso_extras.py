import logging

from django import template
from django.forms.models import model_to_dict

from tom_common.session_utils import get_encrypted_field

from tom_eso.models import ESOProfile


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

register = template.Library()


@register.inclusion_tag('tom_eso/partials/eso_user_profile.html')
def eso_profile_data(user):
    """
    Returns the app specific user information as a dictionary to be used in the context of the above partial.
    """
    try:
        profile: ESOProfile = user.esoprofile
    except ESOProfile.DoesNotExist:
        profile = ESOProfile.objects.create(user=user)

    # Get the basic profile data, excluding the raw encrypted field
    exclude_fields = ['user', 'id', '_p2_password_encrypted']
    eso_profile_data = model_to_dict(profile, exclude=exclude_fields)

    # Use the helper to get the decrypted password
    decrypted_password = get_encrypted_field(user, profile, 'p2_password')

    # Provide a placeholder if decryption failed (returned None)
    if decrypted_password is not None:
        eso_profile_data['p2_password'] = decrypted_password
    else:
        eso_profile_data['p2_password'] = "[Password not available]"

    return {'user': user, 'eso_profile': profile, 'eso_profile_data': eso_profile_data}
