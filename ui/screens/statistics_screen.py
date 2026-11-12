"""
ui/screens/statistics_screen.py
==================================

Qué hace:
    `StatisticsScreen`: destino "Estadísticas" del sidebar. Combina
    dos fuentes reales y deliberadamente distintas (ver docstring de
    `services/statistics_service.py`):

    - `services.statistics_service.StatisticsService`: agregados de
      CUENTA (entre partidas) — vidas jugadas, muertes, logros.
    - `player.statistics` (`models.player.PlayerStatistics`):
      contadores de la vida EN CURSO.

Nota sobre `user_id`:
    El proyecto no tiene todavía un sistema de cuentas/login
    funcional conectado (`database/users_schema.sql` existe pero sin
    flujo de autenticación activo). En un juego local de un solo
    jugador, se usa `player.player_id` como clave de cuenta — no es
    una decisión de diseño nueva, es la clave más razonable
    disponible hasta que exista un sistema de cuentas real.

Autor: Korlo (ui/ añadida en esta sesión)
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

from models.player import Player
from services.statistics_service import StatisticsService
from ui import theme
from ui.widgets.card import Card


def _stat_tile(title: str, value: str, color: str) -> Card:
    card = Card()
    value_label = QLabel(value)
    value_label.setStyleSheet(f"color: {color}; font-size: {theme.FONT_SIZE_H1}px; font-weight: 800;")
    title_label = QLabel(title)
    title_label.setStyleSheet(f"color: {theme.TEXT_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
    card.body_layout.addWidget(value_label)
    card.body_layout.addWidget(title_label)
    return card


class StatisticsScreen(QWidget):
    """Estadísticas de cuenta (StatisticsService) + de la vida actual (player.statistics)."""

    def __init__(self, statistics_service: StatisticsService, parent=None) -> None:
        super().__init__(parent)
        self._statistics_service = statistics_service

        self._layout = QVBoxLayout(self)
        self._layout.setSpacing(theme.SPACE_MD)

        self._empty_label = QLabel("Sin personaje cargado.")
        self._empty_label.setStyleSheet(f"color: {theme.TEXT_DISABLED};")
        self._layout.addWidget(self._empty_label)

        self._grid_widget: Optional[QWidget] = None

    def set_player(self, player: Optional[Player]) -> None:
        if self._grid_widget is not None:
            self._grid_widget.setParent(None)
            self._grid_widget.deleteLater()
            self._grid_widget = None

        self._empty_label.setVisible(player is None)
        if player is None:
            return

        account_stats = self._statistics_service.get_statistics(player.player_id)

        self._grid_widget = QWidget()
        grid = QGridLayout(self._grid_widget)
        grid.setSpacing(theme.SPACE_MD)

        tiles = [
            ("Vidas jugadas (cuenta)", str(account_stats.total_games), theme.ACCENT_PURPLE),
            ("Muertes (cuenta)", str(account_stats.total_deaths), theme.stat_color("stress")),
            ("Logros desbloqueados", str(account_stats.achievements_unlocked), theme.stat_color("charisma")),
            ("Turnos jugados (vida actual)", str(player.statistics.turns_played), theme.ACCENT_PRIMARY),
            ("Decisiones tomadas (vida actual)", str(player.statistics.decisions_made), theme.stat_color("intelligence")),
            ("Momentos clave desbloqueados", str(player.statistics.key_moments_unlocked), theme.stat_color("creativity")),
        ]
        for i, (title, value, color) in enumerate(tiles):
            row, col = divmod(i, 3)
            grid.addWidget(_stat_tile(title, value, color), row, col)

        self._layout.insertWidget(self._layout.count(), self._grid_widget)
