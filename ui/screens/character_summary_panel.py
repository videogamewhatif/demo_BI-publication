"""
ui/screens/character_summary_panel.py
=======================================

Qué hace:
    `CharacterSummaryPanel`: la tarjeta "TU PERSONAJE" de la columna
    derecha, visible mientras se juega la sección Historia. Es un
    vistazo compacto — el sheet completo con TODOS los atributos
    vive en `ui/screens/character_screen.py` (destino "Personaje"
    del sidebar), no aquí.

Qué NO hace (a propósito):
    No hay campo de "nivel" en `models.player.Player` — este no es
    un RPG con niveles, así que donde la referencia visual mostraba
    "Nivel 3" aquí se muestra la edad real (`player.age`), que sí es
    un dato real del personaje. Tampoco hay retrato/avatar generado
    (no hay ningún servicio que lo produzca hoy): el círculo de
    avatar es un placeholder con la inicial del nombre.

    Los seis atributos mostrados aquí son un subconjunto elegido por
    espacio (columna angosta); el conjunto completo (los 9-10
    atributos reales más datos económicos/identidad) se ve en
    `character_screen.py`, no se pierde información, solo se
    reparte entre dos pantallas.

Autor: Korlo (ui/ añadida en esta sesión)
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout

from config.constant import MAX_REPUTATION, MIN_REPUTATION
from models.player import Player
from ui import theme
from ui.widgets.card import Card
from ui.widgets.stat_bar import StatBar

# Subconjunto compacto (el sheet completo está en character_screen.py).
_SUMMARY_STATS = ["reputation", "intelligence", "empathy", "discipline", "happiness", "stress"]
_STAT_LABELS = {
    "health": "Salud",
    "happiness": "Felicidad",
    "stress": "Estrés",
    "reputation": "Reputación",
    "intelligence": "Inteligencia",
    "discipline": "Disciplina",
    "creativity": "Creatividad",
    "charisma": "Carisma",
    "empathy": "Empatía",
    "appearance": "Apariencia",
}


class CharacterSummaryPanel(Card):
    """Tarjeta compacta de personaje: avatar, nombre, edad y un subconjunto de stats reales."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        section_title = QLabel("TU PERSONAJE")
        section_title.setStyleSheet(
            f"color: {theme.ACCENT_PURPLE}; font-size: {theme.FONT_SIZE_SMALL}px; "
            f"font-weight: 700; letter-spacing: 1px; border: none;"
        )
        self.body_layout.addWidget(section_title)

        header = QHBoxLayout()
        self._avatar = QLabel("?")
        self._avatar.setFixedSize(56, 56)
        self._avatar.setAlignment(Qt.AlignCenter)
        self._avatar.setStyleSheet(
            f"""
            background-color: {theme.ACCENT_PURPLE_SOFT};
            color: {theme.ACCENT_PURPLE};
            font-size: {theme.FONT_SIZE_H2}px;
            font-weight: 700;
            border-radius: 28px;
            border: none;
            """
        )

        name_col = QVBoxLayout()
        self._name_label = QLabel()
        self._name_label.setStyleSheet(
            f"color: {theme.TEXT_PRIMARY}; font-size: {theme.FONT_SIZE_H2}px; font-weight: 700; border: none;"
        )
        self._subtitle_label = QLabel()
        self._subtitle_label.setStyleSheet(
            f"color: {theme.TEXT_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px; border: none;"
        )
        self._age_badge = QLabel()
        self._age_badge.setStyleSheet(
            f"""
            color: {theme.ACCENT_PURPLE};
            background-color: {theme.ACCENT_PURPLE_SOFT};
            font-size: {theme.FONT_SIZE_TINY}px;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 8px;
            border: none;
            """
        )
        self._age_badge.setFixedWidth(70)
        self._age_badge.setAlignment(Qt.AlignCenter)

        name_col.addWidget(self._name_label)
        name_col.addWidget(self._subtitle_label)
        name_col.addWidget(self._age_badge)
        name_col.setSpacing(2)

        header.addWidget(self._avatar)
        header.addSpacing(theme.SPACE_SM)
        header.addLayout(name_col)
        header.addStretch(1)
        self.body_layout.addLayout(header)

        self.body_layout.addSpacing(theme.SPACE_SM)

        self._stat_bars: dict[str, StatBar] = {}
        for stat_name in _SUMMARY_STATS:
            minimum, maximum = (MIN_REPUTATION, MAX_REPUTATION) if stat_name == "reputation" else (0, 100)
            bar = StatBar(
                _STAT_LABELS[stat_name],
                0,
                minimum=minimum,
                maximum=maximum,
                color=theme.stat_color(stat_name),
            )
            self._stat_bars[stat_name] = bar
            self.body_layout.addWidget(bar)

    def set_player(self, player: Optional[Player]) -> None:
        """Refresca el panel con el `Player` real actual (o un estado vacío si no hay ninguno)."""
        if player is None:
            self._name_label.setText("Sin personaje")
            self._subtitle_label.setText("")
            self._age_badge.setText("")
            self._avatar.setText("?")
            return

        self._name_label.setText(player.full_name)
        self._avatar.setText((player.first_name or "?")[0].upper())
        self._age_badge.setText(f"{player.age} años")

        subtitle = player.aspiration or player.current_profession or player.civil_status.value.replace("_", " ").title()
        self._subtitle_label.setText(subtitle)

        for stat_name, bar in self._stat_bars.items():
            bar.set_value(getattr(player, stat_name))
