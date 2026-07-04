"""Tests de l'étape 2 : correspondance, images locales, stress mixte,
suggestion de profil."""

from pathlib import Path

import pytest

from tei_reader.core.service import inspect_file, render
from tei_reader.profiles.loader import list_profiles

SAMPLES = Path(__file__).resolve().parent.parent / "samples"
FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


# ------------------------- Correspondance -------------------------

@pytest.fixture(scope="module")
def letter(tmp_path_factory):
    result = render(SAMPLES / "correspondence.xml", profile="correspondence",
                    out_dir=tmp_path_factory.mktemp("letter"))
    assert result.ok
    return result


def test_correspondence_profile_exists():
    assert "correspondence" in list_profiles()


def test_correspondence_structure(letter):
    html = letter.html_path.read_text(encoding="utf-8")
    assert 'class="tei-opener"' in html
    assert 'class="tei-closer"' in html
    assert 'class="tei-dateline"' in html
    assert 'class="tei-salute"' in html
    assert 'class="tei-signed"' in html
    assert 'class="tei-address"' in html
    assert 'class="tei-addrLine"' in html
    # contenu lisible
    assert "1er décembre 1664" in html
    assert "la marquise de Sévigné" in html
    assert "Monsieur de Pomponne," in html


def test_correspondence_css_copied(letter):
    out_dir = letter.html_path.parent
    assert (out_dir / "correspondence.css").is_file()
    assert 'href="correspondence.css"' in letter.html_path.read_text(
        encoding="utf-8")


def test_correspondence_elements_not_unknown(letter):
    unknown = [d for d in letter.diagnostics if d.code == "unknown-elements"]
    if unknown:
        for name in ("opener", "closer", "dateline", "salute",
                     "signed", "address", "addrLine"):
            assert name not in unknown[0].message
    # postscript n'est pas traité : il doit rester lisible en fallback
    html = letter.html_path.read_text(encoding="utf-8")
    assert 'data-tei="postscript"' in html
    assert "avant Noël" in html


def test_correspondence_attributes_kept(letter):
    html = letter.html_path.read_text(encoding="utf-8")
    # la date TEI (élément non traité) garde son contenu et le div son type
    assert 'data-tei-type="letter"' in html
    assert 'data-tei="date"' in html


# ------------------------- Images locales -------------------------

@pytest.fixture(scope="module")
def images(tmp_path_factory):
    result = render(SAMPLES / "images.xml", profile="prose",
                    out_dir=tmp_path_factory.mktemp("images"))
    assert result.ok
    return result


def test_local_graphic_rendered_as_img(images):
    html = images.html_path.read_text(encoding="utf-8")
    assert '<img class="tei-graphic-img"' in html
    assert "vignette.svg" in html
    # le src est une URI file: absolue vers le dossier source
    assert 'src="file:' in html
    # l'attribut savant est conservé sur le conteneur
    assert 'data-tei-url="images/vignette.svg"' in html


def test_missing_graphic_stays_marker(images):
    html = images.html_path.read_text(encoding="utf-8")
    assert "[image : images/absente.png]" in html
    missing = [d for d in images.diagnostics if d.code == "missing-media"]
    assert len(missing) == 1
    assert "absente.png" in missing[0].message
    # la vignette existante et #surf1 ne sont pas signalés
    assert "vignette.svg" not in missing[0].message
    assert "#surf1" not in missing[0].message


def test_pb_facs_local_becomes_link(images):
    html = images.html_path.read_text(encoding="utf-8")
    # pb avec fac-similé local existant : lien
    assert '<a href="file:' in html
    assert "tei-pb-facs" in html
    # pb avec référence interne #surf1 : span ordinaire
    assert 'data-tei-facs="#surf1"' in html
    import re
    span_pb = re.search(r'<span class="tei-pb"[^>]*data-tei-facs="#surf1"',
                        html)
    assert span_pb is not None


