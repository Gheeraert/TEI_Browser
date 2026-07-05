"""Interface desktop pywebview, couche mince au-dessus du cœur métier."""

from __future__ import annotations

import json
import tempfile
import webbrowser
from pathlib import Path
from typing import Any

from tei_reader.core.service import inspect_file, render
from tei_reader.diagnostics.models import Diagnostic, RenderResult
from tei_reader.profiles.loader import list_profiles, load_profile


ASSETS_DIR = Path(__file__).resolve().parent / "assets"


class ReaderApi:
    """API exposée à pywebview.

    Elle délègue toute la logique métier à core.service et profiles.loader.
    """

    def __init__(self, out_dir: Path | None = None) -> None:
        self.current_file: Path | None = None
        self.current_html: Path | None = None
        self.out_dir = out_dir or Path(tempfile.gettempdir()) / "tei-reader-gui"

    def get_profiles(self) -> dict[str, Any]:
        profiles = []
        for name in list_profiles():
            prof = load_profile(name)
            profiles.append({"name": name, "description": prof.description})
        return {"ok": True, "profiles": profiles}

    def open_file_dialog(self) -> dict[str, Any]:
        try:
            import webview

            window = webview.windows[0] if webview.windows else None
            if window is None:
                return _error("Aucune fenêtre webview active.", "ui-no-window")
            paths = window.create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=False,
                file_types=("Fichiers TEI/XML (*.xml)", "Tous les fichiers (*.*)"),
            )
        except Exception as exc:  # pywebview remonte des erreurs dépendantes du backend.
            return _error(str(exc), "ui-open-file")

        if not paths:
            return {"ok": False, "cancelled": True}
        self.current_file = Path(paths[0])
        return {"ok": True, "file_path": str(self.current_file)}

    def render_current(self, file_path: str | None, profile: str = "prose") -> dict[str, Any]:
        path = self._resolve_file(file_path)
        if path is None:
            return _error("Aucun fichier TEI sélectionné.", "ui-no-file")

        result = render(path, profile=profile, out_dir=self.out_dir)
        if result.html_path:
            self.current_html = result.html_path
        return self._result_payload(result)

    def inspect_current(self, file_path: str | None) -> dict[str, Any]:
        path = self._resolve_file(file_path)
        if path is None:
            return _error("Aucun fichier TEI sélectionné.", "ui-no-file")

        result = inspect_file(path)
        payload = self._result_payload(result)
        payload["file_path"] = str(path)
        return payload

    def open_external_html(self) -> dict[str, Any]:
        if not self.current_html:
            return _error("Aucun HTML rendu à ouvrir.", "ui-no-html")
        webbrowser.open(self.current_html.resolve().as_uri())
        return {
            "ok": True,
            "html_path": str(self.current_html),
            "html_url": self.current_html.resolve().as_uri(),
        }

    def _resolve_file(self, file_path: str | None) -> Path | None:
        if file_path:
            self.current_file = Path(file_path)
        return self.current_file

    def _result_payload(self, result: RenderResult) -> dict[str, Any]:
        payload = result_to_payload(result)
        if self.current_file:
            payload["file_path"] = str(self.current_file)
        return payload


def result_to_payload(result: RenderResult) -> dict[str, Any]:
    html_path = str(result.html_path) if result.html_path else None
    html_url = result.html_path.resolve().as_uri() if result.html_path else None
    diagnostics = [diagnostic_to_dict(d) for d in result.diagnostics]
    return {
        "ok": result.ok,
        "html_path": html_path,
        "html_url": html_url,
        "diagnostics": diagnostics,
        "summary": result.summary or {},
        "profile": result.profile,
    }


def diagnostic_to_dict(diag: Diagnostic) -> dict[str, Any]:
    return {
        "level": diag.level,
        "code": diag.code,
        "message": diag.message,
        "details": diag.details,
    }


def _error(message: str, code: str) -> dict[str, Any]:
    return {
        "ok": False,
        "diagnostics": [{
            "level": "error",
            "code": code,
            "message": message,
            "details": {},
        }],
        "summary": {},
        "profile": "-",
    }


def show_app() -> None:
    try:
        import webview
    except ImportError as exc:
        raise SystemExit(
            "pywebview n'est pas installé. "
            "Installez l'extra ui : pip install -e .[ui]"
        ) from exc

    api = ReaderApi()
    index = ASSETS_DIR / "index.html"
    webview.create_window(
        "TEI Reader",
        index.resolve().as_uri(),
        js_api=api,
        width=1280,
        height=860,
        min_size=(900, 620),
    )
    webview.start()


def payload_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)
