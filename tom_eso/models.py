import logging
from enum import Enum
from typing import List, Tuple

from django.db import models
from django.contrib.auth.models import User

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

    This model contains an encrypted property to hold the User's Phase 2 password.
    To set up an encrypted property:
    1. Subclass EncryptableModelMixin.
    2. Add a models.BinaryField to store the raw encrypted data (e.g., `_p2_password_encrypted`).
    3. Add an EncryptedProperty descriptor that points to the binary field
       (e.g., `p2_password = EncryptedProperty('_p2_password_encrypted')`).
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

    _p2_password_encrypted = models.BinaryField(null=True, blank=True)  # encrypted data field (private)
    p2_password = EncryptedProperty('_p2_password_encrypted')  # descriptor that provides access (public)

    def __str__(self) -> str:
        return f'{self.user.username} ESO Profile: {self.p2_username}'
