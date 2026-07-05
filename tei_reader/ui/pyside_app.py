"""Interface desktop PySide6, couche mince au-dessus du coeur métier."""

from __future__ import annotations

import json
import tempfile
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tei_reader.core.service import inspect_file, render
from tei_reader.diagnostics.models import Diagnostic, RenderResult
from tei_reader.profiles.loader import list_profiles, load_profile


PYSIDE_INSTALL_MESSAGE = (
    "PySide6 n'est pas installé. Installez l'extra pyside : "
    "pip install -e .[pyside]"
)


@dataclass
class UiPayload:
    ok: bool
    diagnostics: list[dict[str, Any]]
    summary: dict[str, Any]
    profile: str
    file_path: str | None = None
    html_path: str | None = None
    html_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "diagnostics": self.diagnostics,
            "summary": self.summary,
            "profile": self.profile,
            "file_path": self.file_path,
            "html_path": self.html_path,
            "html_url": self.html_url,
        }


class PysideReaderFacade:
    """Façade testable pour l'interface PySide.

    Elle ne parse pas le XML et ne connaît ni Saxon ni la XSLT : elle délègue
    aux fonctions publiques de la couche métier.
    """

    def __init__(self, out_dir: Path | None = None) -> None:
        self.current_file: Path | None = None
        self.current_html: Path | None = None
        self.current_profile = "prose"
        self.out_dir = out_dir or Path(tempfile.gettempdir()) / "tei-reader-pyside"

    def get_profiles(self) -> list[dict[str, str]]:
        return [
            {"name": name, "description": load_profile(name).description}
            for name in list_profiles()
        ]

    def set_file(self, file_path: str | Path | None) -> UiPayload:
        if not file_path:
            return error_payload("Aucun fichier TEI sélectionné.", "ui-no-file")
        path = Path(file_path)
        if not path.exists():
            return error_payload(f"Fichier introuvable : {path}", "ui-file-missing")
        self.current_file = path
        return UiPayload(
            ok=True,
            diagnostics=[],
            summary={},
            profile=self.current_profile,
            file_path=str(path),
        )

    def inspect_current(self) -> UiPayload:
        if self.current_file is None:
            return error_payload("Aucun fichier TEI sélectionné.", "ui-no-file")
        result = inspect_file(self.current_file)
        return self._result_payload(result)

    def render_current(self, profile: str | None = None) -> UiPayload:
        if self.current_file is None:
            return error_payload("Aucun fichier TEI sélectionné.", "ui-no-file")
        if profile:
            self.current_profile = profile
        result = render(
            self.current_file,
            profile=self.current_profile,
            out_dir=self.out_dir,
        )
        if result.html_path:
            self.current_html = result.html_path
        return self._result_payload(result)

    def open_external_html(self) -> UiPayload:
        if self.current_html is None:
            return error_payload("Aucun HTML rendu à ouvrir.", "ui-no-html")
        html_url = self.current_html.resolve().as_uri()
        webbrowser.open(html_url)
        return UiPayload(
            ok=True,
            diagnostics=[],
            summary={},
            profile=self.current_profile,
            file_path=str(self.current_file) if self.current_file else None,
            html_path=str(self.current_html),
            html_url=html_url,
        )

    def _result_payload(self, result: RenderResult) -> UiPayload:
        html_path = str(result.html_path) if result.html_path else None
        html_url = result.html_path.resolve().as_uri() if result.html_path else None
        return UiPayload(
            ok=result.ok,
            diagnostics=[diagnostic_to_dict(d) for d in result.diagnostics],
            summary=result.summary or {},
            profile=result.profile,
            file_path=str(self.current_file) if self.current_file else None,
            html_path=html_path,
            html_url=html_url,
        )


def diagnostic_to_dict(diag: Diagnostic) -> dict[str, Any]:
    return {
        "level": diag.level,
        "code": diag.code,
        "message": diag.message,
        "details": diag.details,
    }


def error_payload(message: str, code: str) -> UiPayload:
    return UiPayload(
        ok=False,
        diagnostics=[{
            "level": "error",
            "code": code,
            "message": message,
            "details": {},
        }],
        summary={},
        profile="-",
    )


def diagnostics_to_rows(diagnostics: list[dict[str, Any]]) -> list[list[str]]:
    rows: list[list[str]] = []
    for diag in diagnostics:
        details = diag.get("details") or {}
        rows.append([
            str(diag.get("level", "")),
            str(diag.get("code", "")),
            str(diag.get("message", "")),
            json.dumps(details, ensure_ascii=False, sort_keys=True) if details else "",
        ])
    return rows


