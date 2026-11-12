"""
ui/screens/character_creation/character_creation_screen.py
============================================================

Qué hace:
    Orquesta los 3 pasos de creación de personaje en un
    `QStackedWidget`, recoge los datos de cada paso, llama a
    `PlayerManager.create_player()` y emite `creation_complete(Player)`
    cuando termina — o `creation_cancelled` si el jugador pulsa
    "← Atrás" en el paso 1.

    No valida datos por su cuenta: cada paso valida los suyos y
    `PlayerManager` hace la validación final antes de crear el Player.
    Si `create_player()` lanza `PlayerCreationError` (no debería, ya
    que los pasos validaron todo previamente), se muestra el error
    sin crashear.

Autor: Korlo
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QLabel,
    QMessageBox,
    QProgressBar,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from managers.player_manager import PlayerCreationError, PlayerManager
from ui import theme
from ui.screens.character_creation.attributes_step import AttributesStep
from ui.screens.character_creation.identity_step import IdentityStep
from ui.screens.character_creation.origin_step import OriginStep
from ui.widgets.card import Card

_STEP_LABELS = ["1. Identidad", "2. Origen", "3. Atributos"]


class CharacterCreationScreen(QWidget):
    """Flujo completo de creación de personaje en 3 pasos."""

    creation_complete = Signal(object)   # Player real
    creation_cancelled = Signal()

    def __init__(self, player_manager: PlayerManager, parent=None) -> None:
        super().__init__(parent)
        self._player_manager = player_manager
        self._collected: dict = {}
        self._pending_player_id: Optional[str] = None

        layout = QVBoxLayout(self)
        layout.setSpacing(theme.SPACE_MD)

        # Encabezado
        header = Card(padding=theme.SPACE_SM)
        title = QLabel("Crear personaje")
        title.setStyleSheet(
            f"font-size: {theme.FONT_SIZE_H2}px; font-weight: 800; color: {theme.TEXT_PRIMARY};"
        )
        self._step_indicator = QLabel()
        self._step_indicator.setStyleSheet(
            f"color: {theme.TEXT_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;"
        )
        self._progress = QProgressBar()
        self._progress.setRange(0, len(_STEP_LABELS))
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(6)
        self._progress.setStyleSheet(
            f"""
            QProgressBar {{ background-color: {theme.BORDER}; border: none; border-radius: 3px; }}
            QProgressBar::chunk {{ background-color: {theme.ACCENT_PURPLE}; border-radius: 3px; }}
            """
        )
        header.body_layout.addWidget(title)
        header.body_layout.addWidget(self._step_indicator)
        header.body_layout.addWidget(self._progress)
        layout.addWidget(header)

        # Pasos
        self._stack = QStackedWidget()
        self._identity_step = IdentityStep()
        self._origin_step = OriginStep()
        self._attrs_step = AttributesStep(player_manager)

        self._identity_step.step_complete.connect(self._on_identity_done)
        self._origin_step.step_complete.connect(self._on_origin_done)
        self._origin_step.step_back.connect(self._go_back)
        self._attrs_step.step_complete.connect(self._on_attrs_done)
        self._attrs_step.step_back.connect(self._go_back)

        self._stack.addWidget(self._identity_step)
        self._stack.addWidget(self._origin_step)
        self._stack.addWidget(self._attrs_step)

        layout.addWidget(self._stack)

        self._go_to_step(0)

    def set_player_id(self, player_id: Optional[str]) -> None:
        """
        Fija el `player_id` a usar en `create_player()` (el `user.id`
        de una sesión de Supabase iniciada, para que el personaje
        quede ligado a esa cuenta). `None` = modo invitado, id nuevo.
        """
        self._pending_player_id = player_id

    # ==================================================
    # NAVEGACIÓN
    # ==================================================

    def _go_to_step(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        self._step_indicator.setText(
            f"Paso {index + 1} de {len(_STEP_LABELS)} — {_STEP_LABELS[index]}"
        )
        self._progress.setValue(index + 1)

    def _go_back(self) -> None:
        current = self._stack.currentIndex()
        if current == 0:
            self.creation_cancelled.emit()
        else:
            self._go_to_step(current - 1)

    # ==================================================
    # CALLBACKS DE CADA PASO
    # ==================================================

    def _on_identity_done(self, data: dict) -> None:
        self._collected.update(data)
        self._go_to_step(1)

    def _on_origin_done(self, data: dict) -> None:
        self._collected.update(data)
        self._go_to_step(2)

    def _on_attrs_done(self, data: dict) -> None:
        self._collected.update(data)
        try:
            player = self._player_manager.create_player(
                first_name=self._collected["first_name"],
                last_name=self._collected["last_name"],
                gender=self._collected.get("gender"),
                starting_age=self._collected["starting_age"],
                country=self._collected["country"],
                city=self._collected["city"],
                socioeconomic_origin=self._collected["socioeconomic_origin"],
                attr_deltas=self._collected.get("attr_deltas", {}),
                player_id=self._pending_player_id,
            )
        except PlayerCreationError as error:
            QMessageBox.critical(self, "Error al crear el personaje", str(error))
            return
        self.creation_complete.emit(player)

    # ==================================================
    # RESET (para poder reutilizar la pantalla si el jugador vuelve)
    # ==================================================

    def reset(self) -> None:
        self._collected = {}
        self._pending_player_id = None
        self._identity_step.reset()
        self._origin_step.reset()
        self._attrs_step.reset()
        self._go_to_step(0)
