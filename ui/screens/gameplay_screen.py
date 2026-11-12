"""
ui/screens/gameplay_screen.py
================================

Qué hace:
    `GameplayScreen`: el shell de 3 columnas de la referencia visual
    — sidebar izquierda con 7 destinos (Historia, Personaje,
    Estadísticas, Inventario, Logros, Álbum de Vida, Configuración)
    + área de contenido que cambia según el destino activo.

Por qué la navegación interna NO usa `GameScene`
(`managers/scene_manager.py`):
    `GameScene` es el nivel de "pantallas de aplicación" (Menú
    Principal, Pausa, Créditos...) con push/pop para superponer
    pantallas. Los 7 destinos de este sidebar son sub-secciones
    DENTRO de una sola `GameScene.GAMEPLAY` — como pestañas de una
    SPA, no pantallas nuevas de la aplicación. Añadir 7 valores
    nuevos a `GameScene` habría significado modificar
    `scene_manager.py` (que hoy funciona y no necesita tocarse) solo
    para un concepto de navegación que es interno a esta pantalla.
    Por eso `_Section` es un enum local, propio de este archivo.

Guardado:
    Cada vez que `StoryPanel` avanza la historia
    (`story_advanced`), se llama a `SaveManager.quick_save()` — la
    ranura de guardado rápido real. No se usa la política de
    autoguardado por turnos (`autosave_if_due`) porque esa política
    necesita un contador de turno real, y nada en el proyecto
    incrementa `player.statistics.turns_played` todavía (ver
    diagnóstico: Sistema de Consecuencias pendiente).

Inventario y logros:
    `InventoryScreen`/`AchievementsScreen` ya no quedan vacías por
    falta de conexión: `_refresh_all()` les pasa lo que devuelvan
    `InventoryService.get_inventory()` / `AchievementService.list_achievements()`
    para el jugador actual.

    Logros: `AchievementManager.check_all()` SÍ se llama ahora — pero
    no aquí, en `MainWindow._handle_life_ended()`, al terminar la
    vida (decisión explícita: revisar logros contra las
    estadísticas FINALES, no en cada decisión intermedia). Con
    `data/achievements/` vacía hoy, sigue sin desbloquear nada en la
    práctica.

    Inventario: sigue vacío en la práctica — nada llama todavía a
    `add_item()` (ningún `effects` de escena otorga objetos), pero
    `InventoryManager.use_item()` (botón "Usar" de `InventoryScreen`,
    ver `_handle_use_item`) ya funciona de punta a punta en cuanto
    haya contenido en `data/items/`.

Álbum de Vida:
    A diferencia de inventario/logros, ESTE sí produce datos reales
    hoy: `StoryPanel` desbloquea un Momento Clave cada vez que llega
    a una escena marcada con `"memory_moment"` en
    `data/scenarios/*.json` (ver `docs/content_authoring_guide.md`),
    y `MainWindow` desbloquea los otros dos de la lista curada del
    Vision Document ("nacimiento" y "desenlace_final") que no
    dependen de contenido. `_refresh_album()` puebla `AlbumScreen`
    con `MemoryService.list_moments()` — se llama al cargar sesión y
    tras cada decisión (un Momento Clave puede haberse desbloqueado
    recién).

Autor: Korlo (ui/ añadida en esta sesión; story_service -> story_manager
e inventory/achievement service añadidos en la sesión de managers de dominio)
"""

from __future__ import annotations

from enum import Enum, auto
from typing import Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from managers.audio_manager import AudioManager
from managers.event_manager import EventManager
from managers.inventory_manager import InventoryManager
from managers.language_manager import LanguageManager
from managers.memory_manager import MemoryManager
from managers.save_manager import SaveManager
from managers.story_manager import StoryManager
from managers.time_manager import LifeEndResult, TimeManager
from models.player import Player
from models.story import Story
from services.achievement_service import AchievementService
from services.consequence_service import ConsequenceService
from services.inventory_service import InventoryService
from services.memory_service import MemoryService
from services.statistics_service import StatisticsService
from ui import theme
from ui.screens.achievements_screen import AchievementsScreen
from ui.screens.album_screen import AlbumScreen
from ui.screens.character_screen import CharacterScreen
from ui.screens.character_summary_panel import CharacterSummaryPanel
from ui.screens.history_panel import HistoryPanel
from ui.screens.inventory_screen import InventoryScreen
from ui.screens.settings_screen import SettingsScreen
from ui.screens.statistics_screen import StatisticsScreen
from ui.screens.story_panel import StoryPanel
from ui.widgets.card import Card
from ui.widgets.nav_button import SidebarButton


