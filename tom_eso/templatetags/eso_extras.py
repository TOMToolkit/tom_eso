import logging

from cryptography.fernet import Fernet

from django import template
from django.forms.models import model_to_dict
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore

from tom_common.models import UserSession
from tom_common.session_utils import extract_key_from_session_store

from tom_eso.models import ESOProfile

import inspect

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

register = template.Library()



@register.inclusion_tag('tom_eso/partials/eso_user_profile.html')
def eso_profile_data(user):
    """
    Returns the app specific user information as a dictionary to be used in the context of the above partial.
    """
    logger.debug(f"********** {inspect.currentframe().f_code.co_name} **********")

    exclude_fields = ['user', 'id']
    try:
        eso_profile_data = model_to_dict(user.esoprofile, exclude=exclude_fields)
        eso_profile_data['p2_password'] = 'set me!'

        # Extract the p2_password from the ESOProfile model and put it in the eso_profile_data dict
        # first get the cipher_key from the session
        session: Session = UserSession.objects.get(user=user).session
        session_store: SessionStore = SessionStore(session_key=session.session_key)
        cipher_key: bytes = extract_key_from_session_store(session_store)
        logger.debug(f'cipher_key: {cipher_key}')
        cipher = Fernet(cipher_key)
        logger.debug(f'cipher: {cipher}')

        eso_profile_data['p2_password'] = user.esoprofile.get_p2_password(cipher=cipher)
        logger.debug(f'eso_profile_data: {eso_profile_data}')


        #logger.debug(f'_ciphertext_p2_password: {user.esoprofile._ciphertext_p2_password.get_default()}')
        #if user.esoprofile._ciphertext_p2_password.get_default():
        #    # add the encrypted fields to the eso_profile_data dict
        #    # for now, get the encrypted fields from the ESOProfile model, decrypt them, and add them to the eso_profile_data dict
        #    session: Session = UserSession.objects.get(user=user).session
        #    cipher_key: bytes = extract_key_from_session(session)
        #    logger.debug(f'cipher_key: {cipher_key}')
        #    cipher = Fernet(cipher_key)
        #    eso_profile_data['p2_password'] = user.esoprofile.get_p2_password(cipher=cipher)
        #    logger.debug(f'eso_profile_data: {eso_profile_data}')
        #else:
        #    eso_profile_data['p2_password'] = 'set me!'

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
