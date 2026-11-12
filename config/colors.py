"""
colors.py
=========

Paleta oficial de colores para What If?

Todos los colores de la interfaz deben importarse desde aquí.

Autor: Korlo
"""

# ==========================================================
# COLORES BASE
# ==========================================================

WHITE = "#FFFFFF"
BLACK = "#000000"

# Escala de grises
GRAY_50 = "#FAFAFA"
GRAY_100 = "#F5F5F5"
GRAY_200 = "#EEEEEE"
GRAY_300 = "#E0E0E0"
GRAY_400 = "#BDBDBD"
GRAY_500 = "#9E9E9E"
GRAY_600 = "#757575"
GRAY_700 = "#616161"
GRAY_800 = "#424242"
GRAY_900 = "#212121"

# ==========================================================
# IDENTIDAD VISUAL
# ==========================================================

PRIMARY = "#2563EB"       # Azul principal
PRIMARY_DARK = "#1D4ED8"
PRIMARY_LIGHT = "#60A5FA"

SECONDARY = "#0F172A"     # Azul oscuro
ACCENT = "#F59E0B"        # Dorado

# ==========================================================
# FONDOS
# ==========================================================

BACKGROUND = "#F8FAFC"
SURFACE = "#FFFFFF"
CARD = "#FFFFFF"

SIDEBAR = "#F1F5F9"

# ==========================================================
# TEXTO
# ==========================================================

TEXT_PRIMARY = "#111827"
TEXT_SECONDARY = "#6B7280"
TEXT_DISABLED = "#9CA3AF"
TEXT_WHITE = "#FFFFFF"

# ==========================================================
# BOTONES
# ==========================================================

BUTTON_PRIMARY = PRIMARY
BUTTON_PRIMARY_HOVER = PRIMARY_DARK

BUTTON_SECONDARY = "#CBD5E1"
BUTTON_SECONDARY_HOVER = "#94A3B8"

BUTTON_SUCCESS = "#16A34A"
BUTTON_SUCCESS_HOVER = "#15803D"

BUTTON_DANGER = "#DC2626"
BUTTON_DANGER_HOVER = "#B91C1C"

# ==========================================================
# ESTADOS
# ==========================================================

SUCCESS = "#22C55E"
WARNING = "#FACC15"
ERROR = "#EF4444"
INFO = "#3B82F6"

# ==========================================================
# BARRAS DE ESTADÍSTICAS
# ==========================================================

HEALTH = "#EF4444"
MONEY = "#F59E0B"
HAPPINESS = "#FBBF24"
REPUTATION = "#8B5CF6"
KNOWLEDGE = "#06B6D4"
EXPERIENCE = "#10B981"

# ==========================================================
# ATRIBUTOS DE PERSONAJE (models.player.Player)
# ==========================================================
# Añadido junto con ui/: HEALTH, MONEY, HAPPINESS, REPUTATION,
# KNOWLEDGE y EXPERIENCE (arriba) ya cubrían el enum `Stat` de
# config/constant.py, pero no todos los atributos reales que
# `Player` expone hoy (intelligence, discipline, creativity,
# charisma, empathy, appearance, stress). Se añaden aquí en vez de
# reutilizar los existentes para que cada barra de stat en el panel
# de personaje sea visualmente distinguible.

INTELLIGENCE = "#6366F1"
DISCIPLINE = "#0EA5E9"
CREATIVITY = "#EC4899"
CHARISMA = "#F59E0B"
EMPATHY = "#F43F5E"
APPEARANCE = "#14B8A6"
STRESS = "#EF4444"

# ==========================================================
# BORDES
# ==========================================================

BORDER_LIGHT = "#E5E7EB"
BORDER = "#CBD5E1"
BORDER_DARK = "#64748B"

# ==========================================================
# INPUTS
# ==========================================================

INPUT_BACKGROUND = WHITE
INPUT_BORDER = "#D1D5DB"
INPUT_FOCUS = PRIMARY

# ==========================================================
# MENÚ
# ==========================================================

MENU_BACKGROUND = "#FFFFFF"
MENU_HOVER = "#EFF6FF"
MENU_SELECTED = PRIMARY

# ==========================================================
# DIÁLOGOS
# ==========================================================

DIALOG_BACKGROUND = WHITE
OVERLAY = "#00000055"

# ==========================================================
# EVENTOS
# ==========================================================

EVENT_POSITIVE = "#DCFCE7"
EVENT_NEGATIVE = "#FEE2E2"
EVENT_NEUTRAL = "#F3F4F6"
EVENT_SPECIAL = "#EDE9FE"

# ==========================================================
# RAREZA (para futuros eventos o cartas)
# ==========================================================

COMMON = "#9CA3AF"
UNCOMMON = "#22C55E"
RARE = "#3B82F6"
EPIC = "#A855F7"
LEGENDARY = "#F59E0B"

# ==========================================================
# MODO OSCURO
# ==========================================================
# Añadido junto con ui/themes/dark.py. Solo cubre los tokens
# ESTRUCTURALES que de verdad cambian entre modo claro y oscuro
# (fondos, superficies, texto, bordes, acento primario/morado).
# Deliberadamente NO se duplican aquí SUCCESS/WARNING/ERROR/INFO ni
# los colores de estadísticas (HEALTH, REPUTATION, INTELLIGENCE...):
# esos son colores semánticos/categóricos — la salud siempre es roja,
# la reputación siempre morada — y deben significar lo mismo sin
# importar el tema, así que ui/themes/light.py y ui/themes/dark.py
# los reutilizan tal cual desde las secciones de arriba.
#
# Reutiliza valores ya existentes en este archivo donde tiene
# sentido (SECONDARY, PRIMARY_LIGHT, INFO, TEXT_PRIMARY, SIDEBAR,
# BORDER_DARK) en vez de inventar tonos nuevos sin necesidad.

DARK_BACKGROUND = SECONDARY        # "#0F172A" — ya existía como "Azul oscuro"
DARK_SURFACE = "#1E293B"
DARK_CARD = "#1E293B"
DARK_SIDEBAR = TEXT_PRIMARY        # "#111827" — reutilizado: más oscuro que DARK_BACKGROUND, da profundidad a la barra lateral

DARK_TEXT_PRIMARY = SIDEBAR        # "#F1F5F9" — reutilizado como texto claro sobre fondo oscuro
DARK_TEXT_SECONDARY = "#94A3B8"
DARK_TEXT_DISABLED = BORDER_DARK   # "#64748B"
DARK_TEXT_WHITE = WHITE

DARK_BORDER_LIGHT = "#334155"
DARK_BORDER = "#475569"

DARK_ACCENT_PRIMARY = PRIMARY_LIGHT        # "#60A5FA" — más brillante que PRIMARY, lee mejor sobre fondo oscuro
DARK_ACCENT_PRIMARY_HOVER = INFO           # "#3B82F6"
DARK_ACCENT_PRIMARY_LIGHT = "#93C5FD"

DARK_ACCENT_PURPLE = "#A78BFA"             # más brillante que REPUTATION para el mismo motivo
DARK_ACCENT_PURPLE_SOFT = "#312E5C"        # equivalente oscuro de EVENT_SPECIAL (fondo de nav activa)

DARK_INPUT_BACKGROUND = DARK_SURFACE
DARK_INPUT_BORDER = DARK_BORDER