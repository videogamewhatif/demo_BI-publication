"""
managers/input_manager.py
==========================

Qué hace:
    Traduce entradas crudas (por ahora, teclas) a acciones de juego
    abstractas (`GameAction`) mediante un mapa de bindings
    reconfigurable, y notifica a quien esté suscrito cuando ocurre
    una acción.

Cómo funciona:
    No depende de pygame ni de ningún backend de entrada concreto:
    recibe el nombre de una tecla como texto (`"RETURN"`, `"ESCAPE"`,
    etc.) y decide a qué `GameAction` corresponde según el mapa de
    bindings actual. Quien capture los eventos reales del teclado
    (la futura capa `ui/`, probablemente sobre pygame) le pasa el
    nombre de la tecla a `handle_key_press()`; este manager no sabe
    ni le importa de dónde vino esa tecla — así se puede probar sin
    ninguna ventana ni dispositivo real, y se puede reemplazar
    pygame por otra biblioteca de entrada sin tocar esta clase.

    No contiene lógica de juego (qué hacer cuando se confirma algo):
    solo decide QUÉ acción ocurrió y AVISA a los suscriptores — ellos
    (por ejemplo, el componente de UI de la escena activa, coordinado
    por `SceneManager`) deciden qué hacer con esa acción.

Dependencias:
    - Solo biblioteca estándar.

Cómo interactúa con otros módulos:
    Complementa a `managers/scene_manager.py`: normalmente se
    deshabilita (`disable()`) mientras una escena no debe recibir
    entradas (por ejemplo, durante una transición o mientras se
    escribe texto en un campo), y se reactiva después.

Autor: Korlo
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class GameAction(Enum):
    """Acciones de juego abstractas, independientes del dispositivo de entrada."""
    CONFIRM = "confirm"
    CANCEL = "cancel"
    MOVE_UP = "move_up"
    MOVE_DOWN = "move_down"
    MOVE_LEFT = "move_left"
    MOVE_RIGHT = "move_right"
    PAUSE = "pause"
    OPEN_ALBUM = "open_album"


DEFAULT_KEY_BINDINGS: Dict[str, GameAction] = {
    "RETURN": GameAction.CONFIRM,
    "SPACE": GameAction.CONFIRM,
    "ESCAPE": GameAction.CANCEL,
    "UP": GameAction.MOVE_UP,
    "DOWN": GameAction.MOVE_DOWN,
    "LEFT": GameAction.MOVE_LEFT,
    "RIGHT": GameAction.MOVE_RIGHT,
    "P": GameAction.PAUSE,
    "TAB": GameAction.OPEN_ALBUM,
}

ActionCallback = Callable[[GameAction], None]


class InputManager:
    """
    Traduce teclas crudas a `GameAction` mediante un mapa de
    bindings reconfigurable, y notifica a los suscriptores.
    """

    def __init__(self, key_bindings: Optional[Dict[str, GameAction]] = None) -> None:
        self._key_bindings: Dict[str, GameAction] = dict(
            key_bindings if key_bindings is not None else DEFAULT_KEY_BINDINGS
        )
        self._subscribers: List[ActionCallback] = []
        self._enabled = True

    # ==================================================
    # SUSCRIPCIÓN
    # ==================================================

    def subscribe(self, callback: ActionCallback) -> None:
        """Registra `callback` para recibir cada `GameAction` disparada."""
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: ActionCallback) -> None:
        """Retira `callback` de la lista de suscriptores, si estaba registrado."""
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    # ==================================================
    # ENTRADA
    # ==================================================

    def handle_key_press(self, key_name: str) -> Optional[GameAction]:
        """
        Traduce `key_name` a una `GameAction` según el binding
        actual y notifica a los suscriptores.

        Si el manager está deshabilitado (`disable()`), o la tecla no
        tiene ninguna acción asociada, no notifica a nadie y devuelve
        None.

        Returns:
            La `GameAction` disparada, o None si no hubo ninguna.
        """
        if not self._enabled:
            logger.debug("InputManager: entrada ignorada (deshabilitado): '%s'", key_name)
            return None

        action = self._key_bindings.get(key_name.upper())
        if action is None:
            logger.debug("InputManager: sin binding para la tecla '%s'", key_name)
            return None

        logger.debug("InputManager: '%s' -> %s", key_name, action.value)
        for callback in self._subscribers:
            callback(action)
        return action

    # ==================================================
    # REBINDING
    # ==================================================

    def rebind(self, key_name: str, action: GameAction) -> None:
        """Asigna `action` a `key_name`, reemplazando cualquier binding previo de esa tecla."""
        self._key_bindings[key_name.upper()] = action
        logger.info("InputManager: '%s' reasignada a %s", key_name, action.value)

    def unbind(self, key_name: str) -> None:
        """Quita el binding de `key_name`, si existía."""
        self._key_bindings.pop(key_name.upper(), None)

    def binding_for(self, key_name: str) -> Optional[GameAction]:
        """Devuelve la acción asignada a `key_name`, o None si no tiene ninguna."""
        return self._key_bindings.get(key_name.upper())

    def keys_for(self, action: GameAction) -> List[str]:
        """Devuelve todas las teclas actualmente asignadas a `action`."""
        return [key for key, bound_action in self._key_bindings.items() if bound_action is action]

    # ==================================================
    # HABILITAR / DESHABILITAR
    # ==================================================

    def disable(self) -> None:
        """Deja de procesar entradas (por ejemplo, durante una transición de escena)."""
        self._enabled = False

    def enable(self) -> None:
        """Reanuda el procesamiento de entradas."""
        self._enabled = True

    def is_enabled(self) -> bool:
        """Indica si el manager está procesando entradas actualmente."""
        return self._enabled