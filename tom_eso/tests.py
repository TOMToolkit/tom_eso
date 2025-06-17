from django.contrib.auth.models import User
from django.test import TestCase  # subclass of unittest.TestCase

from cryptography.fernet import Fernet

from tom_eso.models import ESOProfile


class TestESO(TestCase):
    def test_eso(self):
        self.assertTrue(True)


class TestCustomEncryptedBinaryField(TestCase):
    def setUp(self):
        self.cipher = Fernet.generate_key()
        self.cipher = Fernet(self.cipher)
        self.test_profile = ESOProfile.objects.create(user=User.objects.create(username="test_user"))
        self.test_profile.p2_password = "test_password"
        self.test_profile.save()

    def test_encryption_decryption(self):
        self.assertEqual(self.test_profile.p2_password, "test_password")
