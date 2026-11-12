# Changelog — What If?

> El proyecto no tiene todavía versionado formal (sin tags, sin
> paquete publicado), así que las entradas se agrupan por entrega de
> trabajo, no por número de versión. Orden: más reciente primero.
> Cada entrada lista solo cambios reales, verificados contra el
> código — no un resumen de intenciones.

---

## [Sin versionar] — Contenido narrativo real, managers de dominio conectados, dependencias reales verificadas, `database/` activado

### Contenido narrativo real
- `data/scenarios/primer_empleo.json`: primera historia real del
  proyecto ("El primer empleo") — 16 escenas, 4 ramas desde la
  graduación (trabajo estable / universidad / emprendimiento / año
  sabático), 11 finales únicos con `ending_id` propio, `effects` en
  cada opción usando solo claves válidas de `ConsequenceService`.
  Validado con `tools/validate_scenario.py` (0 errores, 0 warnings)
  y `tests/test_scenario_content.py`. `example_ui_fixture.json` se
  deja intacto (lo sigue usando `ui/dev_preview.py`).

### Managers de dominio conectados al gameplay real
`main.py` no instanciaba `EventManager`/`EndingManager`/
`AchievementManager`/`InventoryManager` — existían como clases, sin
ningún objeto real en la app. Decisiones de cuándo se disparan,
tomadas explícitamente por el usuario:
- `AchievementManager.check_all()`: al terminar la vida (no tras
  cada decisión) — `ui/windows/main_window.py::_handle_life_ended()`.
- `EndingManager.determine_ending()`: también al terminar la vida,
  mismo método; el resultado se muestra en `GameOverScreen`
  (`show_result()` acepta ahora `ending_title`).
- `EventManager`: un evento aleatorio del catálogo por año, junto al
  avance de `TimeManager` — `ui/screens/story_panel.py::_trigger_random_event_if_any()`.
- `InventoryManager.use_item()`: botón "Usar" nuevo en
  `ui/screens/inventory_screen.py`, conectado en
  `ui/screens/gameplay_screen.py::_handle_use_item()`.

Los 4 catálogos (`data/events/`, `data/endings/`,
`data/achievements/`, `data/items/`) siguen vacíos — sin cambio de
comportamiento visible en el juego real todavía, verificado con
catálogos temporales reales en pruebas manuales.

### Verificación con dependencias reales (no stubs)
`pip install -r requirements.txt` real (PySide6, pygame-ce,
SQLAlchemy, pytest, todas las demás) — hasta ahora nunca se había
corrido `tests/test_database.py` contra SQLAlchemy real en este
entorno. Surgieron 2 bugs reales, invisibles con el stub:
`database/repositories.py::remove_item()`/`unlock_achievement()`
usaban `.first()` sin `.mappings()` y accedían `row["id"]` — con
SQLAlchemy 2.x real, `Row` no admite índice por string ahí.
Corregido (2 líneas). `python main.py` real confirmado arrancando
sin excepciones.

### Activación de `database/` como backend real
Decisión explícita del usuario: activar los 4 adaptadores
(Save/Stats/Achievements/Inventory) de una vez, no de a uno.
- `database/adapters.py` (nuevo): `SQLStatisticsRepository`,
  `SQLAchievementRepository`, `SQLInventoryRepository`,
  `SQLSaveRepository` — implementan `KeyValueRepository`
  delegando en los repositorios tipados de `database/repositories.py`.
  `set()` = borrar+reinsertar (los 4 services ya seguían el patrón
  "leo el blob entero → lo muto → lo reescribo entero", nunca piden
  actualización parcial). Limitaciones documentadas ahí mismo: NPCs
  sin tabla, capacidad de inventario sin columna, guardado no es una
  foto congelada (ya documentado en `architecture.md`).
- `database/repositories.py`: 2 métodos nuevos, mismo patrón que los
  existentes — `AchievementRepository.clear_achievements()`,
  `SaveSlotRepository.get_slot()`.
- `database/models.py`: 2 bugs reales corregidos, encontrados al
  probar el adaptador de guardado de punta a punta —
  `players.city` y `story_progress.story_content_id` eran
  `nullable=False` pero sus dataclasses los declaran
  `Optional[...] = None`; cualquier jugador/historia sin esos datos
  rompía el guardado real.
