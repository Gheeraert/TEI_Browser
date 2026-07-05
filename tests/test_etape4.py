"""Tests de l'étape 4 : éléments savants communs et audit fixtures."""

from pathlib import Path

import pytest

from tei_reader.core.service import inspect_file, render


FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_common_scholarly_elements_contract(tmp_path):
    source = tmp_path / "scholarly.xml"
    source.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt><title>Test</title></titleStmt>
      <publicationStmt><p>Test.</p></publicationStmt>
      <sourceDesc><p>Test.</p></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <body>
      <p xml:id="p1">
        <date when="1919-01-01">1er janvier 1919</date>
        <name key="n1">un nom</name>
        <persName ref="#p1">Marcel Proust</persName>
        <placeName ref="#paris">Paris</placeName>
        <orgName key="org1">une revue</orgName>
        <title type="book">Du côté de chez Swann</title>
        <term type="genre">roman</term>
        <ref target="#p1">voir ce passage</ref>
        <ref target="nota:prudent">cible prudente</ref>
        <ptr target="#p1"/>
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
        "tei-date", "tei-name", "tei-persName", "tei-placeName",
        "tei-orgName", "tei-title", "tei-term", "tei-ref", "tei-ptr",
    ):
        assert f'class="{cls}' in html

    for text in (
        "1er janvier 1919", "un nom", "Marcel Proust", "Paris",
        "une revue", "Du côté de chez Swann", "roman",
        "voir ce passage", "cible prudente", "[référence : #p1]",
    ):
        assert text in html

    assert 'data-tei-when="1919-01-01"' in html
    assert 'data-tei-key="n1"' in html
    assert 'data-tei-ref="#p1"' in html
    assert 'data-tei-type="book"' in html
    assert 'data-tei-target="#p1"' in html
    assert '<a href="#p1" class="tei-ref" data-tei-target="#p1">' in html
    assert '<a href="#p1" class="tei-ptr" data-tei-target="#p1">' in html
    assert '<span class="tei-ref" data-tei-target="nota:prudent">' in html

    unknown = [d for d in result.diagnostics if d.code == "unknown-elements"]
    assert not unknown


@pytest.mark.parametrize("fixture", sorted(FIXTURES.rglob("*.xml")))
def test_real_fixtures_render_without_crash(fixture, tmp_path):
    inspected = inspect_file(fixture)
    assert inspected.ok
    result = render(
        fixture,
        profile=inspected.summary["suggested_profile"],
        out_dir=tmp_path / fixture.stem,
    )
    assert result.ok
    assert result.html_path.is_file()
