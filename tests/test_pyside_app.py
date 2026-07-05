"""Tests de la façade PySide sans lancer de fenêtre Qt."""

from pathlib import Path

from tei_reader.ui.pyside_app import (
    PYSIDE_INSTALL_MESSAGE,
    PysideReaderFacade,
    diagnostics_to_rows,
    error_payload,
    summary_to_rows,
)


SAMPLES = Path(__file__).resolve().parent.parent / "samples"


def test_pyside_module_imports_without_qtwebengine():
    assert "pip install -e .[pyside]" in PYSIDE_INSTALL_MESSAGE


def test_pyside_facade_loads_profiles_without_window(tmp_path):
    facade = PysideReaderFacade(out_dir=tmp_path)

    profiles = facade.get_profiles()

    assert {profile["name"] for profile in profiles} >= {"prose", "diagnostic"}


def test_pyside_facade_reports_no_file_cleanly(tmp_path):
    facade = PysideReaderFacade(out_dir=tmp_path)

    inspected = facade.inspect_current().to_dict()
    rendered = facade.render_current().to_dict()

    assert inspected["ok"] is False
    assert inspected["diagnostics"][0]["code"] == "ui-no-file"
    assert rendered["ok"] is False
    assert rendered["diagnostics"][0]["code"] == "ui-no-file"


def test_diagnostics_to_rows_keeps_open_shape():
    payload = error_payload("Aucun fichier TEI sélectionné.", "ui-no-file")

    rows = diagnostics_to_rows(payload.diagnostics)

    assert rows == [["error", "ui-no-file", "Aucun fichier TEI sélectionné.", ""]]


def test_summary_to_rows_handles_missing_keys_and_counts():
    rows = summary_to_rows({
        "suggested_profile": "prose",
        "counts": {"note": 2, "pb": 1},
        "unhandled_elements": ["sound", "event"],
    })

    assert ["Profil suggéré", "prose"] in rows
    assert ["Éléments non traités", "sound, event"] in rows
    assert ["Nombre de note", "2"] in rows
    assert ["Nombre de app", "0"] in rows


def test_pyside_facade_inspects_and_renders_sample(tmp_path):
    facade = PysideReaderFacade(out_dir=tmp_path)

    selected = facade.set_file(SAMPLES / "prose.xml").to_dict()
    inspected = facade.inspect_current().to_dict()
    rendered = facade.render_current("prose").to_dict()

    assert selected["ok"] is True
    assert inspected["ok"] is True
    assert inspected["summary"]["suggested_profile"] == "prose"
    assert rendered["ok"] is True
    assert rendered["html_url"].startswith("file:")
    assert rendered["html_path"].endswith("prose.html")
