"""Stable reference data for Quantum Platform identities."""

INSTITUTIONS = (
    ("AIMS", "African Institute of Mathematical Sciences (AIMS)"),
    ("CPUT", "Cape Peninsula University of Technology (CPUT)"),
    ("CSIR", "Council for Scientific and Industrial Research (CSIR)"),
    ("CUT", "Central University of Technology (CUT)"),
    ("DUT", "Durban University of Technology (DUT)"),
    ("MUT", "Mangosuthu University of Technology (MUT)"),
    ("NMU", "Nelson Mandela University (NMU)"),
    ("NWU", "North-West University (NWU)"),
    ("RU", "Rhodes University (RU)"),
    ("SMU", "Sefako Makgatho Health Sciences University (SMU)"),
    ("SPU", "Sol Plaatje University (SPU)"),
    ("SU", "Stellenbosch University (SU)"),
    ("TUT", "Tshwane University of Technology (TUT)"),
    ("UCT", "University of Cape Town (UCT)"),
    ("UFH", "University of Fort Hare (UFH)"),
    ("UFS", "University of Free State (UFS)"),
    ("UJ", "University of Johannesburg (UJ)"),
    ("UKZN", "University of KwaZulu-Natal (UKZN)"),
    ("UL", "University of Limpopo (UL)"),
    ("UMP", "University of Mpumalanga (UMP)"),
    ("UP", "University of Pretoria (UP)"),
    ("UNISA", "University of South Africa (Unisa)"),
    ("UWC", "University of the Western Cape (UWC)"),
    ("UNIVEN", "University of Venda (Univen)"),
    ("UNIZULU", "University of Zululand (UniZulu)"),
    ("VUT", "Vaal University of Technology (VUT)"),
    ("WSU", "Walter Sisulu University (WSU)"),
    ("WITS", "University of the Witwatersrand (Wits)"),
)

INSTITUTION_LABELS = dict(INSTITUTIONS)
INSTITUTION_CODES = frozenset(INSTITUTION_LABELS)


def normalise_institution(value: str) -> str:
    code = str(value or "").strip().upper()
    if code not in INSTITUTION_CODES:
        raise ValueError("Unknown institution code.")
    return code


def institution_payload() -> list[dict[str, str]]:
    return [{"code": code, "label": label} for code, label in INSTITUTIONS]
