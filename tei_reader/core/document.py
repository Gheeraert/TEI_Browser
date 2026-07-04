"""Chargement sécurisé du XML source et analyse du document.

Le parsing préalable avec lxml sert trois objectifs :
1. sécurité — entités externes, DTD et réseau désactivés avant tout
   passage à SaxonC ;
2. diagnostics — inventaire des éléments non traités, vérification des
   références locales et des médias liés ;
3. résumé — comptages utiles (notes, apparats, sauts de page, images).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import re
from pathlib import Path

from lxml import etree

TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"

# Éléments disposant d'un template dédié dans resources/xsl/tei-common.xsl.
# La synchronisation est vérifiée par tests/test_contract_sync.py.
HANDLED_ELEMENTS = frozenset({
    # structure
    "TEI", "teiCorpus", "teiHeader", "text", "front", "body", "back",
    "div", "head", "p",
    # inline
    "hi", "emph", "foreign", "quote", "q",
    # notes, sauts
    "note", "lb", "pb",
    # poésie
    "lg", "l",
    # théâtre
    "sp", "speaker", "stage", "castList", "castItem", "role", "roleDesc",
    # correspondance
    "opener", "closer", "dateline", "salute", "signed", "address", "addrLine",
    # apparat critique et témoins
    "app", "lem", "rdg", "listWit", "witness",
    # transcription et normalisation éditoriale
    "add", "del", "subst", "choice", "orig", "reg", "sic", "corr",
    "abbr", "expan", "unclear", "gap", "supplied",
    # fac-similés
    "graphic",
})

# Reconnus mais au rendu volontairement minimal à ce stade.
RECOGNIZED_MINIMAL = frozenset({
    "app", "lem", "rdg", "listWit", "witness", "graphic",
})

# Présents mais hors rendu (subtree supprimé par la XSLT), signalés.
SIGNALED_ONLY = frozenset({"facsimile", "surface", "zone", "standOff"})

# Attributs pouvant contenir des références locales "#id".
REF_ATTRIBUTES = ("ref", "target", "corresp", "ana", "wit", "who", "facs")

# Éléments comptés dans le résumé des diagnostics.
SUMMARY_COUNTED = ("note", "app", "pb", "graphic")


class DocumentError(Exception):
    """XML illisible : mal formé, introuvable ou vide."""


@dataclass
class Analysis:
    inventory: dict[str, Counter]
    summary: dict
    broken_refs: list[str] = field(default_factory=list)
    missing_media: list[str] = field(default_factory=list)
    local_media: list[str] = field(default_factory=list)


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


def is_tei(tree: etree._ElementTree) -> bool:
    return etree.QName(tree.getroot()).namespace == TEI_NS


def analyze(tree: etree._ElementTree, source_path: Path) -> Analysis:
    """Analyse complète du document : inventaire, résumé, références, médias."""
    unknown: Counter = Counter()
    non_tei: Counter = Counter()
    minimal: Counter = Counter()
    signaled: Counter = Counter()
    all_tei: Counter = Counter()

    root = tree.getroot()
    header_tag = f"{{{TEI_NS}}}teiHeader"
    ids: set[str] = set()

    elements = []
    for el in root.iter():
        if not isinstance(el.tag, str):
            continue  # commentaires, PI
        elements.append(el)
        xml_id = el.get(XML_ID)
        if xml_id:
            ids.add(xml_id)

    for el in elements:
        qname = etree.QName(el)
        name = qname.localname
        if qname.namespace != TEI_NS:
            non_tei[name] += 1
            continue
        all_tei[name] += 1
        if name in SIGNALED_ONLY:
            signaled[name] += 1
            continue
        in_header = el.tag == header_tag or any(
            anc.tag == header_tag for anc in el.iterancestors()
        )
        if in_header:
            continue
        if name in RECOGNIZED_MINIMAL:
            minimal[name] += 1
        elif name not in HANDLED_ELEMENTS:
            unknown[name] += 1

    broken_refs = _check_local_refs(elements, ids)
    local_media, missing_media = _check_local_media(elements, source_path)

    suggested, reason = _suggest_profile(all_tei)
    summary = {
        "distinct_tei_elements": len(all_tei),
        "unhandled_elements": sorted(unknown),
        "unhandled_occurrences": sum(unknown.values()),
        "counts": {name: all_tei.get(name, 0) for name in SUMMARY_COUNTED},
        "suggested_profile": suggested,
        "suggestion_reason": reason,
    }

    return Analysis(
        inventory={
            "unknown": unknown,
            "non_tei": non_tei,
            "minimal": minimal,
            "signaled": signaled,
        },
        summary=summary,
        broken_refs=broken_refs,
        missing_media=missing_media,
        local_media=local_media,
    )


# Seuil de la règle « beaucoup de vers » de l'heuristique de profil.
MANY_VERSE_LINES = 10


def _suggest_profile(counts: Counter) -> tuple[str, str]:
    """Suggestion de profil par règles simples et documentées (pas de ML).

    Ordre des règles (le théâtre d'abord : une pièce en vers contient
    aussi des lg/l) :
    1. sp ou speaker présents -> drama ;
    2. lg présent, ou au moins MANY_VERSE_LINES éléments l -> verse ;
    3. opener ou closer présents -> correspondence ;
    4. sinon -> prose.
    """
    if counts["sp"] or counts["speaker"]:
        return "drama", "présence de <sp>/<speaker>"
    if counts["lg"] or counts["l"] >= MANY_VERSE_LINES:
        return "verse", (
            "présence de <lg>" if counts["lg"]
            else f"au moins {MANY_VERSE_LINES} <l>"
        )
    if counts["opener"] or counts["closer"]:
        return "correspondence", "présence de <opener>/<closer>"
    return "prose", "aucun marqueur de genre détecté"


def _check_local_refs(elements: list, ids: set[str]) -> list[str]:
    """Références locales "#id" ne correspondant à aucun xml:id du document."""
    broken: list[str] = []
    seen: set[tuple[str, str]] = set()
    for el in elements:
        for attr in REF_ATTRIBUTES:
            value = el.get(attr)
            if not value:
                continue
            for token in value.split():
                if not token.startswith("#"):
                    continue
                target = token[1:]
                if target and target not in ids and (attr, token) not in seen:
                    seen.add((attr, token))
                    broken.append(
                        f"@{attr}=\"{token}\" sur <{etree.QName(el).localname}>"
                    )
    return broken


def _check_local_media(
    elements: list, source_path: Path
) -> tuple[list[str], list[str]]:
    """Chemins locaux de graphic/@url et pb/@facs : (existants, introuvables).

    Les valeurs existantes sont retournées telles qu'écrites dans le TEI :
    elles servent à la XSLT pour décider d'afficher une image ou un lien
    (paramètre existing-media). Les références "#id", les URL distantes et
    les data: sont ignorées — aucune ressource distante n'est chargée.
    """
    existing: list[str] = []
    missing: list[str] = []
    seen: set[str] = set()
    base = source_path.resolve().parent
    for el in elements:
        name = etree.QName(el).localname
        if name == "graphic":
            value = el.get("url")
        elif name == "pb":
            value = el.get("facs")
        else:
            continue
        if not _is_local_media_reference(value):
            continue
        if value in seen:
            continue
        seen.add(value)
        if (base / value).is_file():
            existing.append(value)
        else:
            missing.append(f"<{name}> → {value}")
    return existing, missing


def _is_local_media_reference(value: str) -> bool:
    """True pour les chemins de fichiers locaux relatifs au TEI source.

    Seuls les chemins relatifs simples sont acceptés. Les URI avec schéma,
    les URL protocol-relative, les chemins absolus POSIX/Windows/UNC et les
    remontées de dossier (`..`) ne doivent ni déclencher d'accès disque/réseau
    ni produire de faux diagnostics `missing-media`.
    """
    if not value or value != value.strip() or value.startswith("#"):
        return False
    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", value):
        return False
    if value.startswith(("/", "\\", "//", "\\\\")):
        return False
    if re.match(r"^[A-Za-z]:[\\/]", value):
        return False
    parts = re.split(r"[\\/]+", value)
    if ".." in parts:
        return False
    return True
