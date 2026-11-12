"""
managers/event_manager.py
============================

Qué hace:
    Cuarto manager de dominio. Dos responsabilidades:

    1. Catálogo de eventos: lee definiciones de
       `data/events/<event_id>.json` (mismo mecanismo que
       `StoryService` usa para escenas — `JSONContentRepository`, no
       una abstracción nueva).
    2. Disparar un evento: comprueba requisitos de estadísticas, y
       si se cumplen, aplica sus efectos vía
       `services.consequence_service.ConsequenceService` — reutiliza
       ese sistema en vez de escribir en `Player` por su cuenta.

Qué NO hace (alcance dejado fuera a propósito):
    No inventa ningún evento — `data/events/` existe pero está vacía
    (ver `data/events/.gitkeep`); crear eventos reales es contenido
    de diseño, igual que las historias. Este manager solo construye
    el mecanismo de lectura/disparo, no el contenido.

    El `event_engine.py` original (antes de esta sesión) esperaba
    también "eventos programados por fecha/hora" — no existe ningún
    concepto de calendario en el proyecto (ver `managers/time_manager.py`,
    que solo cuenta años, no días/horas), así que esa parte no se
    replica; ver `engine/time_engine.py` para el ajuste equivalente.

Formato esperado de un evento (mismo patrón que `effects` en
opciones de historia — ver `docs/content_authoring_guide.md`):

    {
      "title": "...",
      "category": "...",
      "requirements": {"stats": {"intelligence": 40}},
      "effects": {"stats": {"happiness": -5}}
    }

Autor: Korlo
"""

from __future__ import annotations

import logging
import random as _random
from typing import Any, Dict, List, Optional, Tuple

from config.paths import EVENTS_DIR
from models.player import Player
from services.consequence_service import ConsequenceService
from services.repositories import ContentRepository, JSONContentRepository
from utils.random_utils import weighted_choice

logger = logging.getLogger(__name__)


class EventNotFoundError(Exception):
    """No existe ningún evento con ese id en el catálogo."""


class EventRequirementsNotMetError(Exception):
    """El jugador no cumple los requisitos de estadísticas del evento."""


class EventManager:
    """Catálogo de eventos + disparo (requisitos + efectos vía ConsequenceService)."""

    def __init__(
        self,
        repository: Optional[ContentRepository] = None,
        consequence_service: Optional[ConsequenceService] = None,
        rng: Optional[_random.Random] = None,
    ) -> None:
        self._repository: ContentRepository = repository or JSONContentRepository(EVENTS_DIR)
        self._consequence_service = consequence_service
        self._rng = rng

    # ==================================================
    # CATÁLOGO
    # ==================================================

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Devuelve la definición del evento, o None si no existe."""
        return self._repository.load(event_id)

    def get_random_event(self, category: Optional[str] = None) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        Un `(event_id, evento)` elegido con probabilidad ponderada
        por el campo `"weight"` de cada definición (1.0 si no lo
        trae) — vía `utils.random_utils.weighted_choice`, ya
        construido para esto. Devuelve el id junto con el contenido
        porque el id vive en el nombre del archivo, no dentro del
        JSON — sin esto, quien lo recibe no podría volver a
        dispararlo por id. Opcionalmente filtrado por 'category'.
        """
        candidates = self._repository.list_keys()
        loaded = {key: (self._repository.load(key) or {}) for key in candidates}
        if category is not None:
            loaded = {key: event for key, event in loaded.items() if event.get("category") == category}
        if not loaded:
            return None
        weights = {key: float(event.get("weight", 1.0)) for key, event in loaded.items()}
        chosen_id = weighted_choice(weights, rng=self._rng)
        return chosen_id, loaded[chosen_id]

    def list_events(self) -> List[str]:
        """Todos los ids de evento disponibles en el catálogo."""
        return self._repository.list_keys()

    # ==================================================
    # DISPARO
    # ==================================================

    def can_trigger(self, player: Player, event: Dict[str, Any]) -> bool:
        """Comprueba si `player` cumple los requisitos de estadísticas del evento."""
        requirements = event.get("requirements", {}).get("stats", {})
        for stat, minimum in requirements.items():
            value = getattr(player, stat, None)
            if value is None or value < minimum:
                return False
        return True

    def trigger_event(self, player: Player, event_id: str) -> Tuple[Dict[str, Any], List[str]]:
        """
        Dispara el evento `event_id` sobre `player`: comprueba
        requisitos, aplica efectos vía `ConsequenceService` si hay
        uno configurado. Devuelve `(evento, efectos_aplicados)`.

        Raises:
            EventNotFoundError: si `event_id` no está en el catálogo.
            EventRequirementsNotMetError: si `player` no cumple los requisitos.
        """
        event = self.get_event(event_id)
        if event is None:
            raise EventNotFoundError(f"No existe el evento '{event_id}'.")
        if not self.can_trigger(player, event):
            raise EventRequirementsNotMetError(
                f"'{player.player_id}' no cumple los requisitos de '{event_id}'."
            )
        applied: List[str] = []
        effects = event.get("effects", {}).get("stats", {})
        if self._consequence_service is not None and effects:
            applied = self._consequence_service.apply_effects(
                player, effects, reason=f"evento: {event.get('title', event_id)}"
            )
        logger.info("EventManager: evento '%s' disparado sobre %s", event_id, player.player_id)
        return event, applied
