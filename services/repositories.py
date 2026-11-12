"""
services/repositories.py
=========================

Qué hace:
    Define las abstracciones de persistencia (Repository Pattern) de
    las que dependen los servicios de `services/`, y una
    implementación por defecto basada en archivos JSON locales.

    No estaba en la lista de archivos pedida originalmente, pero es
    una utilidad que varios de los servicios pedidos necesitan ("Si
    un servicio necesita utilidades, créalas"): sin esto, cada
    servicio tendría que reimplementar su propia lectura/escritura
    de archivos, duplicando lógica de manejo de errores y de rutas.

Cómo funciona:
    Expone dos `Protocol` (interfaces estructurales, sin herencia
    obligatoria):

    - `ContentRepository`: acceso de SOLO LECTURA a contenido
      narrativo/estático (historias, localización...). Corresponde a
      la mitad "JSON" de la separación de datos del proyecto.
    - `KeyValueRepository`: acceso de lectura/escritura a estado
      dinámico (partidas guardadas, progreso de historias,
      estadísticas). Es un sustituto temporal de la capa SQLite que
      todavía no existe (ver database/, pendiente de consolidación
      en un esquema único con SQLAlchemy).

    Los servicios de negocio (`save_service`, `story_service`,
    `statistics_service`, `localization_service`) dependen de estas
    interfaces, nunca de `JSONContentRepository`/
    `JSONKeyValueRepository` directamente (Dependency Inversion):
    así, cuando `database/` tenga un esquema SQLAlchemy consolidado,
    bastará con escribir una clase que cumpla `KeyValueRepository` y
    pasarla al construir cada servicio — ningún servicio necesitará
    cambiar una sola línea.

    Nota de revisión: las dos implementaciones por defecto usaban
    cada una su propia lectura/escritura de JSON y su propia
    normalización de nombre de archivo, duplicadas entre sí. Con
    `utils/` ya construido, ambas pasan a reutilizar
    `utils.file_utils` — mismo comportamiento observable, sin la
    duplicación (y con una normalización de nombre de archivo algo
    más estricta: además de barras, ahora también reemplaza
    cualquier otro carácter no seguro para un nombre de archivo).

Dependencias:
    - utils.file_utils: safe_filename, ensure_directory, read_json, write_json.

Cómo interactúa con otros módulos:
    Lo importan todos los archivos de `services/` que necesitan leer
    contenido o persistir estado. `config.paths` define los
    directorios base que se le pasan a las implementaciones por
    defecto.

Autor: Korlo
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from utils.file_utils import ensure_directory, read_json, safe_filename, write_json

logger = logging.getLogger(__name__)


# ==================================================
# INTERFACES (Protocols)
# ==================================================


@runtime_checkable
class ContentRepository(Protocol):
    """
    Acceso de solo lectura a contenido narrativo/estático (JSON).

    Implementado por adaptadores que leen `data/` (historias,
    localización, finales, etc.). El contenido nunca se escribe en
    tiempo de ejecución: lo edita el equipo de diseño directamente
    en los archivos JSON.
    """

    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Carga el contenido asociado a `key`, o None si no existe."""
        ...

    def exists(self, key: str) -> bool:
        """Indica si existe contenido asociado a `key`."""
        ...

    def list_keys(self, prefix: str = "") -> List[str]:
        """Lista las claves de contenido existentes, opcionalmente filtradas por prefijo."""
        ...


@runtime_checkable
class KeyValueRepository(Protocol):
    """
    Acceso de lectura/escritura a estado dinámico (partidas,
    progreso de historias, estadísticas).

    Sustituto temporal de la capa SQLAlchemy todavía no construida.
    Cualquier implementación futura basada en SQLite debe cumplir
    este mismo contrato para poder reemplazar a
    `JSONKeyValueRepository` sin tocar los servicios que lo usan.
    """

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Recupera el valor asociado a `key`, o None si no existe."""
        ...

    def set(self, key: str, value: Dict[str, Any]) -> None:
        """Guarda `value` bajo `key`, sobrescribiendo si ya existía."""
        ...

    def delete(self, key: str) -> None:
        """Elimina el valor asociado a `key`, si existe. No falla si no existe."""
        ...

    def list_keys(self, prefix: str = "") -> List[str]:
        """Lista las claves existentes, opcionalmente filtradas por prefijo."""
        ...


# ==================================================
# IMPLEMENTACIÓN POR DEFECTO — ARCHIVOS JSON
# ==================================================


class JSONContentRepository:
    """
    Implementación por defecto de `ContentRepository`: cada `key`
    corresponde a un archivo `<key>.json` dentro de un directorio
    base (típicamente una subcarpeta de `config.paths.DATA_DIR`).
    """

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = ensure_directory(Path(base_dir))

    def load(self, key: str) -> Optional[Dict[str, Any]]:
        path = self._path_for(key)
        if not path.exists():
            logger.debug("ContentRepository: '%s' no encontrado en %s", key, path)
            return None
        return read_json(path)

    def exists(self, key: str) -> bool:
        return self._path_for(key).exists()

    def list_keys(self, prefix: str = "") -> List[str]:
        return sorted(p.stem for p in self._base_dir.glob(f"{prefix}*.json"))

    def _path_for(self, key: str) -> Path:
        return self._base_dir / f"{safe_filename(key)}.json"


class JSONKeyValueRepository:
    """
    Implementación por defecto de `KeyValueRepository`: cada `key`
    se guarda como un archivo `<key>.json` independiente dentro de
    un directorio base (típicamente `config.paths.SAVES_DIR`).

    Nota de arquitectura: es una solución de arranque para poder
    probar los servicios de principio a fin HOY, no la persistencia
    definitiva. Las instrucciones originales del proyecto son
    explícitas: "toda la información dinámica del jugador vive en
    SQLite". Cuando `database/` tenga un esquema SQLAlchemy
    consolidado (pendiente, ver análisis de esa carpeta), debe
    escribirse una implementación de `KeyValueRepository` respaldada
    por SQLite y usarla en su lugar.
    """

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = ensure_directory(Path(base_dir))

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        return read_json(self._path_for(key))

    def set(self, key: str, value: Dict[str, Any]) -> None:
        write_json(self._path_for(key), value)
        logger.debug("KeyValueRepository: '%s' guardado en %s", key, self._path_for(key))

    def delete(self, key: str) -> None:
        path = self._path_for(key)
        if path.exists():
            path.unlink()
            logger.debug("KeyValueRepository: '%s' eliminado", key)

    def list_keys(self, prefix: str = "") -> List[str]:
        return sorted(p.stem for p in self._base_dir.glob(f"{prefix}*.json"))

    def _path_for(self, key: str) -> Path:
        return self._base_dir / f"{safe_filename(key)}.json"