def summary_to_rows(summary: dict[str, Any]) -> list[list[str]]:
    rows: list[list[str]] = []
    labels = [
        ("Profil suggéré", "suggested_profile"),
        ("Raison", "suggestion_reason"),
        ("Éléments TEI distincts", "distinct_tei_elements"),
        ("Occurrences non traitées", "unhandled_occurrences"),
    ]
    for label, key in labels:
        if key in summary:
            rows.append([label, _format_value(summary[key])])

    unhandled = summary.get("unhandled_elements")
    if unhandled is not None:
        rows.append(["Éléments non traités", _format_value(unhandled)])

    counts = summary.get("counts")
    if isinstance(counts, dict):
        for key in ("note", "app", "pb", "graphic"):
            rows.append([f"Nombre de {key}", str(counts.get(key, 0))])

    for key in ("broken_refs", "missing_media"):
        if key in summary:
            rows.append([key, _format_value(summary[key])])
    return rows


def _format_value(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) if value else "0"
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def _apply_light_palette(app, QtGui) -> None:
    """Force une palette claire indépendante du thème système Windows."""
    palette = QtGui.QPalette()
    c = QtGui.QColor
    Active = QtGui.QPalette.ColorGroup.Active
    Inactive = QtGui.QPalette.ColorGroup.Inactive
    Disabled = QtGui.QPalette.ColorGroup.Disabled
    R = QtGui.QPalette.ColorRole

    colors = {
        R.Window: c(245, 245, 245),
        R.WindowText: c(30, 30, 30),
        R.Base: c(255, 255, 255),
        R.AlternateBase: c(235, 235, 235),
        R.Text: c(30, 30, 30),
        R.BrightText: c(0, 0, 0),
        R.Button: c(225, 225, 225),
        R.ButtonText: c(30, 30, 30),
        R.Highlight: c(66, 133, 244),
        R.HighlightedText: c(255, 255, 255),
        R.ToolTipBase: c(255, 255, 220),
        R.ToolTipText: c(30, 30, 30),
        R.Link: c(30, 90, 200),
        R.LinkVisited: c(100, 50, 180),
        R.Mid: c(200, 200, 200),
        R.Dark: c(160, 160, 160),
        R.Shadow: c(100, 100, 100),
        R.Light: c(255, 255, 255),
        R.Midlight: c(230, 230, 230),
    }
    for role, color in colors.items():
        palette.setColor(Active, role, color)
        palette.setColor(Inactive, role, color)

    disabled_text = c(130, 130, 130)
    disabled_bg = c(210, 210, 210)
    palette.setColor(Disabled, R.Window, disabled_bg)
    palette.setColor(Disabled, R.WindowText, disabled_text)
    palette.setColor(Disabled, R.Base, c(240, 240, 240))
    palette.setColor(Disabled, R.Text, disabled_text)
    palette.setColor(Disabled, R.Button, disabled_bg)
    palette.setColor(Disabled, R.ButtonText, disabled_text)
    palette.setColor(Disabled, R.Highlight, c(180, 180, 180))
    palette.setColor(Disabled, R.HighlightedText, c(100, 100, 100))

    app.setPalette(palette)


def show_app() -> None:
    try:
        from PySide6 import QtCore, QtGui, QtWidgets
    except ImportError as exc:
        raise SystemExit(PYSIDE_INSTALL_MESSAGE) from exc

    try:
        from PySide6.QtWebEngineWidgets import QWebEngineView
    except ImportError:
        QWebEngineView = None

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    app.setApplicationName("TEI Reader")
    app.setStyle("Fusion")
    _apply_light_palette(app, QtGui)
    window = _create_main_window(QtCore, QtGui, QtWidgets, QWebEngineView)
    window.show()
    app.exec()


