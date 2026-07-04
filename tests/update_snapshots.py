"""Régénération VOLONTAIRE des snapshots HTML de non-régression.

À lancer uniquement quand un changement du HTML produit est assumé
(évolution du contrat, nouveau rendu), puis relire le diff git des
snapshots avant de committer :

    .\\.venv\\Scripts\\python tests\\update_snapshots.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from snapshot_common import CASES, SAMPLES, SNAPSHOT_DIR, normalize_html, \
    snapshot_path  # noqa: E402

from tei_reader.core.service import render  # noqa: E402


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for sample, profile in CASES:
            result = render(SAMPLES / f"{sample}.xml", profile=profile,
                            out_dir=Path(tmp) / f"{sample}--{profile}")
            if not result.ok:
                print(f"ÉCHEC : {sample} ({profile}) : "
                      f"{result.errors[0].message}")
                return 1
            html = result.html_path.read_text(encoding="utf-8")
            path = snapshot_path(sample, profile)
            path.write_text(normalize_html(html), encoding="utf-8")
            print(f"écrit : {path.relative_to(SNAPSHOT_DIR.parent.parent)}")
    print("Relire le diff git des snapshots avant de committer.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
