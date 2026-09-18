"""Deterministic infrastructure identifiers for research programmes."""

from __future__ import annotations

import re
import unicodedata

from django.db import connection

MAX_PROGRAMME_IDENTIFIER_LENGTH = 32

GENERIC_WORDS = {
    "a", "an", "and", "for", "from", "framework", "hybrid",
    "in", "of", "on", "platform", "program", "programme",
    "project", "research", "the", "to", "with", "workflow", "workflows",
}

TOKEN_CODES = {
    "artificial": "a",
    "centered": "c",
    "centred": "c",
    "centric": "c",
    "computing": "c",
    "intelligence": "i",
    "learning": "l",
    "machine": "m",
    "medical": "m",
    "medicine": "m",
    "nuclear": "n",
    "optics": "o",
    "photonics": "p",
    "physics": "p",
    "quantum": "q",
    "simulation": "s",
    "supercomputer": "sc",
    "supercomputing": "sc",
}


def _words(value: str) -> list[str]:
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = value.encode("ascii", "ignore").decode("ascii").lower()
    return re.findall(r"[a-z0-9]+", value)


def programme_code(name: str) -> str:
    raw = _words(name)
    meaningful = [word for word in raw if word not in GENERIC_WORDS]
    code = "".join(TOKEN_CODES.get(word, word[:1]) for word in meaningful)
    if len(code) < 2:
        code = (code + "".join(word[:1] for word in raw))[:2]
    return (code or "rp")[:6]


def _candidate(institution: str, username: str, code: str, suffix: str) -> str:
    prefix = f"{institution.lower()}-{username.lower()}-"
    room = MAX_PROGRAMME_IDENTIFIER_LENGTH - len(prefix) - len(suffix)
    if room < 2:
        raise ValueError("Institution/username leave no room for a programme code.")
    return f"{prefix}{code[:room]}{suffix}"


def allocate_programme_identifier(
    institution: str,
    username: str,
    programme_name: str,
    *,
    exclude_application_id: int | None = None,
) -> str:
    from .models import PIApplication, ResearchProgramme

    base_code = programme_code(programme_name)
    lock_key = f"{institution.lower()}:{username.lower()}:{base_code}"

    if connection.vendor == "postgresql":
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT pg_advisory_xact_lock(hashtext(%s))",
                [f"quantum-platform:programme:{lock_key}"],
            )

    number = 0
    while True:
        suffix = "" if number == 0 else str(number)
        candidate = _candidate(institution, username, base_code, suffix)

        applications = PIApplication.objects.filter(programme_acronym=candidate)
        if exclude_application_id is not None:
            applications = applications.exclude(pk=exclude_application_id)

        if (
            not applications.exists()
            and not ResearchProgramme.objects.filter(acronym=candidate).exists()
        ):
            return candidate
        number += 1