- `main.py`: crea el engine real (`create_database_engine()` +
  `create_all()`) y lo usa para los 4 services activados.
  `StoryService`/`EndingManager` quedan en JSON (no se pidieron).
- `docs/architecture.md`, `docs/roadmap.md`, `database/__init__.py`:
  actualizados — ya no dicen "decisión pendiente, no tomada" ni que
  `database/repositories.py` implementa `KeyValueRepository`
  directamente (era falso; por eso hizo falta `adapters.py`).

Verificado: `pytest` completo → 108 passed. `python main.py` real
crea `saves/whatif.db` con las 7 tablas y arranca sin excepciones.



### Añadido
- `managers/resource_manager.py`: 4 getters nuevos —
  `get_background()`, `get_character_image()`, `get_ui_image()`,
  `get_ending_image()` — para las 4 carpetas de `assets/images/`
  que existían desde la sesión de assets sin ningún método que las
  leyera. Mismo patrón exacto que `get_image()`/`get_icon()`, sin
  mecanismo nuevo.
- `database/` reconstruida desde cero (la anterior a esta sesión
  estaba rota: `migrations/migration_manager.py` importaba
  `database.database`, que no existe; 3 esquemas SQL sin relación
  entre sí; `users_database.py` abría una conexión SQLite al
  importar el módulo, contra un archivo que ni coincidía con el que
  había en disco — retirada por completo, decisión explícita del
  usuario). La reconstrucción usa **SQLAlchemy Core** (`Table`/
  `Column`/`select`/`insert`/`update`/`delete`), no el ORM
  declarativo — decisión de diseño, no una limitación: con Core,
  cada método de `database/repositories.py` controla exactamente
  qué SQL se ejecuta, sin sesión con estado implícito ni ambigüedad
  sobre cuándo es un `INSERT` vs. un `UPDATE` — mismo criterio de
  "explícito antes que mágico" que ya regía el resto del proyecto
  (mutadores de `Player`, `to_dict()`/`from_dict()` de cada
  dataclass). 7 tablas reales (`players`, `story_progress`,
  `inventory_items`, `player_achievements`, `unlocked_endings`,
  `account_statistics`, `save_slots`), 7 repositorios con métodos
  tipados sobre las dataclasses reales (`PlayerRepository`,
  `StoryRepository`, `InventoryRepository`, `AchievementRepository`,
  `EndingRepository`, `StatisticsRepository`, `SaveSlotRepository`)
  — decisión explícita del usuario ("relacional completo") sobre la
  alternativa más simple (clave-valor genérica). `main.py` sigue
  usando los repositorios JSON de `services/repositories.py` por
  defecto — no se forzó el cambio de backend sin que se pidiera.
- `SQLAlchemy>=2.0.51,<3.0.0` en `requirements.txt`.
- `tests/test_database.py`: 12 pruebas de ida y vuelta completas
  (guardar un `Player`/`Story`/`Item`/`Achievement` real y
  recuperarlo, verificando cada campo — incluidas las listas que se
  guardan en tablas relacionadas aparte) contra un SQLite temporal
  real.

### Consolidación de `config/` (el A.4 pendiente desde el inicio de la sesión)
Auditado con grep, no asumido: de ~50 constantes en
`config/settings.py` solo 7 tenían consumidor real; de ~40 en
`config/game_config.py`, solo 1 (`RANDOM_DEATH_CHANCE_PER_YEAR`). El
resto eran duplicados muertos de `config/paths.py`/`config/colors.py`/
`config/constant.py` con valores distintos (`PRIMARY_COLOR="#1E88E5"`
vs `colors.py::PRIMARY="#2563EB"`), o contradecían los defaults
reales de `Player` (`INITIAL_HAPPINESS=100` vs `happiness: int = 70`).

- `config/settings.py`: reducido a los 7 símbolos reales
  (`GAME_NAME`, `GAME_VERSION`, `WINDOW_TITLE`, `WINDOW_WIDTH`,
  `WINDOW_HEIGHT`, `MIN_WIDTH`, `MIN_HEIGHT`).
