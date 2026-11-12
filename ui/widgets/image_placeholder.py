"""
ui/widgets/image_placeholder.py
=================================

Qué hace:
    `SceneImage`: el recuadro grande sobre el texto narrativo,
    reservado para la imagen de la escena.

Alcance deliberadamente limitado (léase antes de tocar este archivo):
    Hoy NO existe en el proyecto ningún sistema que genere una
    imagen por escena de historia — `services/image_service.py`
    genera ilustraciones para los "Momentos Clave" del Álbum de
    Vida, un concepto distinto (ver análisis del proyecto). Por eso
    este widget no llama a ningún generador: solo sabe pintar un
    placeholder elegante, o una imagen ya generada si
    `set_image_path()` recibe una ruta válida.

    `set_scene(scene: dict)` busca la clave `"image"` (o la que se
    decida cuando exista ese sistema) en la escena servida por
    `services/story_service.py`; si no está, se queda en modo
    placeholder. No inventa ninguna conexión nueva.

Autor: Korlo (ui/ añadida en esta sesión)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from ui import theme

logger = logging.getLogger(__name__)


class SceneImage(QWidget):
    """Recuadro de imagen de escena: placeholder elegante o imagen real si existe."""

    def __init__(self, parent=None, *, height: int = 260) -> None:
        super().__init__(parent)
        self.setFixedHeight(height)
        self.setObjectName("SceneImage")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel()
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setWordWrap(True)
        layout.addWidget(self._label)

        self._show_placeholder()

    def set_scene(self, scene: Optional[Dict[str, Any]]) -> None:
        """
        Actualiza el recuadro a partir de la escena actual. Espera
        el mismo diccionario que devuelve
        `StoryService.get_current_scene()`.
        """
        image_ref = (scene or {}).get("image")
        if image_ref:
            self.set_image_path(str(image_ref))
        else:
            self._show_placeholder()

    def set_image_path(self, path: str) -> None:
        """Muestra una imagen real desde disco; si no se puede cargar, vuelve al placeholder."""
        pixmap = QPixmap(path)
        if pixmap.isNull():
            logger.warning("SceneImage: no se pudo cargar la imagen '%s'; se muestra el placeholder.", path)
            self._show_placeholder()
            return
        scaled = pixmap.scaled(
            self.width() or 800,
            self.height(),
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation,
        )
        self._label.setPixmap(scaled)
        self.setStyleSheet(
            f"#SceneImage {{ border-radius: {theme.RADIUS_MD}px; background-color: {theme.BORDER}; }}"
        )

    def _show_placeholder(self) -> None:
        self._label.setPixmap(QPixmap())
        self._label.setText("🖼️\n\nImagen de la escena\n(pendiente de generación)")
        self._label.setStyleSheet(
            f"color: {theme.TEXT_DISABLED}; font-size: {theme.FONT_SIZE_BODY}px;"
        )
        self.setStyleSheet(
            f"""
            #SceneImage {{
                border-radius: {theme.RADIUS_MD}px;
                background-color: {theme.BACKGROUND};
                border: 1px dashed {theme.BORDER_STRONG};
            }}
            """
        )
