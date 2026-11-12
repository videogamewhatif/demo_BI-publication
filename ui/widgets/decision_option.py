"""
ui/widgets/decision_option.py
===============================

Qué hace:
    `DecisionOptionCard`: una tarjeta clicable que representa UNA
    opción de la escena actual (`scene["options"][i]`). Al hacer
    clic emite `chosen(option_index)`; no ejecuta ninguna lógica de
    juego por sí misma — quien la instancia (`ui/screens/story_panel.py`)
    conecta esa señal a `services.story_service.StoryService.choose_option()`,
    la función real que avanza la historia.

Por qué N tarjetas y no 2:
    El número de tarjetas que arma `StoryPanel` depende de
    `len(scene["options"])`, nunca hardcodeado a 2 — tu instrucción
    explícita ("no asumas que siempre existirán exactamente dos").

Autor: Korlo (ui/ añadida en esta sesión; colores recalculados por
llamada, no cacheados a nivel de módulo, desde que existe ui/themes/
— ver la nota en `_accents()`)
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel

from ui import theme
from ui.widgets.card import Card


def _accents() -> list[str]:
    """
    Colores por posición de tarjeta, recalculados en cada llamada
    (nunca cacheados en un global de módulo): un global calculado
    una sola vez al importar el archivo se habría congelado con el
    tema activo en ESE momento y no habría cambiado nunca más, ni
    siquiera llamando a `theme.set_theme()` después.
    """
    return [theme.ACCENT_PRIMARY, theme.ACCENT_PURPLE, theme.stat_color("charisma"), theme.stat_color("empathy")]


class DecisionOptionCard(Card):
    """Tarjeta clicable para una opción de decisión de la escena actual."""

    chosen = Signal(int)

    def __init__(self, option_index: int, label: str, parent=None) -> None:
        accents = _accents()
        accent = accents[option_index % len(accents)]
        super().__init__(parent, accent_color=accent, clickable=True)
        self._option_index = option_index

        title = QLabel(label)
        title.setWordWrap(True)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"color: {accent}; font-size: {theme.FONT_SIZE_H2}px; font-weight: 700; border: none;"
        )
        self.body_layout.addWidget(title)
        self.body_layout.addStretch(1)

        hint = QLabel("Consecuencias desconocidas")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet(f"color: {theme.TEXT_DISABLED}; font-size: {theme.FONT_SIZE_TINY}px; border: none;")
        self.body_layout.addWidget(hint)

    def mousePressEvent(self, event) -> None:  # noqa: N802 (nombre exigido por Qt)
        super().mousePressEvent(event)
        self.chosen.emit(self._option_index)
