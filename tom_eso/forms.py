from django import forms
from tom_eso.models import ESOProfile


class ESOProfileForm(forms.ModelForm):
    p2_password = forms.CharField(
        #widget=forms.PasswordInput,
        required=False,
        label="ESO Phase 2 Tool Password",
        help_text="Enter your Phase 2 Tool password."
    )

    class Meta:
        model = ESOProfile
        fields = ['p2_environment', 'p2_username', 'p2_password']

    def save(self, commit=True):
        """Override save to handle the custom encrypted field."""
        instance = super().save(commit=False)
        cleaned_p2_password = self.cleaned_data['p2_password']
        if cleaned_p2_password:
            # Encrypt and save the password using the custom setter
            instance.set_p2_password(cleaned_p2_password, cipher=self.initial['cipher'])
        if commit:
            instance.save()
        return instance
