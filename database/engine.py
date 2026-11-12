"""
database/engine.py
=====================

Qué hace:
    Crea el `Engine` de SQLAlchemy apuntando a un archivo SQLite, y
    crea las 7 tablas de `database/models.py` si no existen. Un solo
    lugar para esto — nadie más en el proyecto debería construir un
    `Engine` por su cuenta.

Cómo se usa:

    from database.engine import create_database_engine, create_all

    engine = create_database_engine()  # config.paths.DATABASE_PATH por defecto
    create_all(engine)

    # Contra Postgres (Supabase u otro), pasando la cadena de conexión
    # explícita — nunca se lee de `os.environ` aquí, eso es
    # responsabilidad de quien llama (ver main.py):
    engine = create_database_engine(db_url="postgresql://...")
    create_all(engine)

Autor: Korlo (reconstruido en la sesión de deuda técnica; `db_url`
añadido para Postgres remoto)
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from sqlalchemy import create_engine

from config.paths import DATABASE_PATH
from database.models import metadata


def create_database_engine(
    db_path: Optional[Union[str, Path]] = None, *, db_url: Optional[str] = None, echo: bool = False
):
    """
    Crea el `Engine`. Si se pasa `db_url` (p. ej. la cadena Postgres
    de Supabase), se usa tal cual; si no, apunta a `db_path` (por
    defecto, `config.paths.DATABASE_PATH`) como SQLite local, creando
    la carpeta contenedora si no existe.
    """
    if db_url:
        return create_engine(db_url, echo=echo)
    path = Path(db_path) if db_path is not None else DATABASE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{path}", echo=echo)


def create_all(engine) -> None:
    """Crea las 7 tablas de `database.models` que todavía no existan. Segura de llamar más de una vez."""
    metadata.create_all(engine)