- `config/game_config.py`: reducido a `RANDOM_DEATH_CHANCE_PER_YEAR`
  más `SMALL_IMPACT`/`MEDIUM_IMPACT`/`LARGE_IMPACT`/`EXTREME_IMPACT`
  (conservados por decisión explícita del usuario, como referencia
  para quien escriba `effects` — ahora documentados en
  `docs/content_authoring_guide.md`). El sistema de dificultad
  completo (`EASY`/`NORMAL`/`HARD`/`NIGHTMARE`) se borró por decisión
  explícita: sin ningún consumidor real.

### Verificado
Construí un stub de SQLAlchemy Core respaldado por `sqlite3` real
(no está instalado en este entorno — la red bloqueó `pypi.org` al
intentar instalarlo, pese a estar en la lista de dominios
permitidos) — traduce `Table`/`Column`/`select`/`insert`/`update`/
`delete` a SQL real ejecutado contra un archivo SQLite real, así que
si una prueba pasa, el SQL generado es válido de verdad, no solo "la
lógica de Python no truena". Las 12 pruebas de `tests/test_database.py`
pasaron contra este stub en el primer intento (12/12), más los 59
smoke tests de sesiones anteriores como regresión completa, sin
ningún fallo. Aun así: correr `pip install -r requirements.txt` con
SQLAlchemy real y confirmar antes de usar `database/` para algo
importante — un stub, por cuidadoso que sea, no reemplaza probar
contra la librería real.

---



### Eliminado
- `config/settings.py`: reducido de ~50 constantes a las 7 que
  `main.py`/`ui/windows/main_window.py` usan de verdad (metadatos de
  app/ventana). Se borraron rutas duplicadas y con estructura vieja
  (superseded por `config/paths.py`), colores duplicados con
  valores distintos (superseded por `config/colors.py`), tipografía,
  audio/debug/IA sin consumidor, y una sección "JUGABILIDAD" sin
  consumidor que además contradecía los defaults reales de `Player`.
- `config/game_config.py`: reducido de ~40 constantes a
  `RANDOM_DEATH_CHANCE_PER_YEAR` (con consumidor real) y
  `SMALL_IMPACT`/`MEDIUM_IMPACT`/`LARGE_IMPACT`/`EXTREME_IMPACT`
  (conservados por decisión explícita, como valores de referencia
  para quien escriba `effects` — ahora documentados en
  `docs/content_authoring_guide.md`). Se borró el sistema de
  dificultad completo (`EASY`/`NORMAL`/`HARD`/`NIGHTMARE`, por
  decisión explícita: sin consumidor) y duplicados muertos de
  `MIN_STAT`/`MAX_STAT`/`MIN_MONEY`/`MAX_MONEY` (ya viven en
  `config/constant.py`, que es de donde `Player` los importa de
  verdad).
- Carpeta `database/` anterior: import roto
  (`from database.database import db`, ese módulo nunca existió), 3
  esquemas de base de datos sin relación entre sí (`users_schema.sql`
  con tablas de cuentas, `migration_001` con una tabla `players`
  mínima sin relación con el `Player` real, `migration_002`/`003`
  con tablas sueltas), y un antipatrón (`user_db = UserDatabase()` a
  nivel de módulo, abre una conexión SQLite como efecto secundario
  de solo importar el archivo). Cero conexión con el resto del
  proyecto, confirmado con grep antes de borrar — decisión explícita
  del usuario.

---

## [Sin versionar] — Desbloqueo completo de `engine/`

### Contexto (por qué esta entrega es más grande de lo que el roadmap anticipaba)
Auditar los 6 archivos de `engine/` que todavía fallaban reveló que
el problema nunca fue solo "faltan managers": los 9 archivos estaban
escritos contra una API completamente distinta e incompatible con la
real (constructores sin argumentos que implican un "jugador actual"
único e implícito, métodos como `get_stat()`/`modify_stat()` que
nunca existieron en ningún `PlayerManager` real). Se confirmó
empíricamente: `GameEngine()` y `StoryEngine()` — los únicos 2 que
"importaban" antes de esta entrega — fallaban igual al instanciarse
(`TypeError: StoryManager.__init__() missing 1 required positional
argument`). Se le presentó esto al usuario, que eligió explícitamente
reescribir los 9 archivos contra la API real, aceptando que duplica
la orquestación que `ui/` ya hace.

