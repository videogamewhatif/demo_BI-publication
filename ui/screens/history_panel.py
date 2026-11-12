"""
ui/screens/history_panel.py
=============================

Qué hace:
    `HistoryPanel`: la tarjeta "HISTORIAL RECIENTE" de la columna
    derecha. Muestra `story.important_choices` (las etiquetas de las
    opciones que el jugador ya eligió, registradas por
    `StoryService.choose_option()` vía `Story.add_choice()`), las
    más recientes primero.

Por qué no hay iconos de "correcto/incorrecto" como en la imagen
de referencia:
    La referencia usaba ✓/✕/★ para sugerir juicio moral sobre cada
    decisión ("mentiste", "ayudaste a un extraño"). Eso contradice
    un pilar de diseño explícito del proyecto
    (`What_If_Vision_Document.md` §1-2.2 y el docstring de
    `models.player.PlayerStatistics`): el juego NO juzga las
    decisiones del jugador ni lleva contador de "buenas/malas". Por
    eso cada entrada usa un marcador neutro, nunca un ✓/✕/★.

    Tampoco se etiqueta cada entrada con su capítulo: `Story` no
    guarda a qué capítulo perteneció cada decisión (solo una lista
    plana de texto), así que mostrarlo sería inventar un dato que no
    existe.

Autor: Korlo (ui/ añadida en esta sesión)
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from models.story import Story
from ui import theme
from ui.widgets.card import Card

_MAX_ENTRIES = 6


class HistoryPanel(Card):
    """Tarjeta de historial reciente de decisiones (sin calificarlas de buenas/malas)."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        title = QLabel("HISTORIAL RECIENTE")
        title.setStyleSheet(
            f"color: {theme.ACCENT_PURPLE}; font-size: {theme.FONT_SIZE_SMALL}px; "
            f"font-weight: 700; letter-spacing: 1px; border: none;"
        )
        self.body_layout.addWidget(title)

        self._list_container = QVBoxLayout()
        self._list_container.setSpacing(theme.SPACE_SM)
        self.body_layout.addLayout(self._list_container)

        self._empty_label = QLabel("Todavía no hay decisiones registradas.")
        self._empty_label.setWordWrap(True)
        self._empty_label.setStyleSheet(
            f"color: {theme.TEXT_DISABLED}; font-size: {theme.FONT_SIZE_SMALL}px; border: none;"
        )
        self.body_layout.addWidget(self._empty_label)

    def set_story(self, story: Optional[Story]) -> None:
        """Refresca la lista con las decisiones más recientes de `story`."""
        while self._list_container.count():
            item = self._list_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        choices = list(story.important_choices) if story else []
        recent = list(reversed(choices))[:_MAX_ENTRIES]

        self._empty_label.setVisible(not recent)

        for choice_text in recent:
            entry = QWidget()
            row = QVBoxLayout(entry)
            row.setContentsMargins(0, 0, 0, 0)

            label = QLabel(f"•  {choice_text}")
            label.setWordWrap(True)
            label.setStyleSheet(
                f"color: {theme.TEXT_PRIMARY}; font-size: {theme.FONT_SIZE_SMALL}px; border: none;"
            )
            row.addWidget(label)
            self._list_container.addWidget(entry)
