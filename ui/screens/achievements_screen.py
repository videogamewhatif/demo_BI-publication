"""
ui/screens/achievements_screen.py
====================================

Qué hace:
    `AchievementsScreen`: destino "Logros" del sidebar.

Por qué está vacía por diseño:
    `models/achievement.py` (`Achievement`) sí se puede importar sin
    problema, pero no existe ningún `services/achievement_service.py`
    ni repositorio que resuelva "los logros desbloqueados por el
    jugador X" — `engine/achievement_engine.py` intentaba ese rol
    pero importa `managers.achievement_manager`, inexistente (ver
    diagnóstico). Mostrar logros aquí sería inventar contenido.

    Listo para `set_achievements()` con la lista real en cuanto ese
    servicio exista.

Autor: Korlo (ui/ añadida en esta sesión)
"""

from __future__ import annotations

from typing import List, Optional

from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

from models.achievement import Achievement
from ui import theme
from ui.widgets.card import Card


class AchievementsScreen(QWidget):
    """Destino Logros: listo para datos reales, honestamente vacío hasta que existan."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)

        card = Card()
        title = QLabel("Logros")
        title.setStyleSheet(f"font-size: {theme.FONT_SIZE_H2}px; font-weight: 700; color: {theme.TEXT_PRIMARY};")
        message = QLabel(
            "Todavía no hay un sistema que conecte logros a un jugador concreto "
            "(falta services/achievement_service.py). Esta pantalla está lista para "
            "mostrarlos en cuanto exista esa pieza."
        )
        message.setWordWrap(True)
        message.setStyleSheet(f"color: {theme.TEXT_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        card.body_layout.addWidget(title)
        card.body_layout.addWidget(message)
        layout.addWidget(card)

        self._grid = QGridLayout()
        layout.addLayout(self._grid)
        layout.addStretch(1)

    def set_achievements(self, achievements: Optional[List[Achievement]]) -> None:
        """Punto de extensión real: llamar con los Achievement reales cuando el servicio exista."""
        while self._grid.count():
            child = self._grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for i, achievement in enumerate(achievements or []):
            card = Card()
            name = QLabel(achievement.title)
            name.setStyleSheet(f"font-weight: 700; color: {theme.TEXT_PRIMARY};")
            desc = QLabel(achievement.description)
            desc.setWordWrap(True)
            desc.setStyleSheet(f"color: {theme.TEXT_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
            card.body_layout.addWidget(name)
            card.body_layout.addWidget(desc)
            row, col = divmod(i, 3)
            self._grid.addWidget(card, row, col)
