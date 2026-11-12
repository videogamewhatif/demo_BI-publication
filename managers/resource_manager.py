"""
managers/resource_manager.py
=============================

Qué hace:
    Carga y cachea imágenes, iconos y fuentes bajo demanda desde
    `config.paths` (`IMAGES_DIR`, `ICONS_DIR`, `FONTS_DIR`,
    `BACKGROUNDS_DIR`, `CHARACTER_IMAGES_DIR`, `UI_IMAGES_DIR`,
    `ENDING_IMAGES_DIR`), para que quien construya la interfaz no
    tenga que preocuparse por rutas de archivo ni recargar el mismo
    recurso dos veces.

Por qué la carga vive aquí y no en `services/`:
    No hay ninguna regla de negocio detrás de "leer un archivo de
    imagen del disco" — es un detalle de infraestructura de
    presentación (qué recurso mostrar, cuándo tenerlo listo en
    memoria), exactamente el tipo de coordinación que corresponde a
    un manager según tu propia definición. Cada método público es
    "revisa el caché; si no está, carga y cachea" — no hay lógica que
    extraer a un servicio separado.

Categorías de imagen (añadidas en la sesión de deuda técnica):
    `config/paths.py` reestructuró `assets/images/` en subcategorías
    (`backgrounds/`, `characters/`, `ui/`, `endings/`, además de
    `icons/`) desde la sesión de assets, pero esta clase solo
    exponía getters para `images/` (plano) e `icons/` — las otras 4
    carpetas existían físicamente sin ningún método que las leyera.
    `get_background()`, `get_character_image()`, `get_ui_image()` y
    `get_ending_image()` cierran ese hueco, con el mismo patrón
    exacto que ya usaban `get_image()`/`get_icon()` — ningún
    mecanismo nuevo, solo más categorías sobre el mismo `_load_image()`.

Cómo funciona:
    Usa Pillow (ya en requirements.txt; también la usa
    `services/image_service.py`) para decodificar imágenes y
    fuentes. Cachea por id de recurso (y, para fuentes, también por
    tamaño) en diccionarios en memoria — sin límite de tamaño por
    ahora; si el catálogo de assets crece mucho, `clear_cache()`
    permite liberar memoria manualmente (por ejemplo, al cambiar de
    escena).

Dependencias:
    - config.paths: IMAGES_DIR, ICONS_DIR, FONTS_DIR, BACKGROUNDS_DIR,
      CHARACTER_IMAGES_DIR, UI_IMAGES_DIR, ENDING_IMAGES_DIR.
    - Pillow (import perezoso, igual que en services/image_service.py).

Cómo interactúa con otros módulos:
    `ui/` es la consumidora principal: cada pantalla pediría sus
    imágenes/iconos/fuentes por id en vez de tocar el sistema de
    archivos directamente. Ningún widget de `ui/` llama a los 4
    getters nuevos todavía — no hay imágenes reales en
    `assets/images/{backgrounds,characters,ui,endings}/` para cargar
    (carpetas creadas con `.gitkeep`, vacías a propósito). Quedan
    listos para cuando haya assets reales.

Autor: Korlo
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from config.paths import (
    BACKGROUNDS_DIR,
    CHARACTER_IMAGES_DIR,
    ENDING_IMAGES_DIR,
    FONTS_DIR,
    ICONS_DIR,
    IMAGES_DIR,
    UI_IMAGES_DIR,
)

logger = logging.getLogger(__name__)

_IMAGE_EXTENSIONS: Sequence[str] = (".png", ".jpg", ".jpeg", ".webp")
_FONT_EXTENSIONS: Sequence[str] = (".ttf", ".otf")


class ResourceNotFoundError(Exception):
    """Se lanza cuando no se encuentra ningún archivo para el id de recurso pedido."""


class ResourceManager:
    """
    Carga y cachea imágenes, iconos y fuentes bajo demanda.

    Los tipos de retorno (`PIL.Image.Image`, `PIL.ImageFont.FreeTypeFont`)
    no se anotan explícitamente en las firmas para no forzar un
    import de Pillow a nivel de módulo — se importa de forma
    perezosa, igual que en `services/image_service.py`, para que este
    archivo se pueda importar sin error en un entorno sin Pillow.
    """

    def __init__(
        self,
        images_dir: Path = IMAGES_DIR,
        icons_dir: Path = ICONS_DIR,
        fonts_dir: Path = FONTS_DIR,
        backgrounds_dir: Path = BACKGROUNDS_DIR,
        character_images_dir: Path = CHARACTER_IMAGES_DIR,
        ui_images_dir: Path = UI_IMAGES_DIR,
        ending_images_dir: Path = ENDING_IMAGES_DIR,
    ) -> None:
        self._images_dir = Path(images_dir)
        self._icons_dir = Path(icons_dir)
        self._fonts_dir = Path(fonts_dir)
        self._backgrounds_dir = Path(backgrounds_dir)
        self._character_images_dir = Path(character_images_dir)
        self._ui_images_dir = Path(ui_images_dir)
        self._ending_images_dir = Path(ending_images_dir)

        self._image_cache: Dict[str, object] = {}
        self._icon_cache: Dict[str, object] = {}
        self._font_cache: Dict[Tuple[str, int], object] = {}
        self._background_cache: Dict[str, object] = {}
        self._character_image_cache: Dict[str, object] = {}
        self._ui_image_cache: Dict[str, object] = {}
        self._ending_image_cache: Dict[str, object] = {}

    # ==================================================
    # IMÁGENES E ICONOS
    # ==================================================

    def get_image(self, resource_id: str):
        """
        Devuelve la imagen `resource_id` (`PIL.Image.Image`), desde
        caché si ya se cargó antes.

        Raises:
            ResourceNotFoundError: si no existe ningún archivo con
                ese id, o si Pillow no está instalado.
        """
        if resource_id not in self._image_cache:
            self._image_cache[resource_id] = self._load_image(self._images_dir, resource_id)
        return self._image_cache[resource_id]

    def get_icon(self, resource_id: str):
        """
        Devuelve el icono `resource_id` (`PIL.Image.Image`), desde
        caché si ya se cargó antes.

        Raises:
            ResourceNotFoundError: si no existe ningún archivo con
                ese id, o si Pillow no está instalado.
        """
        if resource_id not in self._icon_cache:
            self._icon_cache[resource_id] = self._load_image(self._icons_dir, resource_id)
        return self._icon_cache[resource_id]

    def get_background(self, resource_id: str):
        """
        Devuelve la imagen de fondo `resource_id` desde
        `assets/images/backgrounds/`, desde caché si ya se cargó antes.

        Raises:
            ResourceNotFoundError: si no existe ningún archivo con
                ese id, o si Pillow no está instalado.
        """
        if resource_id not in self._background_cache:
            self._background_cache[resource_id] = self._load_image(self._backgrounds_dir, resource_id)
        return self._background_cache[resource_id]

    def get_character_image(self, resource_id: str):
        """
        Devuelve el retrato/imagen de personaje `resource_id` desde
        `assets/images/characters/` — distinto de
        `data/characters/` (datos narrativos, no imágenes; ver
        `config/paths.py`).

        Raises:
            ResourceNotFoundError: si no existe ningún archivo con
                ese id, o si Pillow no está instalado.
        """
        if resource_id not in self._character_image_cache:
            self._character_image_cache[resource_id] = self._load_image(
                self._character_images_dir, resource_id
            )
        return self._character_image_cache[resource_id]

    def get_ui_image(self, resource_id: str):
        """
        Devuelve la imagen decorativa de interfaz `resource_id` desde
        `assets/images/ui/` — distinto del paquete Python `ui/` (ver
        `config/paths.py`).

        Raises:
            ResourceNotFoundError: si no existe ningún archivo con
                ese id, o si Pillow no está instalado.
        """
        if resource_id not in self._ui_image_cache:
            self._ui_image_cache[resource_id] = self._load_image(self._ui_images_dir, resource_id)
        return self._ui_image_cache[resource_id]

    def get_ending_image(self, resource_id: str):
        """
        Devuelve la imagen de final `resource_id` desde
        `assets/images/endings/` — distinto de `data/endings/`
        (catálogo de definiciones de final, ver
        `managers/ending_manager.py`) y de `Story.ending_id` (el
        cierre de una historia individual).

        Raises:
            ResourceNotFoundError: si no existe ningún archivo con
                ese id, o si Pillow no está instalado.
        """
        if resource_id not in self._ending_image_cache:
            self._ending_image_cache[resource_id] = self._load_image(
                self._ending_images_dir, resource_id
            )
        return self._ending_image_cache[resource_id]

    def preload_images(self, resource_ids: List[str]) -> None:
        """Precarga varias imágenes de una vez (por ejemplo, en una pantalla de carga)."""
        for resource_id in resource_ids:
            self.get_image(resource_id)

    # ==================================================
    # FUENTES
    # ==================================================

    def get_font(self, resource_id: str, size: int):
        """
        Devuelve la fuente `resource_id` al tamaño `size`
        (`PIL.ImageFont.FreeTypeFont`), desde caché si ya se cargó
        antes con ese mismo tamaño.

        Raises:
            ResourceNotFoundError: si no existe ningún archivo con
                ese id, o si Pillow no está instalado.
        """
        cache_key = (resource_id, size)
        if cache_key not in self._font_cache:
            self._font_cache[cache_key] = self._load_font(resource_id, size)
        return self._font_cache[cache_key]

    # ==================================================
    # GESTIÓN DE CACHÉ
    # ==================================================

    def clear_cache(self) -> None:
        """Libera todos los recursos cacheados."""
        self._image_cache.clear()
        self._icon_cache.clear()
        self._font_cache.clear()
        self._background_cache.clear()
        self._character_image_cache.clear()
        self._ui_image_cache.clear()
        self._ending_image_cache.clear()
        logger.info("ResourceManager: caché liberada.")

    def cache_size(self) -> int:
        """Número total de recursos actualmente en caché (para depuración/telemetría)."""
        return (
            len(self._image_cache)
            + len(self._icon_cache)
            + len(self._font_cache)
            + len(self._background_cache)
            + len(self._character_image_cache)
            + len(self._ui_image_cache)
            + len(self._ending_image_cache)
        )

    # ==================================================
    # INTERNO
    # ==================================================

    def _load_image(self, base_dir: Path, resource_id: str):
        try:
            from PIL import Image
        except ImportError as error:
            raise ResourceNotFoundError(
                "Pillow no está instalado; no se pueden cargar imágenes."
            ) from error

        path = self._resolve(base_dir, resource_id, _IMAGE_EXTENSIONS)
        image = Image.open(path)
        image.load()  # fuerza la lectura completa ahora, no perezosamente
        logger.debug("ResourceManager: imagen '%s' cargada desde %s", resource_id, path)
        return image

    def _load_font(self, resource_id: str, size: int):
        try:
            from PIL import ImageFont
        except ImportError as error:
            raise ResourceNotFoundError(
                "Pillow no está instalado; no se pueden cargar fuentes."
            ) from error

        path = self._resolve(self._fonts_dir, resource_id, _FONT_EXTENSIONS)
        font = ImageFont.truetype(str(path), size=size)
        logger.debug(
            "ResourceManager: fuente '%s' (%spx) cargada desde %s", resource_id, size, path
        )
        return font

    @staticmethod
    def _resolve(base_dir: Path, resource_id: str, extensions: Sequence[str]) -> Path:
        for extension in extensions:
            candidate = base_dir / f"{resource_id}{extension}"
            if candidate.exists():
                return candidate
        raise ResourceNotFoundError(
            f"No se encontró ningún recurso para '{resource_id}' en {base_dir} "
            f"(extensiones probadas: {list(extensions)})."
        )