"""Chargement des profils de rendu (fichiers JSON).

Un profil déclare : la feuille XSLT d'entrée, les paramètres passés à
la transformation et la liste des CSS à copier près du HTML produit.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

RESOURCES_DIR = Path(__file__).resolve().parent.parent / "resources"
PROFILES_DIR = RESOURCES_DIR / "profiles"


class ProfileError(Exception):
    """Profil introuvable ou invalide."""


@dataclass(frozen=True)
class Profile:
    name: str
    description: str
    xslt: Path
    params: dict[str, str] = field(default_factory=dict)
    css: tuple[Path, ...] = ()


def list_profiles() -> list[str]:
    return sorted(p.stem for p in PROFILES_DIR.glob("*.json"))


def load_profile(name: str) -> Profile:
    path = PROFILES_DIR / f"{name}.json"
    if not path.is_file():
        raise ProfileError(
            f"Profil inconnu : {name!r}. Disponibles : {', '.join(list_profiles())}"
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ProfileError(f"Profil {name!r} illisible : {exc}") from exc

    xslt = RESOURCES_DIR / "xsl" / data["xslt"]
    if not xslt.is_file():
        raise ProfileError(f"XSLT introuvable pour le profil {name!r} : {xslt}")

    css_paths = []
    for css_name in data.get("css", []):
        css = RESOURCES_DIR / "css" / css_name
        if not css.is_file():
            raise ProfileError(f"CSS introuvable pour le profil {name!r} : {css}")
        css_paths.append(css)

    return Profile(
        name=data.get("name", name),
        description=data.get("description", ""),
        xslt=xslt,
        params={k: str(v) for k, v in data.get("params", {}).items()},
        css=tuple(css_paths),
    )
