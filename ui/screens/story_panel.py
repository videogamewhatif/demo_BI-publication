"""
ui/screens/story_panel.py
===========================

Qué hace:
    `StoryPanel`: la columna central de la sección Historia —
    encabezado de capítulo/escena, imagen de escena, texto
    narrativo y N tarjetas de decisión — todo obtenido en tiempo
    real de `managers.story_manager.StoryManager`, nunca
    hardcodeado.

Cómo funciona el clic en una decisión:
    `DecisionOptionCard.chosen(option_index)` -> si la opción elegida
    trae un campo `effects` (ver `docs/content_authoring_guide.md`),
    se aplica primero vía `ConsequenceService.apply_effects()` — el
    único sistema autorizado a escribir en `Player` (GDD §5) — y
    luego se llama a `StoryManager.choose_option(story, option_index)`
    para avanzar la historia. `story_advanced` (señal propia) le
    avisa a `GameplayScreen` que refresque los paneles hermanos
    (personaje, historial, estadísticas — las estadísticas SÍ pueden
    haber cambiado ahora) y dispare el guardado.

    `ConsequenceService` es opcional (`None` por defecto): si no se
    pasa, o si la escena/jugador no están disponibles, el clic sigue
    avanzando la historia igual, simplemente sin aplicar efectos —
    así el panel se puede seguir usando en contextos que no tengan
    todavía un `Player` real (como antes de que existiera el
    Sistema de Consecuencias).

    Después de los efectos, si hay un `TimeManager`, avanza 1 año y
    comprueba si la vida terminó (`managers.time_manager.TimeManager`
    — salud, vejez, o una probabilidad baja de accidente/enfermedad).
    Si terminó, NO se avanza la historia: se emite `life_ended` y
    `GameplayScreen` lleva a la pantalla de fin de vida. Si la vida
    sigue y hay un `EventManager`, ese mismo año se intenta además un
    evento aleatorio del catálogo (`data/events/`, vacío hoy) —
    ver `_trigger_random_event_if_any`.

    Además, cada vez que se renderiza una escena nueva (carga inicial
    o tras avanzar), si esa escena está marcada como Momento Clave
    (`memory_moment` — ver `docs/content_authoring_guide.md`) y hay
    un `MemoryManager`, se desbloquea ahí — ver
    `_maybe_unlock_memory_moment`.

Por qué no hay barra de "progreso en %":
    No existe en el proyecto ningún dato de "capítulos totales
    esperados" de una historia — inventar un porcentaje sin ese
    denominador sería fabricar un número. En su lugar se muestra el
    capítulo actual (dato real de `Story.chapter`) y el número de
    decisiones tomadas en esta historia (`len(story.important_choices)`,
    también real).

Autor: Korlo (ui/ añadida en esta sesión; StoryService -> StoryManager
en la sesión de managers de dominio; ConsequenceService conectado
en la sesión del Sistema de Consecuencias)
"""

from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from managers.event_manager import EventManager, EventNotFoundError, EventRequirementsNotMetError
from managers.memory_manager import MemoryManager
from managers.story_manager import SceneNotFoundError, StoryManager
from managers.time_manager import LifeEndResult, TimeManager
from models.player import Player
from models.story import Story
from services.consequence_service import ConsequenceService, InvalidEffectsError
from ui import theme
from ui.widgets.decision_option import DecisionOptionCard
from ui.widgets.image_placeholder import SceneImage

logger = logging.getLogger(__name__)


