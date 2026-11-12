"""
ui/screens/main_menu_screen.py
=================================

Qué hace:
    `MainMenuScreen`: la pantalla `GameScene.MAIN_MENU`. Tres
    acciones reales y una honesta:

    - "Continuar": `SaveManager.quick_load()` — real. Se
      deshabilita si `SaveManager.save_exists(QUICKSAVE_SLOT)` es
      False, en vez de dejar que falle al pulsarlo.
    - "Nueva partida": HONESTA, no simulada. No existe ningún
      Sistema de Creación de Personaje funcional en el proyecto hoy
      (`managers.player_manager` no existe; ver diagnóstico), así
      que este botón lo dice claramente en vez de fabricar un
      personaje como si ese sistema existiera.
    - "Jugar demo": DEMO TEMPORAL - ELIMINAR CUANDO SE INTEGRE LA
      API DE IA. Reemplaza al antiguo botón "Vista previa de
      interfaz (datos de ejemplo)" (mismo lugar/estilo visual) —
      arranca la Partida Demo de presentación a inversionista
      (`services/demo_service.py`), aislada del flujo real. NO usa
      `ui/dev_preview.py` (ese fixture de desarrollo sigue existiendo
      para `tests/test_database.py`, pero ya no se llega a él desde
      este menú).
    - "Salir".

Autor: Korlo (ui/ añadida en esta sesión; botón de demo temporal
añadido en la sesión de la Partida Demo)
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from managers.save_manager import SaveManager, QUICKSAVE_SLOT
from services.save_service import SaveNotFoundError
from managers.story_manager import StoryManager
from ui import theme


def _menu_button(text: str, *, primary: bool = False) -> QPushButton:
    button = QPushButton(text)
    button.setFixedHeight(44)
    button.setMinimumWidth(260)
    if primary:
        button.setStyleSheet(
            f"""
            QPushButton {{ background-color: {theme.ACCENT_PURPLE}; color: {theme.TEXT_WHITE}; }}
            QPushButton:hover {{ background-color: {theme.ACCENT_PRIMARY_HOVER}; }}
            """
        )
    else:
        button.setStyleSheet(
            f"""
            QPushButton {{ background-color: {theme.SURFACE}; color: {theme.TEXT_PRIMARY}; border: 1px solid {theme.BORDER_STRONG}; }}
            QPushButton:hover {{ background-color: {theme.BACKGROUND}; }}
            """
        )
    return button


class MainMenuScreen(QWidget):
    """Pantalla de menú principal, con acciones reales (o honestamente pendientes)."""

    creation_complete = Signal(object)   # Player real
    creation_cancelled = Signal()
    start_gameplay = Signal(object, object)  # (Player, Story)
    start_new_game = Signal()
    # DEMO TEMPORAL - ELIMINAR CUANDO SE INTEGRE LA API DE IA
    start_demo = Signal()
    exit_requested = Signal()

    def __init__(self, save_manager: SaveManager, story_manager: StoryManager, parent=None) -> None:
        super().__init__(parent)
        self._save_manager = save_manager
        self._story_manager = story_manager

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignHCenter)
        layout.setSpacing(theme.SPACE_MD)

        title = QLabel("WHAT IF?")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"font-size: 40px; font-weight: 800; color: {theme.TEXT_PRIMARY};"
        )
        subtitle = QLabel("Un simulador de vida narrativo")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f"color: {theme.TEXT_SECONDARY}; font-size: {theme.FONT_SIZE_BODY}px;")

        layout.addStretch(1)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(theme.SPACE_LG)

        self._continue_button = _menu_button("Continuar", primary=True)
        self._continue_button.setEnabled(save_manager.save_exists(QUICKSAVE_SLOT))
        self._continue_button.clicked.connect(self._handle_continue)
        layout.addWidget(self._continue_button)

        new_game_button = _menu_button("Nueva partida")
        new_game_button.clicked.connect(self._handle_new_game)
        layout.addWidget(new_game_button)

        # DEMO TEMPORAL - ELIMINAR CUANDO SE INTEGRE LA API DE IA
        # Reemplaza al antiguo botón "Vista previa de interfaz (datos de
        # ejemplo)" — misma posición y estilo visual, nuevo propósito.
        demo_button = _menu_button("Jugar demo")
        demo_button.clicked.connect(self._handle_demo)
        layout.addWidget(demo_button)

        exit_button = _menu_button("Salir")
        exit_button.clicked.connect(self.exit_requested.emit)
        layout.addWidget(exit_button)

        layout.addStretch(2)

    def refresh_continue_button(self) -> None:
        """Reevalúa si 'Continuar' debe estar habilitado (llamado al volver del gameplay)."""
        self._continue_button.setEnabled(self._save_manager.save_exists(QUICKSAVE_SLOT))

    def _handle_continue(self) -> None:
        try:
            loaded = self._save_manager.quick_load()
        except SaveNotFoundError:
            QMessageBox.information(self, "Sin partida guardada", "Todavía no hay ninguna partida guardada.")
            self._continue_button.setEnabled(False)
            return
        story = next((s for s in loaded.stories if s.is_active), loaded.stories[0] if loaded.stories else None)
        self.start_gameplay.emit(loaded.player, story)

    def _handle_new_game(self) -> None:
        self.start_new_game.emit()

    # DEMO TEMPORAL - ELIMINAR CUANDO SE INTEGRE LA API DE IA
    def _handle_demo(self) -> None:
        self.start_demo.emit()
