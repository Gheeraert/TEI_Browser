"""Tests de la façade UI sans lancer de fenêtre pywebview."""

from pathlib import Path

from tei_reader.ui.app import ReaderApi, result_to_payload
from tei_reader.core.service import render


SAMPLES = Path(__file__).resolve().parent.parent / "samples"


def test_result_payload_is_serializable_shape(tmp_path):
    result = render(SAMPLES / "prose.xml", profile="prose", out_dir=tmp_path)
    payload = result_to_payload(result)

    assert payload["ok"] is True
    assert payload["html_path"]
    assert payload["html_url"].startswith("file:")
    assert isinstance(payload["diagnostics"], list)
    assert isinstance(payload["summary"], dict)
    assert payload["profile"] == "prose"


def test_reader_api_profiles_and_inspect(tmp_path):
    api = ReaderApi(out_dir=tmp_path)

    profiles = api.get_profiles()
    assert profiles["ok"] is True
    assert {p["name"] for p in profiles["profiles"]} >= {"prose", "diagnostic"}

    inspected = api.inspect_current(str(SAMPLES / "prose.xml"))
    assert inspected["ok"] is True
    assert inspected["summary"]["suggested_profile"] == "prose"
    assert inspected["file_path"].endswith("prose.xml")


def test_reader_api_render_and_external_guard(tmp_path):
    api = ReaderApi(out_dir=tmp_path)

    no_html = api.open_external_html()
    assert no_html["ok"] is False
    assert no_html["diagnostics"][0]["code"] == "ui-no-html"

    rendered = api.render_current(str(SAMPLES / "prose.xml"), "prose")
    assert rendered["ok"] is True
    assert rendered["html_url"].startswith("file:")
    assert rendered["html_path"].endswith("prose.html")
