"""Affichage du HTML produit dans une fenêtre pywebview (Edge WebView2).

Volontairement minimal à l'étape 0 : une fenêtre, un document.
"""

from __future__ import annotations

from pathlib import Path


def show(html_path: Path, title: str = "TEI Reader") -> None:
    try:
        import webview
    except ImportError as exc:
        raise SystemExit(
            "pywebview n'est pas installé. "
            "Installez l'extra ui : pip install -e .[ui]"
        ) from exc

    webview.create_window(title, html_path.resolve().as_uri())
    webview.start()
