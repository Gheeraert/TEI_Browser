"""Non-régression : le HTML produit est comparé à des snapshots normalisés.

Un échec signifie que le HTML produit a changé. Si le changement est
voulu, régénérer les snapshots puis relire leur diff git :

    .\\.venv\\Scripts\\python tests\\update_snapshots.py
"""

import pytest

from snapshot_common import CASES, SAMPLES, normalize_html, snapshot_path

from tei_reader.core.service import render


@pytest.mark.parametrize("sample,profile", CASES,
                         ids=[f"{s}--{p}" for s, p in CASES])
def test_snapshot(sample, profile, tmp_path):
    expected_path = snapshot_path(sample, profile)
    assert expected_path.is_file(), (
        f"Snapshot manquant : {expected_path.name}. "
        "Générer avec : python tests\\update_snapshots.py"
    )
    result = render(SAMPLES / f"{sample}.xml", profile=profile,
                    out_dir=tmp_path)
    assert result.ok
    actual = normalize_html(result.html_path.read_text(encoding="utf-8"))
    expected = expected_path.read_text(encoding="utf-8")
    assert actual == expected, (
        f"Le HTML de {sample} ({profile}) a changé. Si c'est voulu : "
        "python tests\\update_snapshots.py puis relire le diff git."
    )
