"""
constant.py
============

Constantes globales del proyecto What If?.

Este archivo contiene únicamente valores que NO deberían cambiar
durante la ejecución del juego.

Nota de mantenimiento (revisión de análisis): el docstring original
decía "constants.py" (con "s"), pero el archivo real se llama
"constant.py". main.py todavía importa `config.constants`, que no
existe con ese nombre — ese import roto se corrige cuando se aborde
main.py, no aquí, para no mezclar cambios de módulos distintos en
el mismo commit lógico.

Autor: Korlo
"""

from enum import Enum


# ==========================================================
# ESTADOS DEL JUEGO
# ==========================================================

class GameState(Enum):
    MENU = "menu"
    NEW_GAME = "new_game"
    LOAD_GAME = "load_game"
    PLAYING = "playing"
    PAUSED = "paused"
    SETTINGS = "settings"
    CREDITS = "credits"
    GAME_OVER = "game_over"
    ENDING = "ending"
    EXIT = "exit"


# ==========================================================
# TIPOS DE EVENTOS
# ==========================================================

class EventType(Enum):
    STORY = "story"
    RANDOM = "random"
    MORAL = "moral"
    CAREER = "career"
    HEALTH = "health"
    FAMILY = "family"
    LOVE = "love"
    ECONOMY = "economy"
    SPECIAL = "special"


# ==========================================================
# ESTADÍSTICAS DEL JUGADOR
# ==========================================================

class Stat(Enum):
    HEALTH = "health"
    MONEY = "money"
    HAPPINESS = "happiness"
    REPUTATION = "reputation"
    KNOWLEDGE = "knowledge"
    EXPERIENCE = "experience"
    RELATIONSHIPS = "relationships"


# ==========================================================
# DIFICULTAD
# ==========================================================

class Difficulty(Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    NIGHTMARE = "nightmare"


# ==========================================================
# PERSONAJE — ESTADO DE PERSONAJE (EP)
# ==========================================================
# Vocabulario cerrado del dominio de personaje/NPC (ver
# What_If_Vision_Document.md §5.1 y VITA_Game_Design_Document.md
# §2-3, §11). Vive aquí junto a GameState/EventType/Stat/Difficulty
# porque son cierres de vocabulario que la LÓGICA del motor
# consulta directamente para calcular consecuencias — a diferencia
# del contenido narrativo (historias, diálogos, textos de eventos),
# que vive en JSON bajo data/ y nunca debe codificarse aquí.

class SocioeconomicLevel(Enum):
    """Nivel socioeconómico de la familia de origen del personaje."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class CivilStatus(Enum):
    """Estado civil actual del personaje."""
    SINGLE = "single"
    IN_RELATIONSHIP = "in_relationship"
    ENGAGED = "engaged"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"


class EducationLevel(Enum):
    """Nivel educativo alcanzado por el personaje."""
    NONE = "none"
    PRIMARY = "primary"
    SECONDARY = "secondary"
    TECHNICAL = "technical"
    UNIVERSITY = "university"
    POSTGRADUATE = "postgraduate"
    DOCTORATE = "doctorate"


class PersonalityTrait(Enum):
    """
    Rasgo de personalidad del personaje o de un NPC.

    En la creación de personaje se asignan hasta 3 (ver
    VITA_Game_Design_Document.md §2); esa regla la aplica el futuro
    servicio de creación de personaje, no este enum — el enum solo
    define el catálogo cerrado de valores posibles.
    """
    AMBITIOUS = "ambitious"
    CAUTIOUS = "cautious"
    IMPULSIVE = "impulsive"
    GENEROUS = "generous"
    STUBBORN = "stubborn"
    OPTIMISTIC = "optimistic"
    PESSIMISTIC = "pessimistic"
    INTROVERTED = "introverted"
    EXTROVERTED = "extroverted"
    HONEST = "honest"
    MANIPULATIVE = "manipulative"
    LOYAL = "loyal"
    REBELLIOUS = "rebellious"
    PERFECTIONIST = "perfectionist"
    CURIOUS = "curious"
    ANXIOUS = "anxious"
    RESILIENT = "resilient"
    COMPETITIVE = "competitive"
    IDEALISTIC = "idealistic"
    PRAGMATIC = "pragmatic"


class Talent(Enum):
    """Predisposición innata del personaje (Vision Document §5.1)."""
    ARTISTIC = "artistic"
    ANALYTICAL = "analytical"
    PHYSICAL = "physical"
    SOCIAL = "social"
    MUSICAL = "musical"
    TECHNICAL = "technical"
    LITERARY = "literary"
    LEADERSHIP = "leadership"


class RelationshipType(Enum):
    """Tipo de vínculo entre el jugador y un NPC (VITA GDD §11)."""
    PARENT = "parent"
    SIBLING = "sibling"
    CHILD = "child"
    SPOUSE = "spouse"
    PARTNER = "partner"
    FRIEND = "friend"
    COLLEAGUE = "colleague"
    ACQUAINTANCE = "acquaintance"
    RIVAL = "rival"
    OTHER = "other"

class StoryStatus(Enum):
    """
    Estado de una historia (arco narrativo discreto con capítulos)
    dentro de la vida de un personaje. Reemplaza los dos booleanos
    independientes `completed`/`failed` del Story original, que
    podían quedar en un estado inconsistente (ambos en True, o
    ninguno, sin que la historia estuviera realmente activa).
    """
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"


# ==========================================================
# DECISIONES
# ==========================================================

OPTION_A = "A"
OPTION_B = "B"
OPTION_C = "C"
OPTION_D = "D"


# ==========================================================
# LÍMITES
# ==========================================================

MIN_STAT = 0
MAX_STAT = 100

MIN_REPUTATION = -100
MAX_REPUTATION = 100

MIN_MONEY = -999999
MAX_MONEY = 999999999

MAX_HISTORY_EVENTS = 1000


# ==========================================================
# GUARDADO
# ==========================================================

SAVE_VERSION = "1.0"


# ==========================================================
# FORMATOS
# ==========================================================

DATE_FORMAT = "%d/%m/%Y"
TIME_FORMAT = "%H:%M:%S"
DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"


# ==========================================================
# RESULTADOS
# ==========================================================

SUCCESS = "SUCCESS"
ERROR = "ERROR"
WARNING = "WARNING"


# ==========================================================
# LOGS
# ==========================================================

LOG_FORMAT = (
    "%(asctime)s | "
    "%(levelname)s | "
    "%(name)s | "
    "%(message)s"
)


# ==========================================================
# MENSAJES
# ==========================================================

GAME_STARTED = "Nueva partida iniciada."
GAME_SAVED = "Partida guardada correctamente."
GAME_LOADED = "Partida cargada correctamente."
GAME_OVER = "Fin de la partida."


# ==========================================================
# EXTENSIONES
# ==========================================================

JSON_EXTENSION = ".json"
SAVE_EXTENSION = ".save"
PNG_EXTENSION = ".png"
JPG_EXTENSION = ".jpg"
MP3_EXTENSION = ".mp3"
WAV_EXTENSION = ".wav"


# ==========================================================
# PRIORIDADES
# ==========================================================

LOW = 1
MEDIUM = 2
HIGH = 3
CRITICAL = 4