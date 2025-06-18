import logging
from enum import Enum
from typing import List, Tuple

from cryptography.fernet import Fernet

from django.db import models
from django.contrib.auth.models import User

from tom_common.models import EncryptedBinaryField

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ESOP2Environment(Enum):
    """Enumerate the possible ESO Phase 2 Tool Environments.

    In the ``ESOProfile``, the ``p2_environment`` property will have one
    of these values and determine what API you interact with.
    """
    # value = label
    DEMO = 'demo'
    PRODUCTION = 'production'  # Paranal
    PRODUCTION_LASILLA = 'production_lasilla'

    @classmethod
    def choices(cls) -> List[Tuple[str, str]]:
        """Return a list of tuples suitable for the choices of a models.CharField"""
        return [(member.value, member.name.replace("_", " ").title()) for member in cls]


class ESOProfile(models.Model):
    """User Profile for ESO Facility.

    This model contains an encrypted field to hold the User's Phase 2 password.
    In general, to setup and encrypted field, you need to:
    1. Add an EncryptedBinaryField to the model
    2. Add a `property_name` named argument to the EncryptedBinaryField
    3. Add an `encrypted=True` named argument to the EncryptedBinaryField
    4. Add a setter and getter to the model that matches the `property_name`
    See the `p2_password` field for an example.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    p2_environment = models.CharField(
        max_length=32,
        choices=ESOP2Environment.choices(),
        default=ESOP2Environment.DEMO.value,
    )

    p2_username = models.CharField(max_length=255,
                                   default='520520',
                                   null=True, blank=True)

    _ciphertext_p2_password = EncryptedBinaryField(null=True, blank=True,
                                                   property_name='p2_password',
                                                   encrypted=True)  # see setter/getter below

    # The AppConfig.encrypted_profile_fields method will return the names of the setter/getter methods
    # of the encrypted fields so that they can be re-encrypted when the user changes their password.

    def get_p2_password(self, cipher: Fernet) -> str:
        """Return the Phase 2 password decrypted using the provided cipher

        IMPORTANT: the name of this method must match the property_name of the corresponding EncryptedBinaryField

        So, because this is the getter for the `p2_password` EncryptedBinaryField,
        it must be named `get_p2_password`.
        """
        # different database backends return different types for BinaryField and
        # that affects how we decrypt the value:

        if isinstance(self._ciphertext_p2_password, bytes):
            p2_password: str = cipher.decrypt(self._ciphertext_p2_password).decode() if self._ciphertext_p2_password else ''  # noqa
            # the BinaryField backend is a bytes object (so it's probably SQLite).
            # We don't need to convert it to bytes before decrypting

        else:
            p2_password: str = cipher.decrypt(self._ciphertext_p2_password.tobytes()).decode() if self._ciphertext_p2_password else ''  # noqa
            # the BinaryField backend is a memoryview object so it's probably Posgresql
            # and we need to convert it to bytes before decrypting.
            # details:
            # _chiphertext_p2_password is a memoryview object
            # _chiphertext_p2_password.tobytes() is <class 'bytes'>; the decrypted value is also <class 'bytes'>
            # call `decode()` on the decrypted <class 'bytes'> object to convert it to a string

        return p2_password

    def set_p2_password(self, plaintext_p2_password: str, cipher: Fernet) -> None:
        """Save the Phase 2 password encrypted using the provided cipher

        IMPORTANT: the name of this method must match the property_name of the corresponding EncryptedBinaryField

        So, because this is the setter for the `p2_password` EncryptedBinaryField,
        it must be named `set_p2_password`.
        """
        self._ciphertext_p2_password = cipher.encrypt(plaintext_p2_password.encode())

    def reencrypt_model_fields(self, decoding_cipher: Fernet, encoding_cipher: Fernet) -> None:
        # loop through the fields in the model and re-encrypt any that are marked as encrypted
        for field in self._meta.fields:
            if getattr(field, 'encrypted', False):
                # decrypt the existing value using the decoding cipher
                field_getter = getattr(self, f'get_{field.property_name}')  # get the getter method
                plaintext = field_getter(decoding_cipher)
                logger.debug(f'Decrypted value for {field.property_name}: {plaintext}')

                field_setter = getattr(self, f'set_{field.property_name}')  # get the setter method
                field_setter(plaintext, cipher=encoding_cipher)  # set the value
        self.save()  # save the changes to the database

    def __str__(self) -> str:
        return f'{self.user.username} ESO Profile: {self.p2_username}'
