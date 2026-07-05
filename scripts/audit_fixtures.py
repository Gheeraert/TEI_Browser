"""Audit empirique des fallbacks TEI dans un dossier de fixtures.

Usage :
    python scripts/audit_fixtures.py fixtures

Le script ne transforme pas les fichiers en HTML. Il réutilise le parsing
sécurisé et l'analyse Python du lecteur, puis écrit un rapport Markdown.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from lxml import etree

from tei_reader.core import document


TEI_NS = document.TEI_NS


@dataclass
class FileAudit:
    path: Path
    ok: bool
    error: str | None
    elements: Counter[str]
    unknown: Counter[str]
    profile: str
    profile_reason: str
    broken_refs: list[str]
    missing_media: list[str]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audite les éléments TEI encore rendus par fallback."
    )
    parser.add_argument(
        "root",
        nargs="?",
        default="fixtures",
        help="Dossier de fixtures XML à parcourir récursivement.",
    )
    parser.add_argument(
        "--out",
        default="docs/fallback-audit.md",
        help="Chemin du rapport Markdown à écrire.",
    )
    args = parser.parse_args()

    root = Path(args.root)
    out = Path(args.out)
    audits = audit_tree(root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_markdown(root, audits), encoding="utf-8")
    print(f"Rapport écrit : {out}")
    print(f"Fichiers XML audités : {len(audits)}")
    return 0 if all(a.ok for a in audits) else 1


def audit_tree(root: Path) -> list[FileAudit]:
    return [audit_file(path) for path in sorted(root.rglob("*.xml"))]


def audit_file(path: Path) -> FileAudit:
    try:
        tree = document.safe_parse(path)
    except document.DocumentError as exc:
        return FileAudit(
            path=path,
            ok=False,
            error=str(exc),
            elements=Counter(),
            unknown=Counter(),
            profile="-",
            profile_reason="-",
            broken_refs=[],
            missing_media=[],
        )

    analysis = document.analyze(tree, path)
    return FileAudit(
        path=path,
        ok=True,
        error=None,
        elements=count_tei_elements(tree),
        unknown=analysis.inventory["unknown"],
        profile=analysis.summary["suggested_profile"],
        profile_reason=analysis.summary["suggestion_reason"],
        broken_refs=analysis.broken_refs,
        missing_media=analysis.missing_media,
    )


def count_tei_elements(tree: etree._ElementTree) -> Counter[str]:
    counts: Counter[str] = Counter()
    for el in tree.getroot().iter():
        if not isinstance(el.tag, str):
            continue
        qname = etree.QName(el)
        if qname.namespace == TEI_NS:
            counts[qname.localname] += 1
    return counts


def render_markdown(root: Path, audits: list[FileAudit]) -> str:
    total_elements: Counter[str] = Counter()
    total_unknown: Counter[str] = Counter()
    for audit in audits:
        total_elements.update(audit.elements)
        total_unknown.update(audit.unknown)

    lines: list[str] = [
        "# Audit des fallbacks sur fixtures réelles",
        "",
        "Ce rapport est généré par `python scripts/audit_fixtures.py fixtures`.",
        "Il mesure les éléments TEI encore rendus par le fallback, sans modifier le rendu.",
        "",
        "## Résumé",
        "",
        f"- Dossier audité : `{md(root.as_posix())}`",
        f"- Fichiers XML : {len(audits)}",
        f"- Fichiers lisibles : {sum(1 for a in audits if a.ok)}",
        f"- Éléments TEI distincts : {len(total_elements)}",
        f"- Occurrences TEI : {sum(total_elements.values())}",
        f"- Éléments non traités distincts : {len(total_unknown)}",
        f"- Occurrences non traitées : {sum(total_unknown.values())}",
        "",
        "## Éléments TEI rencontrés",
        "",
    ]
    lines.extend(counter_table(total_elements, "Élément", "Occurrences"))
    lines.extend([
        "",
        "## Éléments non traités par fréquence",
        "",
    ])
    lines.extend(counter_table(total_unknown, "Élément", "Occurrences"))
    lines.extend([
        "",
        "## Profils suggérés par fichier",
        "",
        "| Fichier | Profil suggéré | Raison |",
        "|---|---:|---|",
    ])
    for audit in audits:
        rel = audit.path.as_posix()
        lines.append(
            f"| `{md(rel)}` | `{md(audit.profile)}` | {md(audit.profile_reason)} |"
        )

    lines.extend([
        "",
        "## Éléments non traités par fichier",
        "",
        "| Fichier | Occurrences | Éléments |",
        "|---|---:|---|",
    ])
    for audit in audits:
        rel = audit.path.as_posix()
        if audit.error:
            lines.append(f"| `{md(rel)}` | - | Erreur : {md(audit.error)} |")
            continue
        unknown = ", ".join(
            f"`{md(name)}` × {count}"
            for name, count in audit.unknown.most_common()
        )
        lines.append(
            f"| `{md(rel)}` | {sum(audit.unknown.values())} | {unknown or '—'} |"
        )

    lines.extend([
        "",
        "## Diagnostics importants",
        "",
        "| Fichier | Références cassées | Médias manquants |",
        "|---|---|---|",
    ])
    for audit in audits:
        rel = audit.path.as_posix()
        broken = "<br>".join(md(item) for item in audit.broken_refs) or "—"
        missing = "<br>".join(md(item) for item in audit.missing_media) or "—"
        lines.append(f"| `{md(rel)}` | {broken} | {missing} |")

    lines.extend([
        "",
        "## Candidats fréquents à traiter",
        "",
    ])
    if total_unknown:
        for name, count in total_unknown.most_common(25):
            file_count = sum(1 for audit in audits if audit.unknown.get(name, 0))
            lines.append(f"- `{md(name)}` : {count} occurrence(s), {file_count} fichier(s)")
    else:
        lines.append("- Aucun élément non traité détecté.")

    return "\n".join(lines) + "\n"


def counter_table(counter: Counter[str], name_header: str, count_header: str) -> list[str]:
    lines = [
        f"| {name_header} | {count_header} |",
        "|---|---:|",
    ]
    if not counter:
        lines.append("| — | 0 |")
        return lines
    for name, count in counter.most_common():
        lines.append(f"| `{md(name)}` | {count} |")
    return lines


def md(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    raise SystemExit(main())
