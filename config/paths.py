"""
paths.py
========

Rutas oficiales del proyecto What If?.

Todas las rutas a carpetas y archivos deben obtenerse desde este módulo.

Autor: Korlo
"""

from pathlib import Path

# ==========================================================
# DIRECTORIO RAÍZ
# ==========================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

# ==========================================================
# CARPETAS PRINCIPALES
# ==========================================================

CONFIG_DIR = ROOT_DIR / "config"

ASSETS_DIR = ROOT_DIR / "assets"

DATA_DIR = ROOT_DIR / "data"

ENGINE_DIR = ROOT_DIR / "engine"

UI_DIR = ROOT_DIR / "ui"

MODELS_DIR = ROOT_DIR / "models"

SERVICES_DIR = ROOT_DIR / "services"

UTILS_DIR = ROOT_DIR / "utils"

LOGS_DIR = ROOT_DIR / "logs"

SAVES_DIR = ROOT_DIR / "saves"

# Añadido junto con database/ (backend SQLAlchemy, alternativa
# opcional a los repositorios JSON de SAVES_DIR — ver
# docs/architecture.md). Vive en saves/ igual que los .json, mismo
# criterio: datos de ejecución, no código fuente (ver saves/.gitignore).
DATABASE_PATH = SAVES_DIR / "whatif.db"

TESTS_DIR = ROOT_DIR / "tests"

DOCS_DIR = ROOT_DIR / "docs"

# ==========================================================
# ASSETS
# ==========================================================
# Reestructurado por categorías (antes era plano: images/, icons/,
# fonts/, sounds/, music/, videos/, todos directamente bajo
# ASSETS_DIR). ICONS_DIR pasa a vivir dentro de IMAGES_DIR;
# SOUNDS_DIR se renombra a EFFECTS_DIR (coincide con la carpeta real
# y con el nombre "effects_dir" que services/audio_service.py ya
# usaba) y se mueve, junto con MUSIC_DIR y la nueva AMBIENCE_DIR,
# dentro de un AUDIO_DIR nuevo. VIDEOS_DIR queda igual — no se pidió
# reestructurarlo.
#
# BACKGROUNDS_DIR, CHARACTER_IMAGES_DIR, UI_IMAGES_DIR y
# ENDING_IMAGES_DIR son nuevos: todavía no los consume ningún
# parámetro de ResourceManager (que hoy solo expone images_dir,
# icons_dir, fonts_dir) — quedan definidos y con su carpeta creada,
# listos para cuando se añadan los getters correspondientes.

IMAGES_DIR = ASSETS_DIR / "images"
BACKGROUNDS_DIR = IMAGES_DIR / "backgrounds"
CHARACTER_IMAGES_DIR = IMAGES_DIR / "characters"  # distinto de DATA_DIR/CHARACTERS_DIR (datos narrativos, no imágenes)
ICONS_DIR = IMAGES_DIR / "icons"
UI_IMAGES_DIR = IMAGES_DIR / "ui"                 # distinto de UI_DIR (el paquete ui/ de Python)
ENDING_IMAGES_DIR = IMAGES_DIR / "endings"        # distinto de DATA_DIR/ENDINGS_DIR (datos narrativos, no imágenes)

AUDIO_DIR = ASSETS_DIR / "audio"
MUSIC_DIR = AUDIO_DIR / "music"
AMBIENCE_DIR = AUDIO_DIR / "ambience"
EFFECTS_DIR = AUDIO_DIR / "effects"               # antes SOUNDS_DIR

FONTS_DIR = ASSETS_DIR / "fonts"
VIDEOS_DIR = ASSETS_DIR / "videos"

# ==========================================================
# DATOS
# ==========================================================

EVENTS_DIR = DATA_DIR / "events"

SCENARIOS_DIR = DATA_DIR / "scenarios"

ENDINGS_DIR = DATA_DIR / "endings"

CHARACTERS_DIR = DATA_DIR / "characters"

ITEMS_DIR = DATA_DIR / "items"

# Añadido junto con managers/achievement_manager.py: catálogo de
# DEFINICIONES de logro (con sus requisitos), distinto de qué logros
# tiene OTORGADOS un jugador concreto (eso lo resuelve
# services/achievement_service.py, sin catálogo a propósito).
ACHIEVEMENTS_DIR = DATA_DIR / "achievements"

LOCALIZATION_DIR = DATA_DIR / "localization"

# ==========================================================
# ARCHIVOS IMPORTANTES
# ==========================================================

CONFIG_FILE = CONFIG_DIR / "settings.py"

GAME_SAVE = SAVES_DIR / "save.json"

AUTOSAVE = SAVES_DIR / "autosave.json"

LOG_FILE = LOGS_DIR / "game.log"

# ==========================================================
# MÉTODOS
# ==========================================================

def create_directories():
    """
    Crea automáticamente todas las carpetas necesarias
    si todavía no existen.
    """
    directories = [
        ASSETS_DIR,
        DATA_DIR,
        ENGINE_DIR,
        UI_DIR,
        MODELS_DIR,
        SERVICES_DIR,
        UTILS_DIR,
        LOGS_DIR,
        SAVES_DIR,
        TESTS_DIR,
        DOCS_DIR,
        IMAGES_DIR,
        BACKGROUNDS_DIR,
        CHARACTER_IMAGES_DIR,
        ICONS_DIR,
        UI_IMAGES_DIR,
        ENDING_IMAGES_DIR,
        AUDIO_DIR,
        MUSIC_DIR,
        AMBIENCE_DIR,
        EFFECTS_DIR,
        FONTS_DIR,
        VIDEOS_DIR,
        EVENTS_DIR,
        SCENARIOS_DIR,
        ENDINGS_DIR,
        CHARACTERS_DIR,
        ITEMS_DIR,
        ACHIEVEMENTS_DIR,
        LOCALIZATION_DIR,
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def project_path(*parts) -> Path:
    """
    Devuelve una ruta relativa al directorio raíz.

    Ejemplo:
        project_path("assets", "images", "logo.png")
    """
    return ROOT_DIR.joinpath(*parts)