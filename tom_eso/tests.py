from django.contrib.auth.models import User
from django.test import TestCase  # subclass of unittest.TestCase

from cryptography.fernet import Fernet

from tom_eso.models import ESOProfile


class TestESO(TestCase):
    def test_eso(self):
        self.assertTrue(True)


class TestCustomEncryptedBinaryField(TestCase):
    def setUp(self):
        # Create a user and a cipher for the test
        self.user = User.objects.create(username="test_user")
        key = Fernet.generate_key()
        self.cipher = Fernet(key)

        # Create the profile instance
        self.test_profile = ESOProfile.objects.create(user=self.user)

    def test_encryption_decryption(self):
        # Attach the cipher to the instance before setting the property
        self.test_profile._cipher = self.cipher
        self.test_profile.p2_password = "test_password"
        del self.test_profile._cipher  # Clean up

        self.test_profile.save()

        # To read it back, we need to get a fresh instance from the DB
        # and attach the cipher again
        retrieved_profile = ESOProfile.objects.get(pk=self.test_profile.pk)
        retrieved_profile._cipher = self.cipher

        # Now we can access the decrypted value
        self.assertEqual(retrieved_profile.p2_password, "test_password")

        # Clean up
        del retrieved_profile._cipher

    def test_access_without_cipher_raises_error(self):
        """
        Verify that attempting to access the encrypted property without first
        attaching a cipher raises an AttributeError, as expected.
        """
        # Save a value first (this part needs a cipher)
        self.test_profile._cipher = self.cipher
        self.test_profile.p2_password = "test_password"
        del self.test_profile._cipher
        self.test_profile.save()

        retrieved_profile = ESOProfile.objects.get(pk=self.test_profile.pk)
        # Now, try to access the property without attaching the cipher
        with self.assertRaisesRegex(AttributeError, "A Fernet cipher must be set"):
            _ = retrieved_profile.p2_password