### Añadido
- `managers/event_manager.py`: `EventManager` — catálogo de eventos
  (`data/events/`) + disparo con requisitos + efectos vía
  `ConsequenceService`. Selección aleatoria ponderada vía
  `utils.random_utils.weighted_choice` (ya existía, sin consumidor
  hasta ahora).
- `managers/ending_manager.py`: `EndingManager` — catálogo de
  finales de vida (`data/endings/`, distinto del `ending_id` de una
  `Story` individual) + desbloqueo por jugador.
- `managers/achievement_manager.py`: `AchievementManager` — envuelve
  `AchievementService` (no lo duplica) y añade catálogo de
  requisitos (`data/achievements/`, carpeta nueva); reporta a
  `StatisticsService.record_achievement_unlocked()` en cada
  desbloqueo real.
- `managers/inventory_manager.py`: `InventoryManager` — envuelve
  `InventoryService` (no lo duplica) y añade catálogo de
  definiciones de objeto (`data/items/`) para poder "usar" uno con
  efecto vía `ConsequenceService`.
- `config/paths.py`: `ACHIEVEMENTS_DIR` (aditivo).
- Los 9 archivos de `engine/` reescritos contra la API real:
  `story_engine.py` y `save_engine.py` sobreviven como capas finas
  (decisiones que `tests/test_engine.py` dejaba pendientes, ahora
  resueltas); `decision_engine.py` corregido (ya no es una copia de
  `story_engine.py`, ahora formaliza el objeto "decision_tomada" que
  describe el GDD §4); `game_engine.py`, `time_engine.py`,
  `event_engine.py`, `ending_engine.py`, `achievement_engine.py`,
  `inventory_engine.py` reescritos desde cero.
- `tests/test_engine.py` reescrito por completo: los 9
  `@pytest.mark.skip` (con razones ya desactualizadas) se
  reemplazaron por 11 pruebas reales, todas verificadas.

### Corregido
- `managers/save_manager.py::save_now()` estaba **mal documentado**
  en `docs/api.md` desde la sesión del Sistema de Consecuencias — la
  firma real es `(save_id, player, stories, npcs)`, no
  `(player, stories, save_id)`. Nadie lo había notado porque `ui/`
  solo usa `quick_save()`, nunca `save_now()` directamente. Se
  encontró al ejercitar `GameEngine.save_game()` de verdad.

### Verificado
Los 9 archivos de `engine/` importan Y se instancian sin error
(verificado empíricamente, no asumido). 11 pruebas nuevas de
`tests/test_engine.py` + 2 de `tests/test_scenario_content.py`, más
los 59 smoke tests de sesiones anteriores como regresión completa
— todo en verde.

---

## [Sin versionar] — Sistema de Edad (ciclo de vida del personaje)

### Añadido
- `managers/time_manager.py`: `TimeManager` — tercer manager de
  dominio, el "futuro Sistema de Edad" que
  `Player.advance_age()` ya mencionaba en su propio docstring.
  `advance_time(player)` avanza 1 año por decisión (decisión
  explícita: sin que el contenido lo controle). `check_life_status(player)`
  comprueba, en orden, 3 motivos de fin de vida: salud (`is_alive`
  ya existía), vejez (`age >= life_expectancy`), y una probabilidad
  baja pero no nula de accidente/enfermedad repentina en cada
  decisión (pedido explícitamente por el usuario).
- `config/game_config.py`: `RANDOM_DEATH_CHANCE_PER_YEAR = 0.01` —
  misma magnitud que `LEGENDARY_EVENT_CHANCE`, no un valor inventado
  sin relación con el resto de probabilidades del juego.
- `ui/screens/game_over_screen.py`: `GameOverScreen` — edad final,
  causa (traducida desde la categoría técnica que devuelve
  `TimeManager`), capítulo alcanzado, botón "Volver al menú". Sin
  "Álbum de Vida": ese concepto existe en el Vision Document pero no
  hay ningún pipeline de `memory_moments` construido que lo alimente.

