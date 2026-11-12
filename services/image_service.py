"""
services/image_service.py
==========================

Qué hace:
    Genera y persiste las ilustraciones de los "Momentos Clave" del
    Álbum de Vida (`What_If_Vision_Document.md` §5.3-5.4): construye
    la solicitud de generación (prompt + referencia visual del
    personaje, si existe) y la envía a un proveedor de generación de
    imágenes, guardando el resultado en `IMAGES_DIR`.

Alcance y límites (léase antes de usar este archivo):
    La consistencia visual del personaje a través de decenas de
    ilustraciones es, según el propio Vision Document (§9.2), "el
    mayor riesgo técnico del proyecto" y requiere un spike de
    preproducción todavía no realizado. Este servicio da la interfaz
    limpia para ese mecanismo (acepta una imagen de referencia
    opcional y la reenvía al proveedor), pero NO implementa ni
    resuelve el problema de consistencia en sí — eso depende de qué
    solución técnica (IP-Adapter, LoRA por personaje, u otra)
    resulte del spike. Tratarlo como resuelto aquí sería aparentar
    una solución que en realidad sigue pendiente de investigación.

Cómo funciona:
    Depende de `ImageProvider` (`Protocol`): un proveedor recibe un
    prompt (y opcionalmente una ruta de imagen de referencia) y
    devuelve los bytes de la imagen generada (PNG). `ImageService`
    no sabe ni le importa qué proveedor hay detrás — solo construye
    la solicitud, la envía, y persiste el resultado.

    - `PlaceholderImageProvider`: genera una imagen local simple con
      Pillow (ya en requirements.txt), sin llamadas de red. Es el
      proveedor por defecto, para que el servicio funcione de
      inmediato sin credenciales configuradas — mismo rol que el
      proveedor "local" de `ai/ai_manager.py`.
    - `OpenAIImageProvider`: implementación real contra la API de
      imágenes de OpenAI (paquete `openai`, ya en requirements.txt).
      Importa el paquete de forma perezosa y exige la API key por
      parámetro explícito — nunca la lee de una constante
      hardcodeada como hace hoy `config/settings.py`
      (`OPENAI_API_KEY = ""`, ver análisis previo del proyecto);
      debe cargarse con `python-dotenv` desde una variable de
      entorno.

Dependencias:
    - config.paths: IMAGES_DIR.
    - utils.helpers: wrap_text (envoltura de texto para el marcador de posición).
    - utils.file_utils: safe_filename (nombre de archivo seguro).
    - Pillow (para PlaceholderImageProvider).
    - openai (opcional, solo para OpenAIImageProvider).

Cómo interactúa con otros módulos:
    Complementa a `ai/story_generator.py`: mientras ese módulo genera
    texto narrativo, este genera las ilustraciones de los Momentos
    Clave que `models.player.Player.unlock_memory_moment()` registra
    en el Álbum.

Autor: Korlo
"""

from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Optional, Protocol, runtime_checkable

from config.paths import IMAGES_DIR
from utils.file_utils import safe_filename
from utils.helpers import wrap_text

logger = logging.getLogger(__name__)


class ImageGenerationError(Exception):
    """Se lanza cuando un proveedor de imágenes falla al generar contenido."""


@runtime_checkable
class ImageProvider(Protocol):
    """Interfaz mínima que cualquier proveedor de generación de imágenes debe cumplir."""

    def generate(
        self, prompt: str, reference_image_path: Optional[Path] = None
    ) -> bytes:
        """
        Genera una imagen a partir de `prompt`, opcionalmente guiada
        por una imagen de referencia (para consistencia visual del
        personaje). Devuelve los bytes de la imagen (PNG).

        Raises:
            ImageGenerationError: si el proveedor no puede generar la imagen.
        """
        ...


# ==================================================
# PROVEEDORES
# ==================================================


class PlaceholderImageProvider:
    """
    Proveedor local de respaldo: genera una imagen simple con
    Pillow, sin llamadas de red ni credenciales. Es el proveedor por
    defecto, para que `ImageService` funcione de inmediato — mismo
    rol que el proveedor "local" de `ai/ai_manager.py`.

    No pretende resolver la consistencia visual del personaje (ver
    nota de alcance en el docstring del módulo): cada llamada
    produce una imagen de marcador de posición con el texto del
    prompt, no una ilustración curada.
    """

    _SIZE = (512, 512)
    _BACKGROUND_COLOR = (30, 41, 59)  # coincide con SECONDARY de config/colors.py
    _TEXT_COLOR = (248, 250, 252)
    _MAX_CHARS_PER_LINE = 40

    def generate(
        self, prompt: str, reference_image_path: Optional[Path] = None
    ) -> bytes:
        """Genera una imagen de marcador de posición con el texto del prompt."""
        try:
            from PIL import Image, ImageDraw
        except ImportError as error:
            raise ImageGenerationError(
                "Pillow no está instalado; no se puede generar la imagen "
                "de marcador de posición."
            ) from error

        image = Image.new("RGB", self._SIZE, color=self._BACKGROUND_COLOR)
        draw = ImageDraw.Draw(image)
        draw.multiline_text(
            (20, 20),
            wrap_text(prompt, self._MAX_CHARS_PER_LINE),
            fill=self._TEXT_COLOR,
            spacing=6,
        )

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()


