"""
managers/audio_manager.py
==========================

Qué hace:
    Decide QUÉ pista de música corresponde a cada `GameScene` y
    CUÁNDO reproducirla, suscribiéndose a `managers.scene_manager.SceneManager`
    para reaccionar a los cambios de pantalla. Delega toda la
    reproducción real, el cálculo de volumen y la resolución de
    archivos en `services.audio_service.AudioService`.

Cómo funciona:
    Es el ejemplo más directo de "director de orquesta, sin
    partitura propia": no sabe reproducir audio ni calcular volumen
    (eso es `AudioService`), solo decide, ante cada cambio de escena,
    si corresponde cambiar de pista — y evita reiniciar la música si
    la pista que ya suena es la correcta para la nueva escena (por
    ejemplo, entrar y salir de Pausa sobre Gameplay no debería
    reiniciar el tema de Gameplay).

Dependencias:
    - services.audio_service: AudioService, AudioAssetNotFoundError.
    - managers.scene_manager: GameScene, SceneManager (opcional, solo
      si se usa attach_to_scene_manager).

Cómo interactúa con otros módulos:
    `main.py` ya espera `from managers.audio_manager import AudioManager`.
    Si se le pasa un `SceneManager`, se suscribe automáticamente a
    los cambios de escena; si no, sigue siendo utilizable como una
    fachada delgada sobre `AudioService` (reproducir efectos,
    ajustar volumen) sin coordinación de escenas.

Autor: Korlo
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

from managers.scene_manager import GameScene, SceneManager
from services.audio_service import AudioAssetNotFoundError, AudioService

logger = logging.getLogger(__name__)

DEFAULT_SCENE_TRACKS: Dict[GameScene, str] = {
    GameScene.MAIN_MENU: "main_menu_theme",
    GameScene.CHARACTER_CREATION: "character_creation_theme",
    GameScene.GAMEPLAY: "gameplay_theme",
    GameScene.SETTINGS: "main_menu_theme",
    GameScene.ALBUM: "album_theme",
    GameScene.GAME_OVER: "game_over_theme",
    GameScene.CREDITS: "credits_theme",
    # GameScene.PAUSE no está mapeada a propósito: pausar no debe
    # interrumpir la música de la escena que queda debajo.
}


class AudioManager:
    """
    Coordina `AudioService` en función de los cambios de escena;
    también expone una fachada delgada de conveniencia (volumen,
    silencio, efectos) sobre el mismo servicio.
    """

    def __init__(
        self,
        audio_service: AudioService,
        scene_manager: Optional[SceneManager] = None,
        scene_tracks: Optional[Dict[GameScene, str]] = None,
    ) -> None:
        self._audio_service = audio_service
        self._scene_tracks: Dict[GameScene, str] = (
            dict(scene_tracks) if scene_tracks is not None else dict(DEFAULT_SCENE_TRACKS)
        )
        if scene_manager is not None:
            self.attach_to_scene_manager(scene_manager)

    # ==================================================
    # COORDINACIÓN CON SCENEMANAGER
    # ==================================================

    def attach_to_scene_manager(self, scene_manager: SceneManager) -> None:
        """
        Se suscribe a la entrada de cada escena mapeada en
        `scene_tracks`, para reproducir su música automáticamente.
        """
        for scene in self._scene_tracks:
            scene_manager.on_enter(scene, self._handle_scene_entered)
        logger.info(
            "AudioManager: suscrito a %s escena(s) de SceneManager.",
            len(self._scene_tracks),
        )

    def set_track_for_scene(self, scene: GameScene, track_id: str) -> None:
        """Asigna o reemplaza qué pista corresponde a `scene`."""
        self._scene_tracks[scene] = track_id

    def _handle_scene_entered(self, scene: GameScene, previous: Optional[GameScene]) -> None:
        track_id = self._scene_tracks.get(scene)
        if track_id is None:
            return  # esta escena no tiene música asociada (ej. PAUSE)
        if self._audio_service.current_track_id == track_id:
            return  # ya está sonando; no reiniciar la pista
        try:
            self._audio_service.play_music(track_id)
        except AudioAssetNotFoundError:
            logger.warning(
                "AudioManager: no se encontró la pista '%s' para la escena %s.",
                track_id, scene.value,
            )

    # ==================================================
    # FACHADA DE CONVENIENCIA SOBRE AUDIOSERVICE
    # ==================================================
    # Deliberadamente sin lógica propia: solo delegan.

    def play_sound_effect(self, effect_id: str) -> None:
        """Reproduce un efecto de sonido; ignora (con aviso) si no existe el archivo."""
        try:
            self._audio_service.play_sound_effect(effect_id)
        except AudioAssetNotFoundError:
            logger.warning("AudioManager: efecto de sonido '%s' no encontrado.", effect_id)

    def set_master_volume(self, volume: float) -> None:
        """Fija el volumen maestro (0.0 a 1.0)."""
        self._audio_service.set_master_volume(volume)

    def set_music_volume(self, volume: float) -> None:
        """Fija el volumen de música (0.0 a 1.0)."""
        self._audio_service.set_music_volume(volume)

    def set_effects_volume(self, volume: float) -> None:
        """Fija el volumen de efectos (0.0 a 1.0)."""
        self._audio_service.set_effects_volume(volume)

    def get_master_volume(self) -> float:
        """Volumen maestro configurado (0.0 a 1.0). Añadido junto con ui/settings_screen.py, que necesita mostrar el valor actual, no solo poder fijarlo — AudioService ya lo exponía, faltaba en esta fachada."""
        return self._audio_service.get_master_volume()

    def get_music_volume(self) -> float:
        """Volumen de música configurado (0.0 a 1.0)."""
        return self._audio_service.get_music_volume()

    def get_effects_volume(self) -> float:
        """Volumen de efectos configurado (0.0 a 1.0)."""
        return self._audio_service.get_effects_volume()

    def mute(self) -> None:
        """Silencia música y efectos."""
        self._audio_service.mute()

    def unmute(self) -> None:
        """Restaura el sonido a los niveles configurados."""
        self._audio_service.unmute()

    def is_muted(self) -> bool:
        """Indica si el audio está silenciado."""
        return self._audio_service.is_muted()