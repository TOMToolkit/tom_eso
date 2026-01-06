import logging
from enum import Enum
from typing import List, Tuple

from django.db import models

from tom_common.models import EncryptableModelMixin, EncryptedProperty

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


class ESOProfile(EncryptableModelMixin, models.Model):
    """User Profile for ESO Facility.

    Set the `verbose_name` Field parameter to control the way the field is
    displayed by the Profile partial
    (see `tom_eso/tom_eso/templates/tom_eso/partials/eso_user_partial.html`)

    This model contains an encrypted property to hold the User's Phase 2 password.
    To set up an encrypted property:
    1. Subclass EncryptableModelMixin.
    2. Add a models.BinaryField to store the raw encrypted data (e.g., `_p2_password_encrypted`).
    3. Add an EncryptedProperty descriptor that points to the binary field
       (e.g., `p2_password = EncryptedProperty('_p2_password_encrypted')`).
    """

    # The `user` field (a OneToOneField to the User model) is inherited from
    # the EncryptableModelMixin and should not be redefined here.

    p2_environment = models.CharField(
        max_length=32,
        choices=ESOP2Environment.choices(),
        default=ESOP2Environment.DEMO.value,
        verbose_name='P2 Environment'
    )

    p2_username = models.CharField(max_length=255,
                                   null=True, blank=True,
                                   verbose_name='P2 Username')

    _p2_password_encrypted = models.BinaryField(null=True, blank=True)  # encrypted data field (private)
    p2_password = EncryptedProperty('_p2_password_encrypted')  # descriptor that provides access (public)

    def __str__(self) -> str:
        return f'{self.user.username} ESO Profile: {self.p2_username}'