def _create_main_window(QtCore, QtGui, QtWidgets, QWebEngineView):
    class MainWindow(QtWidgets.QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.facade = PysideReaderFacade()
            self.setWindowTitle("TEI Reader")
            self.resize(1300, 850)
            self._build_actions()
            self._build_menu()
            self._build_toolbar()
            self._build_central()
            self._apply_style()
            self._set_status("prêt")
            self._load_profiles()

        def _build_actions(self) -> None:
            self.open_action = QtGui.QAction("Ouvrir", self)
            self.open_action.triggered.connect(self.open_file)
            self.inspect_action = QtGui.QAction("Inspecter", self)
            self.inspect_action.triggered.connect(self.inspect_current)
            self.render_action = QtGui.QAction("Rendre", self)
            self.render_action.triggered.connect(self.render_current)
            self.reload_action = QtGui.QAction("Recharger", self)
            self.reload_action.triggered.connect(self.reload_current)
            self.external_action = QtGui.QAction("Ouvrir HTML externe", self)
            self.external_action.triggered.connect(self.open_external_html)
            self.quit_action = QtGui.QAction("Quitter", self)
            self.quit_action.triggered.connect(self.close)
            self.about_action = QtGui.QAction("À propos", self)
            self.about_action.triggered.connect(self.show_about)

        def _build_menu(self) -> None:
            file_menu = self.menuBar().addMenu("Fichier")
            file_menu.addAction(self.open_action)
            file_menu.addAction(self.reload_action)
            file_menu.addAction(self.external_action)
            file_menu.addSeparator()
            file_menu.addAction(self.quit_action)

            self.profile_menu = self.menuBar().addMenu("Affichage")
            self.menuBar().addMenu("Aide").addAction(self.about_action)

        def _build_toolbar(self) -> None:
            toolbar = self.addToolBar("Outils")
            toolbar.setMovable(False)
            toolbar.addAction(self.open_action)
            self.profile_combo = QtWidgets.QComboBox()
            self.profile_combo.setMinimumWidth(180)
            self.profile_combo.currentTextChanged.connect(self.set_profile)
            toolbar.addWidget(self.profile_combo)
            toolbar.addAction(self.inspect_action)
            toolbar.addAction(self.render_action)
            toolbar.addAction(self.reload_action)
            toolbar.addAction(self.external_action)

        def _build_central(self) -> None:
            splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
            self.tabs = QtWidgets.QTabWidget()
            self.diagnostics_table = QtWidgets.QTableWidget(0, 4)
            self.diagnostics_table.setHorizontalHeaderLabels(
                ["Niveau", "Code", "Message", "Détails"]
            )
            self.diagnostics_table.horizontalHeader().setStretchLastSection(True)
            self.diagnostics_table.setSelectionBehavior(
                QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
            )
            self.summary_table = QtWidgets.QTableWidget(0, 2)
            self.summary_table.setHorizontalHeaderLabels(["Clé", "Valeur"])
            self.summary_table.horizontalHeader().setStretchLastSection(True)
            self.info_text = QtWidgets.QPlainTextEdit()
            self.info_text.setReadOnly(True)
            self.tabs.addTab(self.diagnostics_table, "Diagnostics")
            self.tabs.addTab(self.summary_table, "Résumé")
            self.tabs.addTab(self.info_text, "Infos")

            if QWebEngineView is None:
                self.web_view = None
                preview = QtWidgets.QLabel(
                    "Aperçu HTML indisponible : QtWebEngine n'est pas installé.\n"
                    "Utilisez \"Ouvrir HTML externe\" après le rendu."
                )
                preview.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                preview.setWordWrap(True)
            else:
                self.web_view = QWebEngineView()
                preview = self.web_view

            splitter.addWidget(self.tabs)
            splitter.addWidget(preview)
            splitter.setSizes([420, 880])
            self.setCentralWidget(splitter)

        def _apply_style(self) -> None:
            self.setStyleSheet("""
                QMainWindow {
                    background: #f5f5f5;
                    color: #1e1e1e;
                }
                QMenuBar {
                    background: #e8e8e8;
                    color: #1e1e1e;
                    border-bottom: 1px solid #c8c8c8;
                }
                QMenuBar::item {
                    background: transparent;
                    color: #1e1e1e;
                    padding: 4px 10px;
                }
                QMenuBar::item:selected {
                    background: #d0d8e8;
                    color: #1e1e1e;
                }
                QMenu {
                    background: #f5f5f5;
                    color: #1e1e1e;
                    border: 1px solid #c0c0c0;
                }
                QMenu::item {
                    background: transparent;
                    color: #1e1e1e;
                    padding: 5px 24px 5px 16px;
                }
                QMenu::item:selected {
                    background: #4285f4;
                    color: #ffffff;
                }
                QMenu::separator {
                    height: 1px;
                    background: #d0d0d0;
                    margin: 2px 8px;
                }
                QToolBar {
                    background: #ececec;
                    color: #1e1e1e;
                    spacing: 6px;
                    padding: 4px 6px;
                    border-bottom: 1px solid #c8c8c8;
                }
                QToolButton {
                    background: transparent;
                    color: #1e1e1e;
                    border: 1px solid transparent;
                    border-radius: 3px;
                    padding: 3px 8px;
                    min-height: 24px;
                }
                QToolButton:hover {
                    background: #d4ddf7;
                    border: 1px solid #b0bce8;
                    color: #1e1e1e;
                }
                QToolButton:pressed {
                    background: #bccaf0;
                }
                QComboBox {
                    background: #ffffff;
                    color: #1e1e1e;
                    border: 1px solid #b8b8b8;
                    border-radius: 3px;
                    padding: 3px 8px;
                    min-height: 24px;
                    min-width: 160px;
                }
                QComboBox:focus {
                    border: 1px solid #4285f4;
                }
                QComboBox QAbstractItemView {
                    background: #ffffff;
                    color: #1e1e1e;
                    selection-background-color: #4285f4;
                    selection-color: #ffffff;
                    border: 1px solid #b0b0b0;
                }
                QTabWidget::pane {
                    border: 1px solid #c8c8c8;
                    background: #ffffff;
                }
                QTabBar::tab {
                    background: #e0e0e0;
                    color: #1e1e1e;
                    border: 1px solid #c0c0c0;
                    border-bottom: none;
                    padding: 5px 14px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background: #ffffff;
                    color: #1e1e1e;
                    border-bottom: 1px solid #ffffff;
                }
                QTabBar::tab:hover:!selected {
                    background: #d4ddf7;
                }
                QTableWidget {
                    background: #ffffff;
                    color: #1e1e1e;
                    gridline-color: #dde0e5;
                    selection-background-color: #4285f4;
                    selection-color: #ffffff;
                    border: none;
                }
                QTableWidget::item {
                    padding: 3px 6px;
                    color: #1e1e1e;
                }
                QHeaderView::section {
                    background: #eaeef2;
                    color: #1e1e1e;
                    padding: 5px 8px;
                    border: none;
                    border-right: 1px solid #d0d4d8;
                    border-bottom: 1px solid #c4c8cc;
                    font-weight: bold;
                }
                QPlainTextEdit {
                    background: #ffffff;
                    color: #1e1e1e;
                    border: none;
                    selection-background-color: #4285f4;
                    selection-color: #ffffff;
                }
                QStatusBar {
                    background: #e8e8e8;
                    color: #1e1e1e;
                    border-top: 1px solid #c8c8c8;
                }
                QLabel {
                    color: #1e1e1e;
                    background: transparent;
                }
                QSplitter::handle {
                    background: #d0d0d0;
                    width: 2px;
                }
            """)

        def _load_profiles(self) -> None:
            profiles = self.facade.get_profiles()
            for prof in profiles:
                name = prof["name"]
                self.profile_combo.addItem(name)
                action = self.profile_menu.addAction(name)
                action.triggered.connect(lambda checked=False, value=name: self._select_profile(value))
            self._select_profile(self.facade.current_profile)

        def _select_profile(self, profile: str) -> None:
            index = self.profile_combo.findText(profile)
            if index >= 0:
                self.profile_combo.setCurrentIndex(index)
            self.set_profile(profile)

        def set_profile(self, profile: str) -> None:
            if profile:
                self.facade.current_profile = profile
                self._set_status("prêt")

        def open_file(self) -> None:
            file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "Ouvrir un fichier TEI",
                "",
                "Fichiers TEI/XML (*.xml);;Tous les fichiers (*.*)",
            )
            if not file_name:
                return
            payload = self.facade.set_file(file_name).to_dict()
            self._apply_payload(payload)
            if payload["ok"]:
                self.inspect_current()

        def inspect_current(self) -> None:
            self._apply_payload(self.facade.inspect_current().to_dict())

        def render_current(self) -> None:
            payload = self.facade.render_current(self.profile_combo.currentText()).to_dict()
            self._apply_payload(payload)
            if payload.get("ok") and payload.get("html_url") and self.web_view is not None:
                self.web_view.load(QtCore.QUrl(payload["html_url"]))

        def reload_current(self) -> None:
            self.inspect_current()
            if self.facade.current_file is not None:
                self.render_current()

        def open_external_html(self) -> None:
            self._apply_payload(self.facade.open_external_html().to_dict())

        def show_about(self) -> None:
            QtWidgets.QMessageBox.about(
                self,
                "À propos",
                "TEI Reader\nInterface desktop PySide6 expérimentale.",
            )

        def _apply_payload(self, payload: dict[str, Any]) -> None:
            self._fill_table(self.diagnostics_table, diagnostics_to_rows(payload["diagnostics"]))
            self._fill_table(self.summary_table, summary_to_rows(payload["summary"]))
            self.info_text.setPlainText(json.dumps(payload, ensure_ascii=False, indent=2))
            state = "rendu OK" if payload["ok"] else "erreur"
            if any(d.get("level") == "warning" for d in payload["diagnostics"]):
                state = "diagnostics"
            if any(d.get("code") == "xml-error" for d in payload["diagnostics"]):
                state = "erreur XML"
            self._set_status(state)

        def _fill_table(self, table, rows: list[list[str]]) -> None:
            table.setRowCount(len(rows))
            for row_index, row in enumerate(rows):
                for col_index, value in enumerate(row):
                    item = QtWidgets.QTableWidgetItem(value)
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
                    table.setItem(row_index, col_index, item)
            table.resizeColumnsToContents()

        def _set_status(self, state: str) -> None:
            file_text = str(self.facade.current_file) if self.facade.current_file else "aucun fichier"
            self.statusBar().showMessage(
                f"Fichier : {file_text} | Profil : {self.facade.current_profile} | État : {state}"
            )

    return MainWindow()
