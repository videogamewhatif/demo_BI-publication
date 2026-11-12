"""
engine/game_engine.py
========================

Motor principal del juego — reescrito en la sesión de "desbloquear
engine/" contra la API real de todos los managers de dominio (antes
esperaba `StoryManager()`/`SaveManager()`/`PlayerManager()` sin
argumentos, y `player_manager.create_player()` sin ningún dato de
personaje).

Qué es esto de verdad (léase antes de usarlo):
    `ui/` ya hace esta misma orquestación hoy —
    `ui/windows/main_window.py` + `ui/screens/gameplay_screen.py` +
    `ui/screens/story_panel.py` juntos cubren exactamente lo que
    `GameEngine` hace aquí, probado con más de 60 pruebas reales.
    Este archivo es una capa de orquestación SIN INTERFAZ gráfica —
    útil para scripts, pruebas automatizadas, o una futura interfaz
    de línea de comandos — no algo que `ui/` deba empezar a usar en
    vez de lo que ya tiene. Duplicar esta orquestación fue una
    decisión explícita del usuario al pedir "desbloquear engine/
    completamente" en vez de retirar la carpeta — ver
    `docs/changelog.md`.

Autor: Korlo
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from config.constant import SocioeconomicLevel
from engine.decision_engine import DecisionEngine
from engine.story_engine import StoryEngine
from engine.time_engine import TimeEngine
from managers.player_manager import PlayerManager
from managers.save_manager import QUICKSAVE_SLOT, SaveManager, SaveNotFoundError
from managers.story_manager import StoryManager
from managers.time_manager import LifeEndResult, TimeManager
from models.player import Player
from services.consequence_service import ConsequenceService


class GameEngine:
    """Motor principal: orquesta creación/carga/guardado de partida y el avance turno a turno."""

    def __init__(
        self,
        story_manager: StoryManager,
        save_manager: SaveManager,
        player_manager: PlayerManager,
        time_manager: Optional[TimeManager] = None,
        consequence_service: Optional[ConsequenceService] = None,
    ) -> None:
        self.story_manager = story_manager
        self.save_manager = save_manager
        self.player_manager = player_manager

        self.story_engine = StoryEngine(story_manager)
        self.decision_engine = DecisionEngine(consequence_service)
        self.time_engine = TimeEngine(time_manager) if time_manager is not None else None

        self.current_player: Optional[Player] = None
        self.running = False

    def start_new_game(
        self,
        *,
        first_name: str,
        last_name: str,
        gender: Optional[str],
        starting_age: int,
        country: str,
        city: str,
        story_content_id: str,
        socioeconomic_origin: SocioeconomicLevel = SocioeconomicLevel.MEDIUM,
        attr_deltas: Optional[Dict[str, int]] = None,
        aspiration: Optional[str] = None,
    ) -> Player:
        """
        Crea un personaje nuevo (vía `PlayerManager`, con los mismos
        datos que pide `ui/screens/character_creation/`) e inicia
        `story_content_id` para él. A diferencia de la versión
        original, no hay forma de crear un personaje "vacío" — el
        `PlayerManager` real siempre exige estos datos.
        """
        self.current_player = self.player_manager.create_player(
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            starting_age=starting_age,
            country=country,
            city=city,
            socioeconomic_origin=socioeconomic_origin,
            attr_deltas=attr_deltas,
            aspiration=aspiration,
        )
        self.story_engine.start(self.current_player.player_id, story_content_id, starting_age)
        self.running = True
        return self.current_player

    def load_game(self, slot: str = QUICKSAVE_SLOT) -> Optional[Player]:
        """
        Carga la partida de `slot`. Devuelve el `Player` cargado, o
        None si no existe (tolerante, sin lanzar excepción).
        """
        try:
            loaded = self.save_manager.load(slot)
        except SaveNotFoundError:
            return None
        self.current_player = loaded.player
        self.story_engine.current_story = loaded.stories[0] if loaded.stories else None
        self.running = True
        return self.current_player

    def save_game(self, slot: str = QUICKSAVE_SLOT) -> None:
        """Guarda el progreso actual (jugador + historia activa, si hay una)."""
        if self.current_player is None:
            return
        stories = [self.story_engine.current_story] if self.story_engine.current_story else []
        self.save_manager.save_now(slot, self.current_player, stories)

    def choose_option(self, option_index: int) -> bool:
        """
        Ejecuta un turno completo: resuelve la decisión, aplica sus
        efectos (`ConsequenceService`, vía `DecisionEngine`), avanza
        el tiempo y comprueba fin de vida (`TimeEngine`, si hay uno
        configurado), y solo si el personaje sigue con vida, avanza
        la historia. Devuelve False si no hay partida en curso, el
        índice no es válido, o el personaje murió en este turno (en
        ese caso `self.running` queda en False — quien use
        `GameEngine` debe comprobar `get_life_end_result()` para
        saber por qué).
        """
        if not self.running or self.current_player is None:
            return False

        scene = self.story_engine.get_current_scene()
        if scene is None:
            return False

        decision = self.decision_engine.resolve(scene, option_index)
        if decision is None:
            return False

        self.decision_engine.apply_consequences(self.current_player, decision)

        if self.time_engine is not None:
            life_end = self.time_engine.advance_year(self.current_player)
            if life_end is not None:
                self._last_life_end_result = life_end
                self.running = False
                return False

        return self.story_engine.choose_option(option_index)

    def get_life_end_result(self) -> Optional[LifeEndResult]:
        """El motivo de fin de vida del último `choose_option()` que terminó una vida, si lo hubo."""
        return getattr(self, "_last_life_end_result", None)

    def update(self) -> None:
        """
        Un "tick" de depuración: registra en el log la escena actual
        (la versión original hacía `print()` — esto es un motor sin
        interfaz, así que usa logging en vez de imprimir a stdout).
        """
        import logging

        logger = logging.getLogger(__name__)
        if not self.running:
            return
        scene = self.story_engine.get_current_scene()
        if scene is None:
            self.running = False
            return
        logger.debug("GameEngine.update(): escena actual: %s", scene.get("title") or scene.get("text", "")[:60])

    def stop(self) -> None:
        """Finaliza la partida en curso (no borra el guardado, solo detiene el motor)."""
        self.running = False

    def is_running(self) -> bool:
        """Indica si el motor tiene una partida activa."""
        return self.running
