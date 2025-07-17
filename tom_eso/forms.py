from django import forms
from tom_eso.models import ESOProfile
from tom_common.session_utils import set_encrypted_field, get_encrypted_field


class ESOProfileForm(forms.ModelForm):

    # even though this is a ModelForm (and we automatically have forms.Fields for
    # each ESOProfile model field), we have to add CharFields for any encrypted
    # fields because they exist in the model as a combination property descriptor
    # and BinaryField. )
    p2_password = forms.CharField(
        required=False,
        label="P2 password",
        help_text="Enter your Phase 2 Tool password. Leave blank to keep unchanged."
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # set the initial value of the p2_password CharField
        if self.instance and self.instance.pk:
            self.fields['p2_password'].initial = get_encrypted_field(self.user, self.instance, 'p2_password')

    class Meta:
        model = ESOProfile
        fields = ['p2_environment', 'p2_username', 'p2_password']

    def save(self, commit=True):
        """Override save to handle the custom encrypted property."""
        # The form's 'p2_password' is not a model field, so super().save() will ignore it,
        # because super() is forms.ModelForm.
        instance = super().save(commit=False)

        cleaned_p2_password = self.cleaned_data.get('p2_password')
        # only update the p2_password if a new one is provided (cleaned_p2_password of '' is False)
        if cleaned_p2_password:
            # The user object is available from the instance
            user = instance.user
            # Use the helper to set the encrypted field
            success = set_encrypted_field(user, instance, 'p2_password', cleaned_p2_password)

            if not success:
                # The helper function returns False on failure. We can add an error to the form.
                self.add_error(None, "Could not save encrypted password due to a server error. "
                                     "Please ensure you are logged in correctly.")

        if commit and not self.errors:
            instance.save()
        return instance
