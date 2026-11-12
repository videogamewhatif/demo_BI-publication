"""
database/adapters.py
=======================

Qué hace:
    La pieza que faltaba para activar `database/` como backend real
    (ver `docs/architecture.md`, sección 3): 4 clases que implementan
    `services.repositories.KeyValueRepository` (`get`/`set`/`delete`/
    `list_keys`, un blob por `key`) delegando en los repositorios
    tipados por dominio de `database/repositories.py`
    (`get_player`/`save_player`, `grant_achievement`, etc.).

    `database/repositories.py` documenta a propósito por qué NO
    implementa `KeyValueRepository` directamente ("se aprovecha mejor
    con métodos que reflejan el dominio real que forzando todo detrás
    de get/set") — este archivo es exactamente el puente que esa
    decisión dejaba pendiente: cada servicio de `services/`
    (`SaveService`, `StatisticsService`, `AchievementService`,
    `InventoryService`) sigue el mismo patrón "leo el blob entero →
    lo muto en Python → lo reescribo entero" contra su
    `KeyValueRepository` — nunca pide una actualización parcial — así
    que cada adaptador puede traducir `set()` como "borra las filas
    de este jugador/ranura y reinserta desde cero", sin necesitar un
    diff fila por fila.

    Achievements/Inventory: `set()` = borrar + reinsertar todo (ya
    había `InventoryRepository.clear_inventory()`; se agregó
    `AchievementRepository.clear_achievements()`, mismo patrón).
    Statistics: mapeo 1:1 con la tabla (`StatisticsRepository` ya
    hacía esta traducción). Save: el más grande — reparte el blob
    entre `PlayerRepository`, `StoryRepository` y `SaveSlotRepository`
    (se agregó `SaveSlotRepository.get_slot()` para leer una ranura
    sin listarlas todas).

Limitaciones conocidas (reales, no hipotéticas — no las inventa este
archivo, ya estaban documentadas o son consecuencia directa del
esquema de `database/models.py`):
    - NPCs: `save_service.py` acepta una lista de `NPC` en cada
      guardado, pero `database/models.py` no tiene una tabla para
      ellos (7 tablas: ninguna es de NPCs). Hoy nada en el juego real
      pasa NPCs a `SaveManager` (confirmado con grep), así que en la
      práctica esto no pierde datos todavía — pero si algo empezara a
      hacerlo, `SQLSaveRepository.set()` lo loguea como advertencia en
      vez de fallar en silencio o fingir que los guardó.
    - Capacidad de inventario: `Inventory.capacity` (JSON) no tiene
      columna en `inventory_items` (tabla de un objeto por fila, sin
      metadata de jugador). Nada en el proyecto asigna hoy una
      capacidad distinta de `None` (ilimitado) — confirmado con
      grep — así que `SQLInventoryRepository` siempre reconstruye
      `capacity=None`, comportamiento observable idéntico al actual.
    - Guardado NO es una foto congelada: a diferencia del backend
      JSON (una copia independiente por `save_id`), `players`/
      `story_progress` tienen una sola fila por `player_id`/
      `story_id`. Dos ranuras del mismo jugador (p. ej. "quicksave" y
      "autosave") comparten la misma fila subyacente — cargar
      cualquiera de las dos devuelve el estado MÁS RECIENTE del
      jugador, no uno histórico. Ya documentado en
      `docs/architecture.md` como limitación conocida del esquema,
      no algo nuevo que introduzca este archivo.
    - `delete()` en `SQLSaveRepository` solo borra la fila-índice de
      `save_slots` (la ranura), no la fila real de `players`/
      `story_progress` — borrarlas sería destructivo si esa persona
      se referencia desde otra ranura, y el contrato genérico de
      `KeyValueRepository.delete()` ("elimina el valor asociado a esa
      key") no implica cascada sobre datos que, en este esquema,
      viven fuera de esa key.
    - `delete()`/`list_keys()` en Statistics/Achievements/Inventory:
      ningún servicio los llama hoy (confirmado con grep — solo usan
      `get`/`set`); se implementan lanzando `NotImplementedError` en
      vez de un no-op silencioso, para que una llamada futura
      inesperada falle de forma ruidosa en vez de fingir que hizo
      algo.

Cómo se usa (ver `main.py`):

    from database.engine import create_all, create_database_engine
    from database.adapters import (
        SQLAchievementRepository, SQLInventoryRepository,
        SQLSaveRepository, SQLStatisticsRepository,
    )

    engine = create_database_engine()
    create_all(engine)
    AchievementService(repository=SQLAchievementRepository(engine))
    # ... mismo patrón para los otros 3.

Autor: Korlo
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from database.repositories import (
    AchievementRepository,
    InventoryRepository,
    PlayerNotFoundError,
    PlayerRepository,
    SaveSlotRepository,
    StatisticsRepository,
    StoryRepository,
)
from models.achievement import Achievement
from models.item import Item
from models.player import Player
from models.story import Story
from services.save_service import SAVE_FORMAT_VERSION
from services.statistics_service import AccountStatistics

logger = logging.getLogger(__name__)


class SQLStatisticsRepository:
    """`KeyValueRepository` de `StatisticsService` respaldado por la tabla `account_statistics` (mapeo 1:1)."""

    _PREFIX = "stats_"

    def __init__(self, engine) -> None:
        self._repo = StatisticsRepository(engine)

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        user_id = key[len(self._PREFIX):]
        return self._repo.get_statistics(user_id).to_dict()

    def set(self, key: str, value: Dict[str, Any]) -> None:
        user_id = key[len(self._PREFIX):]
        self._repo.save_statistics(user_id, AccountStatistics.from_dict(value))

    def delete(self, key: str) -> None:
        raise NotImplementedError("SQLStatisticsRepository.delete(): StatisticsService no lo usa hoy.")

    def list_keys(self, prefix: str = "") -> List[str]:
        raise NotImplementedError("SQLStatisticsRepository.list_keys(): StatisticsService no lo usa hoy.")


class SQLAchievementRepository:
    """`KeyValueRepository` de `AchievementService` respaldado por la tabla `player_achievements` (una fila por logro)."""

    _PREFIX = "achievements_"

    def __init__(self, engine) -> None:
        self._repo = AchievementRepository(engine)

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        player_id = key[len(self._PREFIX):]
        achievements = self._repo.list_achievements(player_id)
        return {"achievements": [a.to_dict() for a in achievements]}

    def set(self, key: str, value: Dict[str, Any]) -> None:
        player_id = key[len(self._PREFIX):]
        self._repo.clear_achievements(player_id)
        for data in value.get("achievements", []):
            self._repo.grant_achievement(player_id, Achievement.from_dict(data))

    def delete(self, key: str) -> None:
        raise NotImplementedError("SQLAchievementRepository.delete(): AchievementService no lo usa hoy.")

    def list_keys(self, prefix: str = "") -> List[str]:
        raise NotImplementedError("SQLAchievementRepository.list_keys(): AchievementService no lo usa hoy.")


class SQLInventoryRepository:
    """`KeyValueRepository` de `InventoryService` respaldado por la tabla `inventory_items` (una fila por objeto)."""

    _PREFIX = "inventory_"

    def __init__(self, engine) -> None:
        self._repo = InventoryRepository(engine)

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        player_id = key[len(self._PREFIX):]
        items = self._repo.get_items(player_id)
        # capacity: no tiene columna en el esquema — ver limitación
        # documentada arriba, siempre None (ilimitado), igual que hoy.
        return {"items": [i.to_dict() for i in items], "capacity": None}

    def set(self, key: str, value: Dict[str, Any]) -> None:
        player_id = key[len(self._PREFIX):]
        self._repo.clear_inventory(player_id)
        for data in value.get("items", []):
            self._repo.add_item(player_id, Item.from_dict(data))

    def delete(self, key: str) -> None:
        raise NotImplementedError("SQLInventoryRepository.delete(): InventoryService no lo usa hoy.")

    def list_keys(self, prefix: str = "") -> List[str]:
        raise NotImplementedError("SQLInventoryRepository.list_keys(): InventoryService no lo usa hoy.")


class SQLSaveRepository:
    """
    `KeyValueRepository` de `SaveService`, respaldado por 3 tablas a
    la vez (`players`, `story_progress`, `save_slots`) — el
    adaptador más grande de este archivo porque `SaveService` es el
    único service cuyo blob junta más de un tipo de dato. Ver
    limitaciones (NPCs, "no es una foto congelada") en el docstring
    del módulo.
    """

    _PREFIX = "save_"

    def __init__(self, engine) -> None:
        self._players = PlayerRepository(engine)
        self._stories = StoryRepository(engine)
        self._slots = SaveSlotRepository(engine)

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        save_id = key[len(self._PREFIX):]
        slot = self._slots.get_slot(save_id)
        if slot is None:
            return None
        try:
            player = self._players.get_player(slot["player_id"])
        except PlayerNotFoundError:
            logger.warning(
                "SQLSaveRepository: la ranura '%s' apunta a un jugador inexistente ('%s').",
                save_id, slot["player_id"],
            )
            return None
        stories = self._stories.list_stories_for_player(player.player_id)
        return {
            "format_version": SAVE_FORMAT_VERSION,
            "saved_at": slot.get("saved_at", ""),
            "player": player.to_dict(),
            "stories": [s.to_dict() for s in stories],
            "npcs": [],
        }

    def set(self, key: str, value: Dict[str, Any]) -> None:
        save_id = key[len(self._PREFIX):]
        player = Player.from_dict(value["player"])
        stories = [Story.from_dict(s) for s in value.get("stories", [])]
        npcs = value.get("npcs") or []
        if npcs:
            logger.warning(
                "SQLSaveRepository: %d NPC(s) en la partida '%s' NO se persisten "
                "— database/models.py todavía no tiene una tabla de NPCs.",
                len(npcs), save_id,
            )

        self._players.save_player(player)
        for story in stories:
            self._stories.save_story(story)
        self._slots.save_slot(
            save_id, player, value.get("saved_at", datetime.now(timezone.utc).isoformat())
        )

    def delete(self, key: str) -> None:
        """Borra solo la ranura (`save_slots`) — ver limitación documentada arriba sobre por qué no borra Player/Story."""
        save_id = key[len(self._PREFIX):]
        self._slots.delete_slot(save_id)

    def list_keys(self, prefix: str = "") -> List[str]:
        keys = [f"{self._PREFIX}{slot['save_id']}" for slot in self._slots.list_slots()]
        return sorted(k for k in keys if k.startswith(prefix))
