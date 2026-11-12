"""
database/repositories.py
===========================

Qué hace:
    7 repositorios con métodos tipados sobre las dataclasses reales
    del proyecto (`Player`, `Story`, `Item`, `Achievement`,
    `AccountStatistics`) — no una interfaz genérica `get(key)`/`set(key, value)`
    como `services/repositories.py::KeyValueRepository`. Se eligió
    así a propósito: "relacional completo" (la opción que se pidió
    explícitamente sobre la alternativa clave-valor genérica) se
    aprovecha mejor con métodos que reflejan el dominio real
    (`add_item`, `unlock_achievement`, `list_stories_for_player`)
    que forzando todo detrás de `get`/`set`.

Por qué SQLAlchemy Core y no el ORM declarativo (`DeclarativeBase`):
    Con Core, cada método de este archivo controla exactamente qué
    SQL se ejecuta — no hay identity map, no hay sesiones con estado
    implícito, no hay ambigüedad sobre cuándo se hace un `INSERT` vs
    un `UPDATE` (`save_player`/`save_story` deciden eso
    explícitamente). Para un puñado de tablas con relaciones
    simples, es más fácil de auditar línea por línea — que es
    justamente el criterio que ya se usó en todo este proyecto
    (mutadores explícitos en `Player`, `to_dict()`/`from_dict()`
    explícitos en cada dataclass, en vez de serialización "mágica").

Reutiliza `to_dict()`/`from_dict()` reales:
    Cada método convierte a/desde dataclass usando el
    `to_dict()`/`from_dict()` que ESE dataclass ya tiene y ya prueba
    su propio test — este archivo no reimplementa la conversión de
    enums a `.value` ni la reconstrucción inversa, solo mapea entre
    ese dict y las columnas de su tabla.

Autor: Korlo (reconstruido en la sesión de deuda técnica)
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, insert, select, update

from database.models import (
    account_statistics,
    inventory_items,
    player_achievements,
    players,
    save_slots,
    story_progress,
    unlocked_endings,
)
from models.achievement import Achievement
from models.item import Item
from models.player import Player
from models.story import Story
from services.statistics_service import AccountStatistics

_PLAYER_JSON_FIELDS = ("personality_traits", "talents", "family", "active_relationships", "memory_moments")
_STORY_JSON_FIELDS = ("events", "important_choices", "active_npcs", "flags")


class PlayerNotFoundError(Exception):
    """No existe ningún `Player` con ese `player_id` en la base de datos."""


class StoryNotFoundError(Exception):
    """No existe ninguna `Story` con ese `story_id` en la base de datos."""


class PlayerRepository:
    """`Player` <-> tabla `players` — una fila por jugador, columnas tipadas."""

    def __init__(self, engine) -> None:
        self._engine = engine

    def save_player(self, player: Player) -> None:
        """Guarda `player`, reemplazando la fila si ya existía (mismo `player_id`)."""
        data = player.to_dict()
        row = {k: v for k, v in data.items() if k not in _PLAYER_JSON_FIELDS}
        for field in _PLAYER_JSON_FIELDS:
            row[field] = json.dumps(data[field])
        stats = data["statistics"]
        row.pop("statistics")
        row["turns_played"] = stats["turns_played"]
        row["decisions_made"] = stats["decisions_made"]
        row["key_moments_unlocked"] = stats["key_moments_unlocked"]

        with self._engine.begin() as conn:
            if self.player_exists(player.player_id):
                conn.execute(update(players).where(players.c.player_id == player.player_id).values(**row))
            else:
                conn.execute(insert(players).values(**row))

    def get_player(self, player_id: str) -> Player:
        """
        Recupera un `Player` completo por su id.

        Raises:
            PlayerNotFoundError: si no existe.
        """
        with self._engine.begin() as conn:
            result = conn.execute(select(players).where(players.c.player_id == player_id))
            row = result.mappings().first()
        if row is None:
            raise PlayerNotFoundError(f"No existe ningún jugador con id '{player_id}'.")

        data = dict(row)
        for field in _PLAYER_JSON_FIELDS:
            data[field] = json.loads(data[field])
        data["statistics"] = {
            "turns_played": data.pop("turns_played"),
            "decisions_made": data.pop("decisions_made"),
            "key_moments_unlocked": data.pop("key_moments_unlocked"),
        }
        return Player.from_dict(data)

    def player_exists(self, player_id: str) -> bool:
        with self._engine.begin() as conn:
            result = conn.execute(select(players.c.player_id).where(players.c.player_id == player_id))
            return result.first() is not None


class StoryRepository:
    """`Story` <-> tabla `story_progress` — `player_id` es una columna real, consultable directo."""

    def __init__(self, engine) -> None:
        self._engine = engine

    def save_story(self, story: Story) -> None:
        """Guarda `story`, reemplazando la fila si ya existía (mismo `story_id`)."""
        data = story.to_dict()
        row = {k: v for k, v in data.items() if k not in _STORY_JSON_FIELDS}
        for field in _STORY_JSON_FIELDS:
            row[field] = json.dumps(data[field])

        with self._engine.begin() as conn:
            exists = conn.execute(
                select(story_progress.c.story_id).where(story_progress.c.story_id == story.story_id)
            ).first() is not None
            if exists:
                conn.execute(
                    update(story_progress).where(story_progress.c.story_id == story.story_id).values(**row)
                )
            else:
                conn.execute(insert(story_progress).values(**row))

    def get_story(self, story_id: str) -> Story:
        """
        Recupera una `Story` completa por su id.

        Raises:
            StoryNotFoundError: si no existe.
        """
        with self._engine.begin() as conn:
            result = conn.execute(select(story_progress).where(story_progress.c.story_id == story_id))
            row = result.mappings().first()
        if row is None:
            raise StoryNotFoundError(f"No existe ninguna historia con id '{story_id}'.")

        data = dict(row)
        for field in _STORY_JSON_FIELDS:
            data[field] = json.loads(data[field])
        return Story.from_dict(data)

    def list_stories_for_player(self, player_id: str) -> List[Story]:
        """`SELECT * FROM story_progress WHERE player_id = ?` real — no lista-todo-y-filtra-en-Python."""
        with self._engine.begin() as conn:
            result = conn.execute(select(story_progress).where(story_progress.c.player_id == player_id))
            rows = result.mappings().all()
        stories = []
        for row in rows:
            data = dict(row)
            for field in _STORY_JSON_FIELDS:
                data[field] = json.loads(data[field])
            stories.append(Story.from_dict(data))
        return stories


class InventoryRepository:
    """`Item` <-> tabla `inventory_items` — una fila POR OBJETO, no un blob por jugador."""

    def __init__(self, engine) -> None:
        self._engine = engine

    def add_item(self, player_id: str, item: Item) -> None:
        data = item.to_dict()
        with self._engine.begin() as conn:
            conn.execute(
                insert(inventory_items).values(
                    player_id=player_id,
                    item_id=data["item_id"],
                    name=data["name"],
                    description=data.get("description", ""),
                    item_type=data.get("item_type", "general"),
                    rarity=data.get("rarity", "common"),
                    quantity=data.get("quantity", 1),
                    stackable=data.get("stackable", True),
                    consumable=data.get("consumable", False),
                    metadata_json=json.dumps(data.get("metadata", {})),
                )
            )

    def get_items(self, player_id: str) -> List[Item]:
        with self._engine.begin() as conn:
            result = conn.execute(select(inventory_items).where(inventory_items.c.player_id == player_id))
            rows = result.mappings().all()
        items = []
        for row in rows:
            items.append(
                Item.from_dict(
                    {
                        "item_id": row["item_id"],
                        "name": row["name"],
                        "description": row["description"],
                        "item_type": row["item_type"],
                        "rarity": row["rarity"],
                        "quantity": row["quantity"],
                        "stackable": bool(row["stackable"]),
                        "consumable": bool(row["consumable"]),
                        "metadata": json.loads(row["metadata_json"]),
                    }
                )
            )
        return items

    def remove_item(self, player_id: str, item_id: str) -> bool:
        """Quita UNA unidad con ese `item_id` (la primera que encuentre). Devuelve False si no existía."""
        with self._engine.begin() as conn:
            row = conn.execute(
                select(inventory_items.c.id)
                .where(inventory_items.c.player_id == player_id)
                .where(inventory_items.c.item_id == item_id)
                .limit(1)
            ).mappings().first()
            if row is None:
                return False
            conn.execute(delete(inventory_items).where(inventory_items.c.id == row["id"]))
            return True

    def clear_inventory(self, player_id: str) -> None:
        with self._engine.begin() as conn:
            conn.execute(delete(inventory_items).where(inventory_items.c.player_id == player_id))


class AchievementRepository:
    """`Achievement` <-> tabla `player_achievements` — un logro otorgado = una fila real."""

    def __init__(self, engine) -> None:
        self._engine = engine

    def grant_achievement(self, player_id: str, achievement: Achievement) -> None:
        data = achievement.to_dict()
        with self._engine.begin() as conn:
            conn.execute(
                insert(player_achievements).values(
                    player_id=player_id,
                    achievement_id=data["achievement_id"],
                    title=data["title"],
                    description=data.get("description", ""),
                    category=data.get("category", "general"),
                    rarity=data.get("rarity", "common"),
                    points=data.get("points", 0),
                    unlocked=data.get("unlocked", False),
                    unlocked_at=data.get("unlocked_at"),
                    required_flags=json.dumps(data.get("required_flags", {})),
                    required_choices=json.dumps(data.get("required_choices", [])),
                    rewards=json.dumps(data.get("rewards", [])),
                    metadata_json=json.dumps(data.get("metadata", {})),
                )
            )

    def list_achievements(self, player_id: str) -> List[Achievement]:
        with self._engine.begin() as conn:
            result = conn.execute(
                select(player_achievements).where(player_achievements.c.player_id == player_id)
            )
            rows = result.mappings().all()
        achievements = []
        for row in rows:
            achievements.append(
                Achievement.from_dict(
                    {
                        "achievement_id": row["achievement_id"],
                        "title": row["title"],
                        "description": row["description"],
                        "category": row["category"],
                        "rarity": row["rarity"],
                        "points": row["points"],
                        "unlocked": bool(row["unlocked"]),
                        "unlocked_at": row["unlocked_at"],
                        "required_flags": json.loads(row["required_flags"]),
                        "required_choices": json.loads(row["required_choices"]),
                        "rewards": json.loads(row["rewards"]),
                        "metadata": json.loads(row["metadata_json"]),
                    }
                )
            )
        return achievements

    def unlock_achievement(self, player_id: str, achievement_id: str, unlocked_at: str) -> bool:
        """Marca como desbloqueado un logro ya otorgado. Devuelve False si el jugador no lo tenía."""
        with self._engine.begin() as conn:
            row = conn.execute(
                select(player_achievements.c.id)
                .where(player_achievements.c.player_id == player_id)
                .where(player_achievements.c.achievement_id == achievement_id)
            ).mappings().first()
            if row is None:
                return False
            conn.execute(
                update(player_achievements)
                .where(player_achievements.c.id == row["id"])
                .values(unlocked=True, unlocked_at=unlocked_at)
            )
            return True

    def clear_achievements(self, player_id: str) -> None:
        """Borra TODOS los logros otorgados a `player_id` (usado por el adaptador de KeyValueRepository para 'set' = reemplazo completo)."""
        with self._engine.begin() as conn:
            conn.execute(delete(player_achievements).where(player_achievements.c.player_id == player_id))


class EndingRepository:
    """Finales de vida desbloqueados <-> tabla `unlocked_endings` — un desbloqueo = una fila real."""

    def __init__(self, engine) -> None:
        self._engine = engine

    def has_ending(self, player_id: str, ending_id: str) -> bool:
        with self._engine.begin() as conn:
            row = conn.execute(
                select(unlocked_endings.c.id)
                .where(unlocked_endings.c.player_id == player_id)
                .where(unlocked_endings.c.ending_id == ending_id)
            ).first()
            return row is not None

    def unlock_ending(self, player_id: str, ending_id: str, unlocked_at: str) -> None:
        if self.has_ending(player_id, ending_id):
            return
        with self._engine.begin() as conn:
            conn.execute(
                insert(unlocked_endings).values(
                    player_id=player_id, ending_id=ending_id, unlocked_at=unlocked_at
                )
            )

    def list_unlocked(self, player_id: str) -> List[str]:
        with self._engine.begin() as conn:
            result = conn.execute(
                select(unlocked_endings.c.ending_id).where(unlocked_endings.c.player_id == player_id)
            )
            return [row["ending_id"] for row in result.mappings().all()]


class StatisticsRepository:
    """`AccountStatistics` <-> tabla `account_statistics` — mapeo directo 1:1, ya era plano."""

    def __init__(self, engine) -> None:
        self._engine = engine

    def get_statistics(self, user_id: str) -> AccountStatistics:
        """
        Estadísticas de cuenta de `user_id`, o unas vacías (todo en
        0) si todavía no tiene ninguna — mismo comportamiento que
        `services.statistics_service.StatisticsService.get_statistics()`
        sobre JSON: no lanza excepción por una cuenta nueva.
        """
        with self._engine.begin() as conn:
            result = conn.execute(
                select(account_statistics).where(account_statistics.c.user_id == user_id)
            )
            row = result.mappings().first()
        if row is None:
            return AccountStatistics(user_id=user_id)
        return AccountStatistics.from_dict(dict(row))

    def save_statistics(self, user_id: str, stats: AccountStatistics) -> None:
        data = stats.to_dict()
        with self._engine.begin() as conn:
            exists = conn.execute(
                select(account_statistics.c.user_id).where(account_statistics.c.user_id == user_id)
            ).first() is not None
            if exists:
                conn.execute(
                    update(account_statistics)
                    .where(account_statistics.c.user_id == user_id)
                    .values(**data)
                )
            else:
                conn.execute(insert(account_statistics).values(**data))


class SaveSlotRepository:
    """Guardado rápido/manual <-> tabla `save_slots` — snapshot ligero (id + nombre), no el `Player` completo."""

    def __init__(self, engine) -> None:
        self._engine = engine

    def save_slot(self, save_id: str, player: Player, saved_at: str) -> None:
        with self._engine.begin() as conn:
            exists = conn.execute(
                select(save_slots.c.save_id).where(save_slots.c.save_id == save_id)
            ).first() is not None
            values: Dict[str, Any] = {
                "player_id": player.player_id,
                "player_name": player.full_name,
                "saved_at": saved_at,
            }
            if exists:
                conn.execute(update(save_slots).where(save_slots.c.save_id == save_id).values(**values))
            else:
                conn.execute(insert(save_slots).values(save_id=save_id, **values))

    def list_slots(self) -> List[Dict[str, Any]]:
        with self._engine.begin() as conn:
            result = conn.execute(select(save_slots))
            return [dict(row) for row in result.mappings().all()]

    def get_slot(self, save_id: str) -> Optional[Dict[str, Any]]:
        """Una sola ranura por `save_id`, o None si no existe (usado por el adaptador de KeyValueRepository para 'get')."""
        with self._engine.begin() as conn:
            result = conn.execute(select(save_slots).where(save_slots.c.save_id == save_id))
            row = result.mappings().first()
        return dict(row) if row is not None else None

    def delete_slot(self, save_id: str) -> None:
        with self._engine.begin() as conn:
            conn.execute(delete(save_slots).where(save_slots.c.save_id == save_id))
