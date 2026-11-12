"""
database/models.py
=====================

Qué hace:
    Define las 7 tablas relacionales con `sqlalchemy.Table`/`Column`
    (Core, no ORM declarativo — ver el porqué en el docstring de
    `database/repositories.py`), una por tipo de dato real del
    proyecto, con columnas tipadas para cada campo escalar.

Listas/diccionarios anidados (`personality_traits`, `family`,
`statistics`, `flags`...) se guardan como columnas `String` con
JSON serializado a mano (`json.dumps`/`json.loads` en
`database/repositories.py`) — no porque el stub de este entorno no
tenga un tipo `JSON` dedicado (no lo tiene), sino porque así el
mismo código funciona igual contra el stub Y contra SQLAlchemy real
sin depender de una función de éste último.

`inventory_items`, `player_achievements` y `unlocked_endings` SÍ son
relacionales de verdad (una fila por objeto/logro/final, no un
blob) — es la diferencia real frente a guardar todo como JSON:
permiten `add`/`remove` de un elemento individual sin reescribir
todo lo demás.

Autor: Korlo (reconstruido en la sesión de deuda técnica)
"""

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, MetaData, String, Table

metadata = MetaData()

players = Table(
    "players", metadata,
    Column("player_id", String, primary_key=True),
    Column("first_name", String, nullable=False),
    Column("last_name", String, nullable=False),
    Column("gender", String, nullable=True),
    Column("birth_year", Integer, nullable=False),
    Column("country", String, nullable=False),
    Column("city", String, nullable=True),
    Column("socioeconomic_origin", String, nullable=False),
    Column("health_genetics", Integer, nullable=False),
    Column("birth_hook", String, nullable=True),
    Column("age", Integer, nullable=False),
    Column("life_expectancy", Float, nullable=False),
    Column("health", Integer, nullable=False),
    Column("appearance", Integer, nullable=False),
    Column("intelligence", Integer, nullable=False),
    Column("discipline", Integer, nullable=False),
    Column("creativity", Integer, nullable=False),
    Column("stress", Integer, nullable=False),
    Column("happiness", Integer, nullable=False),
    Column("charisma", Integer, nullable=False),
    Column("empathy", Integer, nullable=False),
    Column("reputation", Integer, nullable=False),
    Column("aspiration", String, nullable=True),
    Column("net_worth", Float, nullable=False),
    Column("annual_income", Float, nullable=False),
    Column("debt", Float, nullable=False),
    Column("education_level", String, nullable=False),
    Column("current_profession", String, nullable=True),
    Column("civil_status", String, nullable=False),
    # Listas/diccionarios del dataclass original, JSON en texto (ver docstring del módulo)
    Column("personality_traits", String, nullable=False),
    Column("talents", String, nullable=False),
    Column("family", String, nullable=False),
    Column("active_relationships", String, nullable=False),
    Column("memory_moments", String, nullable=False),
    # PlayerStatistics — plano, columnas reales en vez de JSON (es solo 3 enteros)
    Column("turns_played", Integer, nullable=False, default=0),
    Column("decisions_made", Integer, nullable=False, default=0),
    Column("key_moments_unlocked", Integer, nullable=False, default=0),
)

story_progress = Table(
    "story_progress", metadata,
    Column("story_id", String, primary_key=True),
    Column("player_id", String, ForeignKey("players.player_id"), nullable=False),
    Column("title", String, nullable=False),
    Column("story_content_id", String, nullable=True),
    Column("genre", String, nullable=True),
    Column("setting", String, nullable=True),
    Column("objective", String, nullable=True),
    Column("chapter", Integer, nullable=False),
    Column("current_scene_id", String, nullable=False),
    Column("status", String, nullable=False),
    Column("summary", String, nullable=True),
    Column("current_situation", String, nullable=True),
    Column("started_at_age", Integer, nullable=True),
    Column("ending_id", String, nullable=True),
    Column("events", String, nullable=False),
    Column("important_choices", String, nullable=False),
    Column("active_npcs", String, nullable=False),
    Column("flags", String, nullable=False),
)

inventory_items = Table(
    "inventory_items", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("player_id", String, ForeignKey("players.player_id"), nullable=False),
    Column("item_id", String, nullable=False),
    Column("name", String, nullable=False),
    Column("description", String, nullable=False, default=""),
    Column("item_type", String, nullable=False, default="general"),
    Column("rarity", String, nullable=False, default="common"),
    Column("quantity", Integer, nullable=False, default=1),
    Column("stackable", Boolean, nullable=False, default=True),
    Column("consumable", Boolean, nullable=False, default=False),
    Column("metadata_json", String, nullable=False, default="{}"),
)

player_achievements = Table(
    "player_achievements", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("player_id", String, ForeignKey("players.player_id"), nullable=False),
    Column("achievement_id", String, nullable=False),
    Column("title", String, nullable=False),
    Column("description", String, nullable=False, default=""),
    Column("category", String, nullable=False, default="general"),
    Column("rarity", String, nullable=False, default="common"),
    Column("points", Integer, nullable=False, default=0),
    Column("unlocked", Boolean, nullable=False, default=False),
    Column("unlocked_at", String, nullable=True),
    Column("required_flags", String, nullable=False, default="{}"),
    Column("required_choices", String, nullable=False, default="[]"),
    Column("rewards", String, nullable=False, default="[]"),
    Column("metadata_json", String, nullable=False, default="{}"),
)

unlocked_endings = Table(
    "unlocked_endings", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("player_id", String, ForeignKey("players.player_id"), nullable=False),
    Column("ending_id", String, nullable=False),
    Column("unlocked_at", String, nullable=True),
)

account_statistics = Table(
    "account_statistics", metadata,
    Column("user_id", String, primary_key=True),
    Column("total_games", Integer, nullable=False, default=0),
    Column("total_deaths", Integer, nullable=False, default=0),
    Column("total_play_time", Integer, nullable=False, default=0),
    Column("achievements_unlocked", Integer, nullable=False, default=0),
)

save_slots = Table(
    "save_slots", metadata,
    Column("save_id", String, primary_key=True),
    Column("player_id", String, ForeignKey("players.player_id"), nullable=False),
    Column("player_name", String, nullable=False),
    Column("saved_at", String, nullable=False),
)
