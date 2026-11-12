"""
models/story.py
================

Qué hace:
    Define `Story`: un arco narrativo discreto con capítulos y
    escenas dentro de la vida de un `Player` (por ejemplo, "el arco
    de su primer empleo" o "el arco de su primer amor").

    Esta forma de modelar la narrativa fue una decisión explícita:
    el Vision Document y el GDD de VITA describen un loop de vida
    continuo basado en Eventos sin "historias" discretas, pero se
    decidió mantener el modelo de arcos con capítulos por ser el más
    cercano al código ya existente (`engine/story_engine.py`) y al
    SDD ("StoryEngine: cargar historias, validar historias,
    controlar capítulos"). Un personaje puede tener varias `Story`
    activas o completadas a la vez (una por cada arco relevante de
    su vida), todas referenciando el mismo `player_id`.

Cómo funciona:
    Dataclass con validación en `__post_init__`. El estado de la
    historia usa `StoryStatus` (IN_PROGRESS/COMPLETED/FAILED/
    ABANDONED) en vez de los dos booleanos independientes
    (`completed`, `failed`) que tenía la versión anterior — esos dos
    booleanos podían quedar en una combinación inconsistente (ambos
    en True, o ninguno, sin que la historia estuviera realmente
    activa); un único enum de estado lo hace imposible por
    construcción.

    La escena actual se identifica con `current_scene_id: str` (no
    con un entero incremental como antes) porque
    `engine/story_engine.py` ya direcciona las escenas por clave de
    diccionario (`current_story["scenes"].get(current_scene_id)`) y
    las opciones apuntan a la siguiente escena por ese mismo tipo de
    clave (`selected_option["next_scene"]`), no por un índice
    secuencial. Mantener `scene` como entero habría sido
    inconsistente con el motor que ya existe.

Dependencias:
    - config.constant: StoryStatus (enum de estado).

Cómo interactúa con otros módulos:
    Ningún otro archivo importa `models.story` todavía, así que este
    cambio no rompe integraciones existentes. El contenido real de
    capítulos/escenas/opciones vive en JSON bajo `data/` (pendiente
    de crear); este modelo solo guarda el progreso del jugador
    dentro de ese contenido, nunca el contenido en sí. El siguiente
    consumidor previsto es `managers/story_manager.py`.

Autor: Korlo
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from config.constant import StoryStatus

logger = logging.getLogger(__name__)


@dataclass
class Story:
    """
    Progreso de un arco narrativo discreto dentro de la vida de un
    personaje.

    Atributos:
        Identidad: story_id, player_id, title.
        Contenido: story_content_id (referencia a la definición en
            data/scenarios/, ver services/story_service.py).
        Encuadre narrativo: genre, setting, objective.
        Progreso: chapter, current_scene_id, status.
        Contexto para IA: summary, current_situation.
        Historial: events, important_choices, active_npcs, flags.
        Cronología: started_at_age.
        Cierre: ending_id.
    """

    # -- Identidad (obligatorios) --------------------------------
    story_id: str
    player_id: str
    title: str

    # -- Referencia a contenido ---------------------------------------
    # Id de la definición de historia en data/scenarios/ (JSON) de la
    # que se creó esta Story. None para historias construidas sin un
    # archivo de contenido detrás (por ejemplo, en pruebas). Se separa
    # de `story_id` porque story_id identifica esta partida concreta
    # del arco, mientras que story_content_id identifica el "guion"
    # reutilizable del que partió.
    story_content_id: Optional[str] = None

    # -- Encuadre narrativo -----------------------------------------
    genre: str = ""
    setting: str = ""
    objective: str = ""

    # -- Progreso ------------------------------------------------------
    chapter: int = 1
    current_scene_id: str = "start"
    status: StoryStatus = StoryStatus.IN_PROGRESS

    # -- Contexto para la IA ----------------------------------------
    summary: str = ""
    current_situation: str = ""

    # -- Historial ----------------------------------------------------
    events: List[str] = field(default_factory=list)
    important_choices: List[str] = field(default_factory=list)
    active_npcs: List[str] = field(default_factory=list)
    flags: Dict[str, bool] = field(default_factory=dict)

    # -- Cronología (para el Álbum de Vida) ---------------------------
    started_at_age: Optional[int] = None

    # -- Cierre ---------------------------------------------------------
    ending_id: Optional[str] = None

    # ==================================================
    # VALIDACIÓN
    # ==================================================

    def __post_init__(self) -> None:
        """Valida identidad y coherencia básica de los campos de progreso."""
        if not self.story_id:
            raise ValueError("story_id no puede estar vacío.")
        if not self.player_id:
            raise ValueError("player_id no puede estar vacío.")
        if not self.title:
            raise ValueError("title no puede estar vacío.")
        if not self.current_scene_id:
            raise ValueError("current_scene_id no puede estar vacío.")
        if self.chapter < 1:
            raise ValueError("chapter debe ser mayor o igual a 1.")
        if self.started_at_age is not None and self.started_at_age < 0:
            raise ValueError("started_at_age no puede ser negativo.")

    # ==================================================
    # PROGRESO NARRATIVO
    # ==================================================

    def advance_scene(self, scene_id: str) -> None:
        """
        Avanza a la escena indicada (resuelta por
        `engine/story_engine.py` a partir de la opción elegida) y la
        registra en el historial de eventos de la historia.
        """
        if not scene_id:
            raise ValueError("scene_id no puede estar vacío.")
        self.current_scene_id = scene_id
        self.add_event(f"Escena: {scene_id}")

    def advance_chapter(self, first_scene_id: str = "start") -> None:
        """Avanza al siguiente capítulo y reinicia la escena actual."""
        self.chapter += 1
        self.current_scene_id = first_scene_id
        logger.info(
            "Story %s: avanza a capítulo %s", self.story_id, self.chapter
        )

    def add_event(self, event: str) -> None:
        """Añade un evento relevante al historial de la historia."""
        self.events.append(event)

    def add_choice(self, choice: str) -> None:
        """Registra una decisión importante tomada en esta historia."""
        self.important_choices.append(choice)

    def add_flag(self, flag: str, value: bool = True) -> None:
        """Fija una bandera narrativa (para condicionar escenas futuras)."""
        self.flags[flag] = value

    def has_flag(self, flag: str) -> bool:
        """Comprueba si una bandera narrativa está activa."""
        return self.flags.get(flag, False)

    # ==================================================
    # NPC INVOLUCRADOS
    # ==================================================

    def link_npc(self, npc_id: str) -> None:
        """Registra un NPC como activo dentro de esta historia."""
        if npc_id not in self.active_npcs:
            self.active_npcs.append(npc_id)

    def unlink_npc(self, npc_id: str) -> None:
        """Retira un NPC de la lista de activos en esta historia."""
        if npc_id in self.active_npcs:
            self.active_npcs.remove(npc_id)

    # ==================================================
    # CIERRE
    # ==================================================

    def finish(self, ending_id: str) -> None:
        """Marca la historia como completada con el final indicado."""
        if not ending_id:
            raise ValueError("ending_id no puede estar vacío.")
        self.status = StoryStatus.COMPLETED
        self.ending_id = ending_id
        logger.info("Story %s: completada (%s)", self.story_id, ending_id)

    def fail(self, reason: str = "") -> None:
        """Marca la historia como fallida."""
        self.status = StoryStatus.FAILED
        logger.info("Story %s: fallida (%s)", self.story_id, reason)

    def abandon(self, reason: str = "") -> None:
        """
        Marca la historia como abandonada (por ejemplo, la vida del
        personaje terminó antes de resolver este arco).
        """
        self.status = StoryStatus.ABANDONED
        logger.info("Story %s: abandonada (%s)", self.story_id, reason)

    # ==================================================
    # CONSULTA
    # ==================================================

    @property
    def is_active(self) -> bool:
        """Indica si la historia sigue en curso."""
        return self.status == StoryStatus.IN_PROGRESS

    @property
    def is_finished(self) -> bool:
        """Indica si la historia ya llegó a un cierre (de cualquier tipo)."""
        return self.status != StoryStatus.IN_PROGRESS

    # ==================================================
    # SERIALIZACIÓN
    # ==================================================

    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte la Story a un diccionario serializable a JSON.

        Se implementa explícitamente (no `asdict()` a secas) porque
        `status` es un enum y debe serializarse a su `.value`.
        """
        return {
            "story_id": self.story_id,
            "player_id": self.player_id,
            "title": self.title,
            "story_content_id": self.story_content_id,
            "genre": self.genre,
            "setting": self.setting,
            "objective": self.objective,
            "chapter": self.chapter,
            "current_scene_id": self.current_scene_id,
            "status": self.status.value,
            "summary": self.summary,
            "current_situation": self.current_situation,
            "events": list(self.events),
            "important_choices": list(self.important_choices),
            "active_npcs": list(self.active_npcs),
            "flags": dict(self.flags),
            "started_at_age": self.started_at_age,
            "ending_id": self.ending_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Story":
        """Reconstruye una Story desde un diccionario (inverso de to_dict)."""
        return cls(
            story_id=data["story_id"],
            player_id=data["player_id"],
            title=data["title"],
            story_content_id=data.get("story_content_id"),
            genre=data.get("genre", ""),
            setting=data.get("setting", ""),
            objective=data.get("objective", ""),
            chapter=data.get("chapter", 1),
            current_scene_id=data.get("current_scene_id", "start"),
            status=StoryStatus(data.get("status", StoryStatus.IN_PROGRESS.value)),
            summary=data.get("summary", ""),
            current_situation=data.get("current_situation", ""),
            events=list(data.get("events", [])),
            important_choices=list(data.get("important_choices", [])),
            active_npcs=list(data.get("active_npcs", [])),
            flags=dict(data.get("flags", {})),
            started_at_age=data.get("started_at_age"),
            ending_id=data.get("ending_id"),
        )