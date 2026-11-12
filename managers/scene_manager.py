"""
managers/scene_manager.py
==========================

Qué hace:
    Coordina qué PANTALLA de interfaz está activa (menú principal,
    creación de personaje, partida en curso, pausa, ajustes, álbum,
    fin de partida, créditos) y notifica a quien esté interesado
    cuándo se entra o se sale de cada una.

    Nota de nombres, a propósito: "escena" aquí significa PANTALLA
    DE UI (`GameScene`), no tiene relación con `current_scene_id` de
    `models.story.Story` (que es un punto dentro de un árbol de
    diálogo narrativo). Son dos conceptos distintos que comparten
    palabra por herencia del vocabulario típico de videojuegos; lo
    dejo explícito aquí para que no se confundan al leer el código.

Cómo funciona:
    Mantiene una pila de `GameScene`, no solo un valor actual: así
    se puede abrir Pausa SOBRE Gameplay (`push_scene`) y volver
    exactamente a donde estaba al cerrarla (`pop_scene`), en vez de
    perder el contexto con un simple reemplazo. No contiene lógica
    de negocio (no decide qué mostrar en cada pantalla, no sabe nada
    de Player/Story): solo administra el estado de navegación y
    dispara callbacks de entrada/salida — el "director de orquesta"
    que describiste, sin partitura propia.

Dependencias:
    - Solo biblioteca estándar.

Cómo interactúa con otros módulos:
    `managers/audio_manager.py` se suscribe a esta clase para saber
    cuándo cambiar de pista musical según la escena activa. La
    futura capa `ui/` (todavía no existe) sería quien llama a
    `change_scene`/`push_scene`/`pop_scene` en respuesta a la
    navegación del jugador.

Autor: Korlo
"""

from __future__ import annotations

import logging
from collections import defaultdict
from enum import Enum
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class GameScene(Enum):
    """Pantallas de interfaz reconocidas por el juego."""
    LOGIN = "login"
    MAIN_MENU = "main_menu"
    CHARACTER_CREATION = "character_creation"
    GAMEPLAY = "gameplay"
    PAUSE = "pause"
    SETTINGS = "settings"
    ALBUM = "album"
    GAME_OVER = "game_over"
    CREDITS = "credits"


class SceneStackError(Exception):
    """Se lanza ante una operación inválida sobre la pila de escenas."""


# (escena_entrante, escena_saliente_o_None)
SceneCallback = Callable[[GameScene, Optional[GameScene]], None]


class SceneManager:
    """
    Administra la pila de pantallas activas y notifica transiciones
    de entrada/salida a quien se haya suscrito.
    """

    def __init__(self, initial_scene: GameScene = GameScene.MAIN_MENU) -> None:
        self._stack: List[GameScene] = [initial_scene]
        self._on_enter: Dict[GameScene, List[SceneCallback]] = defaultdict(list)
        self._on_exit: Dict[GameScene, List[SceneCallback]] = defaultdict(list)

    # ==================================================
    # CONSULTA
    # ==================================================

    @property
    def current_scene(self) -> GameScene:
        """Escena actualmente activa (tope de la pila)."""
        return self._stack[-1]

    @property
    def stack_depth(self) -> int:
        """Cuántas escenas hay apiladas en este momento."""
        return len(self._stack)

    def is_active(self, scene: GameScene) -> bool:
        """Indica si `scene` está en algún punto de la pila (no solo en el tope)."""
        return scene in self._stack

    # ==================================================
    # NAVEGACIÓN
    # ==================================================

    def change_scene(self, scene: GameScene) -> None:
        """
        Reemplaza la escena actual por `scene` (no apila). Úsalo
        para navegación normal entre pantallas de nivel superior
        (por ejemplo, Menú Principal -> Creación de Personaje).
        """
        previous = self.current_scene
        self._fire_exit(previous, scene)
        self._stack[-1] = scene
        self._fire_enter(scene, previous)
        logger.info("SceneManager: %s -> %s (change)", previous.value, scene.value)

    def push_scene(self, scene: GameScene) -> None:
        """
        Apila `scene` sobre la actual, conservándola debajo. Úsalo
        para pantallas superpuestas (por ejemplo, abrir Pausa sobre
        Gameplay sin perder el estado de Gameplay).
        """
        previous = self.current_scene
        self._fire_exit(previous, scene)
        self._stack.append(scene)
        self._fire_enter(scene, previous)
        logger.info("SceneManager: %s -> %s (push, profundidad=%s)", previous.value, scene.value, len(self._stack))

    def pop_scene(self) -> GameScene:
        """
        Quita la escena actual y vuelve a la que estaba justo debajo.

        Raises:
            SceneStackError: si solo queda una escena en la pila (no
                hay a dónde volver).
        """
        if len(self._stack) <= 1:
            raise SceneStackError(
                "No se puede hacer pop: solo queda una escena en la pila."
            )
        closed = self._stack.pop()
        self._fire_exit(closed, self.current_scene)
        self._fire_enter(self.current_scene, closed)
        logger.info("SceneManager: pop de %s, vuelve a %s", closed.value, self.current_scene.value)
        return closed

    # ==================================================
    # SUSCRIPCIÓN
    # ==================================================

    def on_enter(self, scene: GameScene, callback: SceneCallback) -> None:
        """Registra `callback` para ejecutarse cada vez que se entra a `scene`."""
        self._on_enter[scene].append(callback)

    def on_exit(self, scene: GameScene, callback: SceneCallback) -> None:
        """Registra `callback` para ejecutarse cada vez que se sale de `scene`."""
        self._on_exit[scene].append(callback)

    def off_enter(self, scene: GameScene, callback: SceneCallback) -> None:
        """Retira `callback` de las notificaciones de entrada a `scene`, si estaba registrado."""
        if callback in self._on_enter[scene]:
            self._on_enter[scene].remove(callback)

    def off_exit(self, scene: GameScene, callback: SceneCallback) -> None:
        """Retira `callback` de las notificaciones de salida de `scene`, si estaba registrado."""
        if callback in self._on_exit[scene]:
            self._on_exit[scene].remove(callback)

    # ==================================================
    # INTERNO
    # ==================================================

    def _fire_enter(self, scene: GameScene, previous: Optional[GameScene]) -> None:
        for callback in self._on_enter.get(scene, []):
            callback(scene, previous)

    def _fire_exit(self, scene: GameScene, next_scene: Optional[GameScene]) -> None:
        for callback in self._on_exit.get(scene, []):
            callback(scene, next_scene)