### Cambiado
- `ui/screens/story_panel.py`: tras aplicar `effects` (si los hay),
  ahora también avanza el tiempo y comprueba `check_life_status()`
  antes de llamar a `StoryManager.choose_option()`. Si la vida
  terminó, NO avanza la historia — emite `life_ended` en su lugar.
  Sin `TimeManager` (`None`), el comportamiento es idéntico al de
  antes — compatibilidad hacia atrás verificada con test explícito.
- `ui/screens/gameplay_screen.py`: recibe `time_manager`; maneja
  `life_ended` guardando el estado final y reenviando la señal hacia
  `MainWindow`.
- `ui/windows/main_window.py`: añade `GameOverScreen` como cuarta
  pantalla del stack; conecta `gameplay_screen.life_ended` →
  mostrar resultado + cambiar a `GameScene.GAME_OVER`; "Volver al
  menú" reutiliza el mismo flujo que ya existía para salir de
  Gameplay.
- `main.py`: instancia y propaga `TimeManager`.

---

## [Sin versionar] — Sistema de Consecuencias

### Añadido
- `services/consequence_service.py`: `ConsequenceService`, "el
  único sistema con permiso de escritura sobre el EP" (GDD §5) —
  no existía ni como esqueleto. `apply_effects(player, effects, reason)`
  aplica un diccionario `{atributo: delta}` usando los mutadores
  auditables reales de `Player` (`modify_health()`, etc.), nunca
  escritura directa. Alcance a propósito: los 10 atributos
  0-100/-100..100 más `net_worth` (todos comparten la forma
  `modify_x(amount, reason)`) — `annual_income`/`debt` quedan fuera
  por tener verbos distintos (set/add/reduce), no un delta simple.
- `data/scenarios/*.json`: nuevo campo opcional `effects` en cada
  opción — `{"label": ..., "next_scene": ..., "effects": {"discipline": 5}}`.
  Documentado en `docs/content_authoring_guide.md`.
- `tools/scenario_validator.py`: valida `effects` (claves conocidas,
  valores numéricos) antes de que el contenido llegue a producción.
- `data/scenarios/example_ui_fixture.json`: sus 3 opciones ahora
  traen `effects` de ejemplo, para poder probar el sistema completo
  de punta a punta con "Vista previa de interfaz".

### Cambiado
- `ui/screens/story_panel.py`: recibe `consequence_service` opcional;
  antes de avanzar la historia, si la opción elegida trae `effects`
  y hay `Player`+`ConsequenceService` disponibles, los aplica y llama
  a `player.record_decision()`. Sin `ConsequenceService` (`None`), el
  comportamiento es idéntico al de antes — compatibilidad hacia atrás
  verificada con test explícito.
- `ui/screens/gameplay_screen.py`: pasa `consequence_service` a
  `StoryPanel`; tras cada decisión ahora también refresca el panel
  de personaje compacto y la ficha completa (antes solo refrescaba
  el historial), porque las estadísticas SÍ pueden haber cambiado.
- `ui/windows/main_window.py`, `main.py`: instancian y propagan
  `ConsequenceService`.

---

## [Sin versionar] — Validador de contenido narrativo

### Añadido
- `tools/scenario_validator.py`: valida un archivo de
  `data/scenarios/` contra el esquema real de `StoryService` — más
  allá de lo que `StoryService._validate_content()` ya comprueba en
  producción (solo 3 claves obligatorias), detecta `next_scene` roto
  o faltante, escenas sin salida, contenido inalcanzable, y si algún
  final es alcanzable desde `start_scene`.
- `tools/validate_scenario.py`: CLI (`python tools/validate_scenario.py
  archivo.json` o `--all`), código de salida 1 si hay errores.
- `tests/test_scenario_content.py`: valida automáticamente TODOS los
  `.json` de `data/scenarios/` en cada corrida de `pytest`
  (parametrizado, un caso de prueba por archivo).
- `docs/content_authoring_guide.md`: esquema documentado con
  ejemplos marcados como plantilla — no contenido narrativo real.

No se escribió ningún contenido narrativo real en esta entrega, a
propósito — sigue siendo trabajo del equipo de diseño.

---

