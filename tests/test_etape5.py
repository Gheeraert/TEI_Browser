"""Tests de l'étape 5 : tokenisation, jalons et structures fréquentes."""

from pathlib import Path

import pytest

from tei_reader.core.service import inspect_file, render


FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_tokenization_and_common_structures_contract(tmp_path):
    source = tmp_path / "tokens.xml"
    source.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt><title>Tokens</title></titleStmt>
      <publicationStmt><p>Test.</p></publicationStmt>
      <sourceDesc><p>Test.</p></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <body>
      <div1 type="book" n="1">
        <head>Livre</head>
        <div2 type="chapter" n="1.1">
          <head>Chapitre</head>
          <ab type="line">
            <fw type="header" place="top" n="A">Titre courant</fw>
            <w lemma="amo" pos="VERB" msd="Mood=Ind" norm="aime" join="right">Aim</w><c join="left">e</c><pc type="comma">,</pc>
            <seg type="phrase" subtype="test" ana="#a" n="s1" corresp="#x">segment</seg>
            <milestone unit="line" n="12" type="verse" ana="#v"/>
          </ab>
        </div2>
      </div1>
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
        "tei-w", "tei-c", "tei-pc", "tei-seg", "tei-ab",
        "tei-milestone", "tei-fw", "tei-div1", "tei-div2",
    ):
        assert cls in html

    assert '<section class="tei-div1 tei-div" data-tei-type="book" data-tei-n="1">' in html
    assert '<section class="tei-div2 tei-div" data-tei-type="chapter" data-tei-n="1.1">' in html
    assert '<h2 class="tei-head">Livre</h2>' in html
    assert '<h3 class="tei-head">Chapitre</h3>' in html
    assert '<div class="tei-ab" data-tei-type="line">' in html
    assert 'class="tei-fw"' in html
    assert 'data-tei-place="top"' in html
    assert 'Titre courant' in html
    assert 'data-tei-lemma="amo"' in html
    assert 'data-tei-pos="VERB"' in html
    assert 'data-tei-msd="Mood=Ind"' in html
    assert 'data-tei-norm="aime"' in html
    assert 'data-tei-join="right"' in html
    assert '<span class="tei-w" data-tei-lemma="amo"' in html
    assert '</span><span class="tei-c" data-tei-join="left">e</span><span class="tei-pc" data-tei-type="comma">,</span>' in html
    assert 'class="tei-seg"' in html
    assert 'data-tei-subtype="test"' in html
    assert 'data-tei-corresp="#x"' in html
    assert '>segment</span>' in html
    assert 'class="tei-milestone"' in html
    assert 'data-tei-unit="line"' in html
    assert 'data-tei-n="12"' in html

    unknown = [d for d in result.diagnostics if d.code == "unknown-elements"]
    assert not unknown


@pytest.mark.parametrize("fixture", sorted(FIXTURES.rglob("*.xml")))
def test_real_fixtures_render_without_crash_after_token_support(fixture, tmp_path):
    inspected = inspect_file(fixture)
    assert inspected.ok
    result = render(
        fixture,
        profile=inspected.summary["suggested_profile"],
        out_dir=tmp_path / fixture.stem,
    )
    assert result.ok
    assert result.html_path.is_file()
