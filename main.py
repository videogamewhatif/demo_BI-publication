"""
=========================================================
What If?
Main Entry Point
=========================================================

Qué cambió respecto a la versión anterior de este archivo (y por
qué — léase antes de tocarlo de nuevo):

    1. `from config.settings import Settings` — `Settings` nunca
       existió como clase; `config/settings.py` es un módulo de
       constantes sueltas. Se importa el módulo directamente.

    2. `from config.constants import APP_NAME, VERSION` — el
       archivo se llama `config/constant.py` (sin "s"); su propio
       docstring ya avisaba de este bug pendiente. Se usa
       `config.settings.GAME_NAME`/`GAME_VERSION`, que sí existen y
       cumplen ese rol.

    3. `self.game_engine = GameEngine(save_manager=..., ...)` —
       `engine/game_engine.py` no acepta esos argumentos (su
       constructor real es `GameEngine()`, sin parámetros) y además
       importa `managers.player_manager` (entre otros), que no
       existe — es parte del esqueleto roto de `engine/` (ver
       diagnóstico). `managers.story_manager` sí existe ya, desde la
       sesión de managers de dominio, pero `GameEngine` de todas
       formas no se instancia: `ui/` habla directamente con
       `services/` + `managers/`, que sí funcionan.

    4. `from ui.windows.main_menu import MainMenu` — ni el archivo
       ni la clase existían. La capa `ui/` se construyó en esta
       sesión; el punto de entrada real es
       `ui.windows.main_window.MainWindow`.

    5. `self.save_manager.load_last_save()` — ese método no existe
       en `SaveManager`. Cargar una partida es ahora una decisión
       explícita del jugador desde `MainMenuScreen` ("Continuar"),
       no algo que ocurra automáticamente al arrancar.

Autor: Korlo (main.py corregido junto con ui/ en esta sesión)
=========================================================
"""

import os
import sys

from dotenv import load_dotenv
from PySide6.QtWidgets import QApplication

from config import settings
from database.adapters import (
    SQLAchievementRepository,
    SQLInventoryRepository,
    SQLSaveRepository,
    SQLStatisticsRepository,
)
from database.engine import create_all, create_database_engine
from managers.achievement_manager import AchievementManager
from managers.audio_manager import AudioManager
from managers.ending_manager import EndingManager
from managers.event_manager import EventManager
from managers.inventory_manager import InventoryManager
from managers.language_manager import LanguageManager
from managers.memory_manager import MemoryManager
from managers.player_manager import PlayerManager
from managers.resource_manager import ResourceManager
from managers.save_manager import SaveManager
from managers.scene_manager import GameScene, SceneManager
from managers.story_manager import StoryManager
from managers.time_manager import TimeManager
from services.achievement_service import AchievementService
from services.audio_service import AudioService
from services.auth_service import AuthService
from services.consequence_service import ConsequenceService
from services.image_service import ImageService
from services.inventory_service import InventoryService
from services.localization_service import LocalizationService
from services.memory_service import MemoryService
from services.save_service import SaveService
from services.statistics_service import StatisticsService
from services.story_service import StoryService
from ui.theme import base_stylesheet
from ui.windows.main_window import MainWindow
from utils.logger import setup_logger


