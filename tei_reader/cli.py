"""Interface en ligne de commande.

Usage :
    tei-reader render fichier.xml [--profile prose] [--out out] [--open]
    tei-reader view fichier.xml [--profile prose] [--out out]
    tei-reader inspect fichier.xml
    tei-reader profiles
    tei-reader gui
"""

from __future__ import annotations

import argparse
import sys
import webbrowser
from pathlib import Path

from tei_reader.core.service import inspect_file, render
from tei_reader.profiles.loader import list_profiles, load_profile


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

    sub.add_parser("gui", help="Ouvrir l'interface desktop de consultation")

    p_inspect = sub.add_parser(
        "inspect",
        help="Analyser un fichier TEI (résumé + diagnostics) sans produire de HTML",
    )
    p_inspect.add_argument("file", help="Fichier TEI-XML à analyser")

    sub.add_parser("profiles", help="Lister les profils disponibles")

    args = parser.parse_args(argv)

    if args.command == "profiles":
        for name in list_profiles():
            prof = load_profile(name)
            print(f"{name:<12} {prof.description}")
        return 0

    if args.command == "gui":
        from tei_reader.ui.app import show_app
        show_app()
        return 0

    if args.command == "inspect":
        return _inspect(Path(args.file))

    result = render(Path(args.file), profile=args.profile, out_dir=Path(args.out))
    _print_diagnostics(result.diagnostics)

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


def _inspect(path: Path) -> int:
    result = inspect_file(path)
    _print_diagnostics(result.diagnostics)
    if not result.ok:
        return 1
    s = result.summary
    print(f"Éléments TEI distincts : {s['distinct_tei_elements']}")
    print(f"Éléments non traités : {s['unhandled_occurrences']} occurrence(s)"
          + (f" — {', '.join(s['unhandled_elements'])}"
             if s["unhandled_elements"] else ""))
    for name, count in s["counts"].items():
        print(f"  {name} : {count}")
    broken = next((d for d in result.diagnostics
                   if d.code == "broken-local-ref"), None)
    missing = next((d for d in result.diagnostics
                    if d.code == "missing-media"), None)
    print("Références locales cassées : "
          + str(len(broken.details["refs"]) if broken else 0))
    print("Médias locaux manquants : "
          + str(len(missing.details["media"]) if missing else 0))
    print(f"Profil suggéré : {s['suggested_profile']} "
          f"({s['suggestion_reason']})")
    return 0


def _print_diagnostics(diagnostics) -> None:
    for diag in diagnostics:
        stream = sys.stderr if diag.level == "error" else sys.stdout
        print(f"[{diag.level}] {diag.code}: {diag.message}", file=stream)


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("file", help="Fichier TEI-XML à transformer")
    p.add_argument("--profile", default="prose",
                   help="Profil de rendu (défaut : prose)")
    p.add_argument("--out", default="out",
                   help="Dossier de sortie (défaut : ./out)")


if __name__ == "__main__":
    raise SystemExit(main())
