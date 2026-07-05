"""Tests de l'étape 0 : la chaîne TEI -> SaxonC -> XSLT -> HTML fonctionne,
le fallback ne plante pas, les diagnostics sont produits, les erreurs
sont propres.
"""

import json
from pathlib import Path

import pytest

from tei_reader.core.service import render

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


@pytest.fixture(scope="module")
def prose_result(tmp_path_factory):
    out = tmp_path_factory.mktemp("prose")
    return render(SAMPLES / "prose.xml", profile="prose", out_dir=out)


@pytest.fixture(scope="module")
def unknown_result(tmp_path_factory):
    out = tmp_path_factory.mktemp("unknown")
    return render(SAMPLES / "unknown-element.xml", profile="diagnostic", out_dir=out)


def test_prose_produces_html(prose_result):
    assert prose_result.ok
    assert prose_result.html_path is not None
    html = prose_result.html_path.read_text(encoding="utf-8")
    assert "<!DOCTYPE html" in html.lower() or "<html" in html.lower()
    assert 'class="tei-p"' in html
    assert "m'effraie" in html


def test_prose_html_contract(prose_result):
    html = prose_result.html_path.read_text(encoding="utf-8")
    # classes tei-* et rend-*
    assert 'class="tei-hi rend-italic"' in html
    # xml:id -> id
    assert 'id="p2"' in html
    # attributs savants -> data-tei-*
    assert 'data-tei-type="chapter"' in html
    assert 'data-tei-place="foot"' in html
    # saut de page et saut de ligne
    assert 'class="tei-pb"' in html and 'data-tei-n="12"' in html
    assert 'class="tei-lb"' in html
    # xml:lang -> lang
    assert 'lang="la"' in html
    # titre extrait du teiHeader
    assert "Pensées diverses" in html
    # le teiHeader n'est pas rendu dans le corps
    assert "domaine public" not in html


def test_prose_copies_css(prose_result):
    out_dir = prose_result.html_path.parent
    assert (out_dir / "base.css").is_file()
    html = prose_result.html_path.read_text(encoding="utf-8")
    assert 'href="base.css"' in html


def test_unknown_element_does_not_crash(unknown_result):
    assert unknown_result.ok
    html = unknown_result.html_path.read_text(encoding="utf-8")
    # élément inventé : rendu fallback, texte lisible, nom conservé
    assert 'data-tei="blorb"' in html
    assert "texte dans un élément" in html
    # élément TEI réel désormais traité : texte lisible, attribut conservé
    assert 'class="tei-persName"' in html
    assert "Blaise Pascal" in html
    assert 'data-tei-ref="#pascal"' in html


def test_apparatus_minimal_rendering(unknown_result):
    html = unknown_result.html_path.read_text(encoding="utf-8")
    assert 'class="tei-lem"' in html
    assert 'class="tei-rdg"' in html
    assert 'data-tei-wit="#B"' in html


def test_diagnostics_produced(unknown_result):
    assert unknown_result.diagnostics_path is not None
    data = json.loads(unknown_result.diagnostics_path.read_text(encoding="utf-8"))
    codes = {d["code"] for d in data["diagnostics"]}
    assert "unknown-elements" in codes
    assert "minimal-rendering" in codes
    unknown = next(
        d for d in data["diagnostics"] if d["code"] == "unknown-elements"
    )
    assert "blorb" in unknown["details"]["elements"]
    assert "persName" not in unknown["details"]["elements"]


def test_malformed_fails_cleanly(tmp_path):
    result = render(SAMPLES / "malformed.xml", profile="prose", out_dir=tmp_path)
    assert not result.ok
    assert result.html_path is None
    assert result.errors
    assert result.errors[0].code == "xml-error"


def test_missing_file_fails_cleanly(tmp_path):
    result = render(SAMPLES / "does-not-exist.xml", out_dir=tmp_path)
    assert not result.ok
    assert result.errors[0].code == "xml-error"


def test_unknown_profile_fails_cleanly(tmp_path):
    result = render(SAMPLES / "prose.xml", profile="inexistant", out_dir=tmp_path)
    assert not result.ok
    assert result.errors[0].code == "profile-unknown"
