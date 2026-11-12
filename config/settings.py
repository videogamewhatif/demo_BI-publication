"""
config/settings.py
====================

Qué hace:
    Metadatos de aplicación y de ventana — nombre/versión del juego,
    título y dimensiones de la ventana principal. Nada más.

Por qué este archivo se redujo tanto (léase antes de añadir algo aquí):
    Antes de la sesión de consolidación de `config/`, este archivo
    tenía ~50 constantes: rutas (duplicadas y con una estructura más
    vieja e incompatible con `config/paths.py`), colores (duplicados
    y con valores distintos a `config/colors.py`), tipografía,
    audio, IA, debug, y una sección "JUGABILIDAD" con valores
    iniciales de estadísticas que ni se usaban en ningún lado NI
    coincidían con los defaults reales de `models.player.Player`
    (`INITIAL_HAPPINESS=100` aquí vs `happiness: int = 70` en
    `Player`). Se verificó con grep, no se asumió: de todo ese
    archivo, `main.py` y `ui/windows/main_window.py` solo leían
    estos 7 símbolos. Todo lo demás se borró en vez de
    "consolidarse" — no había ningún valor en juego que rescatar,
    porque nada lo usaba.

    Antes de añadir algo nuevo aquí: comprobá primero si ya existe
    en `config/paths.py` (rutas), `config/colors.py` (colores),
    `config/constant.py` (enums y límites de estadísticas) o
    `config/game_config.py` (parámetros de balance) — la lección de
    esta sesión es exactamente no repetir un valor en dos archivos.

Autor: Korlo (consolidado en la sesión de deuda técnica)
"""

GAME_NAME = "What If?"
GAME_VERSION = "0.1.0"

WINDOW_TITLE = f"{GAME_NAME} v{GAME_VERSION}"

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

MIN_WIDTH = 1000
MIN_HEIGHT = 600
