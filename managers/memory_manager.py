"""
managers/memory_manager.py
============================

Qué hace:
    Decide QUÉ pasa cuando se desbloquea un Momento Clave del Álbum
    de Vida (`What_If_Vision_Document.md` §5.3, §5.5): un único
    punto de entrada, `unlock_moment()`, que:
        1. No hace nada si `player` ya tiene ese `moment_id`
           (`Player.memory_moments` es la fuente de verdad rápida
           para esa comprobación — ya existía, no se duplica).
        2. Genera la ilustración vía `ImageService`, si hay uno
           configurado (opcional: sin él, el momento igual se
           desbloquea, solo que sin imagen — un fallo de imagen
           nunca debe bloquear el desbloqueo del momento en sí).
        3. Persiste la ficha completa vía `MemoryService`.
        4. Registra el ID en `Player.memory_moments`
           (`Player.unlock_memory_moment()`, ya existía).

    Los disparadores concretos (cuándo se llama a `unlock_moment()`)
    viven en `ui/`: `ui/screens/story_panel.py` para momentos
    marcados en el contenido de una escena
    (`docs/content_authoring_guide.md`), y
    `ui/windows/main_window.py` para "nacimiento" (creación de
    personaje) y "desenlace_final" (fin de vida) — los dos únicos
    momentos de la lista curada del Vision Document que no dependen
    de una escena concreta.

Dependencias:
    - services.memory_service: MemoryService.
    - services.image_service: ImageService, ImageGenerationError (opcional).
    - models.memory_moment: MemoryMoment.
    - models.player: Player.

Autor: Korlo
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from models.memory_moment import MemoryMoment
from models.player import Player
from services.image_service import ImageGenerationError, ImageService
from services.memory_service import MemoryService

logger = logging.getLogger(__name__)


class MemoryManager:
    """Orquesta el desbloqueo de Momentos Clave: imagen (opcional) + persistencia + registro en Player."""

    def __init__(
        self,
        memory_service: MemoryService,
        image_service: Optional[ImageService] = None,
    ) -> None:
        self._memory_service = memory_service
        self._image_service = image_service

    def unlock_moment(
        self,
        player: Player,
        *,
        moment_id: str,
        category: str,
        title: str,
        text: str,
        origin_decision: Optional[str] = None,
    ) -> Optional[MemoryMoment]:
        """
        Desbloquea el Momento Clave `moment_id` para `player`, si no
        lo tenía ya. Devuelve el `MemoryMoment` creado, o None si ya
        estaba desbloqueado (no hace nada — silencioso a propósito,
        ver docstring del módulo).
        """
        if moment_id in player.memory_moments:
            return None

        image_path: Optional[str] = None
        if self._image_service is not None:
            try:
                path = self._image_service.generate_memory_moment_image(
                    player.player_id, moment_id, text
                )
                image_path = str(path)
            except ImageGenerationError:
                logger.warning(
                    "MemoryManager: no se pudo generar la ilustración de '%s' "
                    "para %s — el momento se desbloquea igual, sin imagen.",
                    moment_id, player.player_id,
                )

        moment = MemoryMoment(
            moment_id=moment_id,
            player_id=player.player_id,
            category=category,
            title=title,
            text=text,
            age_at_moment=player.age,
            origin_decision=origin_decision,
            image_path=image_path,
            unlocked_at=datetime.now(timezone.utc).isoformat(),
        )
        self._memory_service.add_moment(player.player_id, moment)
        player.unlock_memory_moment(moment_id)
        logger.info(
            "MemoryManager: '%s' (%s) desbloqueado para %s a los %s años",
            moment_id, category, player.player_id, player.age,
        )
        return moment
