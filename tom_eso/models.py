import logging
from enum import Enum
from typing import List, Tuple

from django.db import models
from django.contrib.auth.models import User

from tom_common.encryption import EncryptedModelField

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

    Set the `verbose_name` Field parameter to control the way the field is
    displayed by the Profile partial
    (see `tom_eso/tom_eso/templates/tom_eso/partials/eso_user_partial.html`)

    This model contains an encrypted property to hold the User's Phase 2 password.
    To learn more about encrypted fields see
    https://tom-toolkit.readthedocs.io/en/stable/customization/encrypted_model_fields.html
    """

    # The `user` field (a OneToOneField to the User model) is inherited from
    # the EncryptableModelMixin and should not be redefined here.

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    p2_environment = models.CharField(
        max_length=32,
        choices=ESOP2Environment.choices(),
        default=ESOP2Environment.DEMO.value,
        verbose_name='P2 Environment'
    )

    p2_username = models.CharField(max_length=255,
                                   null=True, blank=True,
                                   verbose_name='P2 Username')
    p2_password = EncryptedModelField(null=True, blank=True)

    def __str__(self) -> str:
        return f'{self.user.username} ESO Profile: {self.p2_username}'
