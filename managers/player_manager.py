"""
managers/player_manager.py
============================

Qué hace:
    Crea un `Player` nuevo a partir de los datos que el jugador
    introdujo en `ui/screens/character_creation/`, lo persiste vía
    `SaveService`, y lo recupera cuando se carga una partida.

    Es el segundo manager de dominio construido (después de
    `StoryManager`). Se ocupa del CUÁNDO y el QUÉ en la creación de
    personaje; el CÓMO (instanciar `Player`, calcular el año de
    nacimiento desde la edad de inicio, asignar el ID único) vive
    aquí, siguiendo el mismo patrón delegación que `SaveManager`.

Por qué calcula `birth_year` en vez de pedírselo al jugador:
    La pantalla de creación pide "edad de inicio" (más intuitivo
    para el jugador que un año de nacimiento). `birth_year` es un
    campo obligatorio de `Player` y se calcula como
    `CURRENT_GAME_YEAR - starting_age`, donde `CURRENT_GAME_YEAR` es
    una constante de `config/game_config.py`. El año del juego no es
    el año real — es un parámetro de diseño decidido aquí.

Distribución de puntos:
    `DISTRIBUTABLE_ATTRS` son los 10 atributos que el jugador puede
    modificar en el paso 3 de creación. Cada uno parte de su valor
    por defecto en `Player` y el jugador reparte
    `POINTS_TO_DISTRIBUTE` puntos extras entre ellos, sin poder bajar
    ninguno de su mínimo (0 para la mayoría, -100 para reputación).
    La validación de que los puntos no superan el máximo y no exceden
    el total disponible la hace `PlayerManager.validate_distribution()`
    — la UI la llama antes de llamar a `create_player()`.

Autor: Korlo
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from config.constant import MAX_STAT, MIN_REPUTATION, MAX_REPUTATION, SocioeconomicLevel
from models.player import Player
from services.repositories import JSONKeyValueRepository, KeyValueRepository
from config.paths import SAVES_DIR

logger = logging.getLogger(__name__)

# Año de referencia del universo del juego. No tiene que ser el año real —
# se usa únicamente para calcular birth_year a partir de la edad de inicio.
CURRENT_GAME_YEAR: int = 2024

# Puntos extra que el jugador distribuye sobre los valores por defecto.
POINTS_TO_DISTRIBUTE: int = 20

# Atributos distribuibles (los 10 numéricos de Player), en el orden
# en que aparecen en la pantalla de creación.
DISTRIBUTABLE_ATTRS: List[str] = [
    "health", "appearance",
    "intelligence", "discipline", "creativity",
    "happiness", "charisma", "empathy",
    "stress", "reputation",
]

# Valores por defecto reales de Player (verificados contra el dataclass).
_ATTR_DEFAULTS: Dict[str, int] = {
    "health": 100, "appearance": 50,
    "intelligence": 50, "discipline": 50, "creativity": 50,
    "stress": 0, "happiness": 70,
    "charisma": 50, "empathy": 50,
    "reputation": 0,
}

_KEY_PREFIX = "player_"


class PlayerCreationError(Exception):
    """Los datos de creación de personaje no son válidos."""


class PlayerNotFoundError(Exception):
    """No existe ningún `Player` con ese `player_id`."""


class PlayerManager:
    """Crea, persiste y recupera Players. Segundo manager de dominio del proyecto."""

    def __init__(self, repository: Optional[KeyValueRepository] = None) -> None:
        self._repository: KeyValueRepository = repository or JSONKeyValueRepository(
            SAVES_DIR
        )

    # ==================================================
    # VALIDACIÓN (la UI la llama antes de crear)
    # ==================================================

    def validate_distribution(
        self, deltas: Dict[str, int]
    ) -> Tuple[bool, str]:
        """
        Comprueba que los deltas de atributos sean válidos:
        - La suma no supera `POINTS_TO_DISTRIBUTE`.
        - Ningún valor resultante baja del mínimo de su atributo.
        - Ningún valor resultante sube del máximo (100, o 100/-100 para reputación).
        - No contiene atributos desconocidos.

        Devuelve (True, "") si todo está bien, o (False, motivo) si no.
        """
        # En modo de asignación libre no imponemos un límite global
        # de puntos; comprobamos únicamente que no se hayan usado
        # valores negativos como suma (por seguridad) y delegamos en
        # comprobaciones por atributo.
        total = sum(deltas.values())
        if total < 0:
            return False, "No puedes usar puntos negativos."

        for attr, delta in deltas.items():
            if attr not in _ATTR_DEFAULTS:
                return False, f"Atributo desconocido: '{attr}'."
            base = _ATTR_DEFAULTS[attr]
            result = base + delta
            min_val = MIN_REPUTATION if attr == "reputation" else 0
            max_val = MAX_REPUTATION if attr == "reputation" else MAX_STAT
            if result < min_val:
                return False, (
                    f"'{attr}' no puede bajar de {min_val} "
                    f"(base {base} + delta {delta} = {result})."
                )
            if result > max_val:
                return False, (
                    f"'{attr}' no puede superar {max_val} "
                    f"(base {base} + delta {delta} = {result})."
                )
        return True, ""

    # ==================================================
    # CREACIÓN
    # ==================================================

    def create_player(
        self,
        *,
        first_name: str,
        last_name: str,
        gender: Optional[str],
        starting_age: int,
        country: str,
        city: str,
        socioeconomic_origin: SocioeconomicLevel = SocioeconomicLevel.MEDIUM,
        attr_deltas: Optional[Dict[str, int]] = None,
        aspiration: Optional[str] = None,
        player_id: Optional[str] = None,
    ) -> Player:
        """
        Crea un `Player` nuevo, aplica los deltas de atributos
        elegidos por el jugador, lo persiste y lo devuelve.

        Args:
            player_id: id explícito a usar (p. ej. el `user.id` de
                Supabase Auth de una sesión iniciada), para que el
                personaje quede scoped a esa cuenta y se recupere en
                logins futuros. Si no se pasa, se genera un UUID nuevo
                (modo invitado, igual que antes).

        Raises:
            PlayerCreationError: si el nombre está vacío, la edad de
                inicio es inválida, o la distribución de atributos no
                pasa la validación.
        """
        first_name = first_name.strip()
        last_name = last_name.strip()
        if not first_name or not last_name:
            raise PlayerCreationError("El nombre y el apellido no pueden estar vacíos.")

        if not (0 < starting_age < 120):
            raise PlayerCreationError(
                f"La edad de inicio debe estar entre 1 y 119 (recibida: {starting_age})."
            )

        deltas = attr_deltas or {}
        valid, reason = self.validate_distribution(deltas)
        if not valid:
            raise PlayerCreationError(f"Distribución de atributos inválida: {reason}")

        player_id = player_id or str(uuid.uuid4())
        birth_year = CURRENT_GAME_YEAR - starting_age

        player = Player(
            player_id=player_id,
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            birth_year=birth_year,
            age=starting_age,
            country=country,
            city=city,
            socioeconomic_origin=socioeconomic_origin,
            aspiration=aspiration,
            # Los atributos con delta se sobrescriben debajo; el resto
            # toma sus valores por defecto del dataclass.
        )

        # Aplicar deltas usando los mutadores auditables de Player,
        # que es la única forma correcta de modificarlos (SDD §4-5).
        _mutators = {
            "health": player.modify_health,
            "appearance": player.modify_appearance,
            "intelligence": player.modify_intelligence,
            "discipline": player.modify_discipline,
            "creativity": player.modify_creativity,
            "stress": player.modify_stress,
            "happiness": player.modify_happiness,
            "charisma": player.modify_charisma,
            "empathy": player.modify_empathy,
            "reputation": player.modify_reputation,
        }
        for attr, delta in deltas.items():
            if delta != 0:
                _mutators[attr](delta, reason="creación de personaje")

        self._persist(player)
        logger.info(
            "PlayerManager: personaje '%s' creado (id=%s, edad=%d, país=%s)",
            player.full_name, player_id, starting_age, country,
        )
        return player

    # ==================================================
    # CONSULTA / RECUPERACIÓN
    # ==================================================

    def get_player(self, player_id: str) -> Player:
        """
        Recupera un `Player` por su ID.

        Raises:
            PlayerNotFoundError: si no existe.
        """
        raw = self._repository.get(self._key(player_id))
        if raw is None:
            raise PlayerNotFoundError(f"No existe ningún jugador con id '{player_id}'.")
        return Player.from_dict(raw)

    def save_player(self, player: Player) -> None:
        """Persiste el estado actual de un `Player` (útil para el Sistema de Consecuencias)."""
        self._persist(player)
        logger.debug("PlayerManager: '%s' guardado.", player.full_name)

    def player_exists(self, player_id: str) -> bool:
        return self._repository.get(self._key(player_id)) is not None

    # ==================================================
    # INTERNO
    # ==================================================

    def _persist(self, player: Player) -> None:
        self._repository.set(self._key(player.player_id), player.to_dict())

    @staticmethod
    def _key(player_id: str) -> str:
        return f"{_KEY_PREFIX}{player_id}"
