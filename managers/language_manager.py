"""
managers/language_manager.py
=============================

Qué hace:
    Coordina el cambio de idioma activo y notifica a quien esté
    suscrito (típicamente, la futura capa `ui/`, para refrescar todo
    el texto en pantalla) cuando ocurre. Delega toda la resolución
    de texto y la carga de archivos de idioma en
    `services.localization_service.LocalizationService`.

Cómo funciona:
    `LocalizationService` no sabe ni le importa "quién está
    escuchando" cuando cambia el idioma — resuelve texto, punto. La
    coordinación de "avisar a todo el mundo que debe refrescarse" es
    exactamente el tipo de responsabilidad que corresponde a un
    manager, no a un servicio.

Dependencias:
    - services.localization_service: LocalizationService, LocaleNotFoundError.

Cómo interactúa con otros módulos:
    `main.py` instancia hoy directamente un `LocalizationService`
    (`from services.localization_service import LocalizationService`);
    este manager es la capa de coordinación que se apoya en él sin
    reemplazarlo — `main.py` puede seguir usando el servicio
    directamente para texto simple, y usar este manager cuando
    necesite reaccionar a cambios de idioma (por ejemplo, un menú de
    ajustes).

Autor: Korlo
"""

from __future__ import annotations

import logging
from typing import Any, Callable, List

from services.localization_service import LocaleNotFoundError, LocalizationService

logger = logging.getLogger(__name__)

LanguageChangeCallback = Callable[[str], None]

__all__ = ["LanguageManager", "LocaleNotFoundError"]


class LanguageManager:
    """
    Orquesta el cambio de idioma activo y notifica a los
    suscriptores, delegando la resolución de texto en
    `LocalizationService`.
    """

    def __init__(self, localization_service: LocalizationService) -> None:
        self._localization_service = localization_service
        self._subscribers: List[LanguageChangeCallback] = []

    # ==================================================
    # SUSCRIPCIÓN
    # ==================================================

    def subscribe(self, callback: LanguageChangeCallback) -> None:
        """Registra `callback` para recibir el nuevo locale cada vez que cambie."""
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: LanguageChangeCallback) -> None:
        """Retira `callback` de la lista de suscriptores, si estaba registrado."""
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    # ==================================================
    # CAMBIO DE IDIOMA
    # ==================================================

    def change_language(self, locale: str) -> None:
        """
        Cambia el idioma activo y notifica a los suscriptores.

        Raises:
            LocaleNotFoundError: si no existe contenido para ese locale.
        """
        self._localization_service.set_locale(locale)
        logger.info("LanguageManager: idioma cambiado a '%s'.", locale)
        for callback in self._subscribers:
            callback(locale)

    def current_language(self) -> str:
        """Devuelve el código del idioma actualmente activo."""
        return self._localization_service.get_locale()

    def available_languages(self) -> List[str]:
        """Lista los códigos de idioma con contenido disponible."""
        return self._localization_service.list_available_locales()

    # ==================================================
    # TRADUCCIÓN (fachada de conveniencia)
    # ==================================================

    def translate(self, key: str, **variables: Any) -> str:
        """Traduce `key` en el idioma activo (delegado directo a LocalizationService)."""
        return self._localization_service.translate(key, **variables)