class Application:
    """
    Ensambla `services/` + managers de sistema y lanza `MainWindow`.
    No mantiene el estado de partida (`Player`/`Story` actuales):
    eso vive en `GameplayScreen`, que lo recibe explícitamente al
    entrar a una sesión (ver `ui/screens/main_menu_screen.py`).
    """

    def __init__(self) -> None:
        # Carga SUPABASE_URL/SUPABASE_ANON_KEY/SUPABASE_DB_URL desde
        # un ".env" en la raíz, si existe. Sin ".env", no hay nada
        # que cargar y el juego arranca en modo local (ver punto 5-6
        # más abajo).
        load_dotenv()

        self.logger = setup_logger()
        self.logger.info("========================================")
        self.logger.info("Iniciando %s", settings.GAME_NAME)
        self.logger.info("Versión %s", settings.GAME_VERSION)
        self.logger.info("========================================")

        # ---------------------------------------
        # Managers de sistema
        # ---------------------------------------
        self.resource_manager = ResourceManager()
        self.scene_manager = SceneManager(initial_scene=GameScene.LOGIN)

        self.audio_manager = AudioManager(
            audio_service=AudioService(),
            scene_manager=self.scene_manager,
        )

        self.localization_service = LocalizationService()
        self.language_manager = LanguageManager(self.localization_service)

        # ---------------------------------------
        # Backend real de database/ (activado — ver database/adapters.py
        # para el porqué de cada límite conocido: NPCs sin tabla,
        # capacidad de inventario sin columna, guardado no es una foto
        # congelada). El contenido narrativo (data/scenarios/, etc.)
        # sigue siendo JSON de solo lectura — eso no cambia aquí.
        #
        # Si SUPABASE_DB_URL está configurada, el Engine apunta a esa
        # Postgres remota en vez de al SQLite local — mismo esquema,
        # mismos repositorios, sin cambios ahí (ver database/engine.py).
        # ---------------------------------------
        self.database_engine = create_database_engine(db_url=os.environ.get("SUPABASE_DB_URL") or None)
        create_all(self.database_engine)

        self.save_manager = SaveManager(
            save_service=SaveService(repository=SQLSaveRepository(self.database_engine))
        )

        # ---------------------------------------
        # Cuentas de usuario (opcional — solo si SUPABASE_URL y
        # SUPABASE_ANON_KEY están configuradas; si no, `auth_service`
        # queda en None y `LoginScreen` solo ofrece "Seguir sin
        # cuenta", sin bloquear el juego).
        # ---------------------------------------
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_ANON_KEY")
        self.auth_service = (
            AuthService(supabase_url, supabase_key) if supabase_url and supabase_key else None
        )

        # ---------------------------------------
        # Servicios de dominio
        # ---------------------------------------
        self.story_service = StoryService()
        self.statistics_service = StatisticsService(
            repository=SQLStatisticsRepository(self.database_engine)
        )
        self.inventory_service = InventoryService(
            repository=SQLInventoryRepository(self.database_engine)
        )
        self.achievement_service = AchievementService(
            repository=SQLAchievementRepository(self.database_engine)
        )
        self.consequence_service = ConsequenceService()

        # ---------------------------------------
        # Managers de dominio
        # ---------------------------------------
        self.story_manager = StoryManager(self.story_service)
        self.player_manager = PlayerManager()
        self.time_manager = TimeManager()
        self.event_manager = EventManager(consequence_service=self.consequence_service)
        self.ending_manager = EndingManager()
        self.achievement_manager = AchievementManager(
            self.achievement_service, statistics_service=self.statistics_service
        )
        self.inventory_manager = InventoryManager(
            self.inventory_service, consequence_service=self.consequence_service
        )
        # ImageService sin `provider=` explícito -> PlaceholderImageProvider
        # (Pillow local, sin red ni costo). Cambiar a OpenAIImageProvider
        # es una decisión aparte, explícita, que requiere una API key.
        self.image_service = ImageService()
        self.memory_service = MemoryService()
        self.memory_manager = MemoryManager(self.memory_service, image_service=self.image_service)

        # ---------------------------------------
        # Interfaz
        # ---------------------------------------
        self.qt_app = QApplication.instance() or QApplication(sys.argv)
        self.qt_app.setStyleSheet(base_stylesheet())

        self.main_window = MainWindow(
            scene_manager=self.scene_manager,
            story_manager=self.story_manager,
            player_manager=self.player_manager,
            save_manager=self.save_manager,
            statistics_service=self.statistics_service,
            inventory_service=self.inventory_service,
            achievement_service=self.achievement_service,
            consequence_service=self.consequence_service,
            time_manager=self.time_manager,
            event_manager=self.event_manager,
            ending_manager=self.ending_manager,
            achievement_manager=self.achievement_manager,
            inventory_manager=self.inventory_manager,
            memory_manager=self.memory_manager,
            memory_service=self.memory_service,
            audio_manager=self.audio_manager,
            language_manager=self.language_manager,
            auth_service=self.auth_service,
        )

    def run(self) -> int:
        """Muestra la ventana principal y arranca el bucle de eventos de Qt."""
        self.main_window.show()
        self.logger.info("Ventana principal mostrada.")
        return self.qt_app.exec()


def main() -> None:
    try:
        app = Application()
        exit_code = app.run()
    except KeyboardInterrupt:
        print("\nAplicación cerrada por el usuario.")
        return
    except Exception as error:
        print("\nHa ocurrido un error inesperado.")
        print(error)
        raise
    else:
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
