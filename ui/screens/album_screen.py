"""
ui/screens/album_screen.py
=============================

Qué hace:
    `AlbumScreen`: destino "Álbum de Vida" del sidebar
    (`What_If_Vision_Document.md` §5.5 — "interfaz central de
    meta-progresión... registro cronológico de decisiones y
    momentos ilustrados").

    Recibe `MemoryMoment` reales vía `set_moments()`
    (`GameplayScreen` los obtiene de
    `services/memory_service.py::MemoryService.list_moments()`).
    Reutiliza `ui/widgets/image_placeholder.py::SceneImage` para la
    ilustración de cada momento (thumbnail más chico) en vez de
    construir un widget de imagen nuevo — misma imagen generada por
    `services/image_service.py`, si existe; si no, el placeholder
    elegante que `SceneImage` ya sabe dibujar.

Alcance deliberadamente limitado (léase antes de tocar este
archivo):
    Vision Document §5.5 también describe el Álbum como "elemento de
    compartición social (exportable como imagen o secuencia)" — esa
    exportación NO está construida acá. Esta pantalla resuelve la
    mitad "navegable en cualquier momento durante la partida"; la
    mitad "exportable" es una pieza aparte, deliberadamente fuera de
    este alcance.

Autor: Korlo
"""

from __future__ import annotations

from typing import List, Optional

from PySide6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget

from models.memory_moment import MemoryMoment
from ui import theme
from ui.widgets.card import Card
from ui.widgets.image_placeholder import SceneImage

_CATEGORY_LABELS = {
    "nacimiento": "Nacimiento",
    "hito_educativo": "Hito educativo",
    "hito_profesional": "Hito profesional",
    "hito_relacional": "Hito relacional",
    "hito_salud": "Hito de salud",
    "consecuencia_extrema": "Consecuencia extrema",
    "desenlace_final": "Desenlace final",
}


class AlbumScreen(QWidget):
    """Destino Álbum de Vida: registro cronológico de Momentos Clave, con su ilustración si existe."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Álbum de Vida")
        title.setStyleSheet(
            f"font-size: {theme.FONT_SIZE_H2}px; font-weight: 700; color: {theme.TEXT_PRIMARY};"
        )
        outer.addWidget(title)

        self._message = QLabel(
            "Todavía no hay Momentos Clave en este Álbum. Se van a ir "
            "agregando solos a medida que tu personaje viva hitos "
            "importantes — no hay nada que hacer acá para adelantarlo."
        )
        self._message.setWordWrap(True)
        self._message.setStyleSheet(f"color: {theme.TEXT_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        outer.addWidget(self._message)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self._layout = QVBoxLayout(content)
        self._layout.setSpacing(theme.SPACE_MD)
        scroll.setWidget(content)
        outer.addWidget(scroll)

    def set_moments(self, moments: Optional[List[MemoryMoment]]) -> None:
        """Refresca el Álbum con los Momentos Clave reales del jugador, en el orden en que se desbloquearon."""
        while self._layout.count():
            child = self._layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        moments = moments or []
        self._message.setVisible(not moments)

        for moment in moments:
            card = Card()

            image = SceneImage(height=140)
            if moment.image_path:
                image.set_image_path(moment.image_path)
            card.body_layout.addWidget(image)

            name = QLabel(moment.title)
            name.setWordWrap(True)
            name.setStyleSheet(f"font-weight: 700; color: {theme.TEXT_PRIMARY};")
            card.body_layout.addWidget(name)

            category_label = _CATEGORY_LABELS.get(moment.category, moment.category)
            meta = QLabel(f"{category_label} · {moment.age_at_moment} años")
            meta.setStyleSheet(f"color: {theme.TEXT_DISABLED}; font-size: {theme.FONT_SIZE_TINY}px;")
            card.body_layout.addWidget(meta)

            text = QLabel(moment.text)
            text.setWordWrap(True)
            text.setStyleSheet(f"color: {theme.TEXT_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
            card.body_layout.addWidget(text)

            if moment.origin_decision:
                origin = QLabel(f"Decisión: {moment.origin_decision}")
                origin.setWordWrap(True)
                origin.setStyleSheet(
                    f"color: {theme.TEXT_DISABLED}; font-size: {theme.FONT_SIZE_TINY}px; font-style: italic;"
                )
                card.body_layout.addWidget(origin)

            self._layout.addWidget(card)

        self._layout.addStretch(1)
