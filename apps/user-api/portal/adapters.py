from django.db import transaction

from allauth.account.adapter import DefaultAccountAdapter

from .identity import allocate_system_username


class QuantumAccountAdapter(DefaultAccountAdapter):
    """Allocate the immutable SSH/Slurm-compatible identity at signup."""

    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)

        given_names = str(form.cleaned_data.get("given_names", "")).strip()
        family_name = str(form.cleaned_data.get("family_name", "")).strip()

        user.first_name = given_names
        user.last_name = family_name

        if not commit:
            user.username = allocate_system_username(
                given_names,
                family_name,
            )
            return user

        with transaction.atomic():
            user.username = allocate_system_username(
                given_names,
                family_name,
            )
            user.save()

        return user
