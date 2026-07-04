"""Interface en ligne de commande.

Usage :
    tei-reader render fichier.xml [--profile prose] [--out out] [--open]
    tei-reader view fichier.xml [--profile prose] [--out out]
    tei-reader profiles
"""

from __future__ import annotations

import argparse
import sys
import webbrowser
from pathlib import Path

from tei_reader.core.service import render
from tei_reader.profiles.loader import list_profiles


def main(argv: list[str] | None = None) -> int:
    # La console Windows n'est pas toujours en UTF-8.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        prog="tei-reader",
        description="Lecteur TEI-XML : TEI -> XSLT (SaxonC) -> HTML.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_render = sub.add_parser("render", help="Transformer un fichier TEI en HTML")
    _add_common(p_render)
    p_render.add_argument("--open", action="store_true",
                          help="Ouvrir le HTML dans le navigateur par défaut")

    p_view = sub.add_parser("view", help="Transformer puis afficher dans une webview")
    _add_common(p_view)

    sub.add_parser("profiles", help="Lister les profils disponibles")

    args = parser.parse_args(argv)

    if args.command == "profiles":
        for name in list_profiles():
            print(name)
        return 0

    result = render(Path(args.file), profile=args.profile, out_dir=Path(args.out))

    for diag in result.diagnostics:
        stream = sys.stderr if diag.level == "error" else sys.stdout
        print(f"[{diag.level}] {diag.code}: {diag.message}", file=stream)

    if not result.ok:
        return 1

    print(f"HTML : {result.html_path}")
    print(f"Diagnostics : {result.diagnostics_path}")

    if args.command == "view":
        from tei_reader.ui.webview_app import show
        show(result.html_path)
    elif getattr(args, "open", False):
        webbrowser.open(result.html_path.resolve().as_uri())

    return 0


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("file", help="Fichier TEI-XML à transformer")
    p.add_argument("--profile", default="prose",
                   help="Profil de rendu (défaut : prose)")
    p.add_argument("--out", default="out",
                   help="Dossier de sortie (défaut : ./out)")


if __name__ == "__main__":
    raise SystemExit(main())
