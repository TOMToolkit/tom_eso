from django import forms
from tom_eso.models import ESOProfile


class ESOProfileForm(forms.ModelForm):
    p2_password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        label="ESO Phase 2 Tool Password",
        help_text="Enter your Phase 2 Tool password. Leave blank to keep unchanged."
    )

    class Meta:
        model = ESOProfile
        fields = ['p2_environment', 'p2_username', 'p2_password']

    def save(self, commit=True):
        """Override save to handle the custom encrypted property."""
        # The form's 'p2_password' is not a model field, so super().save() will ignore it.
        instance = super().save(commit=False)

        cleaned_p2_password = self.cleaned_data.get('p2_password')
        if cleaned_p2_password:
            cipher = self.initial.get('cipher')
            if not cipher:
                # This should not happen if the form is used correctly from the view.
                raise ValueError("A cipher is required to save the encrypted password.")

            # Attach the cipher to the instance temporarily to use the EncryptedProperty setter
            instance._cipher = cipher
            instance.p2_password = cleaned_p2_password
            del instance._cipher  # Clean up the temporary attribute

        if commit:
            instance.save()
        return instance
