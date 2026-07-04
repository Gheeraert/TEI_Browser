"""Chargement sécurisé du XML source et inventaire des éléments.

Le parsing préalable avec lxml sert deux objectifs :
1. sécurité — entités externes, DTD et réseau désactivés avant tout
   passage à SaxonC ;
2. diagnostics — inventaire des éléments que la XSLT ne traite pas.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from lxml import etree

TEI_NS = "http://www.tei-c.org/ns/1.0"

# Doit rester synchronisé avec les templates de resources/xsl/tei-common.xsl.
HANDLED_ELEMENTS = frozenset({
    "TEI", "teiCorpus", "teiHeader", "text", "front", "body", "back",
    "div", "head", "p",
    "hi", "emph", "foreign", "quote", "q",
    "note", "lb", "pb",
    "lg", "l",
    "app", "lem", "rdg",
    "graphic",
})

# Reconnus mais volontairement rendus de manière minimale à l'étape 0
# (décision utilisateur : apparat et fac-similés viendront plus tard).
RECOGNIZED_MINIMAL = frozenset({
    "app", "lem", "rdg", "graphic",
})

# Présents hors <text>, signalés mais non rendus.
SIGNALED_ONLY = frozenset({"facsimile", "surface", "zone", "listWit", "witness"})


class DocumentError(Exception):
    """XML illisible : mal formé, introuvable ou vide."""


def safe_parse(path: Path) -> etree._ElementTree:
    parser = etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        load_dtd=False,
        dtd_validation=False,
        huge_tree=False,
    )
    try:
        return etree.parse(str(path), parser)
    except OSError as exc:
        raise DocumentError(f"Fichier illisible : {exc}") from exc
    except etree.XMLSyntaxError as exc:
        raise DocumentError(f"XML mal formé : {exc}") from exc


def local_name(element: etree._Element) -> str:
    return etree.QName(element).localname


def is_tei(tree: etree._ElementTree) -> bool:
    root = tree.getroot()
    return etree.QName(root).namespace == TEI_NS


def inventory(tree: etree._ElementTree) -> dict[str, Counter]:
    """Inventorie les éléments du document pour les diagnostics.

    - "unknown"   : éléments TEI de <text> sans template dédié (fallback) ;
    - "non_tei"   : éléments hors espace de noms TEI ;
    - "minimal"   : éléments reconnus mais au rendu volontairement minimal ;
    - "signaled"  : éléments hors rendu (facsimile, listWit...).
    """
    unknown: Counter = Counter()
    non_tei: Counter = Counter()
    minimal: Counter = Counter()
    signaled: Counter = Counter()

    root = tree.getroot()
    header_tag = f"{{{TEI_NS}}}teiHeader"

    for el in root.iter():
        if not isinstance(el.tag, str):
            continue  # commentaires, PI
        qname = etree.QName(el)
        name = qname.localname
        if qname.namespace != TEI_NS:
            non_tei[name] += 1
            continue
        if name in SIGNALED_ONLY:
            signaled[name] += 1
            continue
        in_header = any(
            anc.tag == header_tag for anc in el.iterancestors()
        ) or el.tag == header_tag
        if in_header:
            continue
        if name in RECOGNIZED_MINIMAL:
            minimal[name] += 1
        elif name not in HANDLED_ELEMENTS:
            unknown[name] += 1

    return {
        "unknown": unknown,
        "non_tei": non_tei,
        "minimal": minimal,
        "signaled": signaled,
    }
