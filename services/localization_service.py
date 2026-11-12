"""
services/localization_service.py
=================================

Qué hace:
    Carga y resuelve textos localizados (i18n) desde archivos JSON
    en `data/localization/<locale>.json`, con soporte de claves
    anidadas ("menu.start") e interpolación de variables
    ("Hola, {name}").

    De paso, resuelve un import roto detectado en el análisis
    inicial del proyecto: `main.py` ya hace
    `from services.localization_service import LocalizationService`,
    pero el archivo no existía. El nombre de la clase aquí
    (`LocalizationService`) coincide exactamente con lo que
    `main.py` espera.

Cómo funciona:
    Depende de `ContentRepository` (ver `services/repositories.py`)
    para leer los archivos de idioma; nunca escribe contenido de
    localización (lo edita el equipo de diseño/traducción
    directamente en los JSON). Cachea cada locale cargado en memoria
    para no releer el archivo en cada llamada a `translate()`.

    El proyecto todavía no tiene ningún archivo de locale creado, así
    que este servicio está diseñado para degradarse con gracia en
    vez de fallar al arrancar: si el locale por defecto no tiene
    contenido, se usa un diccionario vacío y cada `translate()`
    faltante devuelve `"[clave]"` con una advertencia en el log, en
    vez de romper la partida. `set_locale()`, en cambio, sí valida
    explícitamente que el locale exista — es la operación que un
    menú de selección de idioma dispararía, y ahí sí tiene sentido
    fallar de forma clara si el idioma elegido no existe.

Formato esperado de un archivo de locale:
    {
      "menu": {
        "start": "Iniciar partida",
        "continue": "Continuar",
        "greeting": "Hola, {name}"
      },
      "game_over": "Fin de la partida"
    }

Dependencias:
    - services.repositories: ContentRepository, JSONContentRepository (por defecto).
    - config.paths: LOCALIZATION_DIR.

Cómo interactúa con otros módulos:
    `main.py` debe instanciar este servicio e inyectarlo donde haga
    falta mostrar texto (la futura capa de UI); ningún otro módulo
    debe leer archivos de idioma directamente.

Autor: Korlo
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from config.paths import LOCALIZATION_DIR
from services.repositories import ContentRepository, JSONContentRepository

logger = logging.getLogger(__name__)

DEFAULT_LOCALE = "en"


class LocaleNotFoundError(Exception):
    """Se lanza al intentar activar explícitamente un locale sin contenido."""


class LocalizationService:
    """
    Resuelve textos localizados a partir de archivos JSON por
    idioma, con claves anidadas e interpolación de variables.
    """

    def __init__(
        self,
        repository: Optional[ContentRepository] = None,
        locale: str = DEFAULT_LOCALE,
        fallback_locale: str = DEFAULT_LOCALE,
    ) -> None:
        self._repository: ContentRepository = repository or JSONContentRepository(
            LOCALIZATION_DIR
        )
        self._fallback_locale = fallback_locale
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._locale = locale
        self._ensure_loaded(locale)

    # ==================================================
    # GESTIÓN DE LOCALE
    # ==================================================

    def set_locale(self, locale: str) -> None:
        """
        Activa `locale` como idioma actual.

        A diferencia de la carga interna usada por `translate()`,
        este método es explícito (por ejemplo, un menú de selección
        de idioma) y por eso sí valida que el locale exista.

        Raises:
            LocaleNotFoundError: si no existe contenido para ese locale.
        """
        if not self._repository.exists(locale):
            raise LocaleNotFoundError(
                f"No existe contenido de localización para '{locale}'."
            )
        self._ensure_loaded(locale)
        self._locale = locale
        logger.info("LocalizationService: locale activo -> '%s'", locale)

    def get_locale(self) -> str:
        """Devuelve el código del locale actualmente activo."""
        return self._locale

    def has_locale(self, locale: str) -> bool:
        """Indica si existe contenido de localización para `locale`."""
        return self._repository.exists(locale)

    def list_available_locales(self) -> List[str]:
        """Lista los códigos de locale con contenido disponible."""
        return self._repository.list_keys()

    # ==================================================
    # TRADUCCIÓN
    # ==================================================

    def translate(self, key: str, locale: Optional[str] = None, **variables: Any) -> str:
        """
        Resuelve `key` (notación de puntos, ej. "menu.start") en el
        locale indicado, o en el locale activo si no se especifica.

        Si la clave no existe en ese locale, intenta el locale de
        reserva. Si tampoco existe ahí, devuelve `"[key]"` y registra
        una advertencia, en vez de lanzar una excepción — un texto
        faltante no debería tumbar la partida.

        Args:
            key: ruta de la clave, con puntos para anidamiento.
            locale: locale específico a usar; por defecto, el activo.
            **variables: valores para interpolar en la plantilla
                (ej. `translate("menu.greeting", name="Ana")`).
        """
        target_locale = locale or self._locale
        value = self._resolve(key, target_locale)

        if value is None and target_locale != self._fallback_locale:
            value = self._resolve(key, self._fallback_locale)

        if value is None:
            logger.warning(
                "LocalizationService: clave '%s' no encontrada en "
                "'%s' ni en el locale de reserva '%s'.",
                key, target_locale, self._fallback_locale,
            )
            return f"[{key}]"

        try:
            return value.format(**variables)
        except (KeyError, IndexError) as error:
            logger.error(
                "LocalizationService: error interpolando '%s': %s", key, error
            )
            return value

    def has_key(self, key: str, locale: Optional[str] = None) -> bool:
        """Indica si `key` existe en el locale indicado (o el activo)."""
        return self._resolve(key, locale or self._locale) is not None

    # ==================================================
    # INTERNO
    # ==================================================

    def _ensure_loaded(self, locale: str) -> Dict[str, Any]:
        """
        Carga `locale` en caché si aún no lo está. Nunca lanza: si no
        hay contenido, cachea un diccionario vacío y registra una
        advertencia (ver nota de diseño en el docstring del módulo).
        """
        if locale not in self._cache:
            data = self._repository.load(locale)
            if data is None:
                logger.warning(
                    "LocalizationService: no existe contenido para '%s'; "
                    "se usa un diccionario vacío.", locale,
                )
                data = {}
            self._cache[locale] = data
        return self._cache[locale]

    def _resolve(self, key: str, locale: str) -> Optional[str]:
        node: Any = self._ensure_loaded(locale)
        for part in key.split("."):
            if not isinstance(node, dict) or part not in node:
                return None
            node = node[part]
        return node if isinstance(node, str) else None