## [Sin versionar] — Sistema de Creación de Personaje

### Añadido
- `managers/player_manager.py`: `PlayerManager` — tercer manager de
  dominio. Crea, persiste y recupera `Player`; calcula `birth_year`
  desde la edad de inicio; `validate_distribution()` valida la
  distribución de 20 puntos entre los 10 atributos reales antes de
  crear el personaje (rangos por atributo, total máximo, sin
  atributos desconocidos).
- `ui/screens/character_creation/`: flujo de 3 pasos —
  `identity_step.py` (nombre, apellido, género),
  `origin_step.py` (edad de inicio, país, ciudad, origen
  socioeconómico real de `SocioeconomicLevel`),
  `attributes_step.py` (distribuidor de puntos con feedback en
  tiempo real), orquestados por `character_creation_screen.py`.

### Cambiado
- `ui/screens/main_menu_screen.py`: "Nueva partida" ya no muestra el
  mensaje de "todavía no disponible" — emite `start_new_game` y abre
  el flujo real.
- `ui/windows/main_window.py`: añade `CharacterCreationScreen` al
  stack; conecta menú → creación → gameplay y cancelar → menú.
- `main.py`: instancia y propaga `PlayerManager`.

---

## [Sin versionar] — Repintado en caliente de temas + selector visible

### Añadido
- `ui/theme.py`: `on_theme_changed(callback)`/`off_theme_changed(callback)`
  — pub/sub interno; `set_theme()`/`toggle_theme()` notifican a los
  suscriptores solo cuando el tema cambia de verdad (no si se pide
  el mismo que ya estaba activo).
- `ui/screens/settings_screen.py`: tarjeta "APARIENCIA" con checkbox
  "Modo oscuro" — nace marcado según el tema activo real, y al
  tocarlo llama a `theme.set_theme()`.
- `ui/screens/gameplay_screen.py`: propiedades públicas
  `current_player`/`current_story`, para que `MainWindow` pueda leer
  la sesión activa sin acceder a atributos privados.

### Cambiado
- `ui/windows/main_window.py`: se suscribe a `on_theme_changed()`.
  Al cambiar el tema, reaplica el QSS global de la `QApplication` y
  reconstruye `MainMenuScreen`/`GameplayScreen` desde cero (la
  construcción se extrajo a un método compartido, `_build_screens()`,
  usado tanto en `__init__` como en el repintado), conservando qué
  pantalla estaba visible y la sesión activa si había una. No
  conserva la sub-sección interna de `GameplayScreen` (siempre
  vuelve a "Historia" tras el cambio) — limitación menor y aceptada.

---

## [Sin versionar] — Primer manager de dominio + servicios de inventario/logros

### Añadido
- `managers/story_manager.py`: `StoryManager`, fachada delgada sobre
  `StoryService` (delegación 1:1, sin política propia) — el primero
  de los 7 managers de dominio que anticipaba el SDD; los otros seis
  siguen sin construirse porque no tienen un service real detrás.
- `services/inventory_service.py`: `InventoryService` (documento
  `Inventory` por `player_id`, mismo patrón que `StatisticsService`).
- `services/achievement_service.py`: `AchievementService` (colección
  de `Achievement` por `player_id`, mismo patrón).
- `models/item.py`: faltaba y bloqueaba el import de
  `models/inventory.py` — mismo estilo que `achievement.py`/`event.py`.

### Cambiado — rewiring de `ui/` para usar los managers/services nuevos
- `ui/screens/story_panel.py`, `ui/screens/main_menu_screen.py`,
  `ui/dev_preview.py`: reciben `StoryManager` en vez de `StoryService`
  directamente (mismos nombres de método, cambio mecánico).
- `ui/screens/gameplay_screen.py`: recibe `story_manager`,
  `inventory_service`, `achievement_service`; `_refresh_all()` ahora
  puebla `InventoryScreen`/`AchievementsScreen` con datos reales
  (`get_inventory()`/`list_achievements()`) en vez de dejarlas
  siempre vacías por diseño — van a seguir vacías casi siempre
  porque nada llama todavía a `add_item()`/`grant_achievement()`,
  pero ahora es un vacío calculado, no fijo.
