"""
ui/
===

Capa de presentación de What If?, construida sobre PySide6
(`requirements.txt`, sección "USER INTERFACE"). No existía en el
proyecto hasta ahora: `main.py`, `config/paths.py` (`UI_DIR`) y
varios docstrings de `managers/` y `services/` ya la referenciaban
como "la futura capa ui/ (todavía no existe)".

Regla de dependencia (VITA_Game_Design_Document.md §26 — "Interfaz"):
la UI es puramente consumidora. Nunca modifica el Estado de
Personaje (`models.player.Player`) directamente, nunca escribe
contenido narrativo, y nunca reimplementa reglas de negocio. Solo
lee snapshots de `services/` y `managers/` y les reenvía la
intención del jugador (elegir una opción, guardar, cambiar de
pantalla). Los mutadores de `Player` (`modify_health`, etc.) están
reservados al futuro Sistema de Consecuencias — la UI no los llama
jamás.

Submódulos:
    - theme.py: paleta, tipografía y hoja de estilos (QSS)
      centralizadas, derivadas de `config/colors.py` (declarado ahí
      como fuente única de colores de interfaz).
    - widgets/: componentes reutilizables sin conocimiento de
      pantalla concreta (Card, StatBar, SidebarButton, etc.).
    - screens/: pantallas/paneles con conocimiento de qué datos
      mostrar (Historia, Personaje, Estadísticas, Inventario,
      Logros, Configuración).
    - windows/: la ventana de nivel de sistema operativo
      (`MainWindow`) que aloja las escenas de `managers.scene_manager`.

Autor: Korlo (capa UI añadida en esta sesión)
"""
