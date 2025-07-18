import logging

from django import template

from tom_common.session_utils import get_encrypted_field

from tom_eso.models import ESOProfile
# Import the form to consistently get the label for the password field.
from tom_eso.forms import ESOProfileForm

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

register = template.Library()


@register.inclusion_tag('tom_eso/partials/eso_user_profile.html')
def eso_profile_data(user) -> dict:
    """
    Gathers the ESO profile data for display in the user profile partial.

    This tag prepares a structured list of data for the template, including
    field labels (verbose_name) and their corresponding values. This is more
    robust than using model_to_dict, as it gives full control over the
    presentation and handles non-model fields (like encrypted properties)
    gracefully.
    """
    try:
        profile: ESOProfile = user.esoprofile
    except ESOProfile.DoesNotExist:
        profile = ESOProfile.objects.create(user=user)

    profile_data_list = []

    # Define the standard model fields we want to display.
    model_fields_to_display = ['p2_environment', 'p2_username']

    for field_name in model_fields_to_display:
        field = profile._meta.get_field(field_name)
        # Use get_..._display() for choice fields to get the human-readable value.
        if hasattr(profile, f'get_{field_name}_display'):
            value = getattr(profile, f'get_{field_name}_display')()
        else:
            value = getattr(profile, field_name)

        profile_data_list.append({
            'label': field.verbose_name,
            'value': value,
        })

    # Handle the special case of the encrypted password field.
    decrypted_password = get_encrypted_field(user, profile, 'p2_password')
    password_label = ESOProfileForm.base_fields['p2_password'].label or 'P2 Password'

    password_value = decrypted_password
    if decrypted_password is None:
        password_value = "[Password not available]"

    profile_data_list.append({'label': password_label, 'value': password_value})

    return {'user': user, 'eso_profile': profile, 'profile_data_list': profile_data_list}
