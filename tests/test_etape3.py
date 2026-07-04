"""Tests de l'étape 3 : transcription manuscrite et choix éditoriaux."""

from tei_reader.core.service import render


def test_transcription_elements_are_readable_and_handled(tmp_path):
    source = tmp_path / "transcription.xml"
    source.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt><title>Transcription</title></titleStmt>
      <publicationStmt><p>Test.</p></publicationStmt>
      <sourceDesc><p>Test.</p></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <body>
      <p>
        <subst><del rend="overstrike">ancien</del><add place="above" hand="#h1">nouveau</add></subst>
        <choice><orig>estoit</orig><reg>était</reg></choice>
        <choice><sic>recueu</sic><corr resp="#ed">reçu</corr></choice>
        <choice><abbr>M.</abbr><expan>Monsieur</expan></choice>
        <unclear cert="low">mot</unclear>
        <gap reason="illegible" extent="2" unit="chars"/>
        <supplied reason="lost">texte restitué</supplied>
      </p>
    </body>
  </text>
</TEI>
""",
        encoding="utf-8",
    )

    result = render(source, profile="diagnostic", out_dir=tmp_path / "out")

    assert result.ok
    html = result.html_path.read_text(encoding="utf-8")
    for cls in (
        "tei-subst", "tei-del", "tei-add", "tei-choice", "tei-orig",
        "tei-reg", "tei-sic", "tei-corr", "tei-abbr", "tei-expan",
        "tei-unclear", "tei-gap", "tei-supplied",
    ):
        assert f'class="{cls}' in html

    for text in (
        "ancien", "nouveau", "estoit", "était", "recueu", "reçu",
        "M.", "Monsieur", "mot", "[lacune]", "texte restitué",
    ):
        assert text in html

    assert 'data-tei-place="above"' in html
    assert 'data-tei-hand="#h1"' in html
    assert 'data-tei-resp="#ed"' in html
    assert 'data-tei-cert="low"' in html
    assert 'data-tei-reason="illegible"' in html
    assert 'data-tei-extent="2"' in html
    assert 'data-tei-unit="chars"' in html

    unknown = [d for d in result.diagnostics if d.code == "unknown-elements"]
    assert not unknown
