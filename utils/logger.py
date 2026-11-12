"""
utils/logger.py
================

Qué hace:
    Configura el logging de toda la aplicación (archivo con rotación
    + consola) y devuelve un logger listo para usar. Resuelve un
    import roto detectado en el análisis inicial del proyecto:
    `main.py` ya hace `from utils.logger import setup_logger` y lo
    llama sin argumentos (`setup_logger()`), y este archivo no
    existía.

Cómo funciona:
    Los handlers (archivo + consola) se registran en el logger
    RAÍZ (`logging.getLogger()`), no solo en el logger con nombre
    propio que se devuelve. Es intencional: todos los demás módulos
    del proyecto (`services/`, `managers/`, `models/`, etc.) ya usan
    el patrón estándar `logging.getLogger(__name__)`, que por
    defecto SÍ propaga hacia el logger raíz. Si los handlers se
    hubieran registrado solo en un logger llamado "what_if", ninguno
    de esos otros loggers (con nombres como "services.save_service")
    los habría heredado — no son descendientes de "what_if" en la
    jerarquía de puntos de `logging`, solo del logger raíz lo son,
    implícitamente, todos. Registrar en la raíz es lo que hace que
    cada `logger.info(...)` que ya existe en el resto del proyecto
    quede capturado sin tener que tocar esos archivos.

    Es idempotente: llamar a `setup_logger()` más de una vez no
    duplica handlers en el logger raíz — evita el error clásico de
    que cada línea se imprima N veces si algo llega a inicializar el
    logging más de una vez en el mismo proceso.

Dependencias:
    - config.paths: LOG_FILE (ubicación por defecto del archivo de log).

Cómo interactúa con otros módulos:
    `main.py` lo llama una única vez, al arrancar. El resto del
    proyecto no necesita importar nada de aquí: basta con que sigan
    usando `logging.getLogger(__name__)` como ya lo hacen.

Autor: Korlo
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from config.paths import LOG_FILE

DEFAULT_MAX_BYTES = 5 * 1024 * 1024  # 5 MB por archivo antes de rotar
DEFAULT_BACKUP_COUNT = 3
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(
    name: str = "what_if",
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
    console: bool = True,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
) -> logging.Logger:
    """
    Configura el logging de toda la aplicación y devuelve un logger
    con nombre `name` listo para usar.

    Args:
        name: nombre del logger que se devuelve para uso directo del
            llamador. No afecta a qué loggers heredan los handlers
            (eso lo determina la jerarquía de `logging`, ver arriba).
        log_file: archivo de log a usar; por defecto,
            `config.paths.LOG_FILE`.
        level: nivel mínimo de severidad a registrar en el logger raíz.
        console: si True, además de al archivo, escribe a consola
            (`stderr`).
        max_bytes: tamaño máximo del archivo de log antes de rotar.
        backup_count: cuántos archivos rotados conservar.

    Returns:
        Un `logging.Logger` con nombre `name`, ya operativo.
    """
    root_logger = logging.getLogger()

    if not root_logger.handlers:
        root_logger.setLevel(level)

        resolved_log_file = Path(log_file) if log_file is not None else LOG_FILE
        resolved_log_file.parent.mkdir(parents=True, exist_ok=True)

        formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

        file_handler = RotatingFileHandler(
            resolved_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        if console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)

    return logging.getLogger(name)