"""
ui/windows/main_window.py
============================

Qué hace:
    `MainWindow`: la ventana de sistema operativo. Aloja
    `LoginScreen`, `MainMenuScreen` y `GameplayScreen` en un
    `QStackedWidget` y mantiene esa pila sincronizada con
    `managers.scene_manager.SceneManager` — cuando la UI cambia de
    escena, se lo notifica a `SceneManager` (`change_scene`) en vez
    de limitarse a cambiar de índice localmente, para que
    `AudioManager` (suscrito a `SceneManager`) siga reaccionando
    igual que ya hace hoy.

    `LoginScreen` (`GameScene.LOGIN`) es la primera pantalla que se
    ve: permite iniciar sesión/registrarse con
    `services.auth_service.AuthService` (Supabase Auth, opcional) o
    seguir sin cuenta — nunca bloquea el juego si Supabase no está
    configurado (ver `main.py`). El `user.id` de una sesión iniciada
    se recuerda en `self._current_user_id` y se usa como `player_id`
    al crear un personaje nuevo, para que sus datos (en Postgres, si
    `SUPABASE_DB_URL` está configurada) queden ligados a esa cuenta.

Por qué no se llama `MainMenu` (el nombre que `main.py` importaba
originalmente):
    `main.py` intentaba `from ui.windows.main_menu import MainMenu`,
    pero ni el archivo ni la clase existían — no había ningún
    comportamiento previo que preservar bajo ese nombre. `MainMenu`
    como nombre describe mejor la pantalla de menú
    (`ui/screens/main_menu_screen.py`) que la ventana completa; la
    ventana se llama `MainWindow`, que es la convención estándar de
    Qt (`QMainWindow`).

Repintado en caliente al cambiar de tema:
    `MainWindow` es el único suscriptor de `ui.theme.on_theme_changed()`
    en todo el proyecto. Ninguno de los ~15 widgets de
    `ui/widgets/`/`ui/screens/` sabe reaplicar su propio estilo — cada
    uno calcula su QSS una sola vez, al construirse, con f-strings que
    leen `theme.XXX` en ese momento. Añadirle a cada uno un método de
    refresco propio habría significado tocar ~15 archivos para un
    cambio que, en Qt, se resuelve igual de bien reconstruyendo: al
    cambiar de tema, `_handle_theme_changed()` reaplica el QSS global
    de la `QApplication` y reconstruye `MainMenuScreen` y
    `GameplayScreen` desde cero (con el tema ya activo), conservando
    qué pantalla estaba visible y, si había una sesión cargada, el
    `Player`/`Story` actuales (vía las propiedades públicas
    `GameplayScreen.current_player`/`current_story`).

    Lo que NO se conserva: la sub-sección interna de `GameplayScreen`
    (Historia/Personaje/Estadísticas/Inventario/Logros/Configuración)
    — la reconstrucción siempre vuelve a mostrar "Historia". Es una
    limitación menor y deliberada: guardar y restaurar también eso
    habría significado exponer más estado interno de `GameplayScreen`
    para un beneficio pequeño.

Partida Demo (DEMO TEMPORAL - ELIMINAR CUANDO SE INTEGRE LA API DE IA):
    El botón "Jugar demo" de `MainMenuScreen` no reutiliza
    `self._gameplay_screen` (la instancia real, con `story_manager`/
    `save_manager` que sí escriben en Supabase/`saves/`) — crea una
    `GameplayScreen` NUEVA y aislada en `_handle_start_demo()`, con
    los `story_manager`/`save_manager` en memoria que arma
    `services/demo_service.py::build_demo_session()`. Se reconstruye
    desde cero en cada clic (mismo patrón que ya usa
    `_handle_theme_changed()` para las demás pantallas: quitar del
    `QStackedWidget`, `deleteLater()`, crear una nueva) para que cada
    demo empiece siempre en el Evento 1, sin arrastrar estado de la
    demo anterior. Buscar "DEMO TEMPORAL" en este archivo localiza
    exactamente las tres piezas añadidas para esto (el import, el
    handler, y las dos líneas de conexión de señales).

Autor: Korlo (ui/ añadida en esta sesión; repintado en caliente por
cambio de tema añadido después; Partida Demo añadida en la sesión de
la demo de presentación a inversionista)
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QStackedWidget

from config import settings
from managers.achievement_manager import AchievementManager
from managers.audio_manager import AudioManager
from managers.ending_manager import EndingManager
from managers.event_manager import EventManager
from managers.inventory_manager import InventoryManager
from managers.language_manager import LanguageManager
from managers.memory_manager import MemoryManager
from managers.player_manager import PlayerManager
from managers.save_manager import SaveManager
from managers.scene_manager import GameScene, SceneManager
from managers.story_manager import StoryManager
from managers.time_manager import TimeManager
from models.story import Story
from services.achievement_service import AchievementService
from services.auth_service import AuthService
from services.consequence_service import ConsequenceService
from services.demo_service import build_demo_session  # DEMO TEMPORAL - ELIMINAR CUANDO SE INTEGRE LA API DE IA
from services.inventory_service import InventoryService
from services.memory_service import MemoryService
from services.statistics_service import StatisticsService
from ui import theme
from ui.screens.character_creation.character_creation_screen import CharacterCreationScreen
from ui.screens.game_over_screen import GameOverScreen
from ui.screens.gameplay_screen import GameplayScreen
from ui.screens.login_screen import LoginScreen
from ui.screens.main_menu_screen import MainMenuScreen

# Historia real con la que arranca "Nueva partida" (data/scenarios/primer_empleo.json)
# — no la del dev_preview (ui/dev_preview.py::PREVIEW_STORY_CONTENT_ID), que es un
# fixture de desarrollo aparte, solo para el botón "Vista previa de interfaz".
NEW_GAME_STORY_CONTENT_ID = "primer_empleo"


class MainWindow(QMainWindow):
    """Ventana principal: aloja Menú Principal y Gameplay, sincronizada con SceneManager."""

    def __init__(
        self,
        *,
        scene_manager: SceneManager,
        story_manager: StoryManager,
        player_manager: PlayerManager,
        save_manager: SaveManager,
        statistics_service: StatisticsService,
        inventory_service: InventoryService,
        achievement_service: AchievementService,
        consequence_service: ConsequenceService,
        time_manager: TimeManager,
        event_manager: Optional[EventManager] = None,
        ending_manager: Optional[EndingManager] = None,
        achievement_manager: Optional[AchievementManager] = None,
        inventory_manager: Optional[InventoryManager] = None,
        memory_manager: Optional[MemoryManager] = None,
        memory_service: Optional[MemoryService] = None,
        audio_manager: AudioManager,
        language_manager: LanguageManager,
        auth_service: Optional[AuthService] = None,
    ) -> None:
        super().__init__()
        self._scene_manager = scene_manager
        self._story_manager = story_manager
        self._player_manager = player_manager
        self._save_manager = save_manager
        self._statistics_service = statistics_service
        self._inventory_service = inventory_service
        self._achievement_service = achievement_service
        self._consequence_service = consequence_service
        self._time_manager = time_manager
        self._event_manager = event_manager
        self._ending_manager = ending_manager
        self._achievement_manager = achievement_manager
        self._inventory_manager = inventory_manager
        self._memory_manager = memory_manager
        self._memory_service = memory_service
        self._audio_manager = audio_manager
        self._language_manager = language_manager
        self._auth_service = auth_service
        self._current_user_id: Optional[str] = None
        # DEMO TEMPORAL - ELIMINAR CUANDO SE INTEGRE LA API DE IA
        self._demo_gameplay_screen: Optional[GameplayScreen] = None
        self._demo_index: Optional[int] = None

        self.setWindowTitle(settings.WINDOW_TITLE)
        self.resize(settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT)
        self.setMinimumSize(settings.MIN_WIDTH, settings.MIN_HEIGHT)

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._build_screens()

        theme.on_theme_changed(self._handle_theme_changed)

    # ==================================================
    # CONSTRUCCIÓN (compartida entre __init__ y el repintado en caliente)
    # ==================================================

    def _build_screens(self) -> None:
        """(Re)crea LoginScreen, MainMenuScreen, CharacterCreationScreen, GameplayScreen y GameOverScreen y las mete en el stack."""
        self._login_screen = LoginScreen(self._auth_service)
        self._main_menu_screen = MainMenuScreen(self._save_manager, self._story_manager)
        self._creation_screen = CharacterCreationScreen(self._player_manager)
        self._gameplay_screen = GameplayScreen(
            story_manager=self._story_manager,
            save_manager=self._save_manager,
            statistics_service=self._statistics_service,
            inventory_service=self._inventory_service,
            achievement_service=self._achievement_service,
            consequence_service=self._consequence_service,
            time_manager=self._time_manager,
            event_manager=self._event_manager,
            inventory_manager=self._inventory_manager,
            memory_manager=self._memory_manager,
            memory_service=self._memory_service,
            audio_manager=self._audio_manager,
            language_manager=self._language_manager,
        )
        self._game_over_screen = GameOverScreen()

        self._login_index = self._stack.addWidget(self._login_screen)
        self._menu_index = self._stack.addWidget(self._main_menu_screen)
        self._creation_index = self._stack.addWidget(self._creation_screen)
        self._gameplay_index = self._stack.addWidget(self._gameplay_screen)
        self._game_over_index = self._stack.addWidget(self._game_over_screen)

        self._login_screen.authenticated.connect(self._handle_authenticated)
        self._login_screen.continue_as_guest.connect(self._handle_guest_continue)
        self._main_menu_screen.start_gameplay.connect(self._handle_start_gameplay)
        self._main_menu_screen.start_new_game.connect(self._handle_start_new_game)
        # DEMO TEMPORAL - ELIMINAR CUANDO SE INTEGRE LA API DE IA
        self._main_menu_screen.start_demo.connect(self._handle_start_demo)
        self._main_menu_screen.exit_requested.connect(self.close)
        self._creation_screen.creation_complete.connect(self._handle_creation_complete)
        self._creation_screen.creation_cancelled.connect(self._handle_creation_cancelled)
        self._gameplay_screen.exit_to_menu.connect(self._handle_exit_to_menu)
        self._gameplay_screen.life_ended.connect(self._handle_life_ended)
        self._game_over_screen.return_to_menu.connect(self._handle_exit_to_menu)

        self._stack.setCurrentIndex(self._login_index)

    def _handle_authenticated(self, user_id: str) -> None:
        self._current_user_id = user_id
        self._stack.setCurrentIndex(self._menu_index)
        self._scene_manager.change_scene(GameScene.MAIN_MENU)

    def _handle_guest_continue(self) -> None:
        self._stack.setCurrentIndex(self._menu_index)
        self._scene_manager.change_scene(GameScene.MAIN_MENU)

    def _handle_life_ended(self, player, life_end_result) -> None:
        """
        Fin de vida real (`TimeManager.check_life_status()`): punto
        único donde se comprueban logros, se determina el final de
        vida, y se desbloquea el Momento Clave "desenlace_final"
        contra las estadísticas finales del jugador — los catálogos
        (`data/achievements/`, `data/endings/`) siguen vacíos hoy,
        así que logros/finales no desbloquean nada todavía, pero el
        Momento Clave de desenlace SÍ se genera siempre (no depende
        de contenido — es uno de los dos de la lista curada del
        Vision Document que no vienen de una escena, ver
        `docs/content_authoring_guide.md`).
        """
        if self._achievement_manager is not None:
            self._achievement_manager.check_all(player)

        ending_title = None
        if self._ending_manager is not None:
            ending_id = self._ending_manager.determine_ending(player)
            if ending_id is not None:
                self._ending_manager.unlock_ending(player.player_id, ending_id)
                ending = self._ending_manager.get_ending(ending_id) or {}
                ending_title = ending.get("title", ending_id)

        if self._memory_manager is not None:
            text = f"A los {life_end_result.age_at_end} años, tu historia llegó a su fin."
            if ending_title:
                text += f" Final: {ending_title}."
            self._memory_manager.unlock_moment(
                player,
                moment_id="desenlace_final",
                category="desenlace_final",
                title="El final de esta vida",
                text=text,
            )

        self._game_over_screen.show_result(
            player, life_end_result, self._gameplay_screen.current_story, ending_title=ending_title
        )
        self._stack.setCurrentIndex(self._game_over_index)
        self._scene_manager.change_scene(GameScene.GAME_OVER)

    def _handle_start_new_game(self) -> None:
        self._creation_screen.reset()
        self._creation_screen.set_player_id(self._current_user_id)
        self._stack.setCurrentIndex(self._creation_index)
        self._scene_manager.change_scene(GameScene.CHARACTER_CREATION)

    def _handle_creation_complete(self, player) -> None:
        if self._memory_manager is not None:
            self._memory_manager.unlock_moment(
                player,
                moment_id="nacimiento",
                category="nacimiento",
                title="El comienzo de esta vida",
                text=f"{player.full_name} comienza su historia en {player.country}.",
            )
        story = self._story_manager.start_story(
            player_id=player.player_id,
            story_content_id=NEW_GAME_STORY_CONTENT_ID,
            started_at_age=player.age,
        )
        self._gameplay_screen.load_session(player, story)
        self._stack.setCurrentIndex(self._gameplay_index)
        self._scene_manager.change_scene(GameScene.GAMEPLAY)

    def _handle_creation_cancelled(self) -> None:
        self._stack.setCurrentIndex(self._menu_index)
        self._scene_manager.change_scene(GameScene.MAIN_MENU)

    def _handle_start_gameplay(self, player, story) -> None:
        self._gameplay_screen.load_session(player, story)
        self._stack.setCurrentIndex(self._gameplay_index)
        self._scene_manager.change_scene(GameScene.GAMEPLAY)

    # ==================================================
    # PARTIDA DEMO — DEMO TEMPORAL - ELIMINAR CUANDO SE INTEGRE LA API DE IA
    # ==================================================
    # Todo este bloque (imports de arriba marcados igual + estos tres
    # métodos + las dos líneas de conexión de señales en
    # `_build_screens()`/`_handle_theme_changed()`) es lo único que hay
    # que borrar de este archivo para quitar la demo por completo.

    def _handle_start_demo(self) -> None:
        """
        Arranca (o reinicia desde cero) la Partida Demo en una
        `GameplayScreen` nueva y aislada — nunca la real
        `self._gameplay_screen`, que usa `story_manager`/`save_manager`
        de verdad (Supabase/`saves/`). Ver `services/demo_service.py`.
        """
        self._teardown_demo_screen()

        demo_session = build_demo_session(on_finished=self._handle_demo_finished)

        self._demo_gameplay_screen = GameplayScreen(
            story_manager=demo_session.story_manager,
            save_manager=demo_session.save_manager,
            statistics_service=self._statistics_service,
            inventory_service=self._inventory_service,
            achievement_service=self._achievement_service,
            consequence_service=self._consequence_service,
            audio_manager=self._audio_manager,
            language_manager=self._language_manager,
        )
        self._demo_gameplay_screen.exit_to_menu.connect(self._handle_exit_to_menu)
        self._demo_index = self._stack.addWidget(self._demo_gameplay_screen)
        self._demo_gameplay_screen.load_session(demo_session.player, demo_session.story)

        self._stack.setCurrentIndex(self._demo_index)
        self._scene_manager.change_scene(GameScene.GAMEPLAY)

    def _handle_demo_finished(self, story: Story) -> None:
        """
        Callback de `CompletionWatchingStoryManager`: se dispara en
        cuanto la Partida Demo llega a su final. Se difiere con
        `QTimer.singleShot(0, ...)` para que `StoryPanel` termine de
        pintar la escena final ("SUJETO ACEPTADO") antes de que
        aparezca el diálogo de cierre encima.
        """
        QTimer.singleShot(0, lambda: self._show_demo_finished_dialog(story))

    def _show_demo_finished_dialog(self, story: Story) -> None:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Information)
        box.setWindowTitle("Fin de la demo")
        box.setText(
            "FIN DE LA DEMO\n\n"
            "En What If?, cada decisión puede cambiar tu historia, "
            "relaciones, recursos y futuro."
        )
        return_button = box.addButton("Volver al inicio", QMessageBox.AcceptRole)
        box.setDefaultButton(return_button)
        box.exec()
        self._handle_exit_to_menu()

    def _teardown_demo_screen(self) -> None:
        """Quita y libera la `GameplayScreen` de demo anterior, si había alguna."""
        if self._demo_gameplay_screen is None:
            return
        self._stack.removeWidget(self._demo_gameplay_screen)
        self._demo_gameplay_screen.deleteLater()
        self._demo_gameplay_screen = None
        self._demo_index = None

    def _handle_exit_to_menu(self) -> None:
        self._main_menu_screen.refresh_continue_button()
        self._stack.setCurrentIndex(self._menu_index)
        self._scene_manager.change_scene(GameScene.MAIN_MENU)

    # ==================================================
    # REPINTADO EN CALIENTE
    # ==================================================

    def _handle_theme_changed(self, theme_name: str) -> None:
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(theme.base_stylesheet())

        # DEMO TEMPORAL - ELIMINAR CUANDO SE INTEGRE LA API DE IA
        # La demo no se preserva a través de un cambio de tema (es
        # efímera por diseño): se descarta aquí para no dejar un
        # widget huérfano en el QStackedWidget; el usuario vuelve al
        # menú, igual que si nunca hubiera habido una sesión cargada.
        self._teardown_demo_screen()

        was_on_login = self._stack.currentIndex() == self._login_index
        was_on_gameplay = self._stack.currentIndex() == self._gameplay_index
        preserved_player = self._gameplay_screen.current_player
        preserved_story = self._gameplay_screen.current_story

        old_login_screen = self._login_screen
        old_menu_screen = self._main_menu_screen
        old_creation_screen = self._creation_screen
        old_gameplay_screen = self._gameplay_screen
        old_game_over_screen = self._game_over_screen
        self._stack.removeWidget(old_login_screen)
        self._stack.removeWidget(old_menu_screen)
        self._stack.removeWidget(old_creation_screen)
        self._stack.removeWidget(old_gameplay_screen)
        self._stack.removeWidget(old_game_over_screen)
        old_login_screen.deleteLater()
        old_menu_screen.deleteLater()
        old_creation_screen.deleteLater()
        old_gameplay_screen.deleteLater()
        old_game_over_screen.deleteLater()

        self._build_screens()

        if preserved_player is not None:
            self._gameplay_screen.load_session(preserved_player, preserved_story)
        else:
            self._main_menu_screen.refresh_continue_button()

        if was_on_login:
            self._stack.setCurrentIndex(self._login_index)
        elif was_on_gameplay:
            self._stack.setCurrentIndex(self._gameplay_index)
        else:
            self._stack.setCurrentIndex(self._menu_index)