class OpenAIImageProvider:
    """
    Proveedor real basado en la API de imágenes de OpenAI.

    Importa el paquete `openai` de forma perezosa (dentro de
    `__init__`), para que este módulo se pueda importar sin error en
    un entorno donde el paquete no esté instalado.
    """

    def __init__(self, api_key: str, model: str = "gpt-image-1") -> None:
        """
        Args:
            api_key: clave de la API de OpenAI. Se exige explícita
                a propósito: nunca debe venir hardcodeada en el
                código fuente (cárgala con python-dotenv desde una
                variable de entorno).
            model: modelo de generación de imágenes a usar.

        Raises:
            ValueError: si `api_key` está vacío.
            ImageGenerationError: si el paquete `openai` no está instalado.
        """
        if not api_key:
            raise ValueError(
                "api_key no puede estar vacío. No la hardcodees: cárgala "
                "con python-dotenv desde una variable de entorno."
            )
        try:
            import openai
        except ImportError as error:
            raise ImageGenerationError(
                "El paquete 'openai' no está instalado (ver requirements.txt)."
            ) from error

        self._client = openai.OpenAI(api_key=api_key)
        self._model = model

    def generate(
        self, prompt: str, reference_image_path: Optional[Path] = None
    ) -> bytes:
        """
        Genera una imagen con la API de OpenAI.

        Si se pasa `reference_image_path`, usa el endpoint de
        edición de imágenes (image-to-image) en vez del de
        generación pura, como mecanismo más cercano disponible hoy
        para intentar continuidad visual — sin que esto implique que
        el problema de consistencia (Vision Document §9.2) quede
        resuelto; eso depende del spike técnico todavía pendiente.

        Raises:
            ImageGenerationError: si la API falla o no devuelve
                datos de imagen utilizables.
        """
        import base64

        try:
            if reference_image_path is not None:
                with open(reference_image_path, "rb") as reference_file:
                    response = self._client.images.edit(
                        model=self._model,
                        image=reference_file,
                        prompt=prompt,
                    )
            else:
                response = self._client.images.generate(
                    model=self._model,
                    prompt=prompt,
                )
        except Exception as error:
            raise ImageGenerationError(
                f"Fallo al generar imagen con OpenAI: {error}"
            ) from error

        image_b64 = response.data[0].b64_json
        if image_b64 is None:
            raise ImageGenerationError(
                "La respuesta de OpenAI no incluyó datos de imagen (b64_json)."
            )
        return base64.b64decode(image_b64)


# ==================================================
# SERVICIO
# ==================================================


class ImageService:
    """
    Genera y persiste las ilustraciones de los Momentos Clave del
    Álbum de Vida.
    """

    def __init__(
        self,
        provider: Optional[ImageProvider] = None,
        output_dir: Path = IMAGES_DIR,
    ) -> None:
        self._provider: ImageProvider = provider or PlaceholderImageProvider()
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def generate_memory_moment_image(
        self,
        player_id: str,
        moment_id: str,
        prompt: str,
        reference_image_path: Optional[Path] = None,
    ) -> Path:
        """
        Genera la ilustración de un Momento Clave y la guarda en
        disco, devolviendo la ruta del archivo resultante.

        Raises:
            ImageGenerationError: si el proveedor no puede generar la imagen.
        """
        image_bytes = self._provider.generate(prompt, reference_image_path)
        output_path = self._path_for(player_id, moment_id)
        output_path.write_bytes(image_bytes)
        logger.info(
            "ImageService: imagen del momento '%s' (jugador %s) guardada en %s",
            moment_id, player_id, output_path,
        )
        return output_path

    def get_image_path(self, player_id: str, moment_id: str) -> Optional[Path]:
        """Devuelve la ruta de la imagen ya generada para ese momento, si existe."""
        path = self._path_for(player_id, moment_id)
        return path if path.exists() else None

    def _path_for(self, player_id: str, moment_id: str) -> Path:
        return self._output_dir / f"{safe_filename(player_id)}__{safe_filename(moment_id)}.png"