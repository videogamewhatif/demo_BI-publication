"""
database/
=========

Backend SQLAlchemy opcional para la persistencia del juego —
relacional (una tabla por tipo de dato: `players`, `story_progress`,
`inventory_items`, `player_achievements`, `account_statistics`,
`unlocked_endings`), como alternativa a los repositorios JSON de
`services/repositories.py`.

Qué reemplaza:
    La carpeta `database/` anterior a esta sesión estaba rota
    (`database/migrations/migration_manager.py` importaba
    `database.database`, que no existía) y desconectada — tres
    esquemas SQL sin relación entre sí, ninguno usado por el código
    real. Se retiró por completo (ver `docs/changelog.md`); esta es
    una construcción nueva desde cero, no una reparación de la vieja.

Por qué es opcional y no el backend por defecto:
    `services/repositories.py::JSONKeyValueRepository` está probado
    con 70+ pruebas reales y es lo que usa `main.py` hoy. Cambiar el
    backend por defecto sin que nadie lo pidiera habría arriesgado
    ese camino ya estable. Este paquete es una alternativa
    completamente funcional y probada, lista para activarse — ver
    `docs/architecture.md` para cómo.

Submódulos:
    - models.py: 7 tablas relacionales (`sqlalchemy.Table`/`Column`
      — Core, no ORM declarativo, ver el porqué en el docstring de
      `database/repositories.py`).
    - engine.py: creación de engine/sesión de SQLAlchemy y creación
      de tablas.
    - repositories.py: 7 repositorios con API tipada por dominio
      (`get_player`/`save_player`, `grant_achievement`, etc.) — a
      propósito NO implementan `ContentRepository`/`KeyValueRepository`
      directamente (ver su propio docstring para el porqué).
    - adapters.py: el puente — 4 clases que sí implementan
      `KeyValueRepository` (mismos `Protocol` de
      `services/repositories.py`) delegando en repositories.py.
      `main.py` ya las usa para `SaveService`/`StatisticsService`/
      `AchievementService`/`InventoryService` — activado, no solo
      disponible.

Autor: Korlo (backend SQLAlchemy añadido en la sesión de deuda técnica)
"""
