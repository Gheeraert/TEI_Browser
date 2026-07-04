"""Vérifie que HANDLED_ELEMENTS (core/document.py) reste synchronisé
avec les templates de tei-common.xsl.

Le test extrait les noms tei:* des attributs @match des xsl:template
et les compare aux ensembles déclarés côté Python. Il est volontairement
strict : tout ajout d'un template TEI doit s'accompagner d'une mise à
jour de HANDLED_ELEMENTS (ou des ensembles SIGNALED_ONLY), et inversement.
"""

import re
from pathlib import Path

from lxml import etree

from tei_reader.core.document import HANDLED_ELEMENTS

XSLT_PATH = (
    Path(__file__).resolve().parent.parent
    / "tei_reader" / "resources" / "xsl" / "tei-common.xsl"
)
XSL_TEMPLATE = "{http://www.w3.org/1999/XSL/Transform}template"

# Éléments avec template (de suppression) dans la XSLT mais volontairement
# absents de HANDLED_ELEMENTS : leur sous-arbre n'est pas rendu.
SUPPRESSED_IN_XSLT = {"facsimile", "standOff"}


def _names_in_xslt() -> set[str]:
    tree = etree.parse(str(XSLT_PATH))
    names: set[str] = set()
    for template in tree.iter(XSL_TEMPLATE):
        match = template.get("match")
        if match:
            names.update(re.findall(r"tei:([A-Za-z][A-Za-z0-9]*)", match))
    return names


def test_handled_elements_matches_xslt_templates():
    xslt_names = _names_in_xslt()
    expected = set(HANDLED_ELEMENTS) | SUPPRESSED_IN_XSLT

    missing_in_python = xslt_names - expected
    missing_in_xslt = expected - xslt_names

    assert not missing_in_python, (
        "Templates XSLT sans entrée dans HANDLED_ELEMENTS "
        f"(core/document.py) : {sorted(missing_in_python)}"
    )
    assert not missing_in_xslt, (
        "Éléments déclarés dans HANDLED_ELEMENTS sans template dans "
        f"tei-common.xsl : {sorted(missing_in_xslt)}"
    )
