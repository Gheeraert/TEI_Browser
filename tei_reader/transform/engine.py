"""Interface abstraite du moteur de transformation.

Toute implémentation (SaxonC aujourd'hui, autre moteur demain) doit
respecter ce contrat. Aucun autre module ne doit importer saxonche.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class TransformError(Exception):
    """Échec de compilation ou d'exécution de la transformation."""


class TransformEngine(Protocol):
    def transform(
        self,
        source: Path,
        stylesheet: Path,
        params: dict[str, str],
    ) -> str:
        """Transforme `source` avec `stylesheet` et retourne le HTML.

        Lève TransformError en cas d'échec.
        """
        ...
