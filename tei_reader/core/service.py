"""Façade unique du lecteur : render().

Toute interface (CLI, webview, future webapp) passe par cette fonction
et ne touche ni Saxon, ni les XSLT, ni les profils directement.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from tei_reader.core import document
from tei_reader.diagnostics.models import Diagnostic, RenderResult
from tei_reader.profiles.loader import Profile, ProfileError, load_profile
from tei_reader.transform.engine import TransformEngine, TransformError
from tei_reader.transform.saxon_engine import SaxonEngine

_default_engine: TransformEngine = SaxonEngine()


def render(
    input_path: Path | str,
    profile: str | Profile = "prose",
    out_dir: Path | str = "out",
    engine: TransformEngine | None = None,
) -> RenderResult:
    """Transforme un fichier TEI en HTML et écrit les diagnostics.

    Ne lève jamais d'exception pour un problème de données : les erreurs
    sont retournées dans RenderResult. Seuls les bugs de programmation
    remontent.
    """
    input_path = Path(input_path)
    out_dir = Path(out_dir)
    engine = engine or _default_engine
    diagnostics: list[Diagnostic] = []

    try:
        prof = profile if isinstance(profile, Profile) else load_profile(profile)
    except ProfileError as exc:
        return _failure(str(exc), "profile-error", profile_name=str(profile))

    # 1. Parsing sécurisé + inventaire (lxml, sans réseau ni entités externes)
    try:
        tree = document.safe_parse(input_path)
    except document.DocumentError as exc:
        return _failure(str(exc), "xml-error", profile_name=prof.name)

    if not document.is_tei(tree):
        diagnostics.append(Diagnostic(
            "warning", "not-tei",
            "L'élément racine n'est pas dans l'espace de noms TEI ; "
            "le rendu passera par le fallback.",
        ))

    diagnostics.extend(_inventory_diagnostics(document.inventory(tree)))

    # 2. Transformation
    params = dict(prof.params)
    params["css-hrefs"] = " ".join(c.name for c in prof.css)
    try:
        html = engine.transform(input_path, prof.xslt, params)
    except TransformError as exc:
        diagnostics.append(Diagnostic("error", "transform-error", str(exc)))
        return RenderResult(
            ok=False, html_path=None, diagnostics_path=None,
            diagnostics=diagnostics, profile=prof.name,
        )

    # 3. Écriture des sorties
    out_dir.mkdir(parents=True, exist_ok=True)
    html_path = out_dir / f"{input_path.stem}.html"
    html_path.write_text(html, encoding="utf-8")
    for css in prof.css:
        shutil.copy2(css, out_dir / css.name)

    diagnostics_path = out_dir / f"{input_path.stem}.diagnostics.json"
    diagnostics_path.write_text(
        json.dumps(
            {
                "source": str(input_path),
                "profile": prof.name,
                "diagnostics": [d.to_dict() for d in diagnostics],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return RenderResult(
        ok=True, html_path=html_path, diagnostics_path=diagnostics_path,
        diagnostics=diagnostics, profile=prof.name,
    )


def _failure(message: str, code: str, profile_name: str) -> RenderResult:
    return RenderResult(
        ok=False, html_path=None, diagnostics_path=None,
        diagnostics=[Diagnostic("error", code, message)],
        profile=profile_name,
    )


def _inventory_diagnostics(inv: dict) -> list[Diagnostic]:
    out: list[Diagnostic] = []
    if inv["unknown"]:
        out.append(Diagnostic(
            "warning", "unknown-elements",
            "Éléments TEI sans rendu dédié (affichés via le fallback) : "
            + ", ".join(f"{n} (×{c})" for n, c in sorted(inv["unknown"].items())),
            details={"elements": dict(inv["unknown"])},
        ))
    if inv["non_tei"]:
        out.append(Diagnostic(
            "warning", "non-tei-elements",
            "Éléments hors espace de noms TEI : "
            + ", ".join(f"{n} (×{c})" for n, c in sorted(inv["non_tei"].items())),
            details={"elements": dict(inv["non_tei"])},
        ))
    if inv["minimal"]:
        out.append(Diagnostic(
            "info", "minimal-rendering",
            "Éléments reconnus mais au rendu volontairement minimal à ce stade "
            "(apparat, fac-similés) : "
            + ", ".join(f"{n} (×{c})" for n, c in sorted(inv["minimal"].items())),
            details={"elements": dict(inv["minimal"])},
        ))
    if inv["signaled"]:
        out.append(Diagnostic(
            "info", "signaled-only",
            "Éléments présents mais hors rendu à ce stade : "
            + ", ".join(f"{n} (×{c})" for n, c in sorted(inv["signaled"].items())),
            details={"elements": dict(inv["signaled"])},
        ))
    return out
