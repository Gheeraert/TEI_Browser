"""Tests de l'étape 1 : poésie, théâtre, notes, apparat critique,
diagnostics enrichis, intégrité des profils."""

import json
from pathlib import Path

import pytest

from tei_reader.core.service import inspect_file, render
from tei_reader.profiles.loader import list_profiles, load_profile

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


@pytest.fixture(scope="module")
def verse_html(tmp_path_factory):
    result = render(SAMPLES / "verse.xml", profile="verse",
                    out_dir=tmp_path_factory.mktemp("verse"))
    assert result.ok
    return result.html_path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def drama_html(tmp_path_factory):
    result = render(SAMPLES / "drama.xml", profile="drama",
                    out_dir=tmp_path_factory.mktemp("drama"))
    assert result.ok
    return result.html_path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def apparatus_diag(tmp_path_factory):
    return render(SAMPLES / "apparatus.xml", profile="diagnostic",
                  out_dir=tmp_path_factory.mktemp("app_diag"))


# ---------------------------- Poésie ----------------------------

def test_verse_profile(verse_html):
    assert 'class="tei-lg"' in verse_html or "tei-lg" in verse_html
    assert 'data-tei-type="quatrain"' in verse_html
    assert 'data-tei-met="12"' in verse_html
    assert 'data-tei-n="1"' in verse_html
    assert 'data-tei-part="F"' in verse_html
    assert "mère du doux silence" in verse_html


def test_verse_css_copied(verse_html, tmp_path):
    result = render(SAMPLES / "verse.xml", profile="verse", out_dir=tmp_path)
    assert (tmp_path / "verse.css").is_file()
    assert 'href="verse.css"' in result.html_path.read_text(encoding="utf-8")


# ---------------------------- Théâtre ----------------------------

def test_drama_profile(drama_html):
    assert 'data-tei-type="act"' in drama_html
    assert 'data-tei-type="scene"' in drama_html
    assert 'class="tei-speaker"' in drama_html
    assert 'class="tei-stage"' in drama_html
    assert 'class="tei-castList"' in drama_html
    assert 'class="tei-role"' in drama_html
    assert 'class="tei-roleDesc"' in drama_html
    assert 'data-tei-who="#eraste"' in drama_html
    assert "atteinte secrète" in drama_html


def test_drama_local_refs_resolve(tmp_path):
    result = render(SAMPLES / "drama.xml", profile="drama", out_dir=tmp_path)
    codes = {d.code for d in result.diagnostics}
    assert "broken-local-ref" not in codes


# ---------------------------- Notes ----------------------------

def test_notes_end_mode(tmp_path):
    result = render(SAMPLES / "notes.xml", profile="prose", out_dir=tmp_path)
    assert result.ok
    html = result.html_path.read_text(encoding="utf-8")
    assert 'class="tei-notes"' in html
    assert 'class="tei-note-ref"' in html
    assert "Note infrapaginale de l'éditeur." in html
    # le marqueur @n est respecté
    assert ">a<" in html or ">a.<" in html.replace("</span>", "<")
    # attributs conservés sur les notes finales
    assert 'data-tei-type="gloss"' in html
    assert 'data-tei-place="margin"' in html


def test_notes_inline_mode(tmp_path):
    result = render(SAMPLES / "notes.xml", profile="diagnostic", out_dir=tmp_path)
    html = result.html_path.read_text(encoding="utf-8")
    assert 'class="tei-notes"' not in html
    assert 'class="tei-note"' in html
    assert "Glose en marge" in html


# ------------------------ Apparat critique ------------------------

def test_apparatus_diagnostic_keeps_variants(apparatus_diag):
    html = apparatus_diag.html_path.read_text(encoding="utf-8")
    assert "roseau pensant" in html
    assert "roseau qui pense" in html
    assert 'data-tei-wit="#A"' in html
    assert 'data-tei-wit="#B"' in html
    assert 'class="tei-listWit"' in html
    assert 'class="tei-witness"' in html


def test_apparatus_prose_never_loses_text(tmp_path):
    result = render(SAMPLES / "apparatus.xml", profile="prose", out_dir=tmp_path)
    html = result.html_path.read_text(encoding="utf-8")
    # le lemme est présent et visible
    assert 'class="tei-lem"' in html
    assert "roseau pensant" in html
    # les variantes sont dans le HTML (masquées par CSS, jamais perdues)
    assert "roseau qui pense" in html
    # app sans lem : le premier rdg reste visible
    assert "tei-rdg-default" in html
    assert "confond" in html


def test_apparatus_broken_ref_detected(apparatus_diag):
    broken = [d for d in apparatus_diag.diagnostics
              if d.code == "broken-local-ref"]
    assert broken
    assert "#Z" in broken[0].message


# ---------------------------- Profils ----------------------------

def test_all_profiles_are_valid():
    names = list_profiles()
    assert {"prose", "diagnostic", "verse", "drama"} <= set(names)
    for name in names:
        prof = load_profile(name)  # vérifie l'existence des XSLT et CSS
        assert prof.xslt.is_file()
        for css in prof.css:
            assert css.is_file()
        assert prof.description


# --------------------------- Diagnostics ---------------------------

def test_summary_counts(tmp_path):
    result = render(SAMPLES / "facsimile.xml", profile="prose", out_dir=tmp_path)
    assert result.ok
    data = json.loads(result.diagnostics_path.read_text(encoding="utf-8"))
    counts = data["summary"]["counts"]
    assert counts["pb"] == 2
    assert counts["graphic"] == 2  # une dans facsimile, une dans le texte
    assert data["summary"]["distinct_tei_elements"] > 5

    notes = render(SAMPLES / "notes.xml", profile="prose", out_dir=tmp_path)
    assert notes.summary["counts"]["note"] == 3

    app = render(SAMPLES / "apparatus.xml", profile="prose", out_dir=tmp_path)
    assert app.summary["counts"]["app"] == 3


def test_missing_media_detected(tmp_path):
    result = render(SAMPLES / "facsimile.xml", profile="prose", out_dir=tmp_path)
    missing = [d for d in result.diagnostics if d.code == "missing-media"]
    assert missing
    message = missing[0].message
    assert "page2-absente.png" in message
    assert "vignette-absente.png" in message
    # la référence #surf1 pointe vers une surface existante : pas de faux positif
    assert not any(d.code == "broken-local-ref" for d in result.diagnostics)


def test_inspect_without_render():
    result = inspect_file(SAMPLES / "drama.xml")
    assert result.ok
    assert result.html_path is None
    assert result.summary["distinct_tei_elements"] > 10


def test_inspect_malformed():
    result = inspect_file(SAMPLES / "malformed.xml")
    assert not result.ok
    assert result.errors[0].code == "xml-error"
