"""
utils/file_utils.py
====================

Qué hace:
    Utilidades genéricas de manejo de archivos: lectura/escritura de
    JSON con manejo de errores, normalización de texto a nombre de
    archivo seguro, y creación de directorios.

Por qué existe:
    Al construir `services/repositories.py` y `services/image_service.py`
    en entregas anteriores, terminé escribiendo dos veces la misma
    normalización de nombre de archivo (`key.replace("/", "_")...`)
    y la misma lectura/escritura de JSON con manejo de errores, en
    archivos distintos. Con `utils/` ya existiendo, ese es su lugar
    correcto — así que este archivo consolida esa lógica, y
    `services/repositories.py` y `services/image_service.py` pasan a
    reutilizarla en vez de duplicarla (ver la sección de refactors
    en la Explicación).

Dependencias:
    - Solo biblioteca estándar (json, pathlib, re).

Cómo interactúa con otros módulos:
    Lo usan `services/repositories.py` (lectura/escritura de JSON) y
    `services/image_service.py` (nombre de archivo seguro).
    Cualquier módulo futuro que necesite persistir algo en disco
    debería apoyarse en este archivo en vez de reimplementar su
    propia versión.

Autor: Korlo
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9_.\-]")


def safe_filename(text: str) -> str:
    """
    Convierte `text` en un nombre de archivo seguro: reemplaza
    cualquier carácter que no sea letra, dígito, guion, guion bajo o
    punto por un guion bajo.

    Args:
        text: texto de origen (por ejemplo, un id o un título).

    Returns:
        Una versión de `text` segura para usar como nombre de
        archivo en cualquier sistema operativo común.

    Raises:
        ValueError: si `text` está vacío.

    Examples:
        >>> safe_filename("historia/primer_empleo")
        'historia_primer_empleo'
        >>> safe_filename("María José")
        'Mar_a_Jos_'
    """
    if not text:
        raise ValueError("text no puede estar vacío.")
    return _UNSAFE_FILENAME_CHARS.sub("_", text)


def ensure_directory(path: Path) -> Path:
    """
    Crea `path` (y cualquier carpeta intermedia) si todavía no
    existe, y lo devuelve — pensado para encadenarse:
    `ensure_directory(base_dir) / "archivo.json"`.
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_json(path: Path) -> Optional[dict]:
    """
    Lee y parsea un archivo JSON.

    Returns:
        El contenido parseado, o None si el archivo no existe.

    Raises:
        json.JSONDecodeError: si el archivo existe pero no contiene
            JSON válido.
        OSError: ante cualquier otro error de lectura.
    """
    path = Path(path)
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError) as error:
        logger.error("file_utils: error leyendo JSON de %s: %s", path, error)
        raise


def write_json(path: Path, data: Any) -> None:
    """
    Serializa `data` como JSON y lo escribe en `path`, creando las
    carpetas intermedias si hace falta.

    Raises:
        OSError: si no se puede escribir el archivo.
        TypeError: si `data` no es serializable a JSON.
    """
    path = Path(path)
    ensure_directory(path.parent)
    try:
        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
    except OSError as error:
        logger.error("file_utils: error escribiendo JSON en %s: %s", path, error)
        raise