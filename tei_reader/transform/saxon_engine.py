"""Implémentation SaxonC-HE (saxonche) du moteur de transformation.

Seul module du projet autorisé à importer saxonche.

Le PySaxonProcessor est un singleton de module : créer et détruire
plusieurs processeurs dans un même processus a causé des instabilités
dans certaines versions de SaxonC. Il n'est jamais fermé explicitement ;
l'OS récupère les ressources à la fin du processus.
"""

from __future__ import annotations

import threading
from pathlib import Path

from tei_reader.transform.engine import TransformError

_processor = None
_lock = threading.Lock()


def _get_processor():
    global _processor
    with _lock:
        if _processor is None:
            from saxonche import PySaxonProcessor

            _processor = PySaxonProcessor(license=False)
        return _processor


class SaxonEngine:
    def transform(
        self,
        source: Path,
        stylesheet: Path,
        params: dict[str, str],
    ) -> str:
        proc = _get_processor()
        try:
            xslt = proc.new_xslt30_processor()
            executable = xslt.compile_stylesheet(
                stylesheet_file=str(stylesheet)
            )
            if executable is None:
                raise TransformError(
                    f"Compilation XSLT échouée : {xslt.error_message}"
                )
            for name, value in params.items():
                executable.set_parameter(
                    name, proc.make_string_value(str(value))
                )
            html = executable.transform_to_string(source_file=str(source))
            if html is None:
                raise TransformError(
                    f"Transformation échouée : {executable.error_message}"
                )
            return html
        except TransformError:
            raise
        except Exception as exc:
            raise TransformError(f"Erreur SaxonC : {exc}") from exc