- `ui/windows/main_window.py`, `main.py`: construyen y propagan
  `StoryManager`, `InventoryService`, `AchievementService`.

---

## [Sin versionar] — Resolución de las decisiones A/B/C señaladas al usuario

### Cambiado
- `config/paths.py`: reestructuración de `assets/` — `ICONS_DIR`
  pasa a vivir dentro de `IMAGES_DIR`; `MUSIC_DIR` dentro de un
  `AUDIO_DIR` nuevo junto a `AMBIENCE_DIR` (nuevo) y `EFFECTS_DIR`
  (antes `SOUNDS_DIR`); nuevas `BACKGROUNDS_DIR`,
  `CHARACTER_IMAGES_DIR`, `UI_IMAGES_DIR`, `ENDING_IMAGES_DIR`.
- `services/audio_service.py`: importa `EFFECTS_DIR` en vez de
  `SOUNDS_DIR` (mismo valor semántico, nombre corregido).

### Renombrado
- Carpeta `test/` → `tests/`: `pytest.ini` y
  `config/paths.py::TESTS_DIR` ya decían "tests" desde antes; el
  desajuste estaba solo en el nombre real de la carpeta.

### Añadido
- `saves/.gitignore`, `logs/.gitignore` (`*` + `!.gitignore`): las
  carpetas quedan rastreadas sin versionar datos de ejecución reales.
- `assets/{audio/{music,ambience,effects},images/{backgrounds,characters,icons,ui,endings},fonts}/.gitkeep`,
  `assets/videos/.gitkeep`,
  `data/{events,endings,characters,items}/.gitkeep`: carpetas que
  `config/paths.py` esperaba y no existían físicamente. Cada
  `.gitkeep` documenta qué constante la define y si algún servicio
  ya la consume (ninguna de las de `data/` todavía).
- `docs/architecture.md`, `docs/api.md`, `docs/roadmap.md`,
  `docs/changelog.md` (este archivo).

---

## [Sin versionar] — Sistema de temas

### Añadido
- `ui/themes/__init__.py`: dataclass `Theme` (frozen) + registro
  `THEMES = {"light": LIGHT, "dark": DARK}`.
- `ui/themes/light.py`: tema claro, compuesto desde los valores que
  `ui/theme.py` ya usaba (sin cambiar ningún color existente).
- `ui/themes/dark.py`: tema oscuro, nuevo.
- `config/colors.py`: sección "MODO OSCURO" (aditiva) —
  `DARK_BACKGROUND`, `DARK_SURFACE`, `DARK_CARD`, `DARK_SIDEBAR`,
  `DARK_TEXT_*`, `DARK_BORDER*`, `DARK_ACCENT_*`,
  `DARK_INPUT_*`. Reutiliza valores existentes donde tenía sentido
  (`SECONDARY`, `PRIMARY_LIGHT`, `INFO`, `TEXT_PRIMARY`, `SIDEBAR`,
  `BORDER_DARK`) en vez de inventar tonos nuevos sin necesidad.

### Cambiado
- `ui/theme.py`: reescrito de módulo de constantes estáticas a
  proxy dinámico sobre el tema activo (`__getattr__` de módulo, PEP
  562). Añadidas `set_theme()`, `toggle_theme()`,
  `get_active_theme()`, `current_theme_name()`. Los ~15 archivos que
  ya hacían `from ui import theme` + `theme.BACKGROUND` no
  necesitaron ningún cambio.
- `ui/widgets/decision_option.py`: el color de acento por tarjeta
  (`_ACCENTS`) estaba calculado una sola vez a nivel de módulo al
  importar el archivo, lo que lo habría congelado con el primer
  tema activo para siempre. Cambiado a una función `_accents()` que
  se recalcula en cada tarjeta.

---

## [Sin versionar] — `requirements.txt`

### Cambiado
- `requirements.txt` reescrito por completo a partir de un escaneo
  real de imports (AST, todo `main.py`/`ai/`/`config/`/`database/`/
  `engine/`/`managers/`/`models/`/`services/`/`ui/`/`utils/`/`tests/`),
  no de la documentación de diseño.