class _Section(Enum):
    STORY = auto()
    CHARACTER = auto()
    STATISTICS = auto()
    INVENTORY = auto()
    ACHIEVEMENTS = auto()
    ALBUM = auto()
    SETTINGS = auto()


_SECTION_ORDER = [
    (_Section.STORY, "Historia", "📖"),
    (_Section.CHARACTER, "Personaje", "🧑"),
    (_Section.STATISTICS, "Estadísticas", "📊"),
    (_Section.INVENTORY, "Inventario", "🎒"),
    (_Section.ACHIEVEMENTS, "Logros", "🏆"),
    (_Section.ALBUM, "Álbum de Vida", "📔"),
    (_Section.SETTINGS, "Configuración", "⚙️"),
]


class GameplayScreen(QWidget):
    """Shell de 3 columnas: sidebar de 6 secciones + contenido de la sección activa."""

    exit_to_menu = Signal()
    life_ended = Signal(object, object)  # (Player, LifeEndResult) reenviada hacia MainWindow

    def __init__(
        self,
        *,
        story_manager: StoryManager,
        save_manager: SaveManager,
        statistics_service: StatisticsService,
        inventory_service: InventoryService,
        achievement_service: AchievementService,
        consequence_service: Optional[ConsequenceService] = None,
        time_manager: Optional[TimeManager] = None,
        event_manager: Optional[EventManager] = None,
        inventory_manager: Optional[InventoryManager] = None,
        memory_service: Optional[MemoryService] = None,
        memory_manager: Optional[MemoryManager] = None,
        audio_manager: AudioManager,
        language_manager: LanguageManager,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._story_manager = story_manager
        self._save_manager = save_manager
        self._inventory_service = inventory_service
        self._achievement_service = achievement_service
        self._inventory_manager = inventory_manager
        self._memory_service = memory_service
        self._memory_manager = memory_manager
        self._player: Optional[Player] = None
        self._story: Optional[Story] = None

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # -------------------- SIDEBAR --------------------
        sidebar = QWidget()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet(f"background-color: {theme.SIDEBAR_BG};")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(theme.SPACE_MD, theme.SPACE_LG, theme.SPACE_MD, theme.SPACE_MD)
        sidebar_layout.setSpacing(theme.SPACE_SM)

        logo = QLabel("WHAT IF?")
        logo.setStyleSheet(f"font-size: {theme.FONT_SIZE_H2}px; font-weight: 800; color: {theme.TEXT_PRIMARY};")
        sidebar_layout.addWidget(logo)
        sidebar_layout.addSpacing(theme.SPACE_LG)

        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)
        self._nav_buttons: Dict[_Section, SidebarButton] = {}
        for section, label, glyph in _SECTION_ORDER:
            button = SidebarButton(label, glyph)
            self._nav_group.addButton(button)
            self._nav_buttons[section] = button
            button.clicked.connect(lambda checked, s=section: self._show_section(s))
            sidebar_layout.addWidget(button)

        sidebar_layout.addStretch(1)

        self._progress_card = Card(padding=theme.SPACE_SM)
        progress_title = QLabel("PROGRESO ACTUAL")
        progress_title.setStyleSheet(
            f"color: {theme.ACCENT_PURPLE}; font-size: {theme.FONT_SIZE_TINY}px; font-weight: 700; letter-spacing: 1px;"
        )
        self._progress_body = QLabel("—")
        self._progress_body.setWordWrap(True)
        self._progress_body.setStyleSheet(f"color: {theme.TEXT_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        self._progress_card.body_layout.addWidget(progress_title)
        self._progress_card.body_layout.addWidget(self._progress_body)
        sidebar_layout.addWidget(self._progress_card)

        exit_button = SidebarButton("Salir del juego", "🚪")
        exit_button.setCheckable(False)
        exit_button.setStyleSheet(
            exit_button.styleSheet() + f"QPushButton {{ color: {theme.ERROR}; }}"
        )
        exit_button.clicked.connect(self.exit_to_menu.emit)
        sidebar_layout.addWidget(exit_button)

        root.addWidget(sidebar)

        # -------------------- CONTENIDO --------------------
        content_wrapper = QScrollArea()
        content_wrapper.setWidgetResizable(True)
        content_inner = QWidget()
        content_padding = QVBoxLayout(content_inner)
        content_padding.setContentsMargins(theme.SPACE_LG, theme.SPACE_LG, theme.SPACE_LG, theme.SPACE_LG)

        self._stack = QStackedWidget()
        content_padding.addWidget(self._stack)
        content_wrapper.setWidget(content_inner)
        root.addWidget(content_wrapper, stretch=1)

        # Sección Historia: centro (StoryPanel) + columna derecha (personaje + historial)
        story_section = QWidget()
        story_layout = QHBoxLayout(story_section)
        story_layout.setContentsMargins(0, 0, 0, 0)
        story_layout.setSpacing(theme.SPACE_LG)

        self._story_panel = StoryPanel(
            story_manager, consequence_service, time_manager, event_manager, memory_manager
        )
        self._story_panel.story_advanced.connect(self._handle_story_advanced)
        self._story_panel.life_ended.connect(self._handle_life_ended)
        story_layout.addWidget(self._story_panel, stretch=2)

        right_column = QVBoxLayout()
        right_column.setSpacing(theme.SPACE_MD)
        self._character_summary = CharacterSummaryPanel()
        self._history_panel = HistoryPanel()
        right_column.addWidget(self._character_summary)
        right_column.addWidget(self._history_panel)
        right_column.addStretch(1)
        right_wrapper = QWidget()
        right_wrapper.setLayout(right_column)
        right_wrapper.setFixedWidth(320)
        story_layout.addWidget(right_wrapper)

        self._character_screen = CharacterScreen()
        self._statistics_screen = StatisticsScreen(statistics_service)
        self._inventory_screen = InventoryScreen()
        self._inventory_screen.use_item_requested.connect(self._handle_use_item)
        self._achievements_screen = AchievementsScreen()
        self._album_screen = AlbumScreen()
        self._settings_screen = SettingsScreen(audio_manager, language_manager)

        self._section_index = {}
        for section, widget in [
            (_Section.STORY, story_section),
            (_Section.CHARACTER, self._character_screen),
            (_Section.STATISTICS, self._statistics_screen),
            (_Section.INVENTORY, self._inventory_screen),
            (_Section.ACHIEVEMENTS, self._achievements_screen),
            (_Section.ALBUM, self._album_screen),
            (_Section.SETTINGS, self._settings_screen),
        ]:
            self._section_index[section] = self._stack.addWidget(widget)

        self._nav_buttons[_Section.STORY].setChecked(True)
        self._stack.setCurrentIndex(self._section_index[_Section.STORY])

    # ==================================================
    # CARGA DE SESIÓN
    # ==================================================

    @property
    def current_player(self) -> Optional[Player]:
        """El `Player` de la sesión cargada actualmente, o None si no hay ninguna."""
        return self._player

    @property
    def current_story(self) -> Optional[Story]:
        """La `Story` de la sesión cargada actualmente, o None si no hay ninguna."""
        return self._story

    def load_session(self, player: Player, story: Optional[Story]) -> None:
        """Carga un Player/Story real (de una partida cargada o de la vista previa) y refresca todo."""
        self._player = player
        self._story = story
        self._refresh_all()

    def _refresh_all(self) -> None:
        self._story_panel.set_story(self._story)
        self._story_panel.set_player(self._player)
        self._character_summary.set_player(self._player)
        self._history_panel.set_story(self._story)
        self._character_screen.set_player(self._player)
        self._statistics_screen.set_player(self._player)
        self._refresh_inventory_and_achievements()
        self._refresh_album()
        self._update_progress_card()

    def _refresh_album(self) -> None:
        if self._memory_service is None or self._player is None:
            self._album_screen.set_moments([])
            return
        self._album_screen.set_moments(self._memory_service.list_moments(self._player.player_id))

    def _refresh_inventory_and_achievements(self) -> None:
        if self._player is None:
            self._inventory_screen.set_items([])
            self._achievements_screen.set_achievements([])
            return
        inventory = self._inventory_service.get_inventory(self._player.player_id)
        self._inventory_screen.set_items(inventory.items)
        achievements = self._achievement_service.list_achievements(self._player.player_id)
        self._achievements_screen.set_achievements(achievements)

    def _handle_use_item(self, item_id: str) -> None:
        """
        Botón "Usar" de `InventoryScreen`. Silencioso (sin diálogo de
        error) si falta `InventoryManager`/`Player`, o si
        `InventoryManager.use_item()` devuelve False (objeto no
        poseído o sin definición en el catálogo — `data/items/`
        sigue vacía hoy, así que esto no hace nada visible todavía).
        """
        if self._inventory_manager is None or self._player is None:
            return
        used = self._inventory_manager.use_item(self._player, item_id)
        if not used:
            return
        self._refresh_inventory_and_achievements()
        self._character_summary.set_player(self._player)
        self._character_screen.set_player(self._player)
        self._statistics_screen.set_player(self._player)
        if self._story is not None:
            self._save_manager.quick_save(self._player, [self._story])

    def _update_progress_card(self) -> None:
        if self._story is None:
            self._progress_body.setText("Sin historia activa.")
            return
        decisions = len(self._story.important_choices)
        self._progress_body.setText(
            f"Capítulo {self._story.chapter}\n{decisions} decisión(es) tomada(s)"
        )

    # ==================================================
    # NAVEGACIÓN INTERNA
    # ==================================================

    def _show_section(self, section: _Section) -> None:
        self._stack.setCurrentIndex(self._section_index[section])

    # ==================================================
    # AVANCE DE HISTORIA -> GUARDADO REAL
    # ==================================================

    def _handle_story_advanced(self, updated_story: Story) -> None:
        """
        Se dispara tras cada decisión. Desde que existe
        ConsequenceService (ver StoryPanel._apply_effects_if_any),
        una decisión puede haber cambiado estadísticas de verdad —
        por eso ahora también se refresca el panel de personaje
        compacto y la ficha completa, no solo el historial.
        """
        self._story = updated_story
        self._history_panel.set_story(self._story)
        self._character_summary.set_player(self._player)
        self._character_screen.set_player(self._player)
        self._statistics_screen.set_player(self._player)
        self._refresh_album()
        self._update_progress_card()
        if self._player is not None:
            self._save_manager.quick_save(self._player, [self._story])

    # ==================================================
    # FIN DE VIDA -> GUARDADO FINAL + REENVÍO A MainWindow
    # ==================================================

    def _handle_life_ended(self, player: Player, life_end_result: LifeEndResult) -> None:
        """
        Se dispara cuando TimeManager decide que la vida terminó
        (ver StoryPanel._advance_time_and_check_life). Refresca los
        paneles una última vez (la salud/edad finales deben quedar
        visibles), guarda el estado final, y reenvía la señal hacia
        `MainWindow`, que es quien conoce la pantalla de fin de vida
        — GameplayScreen no la construye ni la conoce.
        """
        self._character_summary.set_player(self._player)
        self._character_screen.set_player(self._player)
        self._statistics_screen.set_player(self._player)
        if self._player is not None:
            stories = [self._story] if self._story is not None else []
            self._save_manager.quick_save(self._player, stories)
        self.life_ended.emit(player, life_end_result)
