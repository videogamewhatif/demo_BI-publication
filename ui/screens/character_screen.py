"""
ui/screens/character_screen.py
=================================

Qué hace:
    `CharacterScreen`: el destino "Personaje" del sidebar — la ficha
    completa, con TODOS los atributos reales de `models.player.Player`
    (a diferencia de `character_summary_panel.py`, que solo muestra
    un subconjunto compacto mientras se juega Historia).

Autor: Korlo (ui/ añadida en esta sesión)
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from config.constant import MAX_REPUTATION, MIN_REPUTATION
from models.player import Player
from ui import theme
from ui.widgets.card import Card
from ui.widgets.stat_bar import StatBar

_ALL_STATS = [
    "health", "happiness", "stress", "reputation",
    "intelligence", "discipline", "creativity",
    "charisma", "empathy", "appearance",
]
_STAT_LABELS = {
    "health": "Salud", "happiness": "Felicidad", "stress": "Estrés",
    "reputation": "Reputación", "intelligence": "Inteligencia",
    "discipline": "Disciplina", "creativity": "Creatividad",
    "charisma": "Carisma", "empathy": "Empatía", "appearance": "Apariencia",
}


def _section_title(text: str) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet(
        f"color: {theme.ACCENT_PURPLE}; font-size: {theme.FONT_SIZE_SMALL}px; "
        f"font-weight: 700; letter-spacing: 1px;"
    )
    return label


def _field_row(label_text: str, value_text: str) -> QWidget:
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    label = QLabel(label_text)
    label.setStyleSheet(f"color: {theme.TEXT_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
    value = QLabel(value_text)
    value.setStyleSheet(f"color: {theme.TEXT_PRIMARY}; font-size: {theme.FONT_SIZE_SMALL}px; font-weight: 600;")
    value.setAlignment(Qt.AlignRight)
    layout.addWidget(label)
    layout.addStretch(1)
    layout.addWidget(value)
    return row


class CharacterScreen(QWidget):
    """Ficha completa de personaje: todos los atributos reales, sin recortar."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self._layout = QVBoxLayout(content)
        self._layout.setSpacing(theme.SPACE_MD)
        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        self._empty_label = QLabel("Sin personaje cargado.")
        self._empty_label.setStyleSheet(f"color: {theme.TEXT_DISABLED};")
        self._layout.addWidget(self._empty_label)

        self._header_card: Optional[Card] = None
        self._stats_card: Optional[Card] = None
        self._economy_card: Optional[Card] = None
        self._identity_card: Optional[Card] = None

    def set_player(self, player: Optional[Player]) -> None:
        for card in (self._header_card, self._stats_card, self._economy_card, self._identity_card):
            if card is not None:
                card.setParent(None)
                card.deleteLater()

        self._empty_label.setVisible(player is None)
        if player is None:
            return

        self._header_card = self._build_header(player)
        self._stats_card = self._build_stats(player)
        self._economy_card = self._build_economy(player)
        self._identity_card = self._build_identity(player)

        for card in (self._header_card, self._stats_card, self._economy_card, self._identity_card):
            self._layout.insertWidget(self._layout.count() - 0, card)

    def _build_header(self, player: Player) -> Card:
        card = Card()
        title = QLabel(player.full_name)
        title.setStyleSheet(f"font-size: {theme.FONT_SIZE_H1}px; font-weight: 800; color: {theme.TEXT_PRIMARY};")
        subtitle_bits = [b for b in [player.aspiration, player.current_profession] if b]
        subtitle = QLabel(" · ".join(subtitle_bits) if subtitle_bits else "Sin aspiración registrada")
        subtitle.setStyleSheet(f"color: {theme.TEXT_SECONDARY}; font-size: {theme.FONT_SIZE_BODY}px;")
        card.body_layout.addWidget(title)
        card.body_layout.addWidget(subtitle)
        return card

    def _build_stats(self, player: Player) -> Card:
        card = Card()
        card.body_layout.addWidget(_section_title("ATRIBUTOS"))
        grid = QGridLayout()
        grid.setHorizontalSpacing(theme.SPACE_LG)
        grid.setVerticalSpacing(theme.SPACE_SM)
        for i, stat_name in enumerate(_ALL_STATS):
            minimum, maximum = (MIN_REPUTATION, MAX_REPUTATION) if stat_name == "reputation" else (0, 100)
            bar = StatBar(
                _STAT_LABELS[stat_name],
                getattr(player, stat_name),
                minimum=minimum,
                maximum=maximum,
                color=theme.stat_color(stat_name),
            )
            row, col = divmod(i, 2)
            grid.addWidget(bar, row, col)
        card.body_layout.addLayout(grid)
        return card

    def _build_economy(self, player: Player) -> Card:
        card = Card()
        card.body_layout.addWidget(_section_title("ECONOMÍA"))
        card.body_layout.addWidget(_field_row("Patrimonio neto", f"${player.net_worth:,.2f}"))
        card.body_layout.addWidget(_field_row("Ingreso anual", f"${player.annual_income:,.2f}"))
        card.body_layout.addWidget(_field_row("Deuda", f"${player.debt:,.2f}"))
        return card

    def _build_identity(self, player: Player) -> Card:
        card = Card()
        card.body_layout.addWidget(_section_title("IDENTIDAD Y TRAYECTORIA"))
        card.body_layout.addWidget(_field_row("Edad", f"{player.age} años"))
        card.body_layout.addWidget(_field_row("País", player.country or "—"))
        card.body_layout.addWidget(_field_row("Ciudad", player.city or "—"))
        card.body_layout.addWidget(
            _field_row("Origen socioeconómico", player.socioeconomic_origin.value.replace("_", " ").title())
        )
        card.body_layout.addWidget(
            _field_row("Nivel educativo", player.education_level.value.replace("_", " ").title())
        )
        card.body_layout.addWidget(
            _field_row("Estado civil", player.civil_status.value.replace("_", " ").title())
        )
        card.body_layout.addWidget(_field_row("Profesión actual", player.current_profession or "—"))
        card.body_layout.addWidget(
            _field_row("Decisiones tomadas (esta vida)", str(player.statistics.decisions_made))
        )
        card.body_layout.addWidget(
            _field_row("Momentos clave desbloqueados", str(player.statistics.key_moments_unlocked))
        )
        return card
