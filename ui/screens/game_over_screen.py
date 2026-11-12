"""
ui/screens/game_over_screen.py
=================================

Qué hace:
    `GameOverScreen`: pantalla simple que se muestra cuando
    `managers.time_manager.TimeManager.check_life_status()` decide
    que una vida terminó — edad final, causa, capítulo alcanzado,
    el final de vida que determinó `EndingManager.determine_ending()`
    (si hay uno aplicable — `data/endings/` sigue vacía hoy, así que
    esto no se muestra todavía en la práctica), y un botón para
    volver al menú principal. No arma un "Álbum de Vida" (ese
    concepto existe en
    `What_If_Vision_Document.md` pero no hay ningún pipeline de
    `memory_moments` construido todavía que lo alimente — ver
    `docs/roadmap.md`).

Por qué las etiquetas de causa se traducen aquí y no en TimeManager:
    `TimeManager` devuelve categorías (`"salud"`, `"vejez"`,
    `"accidente"`, `"enfermedad repentina"`) — texto técnico, no
    narrativo. Esta pantalla decide cómo frasearlo para el jugador;
    si mañana el juego tiene varios idiomas, esta es la capa que
    debería resolverlo vía `LocalizationService`, no `TimeManager`.

Autor: Korlo
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from managers.time_manager import LifeEndResult
from models.player import Player
from models.story import Story
from ui import theme
from ui.widgets.card import Card

_CAUSE_LABELS = {
    "salud": "Falleció por complicaciones de salud.",
    "vejez": "Falleció de vejez.",
    "accidente": "Falleció en un accidente.",
    "enfermedad repentina": "Falleció por una enfermedad repentina.",
}


class GameOverScreen(QWidget):
    """Pantalla de fin de vida: edad final, causa, capítulo alcanzado."""

    return_to_menu = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignHCenter)
        layout.setSpacing(theme.SPACE_LG)
        layout.addStretch(1)

        card = Card()
        card.setFixedWidth(420)

        title = QLabel("Esta vida ha terminado")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"font-size: {theme.FONT_SIZE_H1}px; font-weight: 800; color: {theme.TEXT_PRIMARY};"
        )
        card.body_layout.addWidget(title)
        card.body_layout.addSpacing(theme.SPACE_SM)

        self._name_label = QLabel()
        self._name_label.setAlignment(Qt.AlignCenter)
        self._name_label.setStyleSheet(
            f"color: {theme.ACCENT_PURPLE}; font-size: {theme.FONT_SIZE_H2}px; font-weight: 700;"
        )
        card.body_layout.addWidget(self._name_label)

        self._cause_label = QLabel()
        self._cause_label.setAlignment(Qt.AlignCenter)
        self._cause_label.setWordWrap(True)
        self._cause_label.setStyleSheet(
            f"color: {theme.TEXT_PRIMARY}; font-size: {theme.FONT_SIZE_BODY}px;"
        )
        card.body_layout.addWidget(self._cause_label)

        self._age_label = QLabel()
        self._age_label.setAlignment(Qt.AlignCenter)
        self._age_label.setStyleSheet(
            f"color: {theme.TEXT_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;"
        )
        card.body_layout.addWidget(self._age_label)

        self._chapter_label = QLabel()
        self._chapter_label.setAlignment(Qt.AlignCenter)
        self._chapter_label.setStyleSheet(
            f"color: {theme.TEXT_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;"
        )
        card.body_layout.addWidget(self._chapter_label)

        self._ending_label = QLabel()
        self._ending_label.setAlignment(Qt.AlignCenter)
        self._ending_label.setWordWrap(True)
        self._ending_label.setStyleSheet(
            f"color: {theme.ACCENT_PURPLE}; font-size: {theme.FONT_SIZE_SMALL}px; font-weight: 700;"
        )
        self._ending_label.hide()
        card.body_layout.addWidget(self._ending_label)

        card.body_layout.addSpacing(theme.SPACE_MD)

        btn_menu = QPushButton("Volver al menú")
        btn_menu.setFixedHeight(44)
        btn_menu.setStyleSheet(
            f"QPushButton {{ background-color: {theme.ACCENT_PURPLE}; color: {theme.TEXT_WHITE}; "
            f"border-radius: {theme.RADIUS_SM}px; font-weight: 700; }}"
            f"QPushButton:hover {{ background-color: {theme.ACCENT_PRIMARY_HOVER}; }}"
        )
        btn_menu.clicked.connect(self.return_to_menu.emit)
        card.body_layout.addWidget(btn_menu)

        layout.addWidget(card, alignment=Qt.AlignHCenter)
        layout.addStretch(2)

    def show_result(
        self,
        player: Optional[Player],
        life_end_result: LifeEndResult,
        story: Optional[Story],
        ending_title: Optional[str] = None,
    ) -> None:
        """
        Puebla la pantalla con el resultado real de esta vida.

        `ending_title`: título del final de vida que determinó
        `managers.ending_manager.EndingManager.determine_ending()`
        contra las estadísticas finales del jugador (`data/endings/`)
        — None si no hay `EndingManager` configurado o si ningún
        final del catálogo aplicaba (catálogo vacío hoy).
        """
        name = player.full_name if player is not None else "Tu personaje"
        self._name_label.setText(name)

        cause_text = _CAUSE_LABELS.get(life_end_result.cause, life_end_result.cause)
        self._cause_label.setText(cause_text)

        self._age_label.setText(f"Edad final: {life_end_result.age_at_end} años")

        chapter_text = f"Llegó al capítulo {story.chapter}." if story is not None else "No llegó a iniciar una historia."
        self._chapter_label.setText(chapter_text)

        if ending_title:
            self._ending_label.setText(f"Final: {ending_title}")
            self._ending_label.show()
        else:
            self._ending_label.hide()
