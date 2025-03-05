from django.db import models
from django.contrib.auth.models import User


class ESOProfile(models.Model):
    """User Profile for ESO Facility"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.user.username} ESO Profile'
