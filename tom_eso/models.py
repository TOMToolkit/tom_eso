import os
from enum import Enum
from cryptography.fernet import Fernet
from django.db import models
from django.contrib.auth.models import User


class ESOP2Environment(Enum):
    # value = label
    DEMO = 'demo'
    PRODUCTION = 'production'  # Paranal
    PRODUCTION_LASILLA = 'production_lasilla'

    @classmethod
    def choices(cls):
        return [(key.value, key.name.replace("_", " ").title()) for key in cls]


class ESOProfile(models.Model):
    """User Profile for ESO Facility"""

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    p2_environment = models.CharField(
        max_length=32,
        choices=ESOP2Environment.choices(),
        default=ESOP2Environment.DEMO.value,
    )

    p2_username = models.CharField(unique=True, max_length=255,
                                   default='520520',
                                   null=True, blank=True)
    encrypted_p2_password = models.BinaryField(null=True, blank=True)

    @property
    def p2_password(self) -> str:
        cipher_suite = Fernet(os.environ('ENCRYPTION_KEY', 'default-salt'))
        return cipher_suite.decrypt(self.encrypted_p2_password).decode() if self.encrypted_p2_password else ""

    @p2_password.setter
    def p2_password(self, plaintext_p2_password) -> None:
        cipher_suite = Fernet(os.environ('ENCRYPTION_KEY', 'default-salt'))
        self.encrypted_p2_password = cipher_suite.encrypt(plaintext_p2_password.encode())

    def __str__(self):
        return f'{self.user.username} ESO Profile: {self.p2_username}'
