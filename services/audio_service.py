"""
services/audio_service.py
==========================

Qué hace:
    Reproduce música y efectos de sonido, resolviendo ids de pista a
    archivos bajo `MUSIC_DIR`/`EFFECTS_DIR`, y gestiona volumen
    maestro, volumen por categoría (música/efectos) y silencio.

Cómo funciona:
    La lógica de negocio (resolución de rutas, acotamiento y
    combinación de volúmenes, estado de silencio) vive en
    `AudioService` y NO depende de pygame directamente: depende de
    `AudioBackend` (`Protocol`), para poder probarse sin hardware de
    audio y para no acoplar todo el proyecto a una sola biblioteca.

    - `PygameAudioBackend` es la implementación real (usa
      `pygame.mixer`, ya está en requirements.txt). Importa pygame
      de forma perezosa (dentro de `__init__`, no a nivel de
      módulo) y se degrada con gracia si pygame no está instalado o
      no hay dispositivo de audio disponible (por ejemplo, en un
      servidor o en este mismo entorno de pruebas): en vez de lanzar
      una excepción que tumbe el juego, queda `is_available() ==
      False` y cada operación se vuelve un no-op registrado en el
      log.
    - `NullAudioBackend` es un backend explícito de no-operación,
      útil para pruebas automatizadas y para correr el juego sin
      audio a propósito.

Dependencias:
    - config.paths: MUSIC_DIR, EFFECTS_DIR.
    - models.scales: clamp (reutilizado del mismo módulo compartido
      que usan Player/NPC, para no reimplementar el acotamiento de
      un valor 0.0-1.0).
    - pygame (opcional, solo si se instancia PygameAudioBackend).

Cómo interactúa con otros módulos:
    El futuro `managers/audio_manager.py` (que `main.py` ya espera
    importar) debería ser un envoltorio delgado sobre este servicio,
    no reimplementar esta lógica.

Autor: Korlo
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Protocol, Sequence, runtime_checkable

from config.paths import EFFECTS_DIR, MUSIC_DIR
from models.scales import clamp

logger = logging.getLogger(__name__)

_MUSIC_EXTENSIONS: Sequence[str] = (".mp3", ".ogg", ".wav")
_EFFECT_EXTENSIONS: Sequence[str] = (".wav", ".ogg", ".mp3")


class AudioAssetNotFoundError(Exception):
    """Se lanza cuando no se encuentra ningún archivo de audio para un id de pista."""


# ==================================================
# INTERFAZ DE BACKEND
# ==================================================


@runtime_checkable
class AudioBackend(Protocol):
    """Interfaz mínima que cualquier motor de audio real debe cumplir."""

    def is_available(self) -> bool:
        """Indica si el backend pudo inicializar un dispositivo de audio."""
        ...

    def play_music(self, path: str, loop: bool, volume: float) -> None:
        """Reproduce un archivo de música, reemplazando la pista actual."""
        ...

    def stop_music(self) -> None:
        """Detiene la música en reproducción."""
        ...

    def set_music_volume(self, volume: float) -> None:
        """Ajusta el volumen de la música en reproducción (0.0 a 1.0)."""
        ...

    def play_sound_effect(self, path: str, volume: float) -> None:
        """Reproduce un efecto de sonido corto, sin loop."""
        ...


class NullAudioBackend:
    """
    Backend de no-operación: no reproduce nada, pero cumple
    `AudioBackend`. Pensado para pruebas automatizadas y para
    ejecutar el juego en entornos sin audio (servidores, CI).
    """

    def is_available(self) -> bool:
        return False

    def play_music(self, path: str, loop: bool, volume: float) -> None:
        logger.debug(
            "NullAudioBackend: play_music('%s', loop=%s, volume=%.2f) ignorado.",
            path, loop, volume,
        )

    def stop_music(self) -> None:
        logger.debug("NullAudioBackend: stop_music() ignorado.")

    def set_music_volume(self, volume: float) -> None:
        logger.debug("NullAudioBackend: set_music_volume(%.2f) ignorado.", volume)

    def play_sound_effect(self, path: str, volume: float) -> None:
        logger.debug(
            "NullAudioBackend: play_sound_effect('%s', volume=%.2f) ignorado.",
            path, volume,
        )


class PygameAudioBackend:
    """
    Backend real basado en `pygame.mixer`.

    Importa pygame de forma perezosa (dentro de `__init__`) para que
    este módulo se pueda importar sin error en un entorno sin
    pygame instalado. Si la inicialización del mezclador falla por
    cualquier motivo (biblioteca ausente, sin dispositivo de audio),
    el backend queda marcado como no disponible y todas sus
    operaciones se vuelven no-ops registrados en el log, en vez de
    lanzar una excepción que tumbe el juego.
    """

    def __init__(self) -> None:
        self._available = False
        self._mixer = None
        try:
            import pygame  # import perezoso: no es una dependencia dura de este módulo

            pygame.mixer.init()
            self._mixer = pygame.mixer
            self._available = True
            logger.info("PygameAudioBackend: mezclador de audio inicializado.")
        except ImportError:
            logger.warning(
                "PygameAudioBackend: pygame no está instalado; "
                "el audio queda deshabilitado."
            )
        except Exception as error:  # pygame.error u otros fallos del dispositivo
            logger.warning(
                "PygameAudioBackend: no se pudo inicializar el audio (%s); "
                "el audio queda deshabilitado.", error,
            )

    def is_available(self) -> bool:
        return self._available

    def play_music(self, path: str, loop: bool, volume: float) -> None:
        if not self._available:
            return
        try:
            self._mixer.music.load(path)
            self._mixer.music.set_volume(volume)
            self._mixer.music.play(loops=-1 if loop else 0)
        except Exception as error:
            logger.error(
                "PygameAudioBackend: error reproduciendo música '%s': %s", path, error
            )

    def stop_music(self) -> None:
        if not self._available:
            return
        self._mixer.music.stop()

    def set_music_volume(self, volume: float) -> None:
        if not self._available:
            return
        self._mixer.music.set_volume(volume)

    def play_sound_effect(self, path: str, volume: float) -> None:
        if not self._available:
            return
        try:
            sound = self._mixer.Sound(path)
            sound.set_volume(volume)
            sound.play()
        except Exception as error:
            logger.error(
                "PygameAudioBackend: error reproduciendo efecto '%s': %s", path, error
            )


# ==================================================
# SERVICIO
# ==================================================


class AudioService:
    """
    Reproduce música y efectos de sonido, resolviendo ids de pista a
    archivos y aplicando volumen maestro, por categoría y silencio.
    """

    def __init__(
        self,
        backend: Optional[AudioBackend] = None,
        music_dir: Path = MUSIC_DIR,
        effects_dir: Path = EFFECTS_DIR,
    ) -> None:
        self._backend: AudioBackend = backend or PygameAudioBackend()
        self._music_dir = Path(music_dir)
        self._effects_dir = Path(effects_dir)

        self._master_volume = 1.0
        self._music_volume = 1.0
        self._effects_volume = 1.0
        self._muted = False
        self._current_track_id: Optional[str] = None

    # ==================================================
    # REPRODUCCIÓN
    # ==================================================

    def play_music(self, track_id: str, loop: bool = True) -> None:
        """
        Reproduce la pista `track_id` (sin extensión), resuelta
        dentro del directorio de música configurado.

        Raises:
            AudioAssetNotFoundError: si no existe ningún archivo con
                ese id en ninguna de las extensiones soportadas.
        """
        path = self._resolve(self._music_dir, track_id, _MUSIC_EXTENSIONS)
        self._backend.play_music(str(path), loop=loop, volume=self._effective_music_volume())
        self._current_track_id = track_id
        logger.info("AudioService: reproduciendo música '%s'", track_id)

    def stop_music(self) -> None:
        """Detiene la música en reproducción, si la hay."""
        self._backend.stop_music()
        self._current_track_id = None

    def play_sound_effect(self, effect_id: str) -> None:
        """
        Reproduce el efecto `effect_id` (sin extensión), resuelto
        dentro del directorio de efectos configurado.

        Raises:
            AudioAssetNotFoundError: si no existe ningún archivo con
                ese id en ninguna de las extensiones soportadas.
        """
        path = self._resolve(self._effects_dir, effect_id, _EFFECT_EXTENSIONS)
        self._backend.play_sound_effect(str(path), volume=self._effective_effects_volume())

    def is_playing_music(self) -> bool:
        """Indica si hay una pista de música activa (según este servicio)."""
        return self._current_track_id is not None

    @property
    def current_track_id(self) -> Optional[str]:
        """Id de la pista de música actualmente activa, si la hay."""
        return self._current_track_id

    # ==================================================
    # VOLUMEN Y SILENCIO
    # ==================================================

    def set_master_volume(self, volume: float) -> None:
        """Fija el volumen maestro (0.0 a 1.0); afecta música y efectos."""
        self._master_volume = clamp(volume, 0.0, 1.0)
        self._apply_music_volume()

    def set_music_volume(self, volume: float) -> None:
        """Fija el volumen de música (0.0 a 1.0), independiente de efectos."""
        self._music_volume = clamp(volume, 0.0, 1.0)
        self._apply_music_volume()

    def set_effects_volume(self, volume: float) -> None:
        """Fija el volumen de efectos (0.0 a 1.0), independiente de música."""
        self._effects_volume = clamp(volume, 0.0, 1.0)

    def mute(self) -> None:
        """Silencia música y efectos sin perder los niveles de volumen configurados."""
        self._muted = True
        self._apply_music_volume()

    def unmute(self) -> None:
        """Restaura el sonido a los niveles de volumen configurados."""
        self._muted = False
        self._apply_music_volume()

    def is_muted(self) -> bool:
        """Indica si el audio está silenciado."""
        return self._muted

    def get_master_volume(self) -> float:
        """Volumen maestro configurado (0.0 a 1.0), sin importar el silencio."""
        return self._master_volume

    def get_music_volume(self) -> float:
        """Volumen de música configurado (0.0 a 1.0), sin importar el silencio."""
        return self._music_volume

    def get_effects_volume(self) -> float:
        """Volumen de efectos configurado (0.0 a 1.0), sin importar el silencio."""
        return self._effects_volume

    # ==================================================
    # INTERNO
    # ==================================================

    def _effective_music_volume(self) -> float:
        return 0.0 if self._muted else self._master_volume * self._music_volume

    def _effective_effects_volume(self) -> float:
        return 0.0 if self._muted else self._master_volume * self._effects_volume

    def _apply_music_volume(self) -> None:
        self._backend.set_music_volume(self._effective_music_volume())

    @staticmethod
    def _resolve(base_dir: Path, track_id: str, extensions: Sequence[str]) -> Path:
        for extension in extensions:
            candidate = base_dir / f"{track_id}{extension}"
            if candidate.exists():
                return candidate
        raise AudioAssetNotFoundError(
            f"No se encontró ningún archivo de audio para '{track_id}' en "
            f"{base_dir} (extensiones probadas: {list(extensions)})."
        )