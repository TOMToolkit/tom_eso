import logging

from cryptography.fernet import Fernet

from django import template
from django.forms.models import model_to_dict
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore

from tom_common.models import UserSession
from tom_common.session_utils import get_key_from_session_store

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
        profile = user.esoprofile
    except ESOProfile.DoesNotExist:
        profile = ESOProfile.objects.create(user=user)

    # Get the basic profile data, excluding the raw encrypted field
    exclude_fields = ['user', 'id', '_p2_password_encrypted']
    eso_profile_data = model_to_dict(profile, exclude=exclude_fields)

    # Now, try to decrypt the password. Default to a placeholder if decryption fails.
    decrypted_password = "[Password not available]"

    try:
        # Get the session and create a cipher
        session: Session = UserSession.objects.get(user=user).session
        session_store: SessionStore = SessionStore(session_key=session.session_key)
        cipher_key: bytes = get_key_from_session_store(session_store)
        cipher = Fernet(cipher_key)

        # Attach the cipher, get the value, and then clean up
        profile._cipher = cipher
        decrypted_password = profile.p2_password

    except (UserSession.DoesNotExist, KeyError) as e:
        logger.warning(f"Could not get encryption key for user {user.username} to display password: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while decrypting password for user {user.username}: {e}")
    finally:
        # Ensure the temporary cipher is always removed from the instance
        if hasattr(profile, '_cipher'):
            del profile._cipher

    eso_profile_data['p2_password'] = decrypted_password

    return {'user': user, 'eso_profile': profile, 'eso_profile_data': eso_profile_data}
