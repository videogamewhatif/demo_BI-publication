# Roadmap — What If?

> Refleja el estado real encontrado en las auditorías del proyecto,
> no una lista de deseos. Cada pendiente incluye por qué está
> pendiente (qué le falta exactamente), no solo que "falta hacerlo".

## Hecho

- **Modelos rediseñados**: `Player`, `Story`, `NPC` alineados a los
  documentos de diseño, con enums de dominio en `config/constant.py`.
- **`services/`** (10 archivos): `story_service`, `save_service`,
  `statistics_service`, `localization_service`, `audio_service`,
  `image_service`, `repositories`, `inventory_service`,
  `achievement_service`, más `consequence_service` (nuevo — "el
  único sistema con permiso de escritura sobre el EP" según el GDD).
- **`managers/`** (13 archivos): `resource_manager`, `audio_manager`,
  `scene_manager`, `save_manager`, `input_manager`, `language_manager`,
  `story_manager`, `player_manager`, `time_manager`, más
  `event_manager`, `ending_manager`, `achievement_manager`,
  `inventory_manager` (nuevos — completan los 7 managers de dominio
  que el SDD original anticipaba). `resource_manager` también sumó
  4 getters (`get_background`, `get_character_image`, `get_ui_image`,
  `get_ending_image`) para las carpetas de `assets/images/` que no
  tenían ninguno todavía.
- **`database/`**: backend SQLAlchemy real (Core), 7 repositorios,
  una tabla por tipo de dato — reconstruida desde cero (la anterior
  tenía un import roto y 3 esquemas sin relación entre sí, ver
  `docs/changelog.md`). Infraestructura lista, no es el backend
  activo por defecto todavía.
- **`config/` consolidado**: `settings.py`/`game_config.py`
  reducidos a lo que tiene consumidor real — ver `docs/changelog.md`.
- **`engine/` completamente desbloqueado**: los 9 archivos importan
  Y se instancian sin error (verificado empíricamente). Reescritos
  contra la API real en vez de la que tenían antes (incompatible:
  constructores sin argumentos, métodos que nunca existieron —
  ver `docs/architecture.md` §2 para el detalle). Duplica la
  orquestación que `ui/` ya hace — decisión explícita del usuario,
  no un descuido.
- **Sistema de Edad**: `TimeManager` avanza 1 año por decisión y
  decide fin de vida por salud, vejez, o una probabilidad baja de
  accidente/enfermedad — conectado de punta a punta hasta
  `GameOverScreen` (edad final, causa, capítulo alcanzado → vuelve
  al menú).
- **Sistema de Consecuencias**: `ConsequenceService` conectado en
  `ui/screens/story_panel.py` — elegir una opción con `effects` en su
  JSON cambia estadísticas reales de `Player` de verdad, vía sus
  mutadores auditables. Ver `docs/content_authoring_guide.md` para
  el formato.
- **Sistema de Creación de Personaje**: flujo real de 3 pasos
  (`ui/screens/character_creation/`) — identidad, origen,
  distribución de 20 puntos entre los 10 atributos reales de
  `Player`. "Nueva partida" ya no es un mensaje de "no disponible".
- **Validador de contenido narrativo** (`tools/scenario_validator.py`):
  CLI + test automático en `pytest` para que quien escriba historias
  reales en `data/scenarios/` detecte errores de estructura (incluido
  `effects` mal formado) antes de producción.
- **`ui/`** completa sobre PySide6: ventana principal, sidebar de 6
  secciones, pantalla Historia con capítulo/escena/decisiones
  dinámicos conectados a `StoryManager.choose_option()` real,
  panel de personaje y estadísticas con datos reales, Inventario y
  Logros ahora conectados a datos reales (vacíos casi siempre, pero
  reales), guardado automático tras cada decisión.
- **Estructura de `assets/` y `data/`** completa: todas las
  carpetas que `config/paths.py` define (30 constantes `*_DIR`)
  existen físicamente, verificado una por una.
- **Sistema de temas** (`ui/themes/light.py` / `dark.py`): tema
  claro y oscuro, con repintado en caliente real —
  `ui.theme.set_theme()` reconstruye la ventana completa
  conservando la sesión activa — y selector visible ("Modo oscuro")
  en `SettingsScreen`.
- **`requirements.txt`** limpio, basado en un escaneo real de
  imports, con `pygame-ce` en vez de `pygame` (compatibilidad con
  Python 3.14).
- **`test/` → `tests/`**: carpeta renombrada para que coincida con
  lo que `pytest.ini`/`config/paths.py::TESTS_DIR` ya esperaban.
- **`models/item.py`** creado — desbloqueaba el import de
  `models/inventory.py`.
- **Bugs corregidos en el camino** (ver `changelog.md` para el
  detalle): carpeta `Services/`→`services/`, imports rotos de
  `main.py`, getters de volumen faltantes en `AudioManager`, color
  de tarjeta de decisión congelado a nivel de módulo, `SOUNDS_DIR`
  renombrada a `EFFECTS_DIR`.

## En progreso / parcial

- **`config/` tiene duplicación sin resolver**: `settings.py`,
  `paths.py`, `game_config.py` y `colors.py` se solapan (rutas,
  constantes de stat, colores) con valores a veces distintos entre
  sí, y distintos también de los defaults reales de `Player`. No se
  ha tocado porque excede el alcance de las tareas pedidas hasta
  ahora (diseño de UI, dependencias, temas) — consolidarlo es una
  tarea propia, con decisiones de diseño que conviene confirmar
  antes (¿cuál de los 3-4 valores en conflicto es el correcto?).
- **`pytest.ini` apunta a `tests/` pero la carpeta real es `test/`**
  (singular) — con esto, `pytest` probablemente reporta "0 tests"
  en vez de fallar. Detectado, no corregido (fuera del alcance de
  "solo requirements.txt" cuando se encontró).

## Pendiente — y por qué

### ~~Sistema de Consecuencias~~ ✅ hecho
`services/consequence_service.py::ConsequenceService`, conectado a
`ui/screens/story_panel.py`. Alcance actual: 10 atributos +
`net_worth` vía delta simple (`{atributo: delta}` en `effects` de
cada opción); `annual_income`/`debt` quedan fuera por tener verbos
distintos a un delta — ver el docstring del servicio si hace falta
extenderlo.

### ~~Sistema de Creación de Personaje~~ ✅ hecho
No existe ningún `PlayerManager` ni flujo que produzca un `Player`
jugable desde cero. `MainMenuScreen` lo señala explícitamente: el
botón "Nueva partida" muestra un mensaje honesto en vez de simular
esto. `GameScene.CHARACTER_CREATION` ya existe como valor de enum,
esperando una pantalla.

### Contenido narrativo real
`data/scenarios/` solo tiene `example_ui_fixture.json`, marcado como
fixture técnico de desarrollo (texto tipo "[PLACEHOLDER]", no
narrativa real) — creado únicamente para poder ver la pantalla
Historia funcionando de punta a punta. Escribir historias reales
sigue siendo trabajo de diseño narrativo, no de código — pero ya
existe la herramienta para hacerlo con confianza:
`tools/scenario_validator.py` valida la estructura de cualquier
archivo antes de que llegue a producción (referencias rotas, finales
sin salida, escenas muertas), con CLI
(`python tools/validate_scenario.py`) y un test que corre
automáticamente en cada `pytest` (`tests/test_scenario_content.py`).
La guía completa del esquema está en `docs/content_authoring_guide.md`.

### ~~`engine/` — construir los managers de dominio que le faltan~~ ✅ hecho
Los 4 managers que faltaban (`EventManager`, `EndingManager`,
`AchievementManager`, `InventoryManager`) se construyeron, y los 9
archivos de `engine/` se reescribieron contra la API real — no solo
importan, se instancian y se usan sin error (verificado
empíricamente). El "inventar mecánica de juego sin que esté
definida" que bloqueaba esto se resolvió con alcance honesto:
catálogos reales pero vacíos (`data/events/`, `data/endings/`,
`data/achievements/`), sin inventar contenido — ver
`docs/changelog.md` para el detalle completo, incluido un bug real
que se encontró y corrigió en `SaveManager.save_now()`.

### `services/inventory_service.py` y `services/achievement_service.py` ✅ hecho
`models/inventory.py` y `models/achievement.py` existían, pero nada
resolvía "los objetos/logros del jugador X" — ni un repositorio, ni
un service. Ya construidos (mismo patrón que
`statistics_service.py`: un documento por `player_id`) y conectados:
`ui/screens/inventory_screen.py`/`achievements_screen.py` reciben
datos reales de `GameplayScreen` en vez de quedarse siempre vacías
por diseño. Van a seguir mostrando su estado vacío casi siempre,
porque nada llama todavía a `add_item()`/`grant_achievement()` — eso
depende del Sistema de Consecuencias/eventos, no de estos dos
services.

`models/item.py` (bloqueaba el import de `models/inventory.py`) se
creó como parte de esta pieza, mismo estilo que
`achievement.py`/`event.py`.

### ~~Consolidación de `database/` con SQLAlchemy~~ ✅ hecho, y activado
`database/` reconstruida con un backend SQLAlchemy real (Core) — una
tabla por tipo de dato (`players`, `story_progress`, `inventory_items`,
`player_achievements`, `unlocked_endings`, `account_statistics`,
`save_slots`). **Activado** para `SaveService`/`StatisticsService`/
`AchievementService`/`InventoryService` vía `database/adapters.py`
(puente `KeyValueRepository` → repositorios tipados) — `main.py` ya
construye estos 4 con el backend SQLite real. `StoryService` y
`EndingManager` siguen en JSON (fuera del alcance pedido). Ver
`docs/architecture.md` §5 para el detalle y las limitaciones conocidas
(NPCs sin tabla, guardado no es una foto congelada).

### ~~`config/` consolidado~~ ✅ hecho
`settings.py` y `game_config.py` reducidos a lo que de verdad tiene
consumidor (7 y 2 símbolos respectivamente, de ~90 que tenían entre
los dos) — ver `docs/changelog.md` para el detalle completo de qué
se borró y por qué.

### ~~Repintado en caliente de temas~~ ✅ hecho
`ui.theme.set_theme()`/`toggle_theme()` ahora notifican a quien se
suscriba con `on_theme_changed()`. `ui/windows/main_window.py` es el
único suscriptor: al cambiar el tema, reaplica el QSS global y
reconstruye `MainMenuScreen`/`GameplayScreen` desde cero, conservando
la sesión activa (`Player`/`Story`) y qué pantalla estaba visible.
Limitación conocida y aceptada: la sub-sección interna de
`GameplayScreen` (Historia/Personaje/...) no se conserva, siempre
vuelve a "Historia" tras el cambio.

### ~~Selector de tema visible en `SettingsScreen`~~ ✅ hecho
Checkbox "Modo oscuro" en una nueva tarjeta "APARIENCIA", arriba de
Audio. Nace marcado o no según el tema activo real; al tocarlo llama
a `ui.theme.set_theme()`, que dispara el repintado en caliente de
arriba (la propia pantalla de Configuración se reconstruye un
instante después, checkbox incluido).

## Orden sugerido (si hay que priorizar)

1. ~~Sistema de Consecuencias~~ — ✅ hecho.
2. ~~Sistema de Creación de Personaje~~ — ✅ hecho.
3. **Contenido narrativo real** (al menos una historia completa) —
   es el siguiente paso real ahora. Herramienta de validación lista
   (✅, incluida la validación de `effects`); falta que el equipo de
   diseño escriba la historia en sí.
4. ~~`inventory_service` / `achievement_service`~~ — ✅ hecho.
5. ~~Resto de managers de dominio + desbloquear `engine/`~~ — ✅
   hecho (los 7 managers de dominio del SDD original existen; los 9
   archivos de `engine/` funcionan de verdad).
6. ~~Deuda técnica: `config/`, `database/`/SQLAlchemy, `ResourceManager`~~
   — ✅ hecho. Con esto, lo único que queda de todo el roadmap
   original es el **contenido narrativo real** (punto 3), que le
   toca al equipo de diseño, no al código.