def test_no_remote_media_ever(tmp_path):
    # une URL distante ne produit ni img ni missing-media : ignorée
    remote = tmp_path / "remote.xml"
    remote.write_text(
        '<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader><fileDesc>'
        "<titleStmt><title>t</title></titleStmt>"
        "<publicationStmt><p>p</p></publicationStmt>"
        "<sourceDesc><p>s</p></sourceDesc></fileDesc></teiHeader>"
        "<text><body><p>x</p>"
        '<graphic url="https://example.org/image.png"/>'
        "</body></text></TEI>",
        encoding="utf-8",
    )
    result = render(remote, profile="prose", out_dir=tmp_path / "out")
    assert result.ok
    html = result.html_path.read_text(encoding="utf-8")
    assert "<img" not in html
    assert "[image : https://example.org/image.png]" in html
    assert not any(d.code == "missing-media" for d in result.diagnostics)


# ------------------------- Stress mixte -------------------------

@pytest.fixture(scope="module", params=["prose", "verse", "drama",
                                        "correspondence", "diagnostic"])
def stress(request, tmp_path_factory):
    result = render(SAMPLES / "stress-mixed.xml", profile=request.param,
                    out_dir=tmp_path_factory.mktemp(f"stress_{request.param}"))
    return result


def test_stress_never_crashes(stress):
    assert stress.ok
    assert stress.html_path.is_file()
    assert stress.diagnostics_path.is_file()


def test_stress_all_blocks_present(stress):
    html = stress.html_path.read_text(encoding="utf-8")
    # correspondance
    assert 'class="tei-opener"' in html
    assert 'class="tei-signed"' in html
    # prose + apparat : aucune variante perdue
    assert "roseau pensant" in html
    assert "roseau qui pense" in html
    assert "tei-rdg-default" in html
    assert "la coutume" in html
    assert "l'habitude" in html or "l&#39;habitude" in html
    # poésie
    assert 'data-tei-met="12"' in html
    assert "fond de mon cœur" in html
    # théâtre
    assert 'class="tei-speaker"' in html
    assert "Me voici, me voilà !" in html
    # images : la locale en <img>, l'absente en marqueur
    assert '<img class="tei-graphic-img"' in html
    assert "[image : images/introuvable.png]" in html
    # note présente (inline ou en fin de document)
    assert "Pensées" in html


def test_stress_fallback_readable(stress):
    html = stress.html_path.read_text(encoding="utf-8")
    assert 'data-tei="blorb"' in html
    assert "langage inconnu" in html
    assert 'data-tei="persName"' in html
    assert 'data-tei="table"' in html
    assert "Une cellule" in html


def test_stress_diagnostics_coherent(stress):
    codes = {d.code for d in stress.diagnostics}
    assert "unknown-elements" in codes
    assert "broken-local-ref" in codes
    assert "missing-media" in codes
    broken = next(d for d in stress.diagnostics
                  if d.code == "broken-local-ref")
    assert "#nulle-part" in broken.message
    assert "#personnage-fantome" in broken.message
    missing = next(d for d in stress.diagnostics if d.code == "missing-media")
    assert "introuvable.png" in missing.message
    assert "vignette.svg" not in missing.message
    # les témoins W1/W2 existent : pas de faux positif
    assert "#W1" not in broken.message
    assert "#W2" not in broken.message


# --------------------- Suggestion de profil ---------------------

@pytest.mark.parametrize("sample,expected", [
    ("drama", "drama"),
    ("verse", "verse"),
    ("correspondence", "correspondence"),
    ("prose", "prose"),
    ("notes", "prose"),
    # le stress mêle tout : le théâtre gagne (règle 1)
    ("stress-mixed", "drama"),
])
def test_suggested_profile_samples(sample, expected):
    result = inspect_file(SAMPLES / f"{sample}.xml")
    assert result.ok
    assert result.summary["suggested_profile"] == expected
    assert result.summary["suggestion_reason"]


@pytest.mark.parametrize("subdir,expected", [
    ("drama", "drama"),      # Corneille, Le Cid
    ("novel", "prose"),      # Balzac
    ("poetry", "verse"),     # sonnet
])
def test_suggested_profile_real_fixtures(subdir, expected):
    files = sorted((FIXTURES / subdir).glob("*.xml"))
    assert files, f"aucune fixture dans fixtures/{subdir}"
    result = inspect_file(files[0])
    assert result.ok
    assert result.summary["suggested_profile"] == expected