class StoryPanel(QWidget):
    """Columna central: capítulo/escena, imagen, narrativa y decisiones reales."""

    story_advanced = Signal(object)  # emite el Story actualizado
    life_ended = Signal(object, object)  # (Player, LifeEndResult)

    def __init__(
        self,
        story_manager: StoryManager,
        consequence_service: Optional[ConsequenceService] = None,
        time_manager: Optional[TimeManager] = None,
        event_manager: Optional[EventManager] = None,
        memory_manager: Optional[MemoryManager] = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._story_manager = story_manager
        self._consequence_service = consequence_service
        self._time_manager = time_manager
        self._event_manager = event_manager
        self._memory_manager = memory_manager
        self._story: Optional[Story] = None
        self._player: Optional[Player] = None
        self._last_choice_label: Optional[str] = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(theme.SPACE_SM)


        self._breadcrumb = QLabel()
        self._breadcrumb.setStyleSheet(
            f"color: {theme.ACCENT_PURPLE}; font-size: {theme.FONT_SIZE_SMALL}px; font-weight: 700;"
        )
        self._heading = QLabel()
        self._heading.setWordWrap(True)
        self._heading.setStyleSheet(
            f"color: {theme.TEXT_PRIMARY}; font-size: {theme.FONT_SIZE_H1}px; font-weight: 800;"
        )

        root.addWidget(self._breadcrumb)
        root.addWidget(self._heading)

        self._image = SceneImage()
        root.addWidget(self._image)

        self._narrative = QLabel()
        self._narrative.setWordWrap(True)
        self._narrative.setStyleSheet(
            f"color: {theme.TEXT_PRIMARY}; font-size: {theme.FONT_SIZE_BODY}px; line-height: 1.5;"
        )
        root.addWidget(self._narrative)

        self._choice_prompt = QLabel("¿Qué decisión tomarás?")
        self._choice_prompt.setStyleSheet(
            f"color: {theme.ACCENT_PURPLE}; font-size: {theme.FONT_SIZE_BODY}px; font-weight: 700;"
        )
        root.addWidget(self._choice_prompt)

        self._options_grid = QGridLayout()
        self._options_grid.setSpacing(theme.SPACE_MD)
        root.addLayout(self._options_grid)

        self._ending_label = QLabel()
        self._ending_label.setWordWrap(True)
        self._ending_label.setStyleSheet(
            f"color: {theme.TEXT_SECONDARY}; font-size: {theme.FONT_SIZE_BODY}px; font-style: italic;"
        )
        self._ending_label.hide()
        root.addWidget(self._ending_label)

        footer = QHBoxLayout()
        self._progress_label = QLabel()
        self._progress_label.setStyleSheet(
            f"color: {theme.TEXT_DISABLED}; font-size: {theme.FONT_SIZE_TINY}px;"
        )
        footer.addWidget(self._progress_label)
        footer.addStretch(1)
        root.addLayout(footer)

        root.addStretch(1)

    # ==================================================
    # ESTADO
    # ==================================================

    def set_story(self, story: Optional[Story]) -> None:
        """Carga (o recarga) la historia a mostrar y redibuja toda la escena actual."""
        self._story = story
        self._render()

    def set_player(self, player: Optional[Player]) -> None:
        """
        Jugador actual — necesario para poder aplicar `effects` al
        elegir una opción. No dispara redibujado (no hay nada visual
        que dependa de esto en este panel; el panel de personaje
        compacto se actualiza por su cuenta).
        """
        self._player = player

    def _render(self) -> None:
        story = self._story
        if story is None:
            self._breadcrumb.setText("")
            self._heading.setText("No tienes ninguna historia en curso")
            self._narrative.setText(
                "Todavía no hay una historia activa para este personaje. "
                "Esto es honesto respecto al estado actual del proyecto: el contenido "
                "narrativo (data/scenarios/*.json) y el flujo de creación de personaje "
                "todavía no existen — no se simula aquí."
            )
            self._image.set_scene(None)
            self._choice_prompt.hide()
            self._ending_label.hide()
            self._progress_label.setText("")
            self._clear_options()
            return

        self._breadcrumb.setText(f"Capítulo {story.chapter}")

        try:
            scene = self._story_manager.get_current_scene(story)
        except SceneNotFoundError as error:
            self._heading.setText(story.title)
            self._narrative.setText(str(error))
            self._image.set_scene(None)
            self._choice_prompt.hide()
            self._clear_options()
            return

        self._heading.setText(scene.get("title") or story.title)
        self._narrative.setText(scene.get("text", ""))
        self._image.set_scene(scene)
        self._maybe_unlock_memory_moment(scene, story)

        decisions_count = len(story.important_choices)
        self._progress_label.setText(
            f"Capítulo {story.chapter} · {decisions_count} decisión(es) tomada(s) en esta historia"
        )

        if story.is_finished:
            self._choice_prompt.hide()
            self._clear_options()
            self._ending_label.setText(
                f"Esta historia ha terminado (final: {story.ending_id or 'desconocido'})."
            )
            self._ending_label.show()
            return

        self._ending_label.hide()
        options = scene.get("options", [])
        self._choice_prompt.setVisible(bool(options))
        self._render_options(options)

    def _maybe_unlock_memory_moment(self, scene: dict, story: Story) -> None:
        """
        Si la escena actual está marcada como Momento Clave
        (`"memory_moment": {"category": "..."}` — ver
        `docs/content_authoring_guide.md`), la desbloquea vía
        `MemoryManager`. Silencioso si falta `MemoryManager`/
        `Player`, si la escena no está marcada, o si ya estaba
        desbloqueada (`MemoryManager.unlock_moment()` ya es
        idempotente contra `Player.memory_moments`).
        """
        if self._memory_manager is None or self._player is None:
            return
        memory_moment = scene.get("memory_moment")
        if not memory_moment or not memory_moment.get("category"):
            return
        moment_id = f"{story.story_content_id}:{story.current_scene_id}"
        self._memory_manager.unlock_moment(
            self._player,
            moment_id=moment_id,
            category=memory_moment["category"],
            title=scene.get("title") or story.title,
            text=scene.get("text", ""),
            origin_decision=self._last_choice_label,
        )
        self._last_choice_label = None

    def _render_options(self, options: list) -> None:
        self._clear_options()
        columns = 2 if len(options) > 1 else 1
        for index, option in enumerate(options):
            card = DecisionOptionCard(index, option.get("label", f"Opción {index + 1}"))
            card.chosen.connect(self._handle_choice)
            row, col = divmod(index, columns)
            self._options_grid.addWidget(card, row, col)

    def _clear_options(self) -> None:
        while self._options_grid.count():
            item = self._options_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # ==================================================
    # INTERACCIÓN
    # ==================================================

    def _handle_choice(self, option_index: int) -> None:
        if self._story is None:
            return

        self._last_choice_label = self._option_label(option_index)
        self._apply_effects_if_any(option_index)

        life_end_result = self._advance_time_and_check_life()
        if life_end_result is not None:
            self.life_ended.emit(self._player, life_end_result)
            return

        updated = self._story_manager.choose_option(self._story, option_index)
        self._story = updated
        self._render()
        self.story_advanced.emit(updated)

    def _advance_time_and_check_life(self) -> Optional[LifeEndResult]:
        """
        Avanza 1 año y comprueba si la vida terminó. Sin
        `TimeManager` o sin `Player`, no hace nada (devuelve None) —
        mismo criterio de "silencioso si falta la pieza" que
        `_apply_effects_if_any`. Si la vida sigue, intenta además un
        evento aleatorio del catálogo (`_trigger_random_event_if_any`)
        — mismo punto del año que el roll interno de accidente/
        enfermedad de `TimeManager`, pero para contenido de diseño.
        """
        if self._time_manager is None or self._player is None:
            return None
        self._time_manager.advance_time(self._player)
        life_end_result = self._time_manager.check_life_status(self._player)
        if life_end_result is None:
            self._trigger_random_event_if_any()
        return life_end_result

    def _trigger_random_event_if_any(self) -> None:
        """
        Elige un evento al azar del catálogo (`data/events/`, vacío
        hoy) y lo dispara si `Player` cumple sus requisitos —
        aplicando sus efectos vía el `ConsequenceService` que ya
        tenga configurado `EventManager`. Silencioso si falta
        `EventManager`, si el catálogo no tiene nada, o si el evento
        elegido no cumple sus propios requisitos (no es un error de
        contenido, es un caso normal: ese evento no le tocaba a este
        jugador esta vez).
        """
        if self._event_manager is None or self._player is None:
            return
        candidate = self._event_manager.get_random_event()
        if candidate is None:
            return
        event_id, event = candidate
        if not self._event_manager.can_trigger(self._player, event):
            return
        try:
            self._event_manager.trigger_event(self._player, event_id)
        except (EventNotFoundError, EventRequirementsNotMetError):
            logger.exception(
                "StoryPanel: fallo inesperado al disparar el evento aleatorio '%s'.", event_id
            )

    def _option_label(self, option_index: int) -> Optional[str]:
        """Label de la opción `option_index` de la escena actual, o None si no se puede resolver."""
        try:
            scene = self._story_manager.get_current_scene(self._story)
        except SceneNotFoundError:
            return None
        options = scene.get("options", [])
        if not (0 <= option_index < len(options)):
            return None
        return options[option_index].get("label")

    def _apply_effects_if_any(self, option_index: int) -> None:
        """
        Aplica los `effects` de la opción elegida (si trae alguno)
        ANTES de avanzar la historia — necesita leer la escena
        actual, y `choose_option()` ya la deja atrás una vez avanza.
        Silenciosa si falta el ConsequenceService, el Player, o la
        opción no tiene 'effects': la historia igual avanza.
        """
        if self._consequence_service is None or self._player is None:
            return
        try:
            scene = self._story_manager.get_current_scene(self._story)
        except SceneNotFoundError:
            return
        options = scene.get("options", [])
        if not (0 <= option_index < len(options)):
            return
        effects = options[option_index].get("effects")
        if not effects:
            return
        label = options[option_index].get("label", f"opción {option_index}")
        try:
            self._consequence_service.apply_effects(
                self._player, effects, reason=f"decisión: {label}"
            )
        except InvalidEffectsError:
            # El contenido debería haber pasado tools/scenario_validator.py
            # antes de llegar aquí; si no lo hizo, no se crashea el
            # juego por un error de contenido — se registra y se sigue
            # sin aplicar esos efectos concretos.
            logger.exception(
                "StoryPanel: 'effects' inválidos en la opción elegida; se ignoran."
            )
            return
        self._player.record_decision()