- `pygame` → `pygame-ce`: `pygame` clásico no publica builds para
  Python 3.14 (falla compilando por falta de `sdl-config`);
  `pygame-ce` es reemplazo binario 1:1, mismo `import pygame`, sin
  cambios de código.
- Versiones mínimas ajustadas a lo confirmado compatible con Python
  3.14: `PySide6>=6.10.0`, `Pillow>=12.0.0`, `pygame-ce>=2.5.7`.
- `openai` fijado a `<2.0.0` a propósito (existe una serie 2.x, pero
  no se verificó que `client.images.generate()`/`.images.edit()`
  — los métodos que usa `services/image_service.py` — sigan
  funcionando igual ahí).

### Eliminado
- `SQLAlchemy`, `pydantic`, `python-dotenv`, `requests`, `anthropic`,
  `loguru`, `tqdm`: ninguno se importa en ningún archivo `.py` del
  proyecto (verificado, no asumido). Aparecían en el `requirements.txt`
  anterior solo por planes futuros mencionados en comentarios/docstrings.
- Los marcadores de Markdown que habían quedado guardados
  literalmente al inicio y al final del archivo (una línea de
  apertura y otra de cierre de bloque de código, tal como se pegan
  al copiar un fragmento con formato Markdown) y que rompían
  `pip install -r requirements.txt` antes de llegar a cualquier
  paquete.

---

## [Sin versionar] — Capa de interfaz (`ui/`)

Primera versión completa de la interfaz gráfica; no existía ningún
archivo en `ui/` antes de esta entrega.

### Añadido
- Paquete `ui/` completo: `theme.py` (versión inicial, estática),
  `widgets/` (`card`, `stat_bar`, `nav_button`, `image_placeholder`,
  `decision_option`), `screens/` (`main_menu_screen`,
  `gameplay_screen`, `story_panel`, `character_summary_panel`,
  `history_panel`, `character_screen`, `statistics_screen`,
  `inventory_screen`, `achievements_screen`, `settings_screen`),
  `windows/main_window.py`.
- `ui/dev_preview.py` + `data/scenarios/example_ui_fixture.json`:
  fixture técnico de solo-desarrollo (marcado explícitamente como
  no-narrativo) para poder ver la pantalla Historia funcionando de
  punta a punta sin que existan todavía Sistema de Creación de
  Personaje ni contenido narrativo real.

### Cambiado
- `main.py` reescrito: ya no instancia el `GameEngine` roto de
  `engine/`; construye `services/` + managers de sistema
  directamente y lanza `ui.windows.main_window.MainWindow`.
  Corregidos 5 problemas del archivo anterior: `from config.settings
  import Settings` (esa clase nunca existió — es un módulo de
  constantes), `from config.constants import ...` (el archivo real
  es `config/constant.py`, sin "s"), `GameEngine(save_manager=...)`
  con argumentos que su constructor real no acepta,
  `from ui.windows.main_menu import MainMenu` (ni el archivo ni la
  clase existían), `self.save_manager.load_last_save()` (método
  inexistente en `SaveManager`).
- `managers/audio_manager.py`: añadidos `get_master_volume()`,
  `get_music_volume()`, `get_effects_volume()` — ya existían en
  `AudioService` pero faltaban en la fachada; `settings_screen.py`
  los necesita para mostrar el volumen actual, no solo fijarlo.
- `config/colors.py`: añadida sección de colores para los atributos
  reales de `Player` que no tenían color asignado (`INTELLIGENCE`,
  `DISCIPLINE`, `CREATIVITY`, `CHARISMA`, `EMPATHY`, `APPEARANCE`,
  `STRESS`) — aditivo, no se modificó ningún color existente.

### Renombrado
- `Services/` → `services/` (minúscula): en Linux, la carpeta con
  mayúscula rompía todos los imports del proyecto, que ya estaban
  escritos en minúscula en absolutamente todo el código, tests
  incluidos. No era una decisión de diseño, era una inconsistencia
  de mayúsculas que probablemente pasó desapercibida desarrollando
  en Windows/Mac.

### Sin cambios (verificado, no modificado)
- `engine/`, `ai/`, `database/`: auditados, no tocados — ver
  `docs/architecture.md` para por qué siguen fuera del camino de
  ejecución.
