"""Façade unique du lecteur : render() et inspect_file().

Toute interface (CLI, webview, future webapp) passe par ces fonctions
et ne touche ni Saxon, ni les XSLT, ni les profils directement.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from tei_reader.core import document
from tei_reader.core.document import Analysis
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

    try:
        prof = profile if isinstance(profile, Profile) else load_profile(profile)
    except ProfileError as exc:
        return _failure(str(exc), exc.code, profile_name=str(profile))

    # 1. Parsing sécurisé + analyse (lxml, sans réseau ni entités externes)
    try:
        tree = document.safe_parse(input_path)
    except document.DocumentError as exc:
        return _failure(str(exc), "xml-error", profile_name=prof.name)

    analysis = document.analyze(tree, input_path)
    diagnostics = _analysis_diagnostics(tree, analysis)

    # 2. Transformation
    params = dict(prof.params)
    params["css-hrefs"] = " ".join(c.name for c in prof.css)
    # Médias locaux vérifiés sur disque (jamais de ressource distante) :
    # la XSLT ne sait pas tester l'existence d'un fichier, Python la lui
    # fournit. media-base = dossier du fichier source en URI file:, car le
    # HTML est écrit ailleurs (out_dir) et les chemins du TEI sont relatifs
    # à la source.
    if analysis.local_media:
        params["existing-media"] = "\n".join(analysis.local_media)
        params["media-base"] = input_path.resolve().parent.as_uri()
    try:
        html = engine.transform(input_path, prof.xslt, params)
    except TransformError as exc:
        diagnostics.append(Diagnostic("error", "transform-error", str(exc)))
        return RenderResult(
            ok=False, html_path=None, diagnostics_path=None,
            diagnostics=diagnostics, profile=prof.name,
            summary=analysis.summary,
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
                "summary": analysis.summary,
                "diagnostics": [d.to_dict() for d in diagnostics],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return RenderResult(
        ok=True, html_path=html_path, diagnostics_path=diagnostics_path,
        diagnostics=diagnostics, profile=prof.name, summary=analysis.summary,
    )


def inspect_file(input_path: Path | str) -> RenderResult:
    """Analyse un fichier TEI sans le transformer : résumé + diagnostics."""
    input_path = Path(input_path)
    try:
        tree = document.safe_parse(input_path)
    except document.DocumentError as exc:
        return _failure(str(exc), "xml-error", profile_name="-")

    analysis = document.analyze(tree, input_path)
    diagnostics = _analysis_diagnostics(tree, analysis)
    return RenderResult(
        ok=True, html_path=None, diagnostics_path=None,
        diagnostics=diagnostics, profile="-", summary=analysis.summary,
    )


def _failure(message: str, code: str, profile_name: str) -> RenderResult:
    return RenderResult(
        ok=False, html_path=None, diagnostics_path=None,
        diagnostics=[Diagnostic("error", code, message)],
        profile=profile_name,
    )


def _analysis_diagnostics(tree, analysis: Analysis) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    inv = analysis.inventory

    if not document.is_tei(tree):
        diagnostics.append(Diagnostic(
            "warning", "not-tei",
            "L'élément racine n'est pas dans l'espace de noms TEI ; "
            "le rendu passera par le fallback.",
        ))

    if inv["unknown"]:
        diagnostics.append(Diagnostic(
            "warning", "unknown-elements",
            "Éléments TEI sans rendu dédié (affichés via le fallback) : "
            + _fmt(inv["unknown"]),
            details={"elements": dict(inv["unknown"])},
        ))
    if inv["non_tei"]:
        diagnostics.append(Diagnostic(
            "warning", "non-tei-elements",
            "Éléments hors espace de noms TEI : " + _fmt(inv["non_tei"]),
            details={"elements": dict(inv["non_tei"])},
        ))
    if inv["minimal"]:
        diagnostics.append(Diagnostic(
            "info", "minimal-rendering",
            "Éléments reconnus mais au rendu volontairement minimal à ce "
            "stade (apparat, témoins, fac-similés) : " + _fmt(inv["minimal"]),
            details={"elements": dict(inv["minimal"])},
        ))
    if inv["signaled"]:
        diagnostics.append(Diagnostic(
            "info", "signaled-only",
            "Éléments présents mais hors rendu à ce stade : "
            + _fmt(inv["signaled"]),
            details={"elements": dict(inv["signaled"])},
        ))
    if analysis.broken_refs:
        diagnostics.append(Diagnostic(
            "warning", "broken-local-ref",
            "Références locales sans cible dans le document : "
            + " ; ".join(analysis.broken_refs),
            details={"refs": analysis.broken_refs},
        ))
    if analysis.missing_media:
        diagnostics.append(Diagnostic(
            "warning", "missing-media",
            "Images ou fac-similés locaux introuvables : "
            + " ; ".join(analysis.missing_media),
            details={"media": analysis.missing_media},
        ))
    return diagnostics


def _fmt(counter) -> str:
    return ", ".join(f"{n} (×{c})" for n, c in sorted(counter.items()))
