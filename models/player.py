"""
models/player.py
=================

Qué hace:
    Define `Player`: el Estado de Personaje (EP), la estructura de
    datos única que representa todo lo que el personaje jugable es
    en un momento dado de la partida (What_If_Vision_Document.md
    §5.1; VITA_Game_Design_Document.md §2-3).

    Un `Player` representa UNA vida dentro de UNA partida — no la
    cuenta de usuario ni el historial entre partidas. Los contadores
    que sobreviven a la muerte del personaje (total de vidas
    jugadas, total de muertes, etc.) pertenecen a la capa de cuenta
    de usuario (ver database/users_schema.sql, tabla
    user_statistics), no a este modelo.

Cómo funciona:
    `Player` es un dataclass con validación en `__post_init__` y
    mutadores explícitos por grupo de atributos (salud, economía,
    relaciones, etc.). Ningún mutador expone el campo crudo para
    escritura libre: todos aceptan un `reason: str` porque
    VITA_Game_Design_Document.md §3 exige que el Estado de Personaje
    sea auditable ("ninguna variable se modifica [...] sin poder
    mantener un registro auditable de por qué cambió cada valor").
    Este archivo registra ese motivo vía `logging`; un historial
    persistente y estructurado de cambios es responsabilidad de una
    futura capa de Consecuencias (managers/ o services/), no de este
    dataclass.

    Las variables 0-100 (salud, felicidad, estrés, carisma...) se
    acotan con `models.scales.clamp`. La Reputación usa su propio
    rango (-100 a 100). Los valores económicos son absolutos, no
    porcentuales.

Dependencias:
    - config.constant: enums de dominio (SocioeconomicLevel,
      CivilStatus, EducationLevel, PersonalityTrait, Talent) y
      límites numéricos (MIN_STAT, MAX_STAT, MIN_REPUTATION,
      MAX_REPUTATION, MIN_MONEY, MAX_MONEY).
    - models.scales: función `clamp` compartida con NPC.

Cómo interactúa con otros módulos:
    Ningún otro archivo del proyecto importa `models.player`
    todavía (se verificó antes de este rediseño), así que este
    cambio no rompe integraciones existentes. El siguiente consumidor
    previsto es `managers/player_manager.py`, que expondrá estas
    operaciones a `engine/decision_engine.py` sin que la interfaz
    (`ui/`) escriba nunca directamente sobre el EP.

Autor: Korlo
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from config.constant import (
    CivilStatus,
    EducationLevel,
    MAX_MONEY,
    MAX_REPUTATION,
    MAX_STAT,
    MIN_MONEY,
    MIN_REPUTATION,
    MIN_STAT,
    PersonalityTrait,
    SocioeconomicLevel,
    Talent,
)
from models.scales import clamp, is_in_range

logger = logging.getLogger(__name__)


@dataclass
class FamilyTree:
    """
    Referencias a los NPC que conforman la familia inmediata del
    personaje (VITA_Game_Design_Document.md §2-3, §12-13).

    Guarda únicamente IDs, nunca fichas completas: la ficha completa
    de cada familiar vive en `models.npc.NPC` y se resuelve a través
    del futuro repositorio de NPC, no aquí (evita que Player y NPC
    dupliquen la misma información).
    """

    parent_ids: List[str] = field(default_factory=list)
    sibling_ids: List[str] = field(default_factory=list)
    spouse_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el árbol familiar a diccionario serializable."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FamilyTree":
        """Reconstruye un árbol familiar desde un diccionario."""
        return cls(
            parent_ids=list(data.get("parent_ids", [])),
            sibling_ids=list(data.get("sibling_ids", [])),
            spouse_id=data.get("spouse_id"),
            children_ids=list(data.get("children_ids", [])),
        )


@dataclass
class PlayerStatistics:
    """
    Contadores derivados de la partida en curso (una sola vida).

    Deliberadamente NO incluye contadores de "buenas" o "malas"
    decisiones: What_If_Vision_Document.md §1 y §2.2 establecen
    explícitamente que el juego no juzga las decisiones del jugador
    y que no existe un build óptimo ("No hay build óptimo"). Sumar
    un contador de decisiones "buenas/malas" contradiría ese pilar
    de diseño, así que se excluyó a propósito respecto al modelo
    anterior.

    Tampoco incluye contadores que sobreviven a la muerte del
    personaje (total de vidas jugadas, total de muertes): esos son
    agregados de cuenta de usuario, no de una vida individual (ver
    database/users_schema.sql, tabla user_statistics).
    """

    turns_played: int = 0
    decisions_made: int = 0
    key_moments_unlocked: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convierte las estadísticas a diccionario serializable."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlayerStatistics":
        """Reconstruye estadísticas desde un diccionario."""
        return cls(
            turns_played=data.get("turns_played", 0),
            decisions_made=data.get("decisions_made", 0),
            key_moments_unlocked=data.get("key_moments_unlocked", 0),
        )


@dataclass
class Player:
    """
    Estado de Personaje (EP): la vida que el jugador está viviendo
    en la partida actual.

    Atributos:
        Identidad: player_id, first_name, last_name, gender,
            birth_year, country, city.
        Físicos: health, appearance, health_genetics.
        Mentales: intelligence, discipline, creativity, stress,
            happiness.
        Sociales: charisma, empathy, reputation, personality_traits,
            talents, aspiration.
        Económicos: net_worth, annual_income, debt,
            socioeconomic_origin.
        Historial: education_level, current_profession, civil_status,
            family, active_relationships, birth_hook.
        Meta: age, life_expectancy, statistics, memory_moments.

    No incluye inventario ni logros: esos ya tienen su propio modelo
    (`models/inventory.py`, `models/achievement.py`) y agregarlos
    aquí también duplicaría esa responsabilidad (violación de SRP
    presente en el `Player` anterior, corregida en este rediseño).
    """

    # -- Identidad (obligatorios) --------------------------------
    player_id: str
    first_name: str
    last_name: str
    birth_year: int
    country: str

    # -- Identidad (opcionales) -----------------------------------
    city: Optional[str] = None
    gender: Optional[str] = None

    # -- Origen (fijado en la creación del personaje) --------------
    socioeconomic_origin: SocioeconomicLevel = SocioeconomicLevel.MEDIUM
    health_genetics: int = 70
    birth_hook: Optional[str] = None

    # -- Progresión temporal ----------------------------------------
    age: int = 0
    life_expectancy: float = 80.0

    # -- Atributos físicos --------------------------------------------
    health: int = 100
    appearance: int = 50

    # -- Atributos mentales -------------------------------------------
    intelligence: int = 50
    discipline: int = 50
    creativity: int = 50
    stress: int = 0
    happiness: int = 70

    # -- Atributos sociales -------------------------------------------
    charisma: int = 50
    empathy: int = 50
    reputation: int = 0
    personality_traits: List[PersonalityTrait] = field(default_factory=list)
    talents: List[Talent] = field(default_factory=list)
    aspiration: Optional[str] = None

    # -- Economía -----------------------------------------------------
    net_worth: float = 0.0
    annual_income: float = 0.0
    debt: float = 0.0

    # -- Historial / vida social ---------------------------------------
    education_level: EducationLevel = EducationLevel.NONE
    current_profession: Optional[str] = None
    civil_status: CivilStatus = CivilStatus.SINGLE
    family: FamilyTree = field(default_factory=FamilyTree)
    active_relationships: List[str] = field(default_factory=list)

    # -- Meta-progresión (Álbum de Vida) --------------------------------
    statistics: PlayerStatistics = field(default_factory=PlayerStatistics)
    memory_moments: List[str] = field(default_factory=list)

    # ==================================================
    # VALIDACIÓN
    # ==================================================

    def __post_init__(self) -> None:
        """
        Valida invariantes de identidad y acota los atributos
        numéricos a su rango permitido, registrando una advertencia
        cuando un valor de entrada estaba fuera de rango.
        """
        if not self.player_id:
            raise ValueError("player_id no puede estar vacío.")
        if not self.first_name or not self.last_name:
            raise ValueError("first_name y last_name son obligatorios.")
        if self.birth_year < 0:
            raise ValueError("birth_year no puede ser negativo.")
        if self.age < 0:
            raise ValueError("age no puede ser negativo.")
        if self.annual_income < 0:
            raise ValueError("annual_income no puede ser negativo.")
        if self.debt < 0:
            raise ValueError("debt no puede ser negativo.")

        self.health = self._clamp_stat("health", self.health)
        self.appearance = self._clamp_stat("appearance", self.appearance)
        self.health_genetics = self._clamp_stat(
            "health_genetics", self.health_genetics
        )
        self.intelligence = self._clamp_stat("intelligence", self.intelligence)
        self.discipline = self._clamp_stat("discipline", self.discipline)
        self.creativity = self._clamp_stat("creativity", self.creativity)
        self.stress = self._clamp_stat("stress", self.stress)
        self.happiness = self._clamp_stat("happiness", self.happiness)
        self.charisma = self._clamp_stat("charisma", self.charisma)
        self.empathy = self._clamp_stat("empathy", self.empathy)
        self.reputation = self._clamp_reputation(self.reputation)
        self.net_worth = clamp(self.net_worth, MIN_MONEY, MAX_MONEY)

    @staticmethod
    def _clamp_stat(name: str, value: int) -> int:
        """Acota un atributo 0-100, avisando si estaba fuera de rango."""
        if not is_in_range(value, MIN_STAT, MAX_STAT):
            logger.warning(
                "Player: '%s'=%s fuera de rango [%s, %s]; se acota.",
                name, value, MIN_STAT, MAX_STAT,
            )
        return clamp(value, MIN_STAT, MAX_STAT)

    @staticmethod
    def _clamp_reputation(value: int) -> int:
        """Acota la reputación a [-100, 100], avisando si se acotó."""
        if not is_in_range(value, MIN_REPUTATION, MAX_REPUTATION):
            logger.warning(
                "Player: 'reputation'=%s fuera de rango [%s, %s]; se acota.",
                value, MIN_REPUTATION, MAX_REPUTATION,
            )
        return clamp(value, MIN_REPUTATION, MAX_REPUTATION)

    # ==================================================
    # MUTADORES — ATRIBUTOS FÍSICOS Y MENTALES
    # ==================================================
    # Todos aceptan `reason` para dejar un rastro auditable de por
    # qué cambió cada variable (VITA_Game_Design_Document.md §3).
    # La escritura real durante la partida debe pasar siempre por el
    # futuro Sistema de Consecuencias, nunca directamente desde la
    # interfaz.

    def modify_health(self, amount: int, reason: str) -> None:
        """Modifica la salud en `amount` (puede ser negativo)."""
        previous = self.health
        self.health = self._clamp_stat("health", self.health + amount)
        logger.info(
            "Player %s: health %s -> %s (%s)",
            self.player_id, previous, self.health, reason,
        )

    def modify_stress(self, amount: int, reason: str) -> None:
        """Modifica el estrés en `amount`."""
        previous = self.stress
        self.stress = self._clamp_stat("stress", self.stress + amount)
        logger.info(
            "Player %s: stress %s -> %s (%s)",
            self.player_id, previous, self.stress, reason,
        )

    def modify_happiness(self, amount: int, reason: str) -> None:
        """Modifica la felicidad en `amount`."""
        previous = self.happiness
        self.happiness = self._clamp_stat("happiness", self.happiness + amount)
        logger.info(
            "Player %s: happiness %s -> %s (%s)",
            self.player_id, previous, self.happiness, reason,
        )

    def modify_reputation(self, amount: int, reason: str) -> None:
        """Modifica la reputación en `amount` (rango -100 a 100)."""
        previous = self.reputation
        self.reputation = self._clamp_reputation(self.reputation + amount)
        logger.info(
            "Player %s: reputation %s -> %s (%s)",
            self.player_id, previous, self.reputation, reason,
        )

    def modify_intelligence(self, amount: int, reason: str) -> None:
        """Modifica la inteligencia en `amount`."""
        self.intelligence = self._clamp_stat(
            "intelligence", self.intelligence + amount
        )
        logger.info(
            "Player %s: intelligence -> %s (%s)",
            self.player_id, self.intelligence, reason,
        )

    def modify_discipline(self, amount: int, reason: str) -> None:
        """Modifica la disciplina en `amount`."""
        self.discipline = self._clamp_stat("discipline", self.discipline + amount)
        logger.info(
            "Player %s: discipline -> %s (%s)",
            self.player_id, self.discipline, reason,
        )

    def modify_creativity(self, amount: int, reason: str) -> None:
        """Modifica la creatividad en `amount`."""
        self.creativity = self._clamp_stat("creativity", self.creativity + amount)
        logger.info(
            "Player %s: creativity -> %s (%s)",
            self.player_id, self.creativity, reason,
        )

    def modify_charisma(self, amount: int, reason: str) -> None:
        """Modifica el carisma en `amount`."""
        self.charisma = self._clamp_stat("charisma", self.charisma + amount)
        logger.info(
            "Player %s: charisma -> %s (%s)",
            self.player_id, self.charisma, reason,
        )

    def modify_empathy(self, amount: int, reason: str) -> None:
        """Modifica la empatía en `amount`."""
        self.empathy = self._clamp_stat("empathy", self.empathy + amount)
        logger.info(
            "Player %s: empathy -> %s (%s)",
            self.player_id, self.empathy, reason,
        )

    def modify_appearance(self, amount: int, reason: str) -> None:
        """Modifica la apariencia en `amount`."""
        self.appearance = self._clamp_stat("appearance", self.appearance + amount)
        logger.info(
            "Player %s: appearance -> %s (%s)",
            self.player_id, self.appearance, reason,
        )

    # ==================================================
    # MUTADORES — ECONOMÍA
    # ==================================================

    def modify_net_worth(self, amount: float, reason: str) -> None:
        """Modifica el patrimonio neto en `amount` (puede ser negativo)."""
        previous = self.net_worth
        self.net_worth = clamp(self.net_worth + amount, MIN_MONEY, MAX_MONEY)
        logger.info(
            "Player %s: net_worth %s -> %s (%s)",
            self.player_id, previous, self.net_worth, reason,
        )

    def set_annual_income(self, amount: float, reason: str) -> None:
        """Fija el ingreso anual. No puede ser negativo."""
        if amount < 0:
            raise ValueError("annual_income no puede ser negativo.")
        self.annual_income = amount
        logger.info(
            "Player %s: annual_income -> %s (%s)",
            self.player_id, self.annual_income, reason,
        )

    def add_debt(self, amount: float, reason: str) -> None:
        """Incrementa la deuda. `amount` debe ser positivo."""
        if amount < 0:
            raise ValueError("Usa reduce_debt() para disminuir la deuda.")
        self.debt += amount
        logger.info(
            "Player %s: debt +%s -> %s (%s)",
            self.player_id, amount, self.debt, reason,
        )

    def reduce_debt(self, amount: float, reason: str) -> None:
        """Reduce la deuda sin dejarla en negativo."""
        if amount < 0:
            raise ValueError("amount debe ser positivo.")
        self.debt = max(0.0, self.debt - amount)
        logger.info(
            "Player %s: debt -%s -> %s (%s)",
            self.player_id, amount, self.debt, reason,
        )

    # ==================================================
    # RASGOS, TALENTOS Y ASPIRACIÓN
    # ==================================================

    def add_personality_trait(self, trait: PersonalityTrait) -> None:
        """
        Añade un rasgo de personalidad si aún no lo tiene.

        La regla de "hasta 3 rasgos en la creación del personaje"
        (VITA_Game_Design_Document.md §2) es responsabilidad del
        futuro servicio de creación de personaje: este método no la
        impone, porque un rasgo adicional adquirido narrativamente
        más adelante en la vida es un caso de uso legítimo.
        """
        if trait not in self.personality_traits:
            self.personality_traits.append(trait)

    def add_talent(self, talent: Talent) -> None:
        """Añade un talento si el personaje aún no lo tiene."""
        if talent not in self.talents:
            self.talents.append(talent)

    def set_aspiration(self, aspiration: str) -> None:
        """
        Declara la aspiración de vida del personaje.

        El texto de la aspiración proviene del catálogo curado en
        `data/` (contenido narrativo), no de un enum aquí: este
        modelo solo almacena el valor ya resuelto.
        """
        if not aspiration:
            raise ValueError("aspiration no puede estar vacía.")
        self.aspiration = aspiration

    # ==================================================
    # RELACIONES Y FAMILIA
    # ==================================================

    def add_relationship(self, npc_id: str) -> None:
        """Registra una relación activa (amistad, rivalidad, etc.)."""
        if npc_id not in self.active_relationships:
            self.active_relationships.append(npc_id)

    def remove_relationship(self, npc_id: str) -> None:
        """Elimina una relación activa registrada."""
        if npc_id in self.active_relationships:
            self.active_relationships.remove(npc_id)

    def marry(self, spouse_npc_id: str) -> None:
        """Registra un matrimonio con el NPC indicado."""
        self.civil_status = CivilStatus.MARRIED
        self.family.spouse_id = spouse_npc_id
        logger.info("Player %s: se casó con %s", self.player_id, spouse_npc_id)

    def divorce(self) -> None:
        """Registra la disolución del matrimonio actual."""
        self.civil_status = CivilStatus.DIVORCED
        self.family.spouse_id = None
        logger.info("Player %s: se divorció", self.player_id)

    def add_child(self, child_npc_id: str) -> None:
        """Registra el nacimiento o adopción de un hijo."""
        if child_npc_id not in self.family.children_ids:
            self.family.children_ids.append(child_npc_id)

    # ==================================================
    # PROGRESIÓN TEMPORAL Y ÁLBUM DE VIDA
    # ==================================================

    def advance_age(self, years: int = 1) -> None:
        """
        Avanza la edad del personaje.

        El recálculo real de salud/estrés por envejecimiento
        pertenece al futuro Sistema de Edad, no a este modelo (SRP):
        aquí solo se actualiza el contador y el turno jugado.
        """
        if years <= 0:
            raise ValueError("years debe ser positivo.")
        self.age += years
        self.statistics.turns_played += 1

    def record_decision(self) -> None:
        """Incrementa el contador de decisiones tomadas en la vida."""
        self.statistics.decisions_made += 1

    def unlock_memory_moment(self, moment_id: str) -> None:
        """
        Añade un Momento Clave al Álbum de Vida del personaje
        (What_If_Vision_Document.md §5.3, §5.5).

        Solo guarda el ID: la ficha completa del momento (texto,
        fecha narrativa, decisión que lo originó, ilustración) vivirá
        en un modelo `MemoryMoment` propio, pendiente de diseño hasta
        resolver cómo se estructura el flujo de eventos (ver
        conversación sobre `models/story.py`).
        """
        if moment_id not in self.memory_moments:
            self.memory_moments.append(moment_id)
            self.statistics.key_moments_unlocked += 1

    # ==================================================
    # CONSULTA
    # ==================================================

    @property
    def is_alive(self) -> bool:
        """Indica si el personaje sigue con vida."""
        return self.health > 0

    @property
    def full_name(self) -> str:
        """Nombre completo del personaje."""
        return f"{self.first_name} {self.last_name}"

    # ==================================================
    # SERIALIZACIÓN
    # ==================================================

    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el Player a un diccionario serializable a JSON.

        Se implementa explícitamente (en vez de usar `asdict()` a
        secas) porque los enums deben serializarse a su `.value`
        para ser JSON-válidos.
        """
        return {
            "player_id": self.player_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "gender": self.gender,
            "birth_year": self.birth_year,
            "country": self.country,
            "city": self.city,
            "socioeconomic_origin": self.socioeconomic_origin.value,
            "health_genetics": self.health_genetics,
            "birth_hook": self.birth_hook,
            "age": self.age,
            "life_expectancy": self.life_expectancy,
            "health": self.health,
            "appearance": self.appearance,
            "intelligence": self.intelligence,
            "discipline": self.discipline,
            "creativity": self.creativity,
            "stress": self.stress,
            "happiness": self.happiness,
            "charisma": self.charisma,
            "empathy": self.empathy,
            "reputation": self.reputation,
            "personality_traits": [t.value for t in self.personality_traits],
            "talents": [t.value for t in self.talents],
            "aspiration": self.aspiration,
            "net_worth": self.net_worth,
            "annual_income": self.annual_income,
            "debt": self.debt,
            "education_level": self.education_level.value,
            "current_profession": self.current_profession,
            "civil_status": self.civil_status.value,
            "family": self.family.to_dict(),
            "active_relationships": list(self.active_relationships),
            "statistics": self.statistics.to_dict(),
            "memory_moments": list(self.memory_moments),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Player":
        """Reconstruye un Player desde un diccionario (inverso de to_dict)."""
        return cls(
            player_id=data["player_id"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            birth_year=data["birth_year"],
            country=data["country"],
            city=data.get("city"),
            gender=data.get("gender"),
            socioeconomic_origin=SocioeconomicLevel(
                data.get("socioeconomic_origin", SocioeconomicLevel.MEDIUM.value)
            ),
            health_genetics=data.get("health_genetics", 70),
            birth_hook=data.get("birth_hook"),
            age=data.get("age", 0),
            life_expectancy=data.get("life_expectancy", 80.0),
            health=data.get("health", 100),
            appearance=data.get("appearance", 50),
            intelligence=data.get("intelligence", 50),
            discipline=data.get("discipline", 50),
            creativity=data.get("creativity", 50),
            stress=data.get("stress", 0),
            happiness=data.get("happiness", 70),
            charisma=data.get("charisma", 50),
            empathy=data.get("empathy", 50),
            reputation=data.get("reputation", 0),
            personality_traits=[
                PersonalityTrait(t) for t in data.get("personality_traits", [])
            ],
            talents=[Talent(t) for t in data.get("talents", [])],
            aspiration=data.get("aspiration"),
            net_worth=data.get("net_worth", 0.0),
            annual_income=data.get("annual_income", 0.0),
            debt=data.get("debt", 0.0),
            education_level=EducationLevel(
                data.get("education_level", EducationLevel.NONE.value)
            ),
            current_profession=data.get("current_profession"),
            civil_status=CivilStatus(
                data.get("civil_status", CivilStatus.SINGLE.value)
            ),
            family=FamilyTree.from_dict(data.get("family", {})),
            active_relationships=list(data.get("active_relationships", [])),
            statistics=PlayerStatistics.from_dict(data.get("statistics", {})),
            memory_moments=list(data.get("memory_moments", [])),
        )