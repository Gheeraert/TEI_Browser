"""Snapshots HTML normalisés : cas couverts et fonction de normalisation.

Partagé entre tests/test_snapshots.py (comparaison) et
tests/update_snapshots.py (régénération volontaire).

La normalisation est volontairement légère : elle neutralise uniquement
ce qui varie légitimement d'une machine ou d'une exécution à l'autre
(chemins file: absolus, identifiants générés des notes), puis compare
ligne à ligne sans blancs de bord. Tout autre changement du HTML produit
fait échouer le test : c'est le but (non-régression du contrat).
"""

from __future__ import annotations

import re
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
SAMPLES = TESTS_DIR.parent / "samples"
SNAPSHOT_DIR = TESTS_DIR / "snapshots"

# (échantillon, profil) — un snapshot par couple.
CASES = [
    ("prose", "prose"),
    ("verse", "verse"),
    ("drama", "drama"),
    ("apparatus", "diagnostic"),
    ("notes", "prose"),
    ("facsimile", "prose"),
    ("correspondence", "correspondence"),
    ("images", "prose"),
]


def normalize_html(html: str) -> str:
    # chemins absolus locaux (file:///C:/...) -> stable
    html = re.sub(r'file:///[^"]*', "file:LOCAL", html)
    # identifiants générés (generate-id) des notes -> stable
    html = re.sub(r"\b(note(?:ref)?-)[A-Za-z0-9]+", r"\1ID", html)
    lines = [line.strip() for line in html.splitlines()]
    return "\n".join(line for line in lines if line) + "\n"


def snapshot_path(sample: str, profile: str) -> Path:
    return SNAPSHOT_DIR / f"{sample}--{profile}.html"
