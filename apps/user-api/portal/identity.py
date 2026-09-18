"""Allocation of immutable Quantum Platform system usernames."""

from __future__ import annotations

import re
import unicodedata

from django.contrib.auth import get_user_model
from django.db import connection

MAX_SYSTEM_USERNAME_LENGTH = 15

RESERVED_USERNAMES = {
    "admin",
    "administrator",
    "daemon",
    "guest",
    "nobody",
    "postgres",
    "root",
    "slurm",
    "support",
    "ubuntu",
    "user",
}


def _ascii_token(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = value.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]", "", value.lower())


def username_base(given_names: str, family_name: str) -> str:
    given = _ascii_token(given_names)
    family = _ascii_token(family_name)
    base = f"{given[:1]}{family}"

    if not base:
        base = "user"
    if not base[0].isalpha():
        base = f"u{base}"
    if base in RESERVED_USERNAMES:
        base = f"u{base}"

    return base[:MAX_SYSTEM_USERNAME_LENGTH]


def allocate_system_username(given_names: str, family_name: str) -> str:
    """Return nlisa, nlisa1, nlisa2, ... without races on PostgreSQL."""
    User = get_user_model()
    base = username_base(given_names, family_name)

    if connection.vendor == "postgresql":
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT pg_advisory_xact_lock(hashtext(%s))",
                [f"quantum-platform:username:{base}"],
            )

    number = 0
    while True:
        suffix = "" if number == 0 else str(number)
        stem = base[: MAX_SYSTEM_USERNAME_LENGTH - len(suffix)]
        candidate = f"{stem}{suffix}"
        if not User.objects.filter(username=candidate).exists():
            return candidate
        number += 1
