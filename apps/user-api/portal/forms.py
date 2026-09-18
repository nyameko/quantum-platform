from django import forms

from .constants import INSTITUTIONS
from .models import Person


class AccountSignupForm(forms.Form):
    given_names = forms.CharField(max_length=150, label="Given name(s)")
    family_name = forms.CharField(max_length=150, label="Family name")
    institution = forms.ChoiceField(
        choices=INSTITUTIONS,
        label="Primary institution",
    )

    def signup(self, request, user):
        given_names = self.cleaned_data["given_names"].strip()
        family_name = self.cleaned_data["family_name"].strip()

        Person.objects.update_or_create(
            user=user,
            defaults={
                "given_names": given_names,
                "family_name": family_name,
                "preferred_name": (
                    given_names.split()[0] if given_names else ""
                ),
                "institution": self.cleaned_data["institution"],
            },
        )
