# Arquitectura — What If?

> Este documento describe la arquitectura **real** del código tal como
> existe hoy, verificada leyendo los archivos (no la arquitectura
> aspiracional de los documentos de diseño). Donde ambas difieren, se
> señala explícitamente. Para el diseño narrativo/de sistemas de
> juego, ver `VITA_Game_Design_Document.md` y
> `What_If_Vision_Document.md` en la raíz del proyecto.

## 1. Capas y dirección de dependencia

```
ui/            (PySide6 — presentación)
   │
   ▼
managers/      (orquestación de sistema: cuándo y qué)
   │
   ▼
services/      (lógica de negocio: cómo)
   │
   ▼
models/        (datos: Player, Story, NPC...)
```

- **`ui/`** nunca importa `models/` para escribir en él directamente,
  solo para leer (`player.health`, `story.chapter`, ...) y para pasar
  objetos entre pantallas. Nunca llama a los mutadores auditables de
  `Player` (`modify_health()`, etc.) — ver §4.
- **`managers/`** decide *cuándo* y *qué* (p. ej. "¿toca autoguardar
  en este turno?"), y delega el *cómo* a `services/`. Varios
  managers son fachadas delgadas sobre un service homónimo:
  `SaveManager` → `SaveService`, `AudioManager` → `AudioService`,
  `LanguageManager` → `LocalizationService`, `StoryManager` →
  `StoryService` (este último, a diferencia de los otros tres, no
  añade ninguna política propia — ver `docs/api.md`).
  `AchievementManager`/`InventoryManager` siguen el mismo patrón
  sobre `AchievementService`/`InventoryService`, sumando un catálogo
  de definiciones que esos services no tenían a propósito.
  `EventManager`/`EndingManager` no envuelven ningún service —
  gestionan directamente su propio catálogo + persistencia.
- **`services/`** contiene la lógica real: avanzar una historia,
  guardar/cargar, resolver texto localizado, generar audio/imágenes,
  gestionar inventario (`InventoryService`) y logros
  (`AchievementService`) por jugador.
- **`models/`** son las estructuras de datos (mayormente
  `@dataclass`), con algunos mutadores auditables en `Player` (ver §4).

## 2. `engine/` — capa de orquestación paralela a `ui/`, sin interfaz gráfica

El `SOFTWARE DESIGN DOCUMENT.md` original describe una capa
`Game Engine` (`StoryEngine`, `DecisionEngine`, `EventEngine`,
`EndingEngine`, `InventoryEngine`, `AchievementEngine`, `TimeEngine`,
`SaveEngine`) entre `ui/` y los modelos. Existe como carpeta
(`engine/`, 9 archivos) y **ya funciona de verdad** — verificado
empíricamente, no asumido: los 9 archivos importan Y se instancian
sin error (`python -c "import engine.xxx"` y una instanciación real
de cada clase con sus dependencias inyectadas).

No fue una construcción incremental de managers faltantes — al
auditar los 6 archivos que todavía fallaban antes de esta pieza, se
descubrió que el problema real nunca fue "faltan managers": **los 9
archivos estaban escritos contra una API completamente distinta e
incompatible** con la real — constructores sin argumentos que
implican un "jugador actual" único e implícito (`StoryManager()`,
`PlayerManager()` sin parámetros), métodos como `get_stat()`/
`modify_stat()` que nunca existieron en ningún manager real. Se
confirmó que ni siquiera los 2 archivos que ya importaban antes de
esta pieza (`game_engine.py`, `story_engine.py`) funcionaban de
verdad: fallaban igual al instanciarse
(`TypeError: StoryManager.__init__() missing 1 required positional argument`).

Se le presentó este hallazgo al usuario junto con las alternativas
(retirar `engine/`, moverlo a algo como `_deprecated/`, o
reescribirlo contra la API real) — eligió explícitamente
**reescribir los 9 archivos**, aceptando conscientemente que esto
duplica la orquestación que `ui/` ya hace y prueba con más de 70
pruebas reales. `engine/` hoy es una capa de orquestación SIN
interfaz gráfica (útil para scripts, pruebas automatizadas, una
futura CLI) — no algo que `ui/` deba empezar a usar en lugar de lo
que ya tiene.

**Piezas nuevas que hicieron falta para que la reescritura fuera
honesta** (sin inventar mecánica de juego sin catálogo, ver §1):
`managers/event_manager.py`, `managers/ending_manager.py`,
`managers/achievement_manager.py` (envuelve
`services/achievement_service.py`, no lo duplica),
`managers/inventory_manager.py` (envuelve
`services/inventory_service.py`, no lo duplica) — los 4 managers de
dominio que le faltaban a `managers/` para completar los 7 que el
SDD original anticipaba. Cada uno opera sobre un catálogo REAL pero
VACÍO (`data/events/`, `data/endings/`, `data/achievements/`,
`data/items/`) — la mecánica de lectura/disparo existe, el contenido
sigue siendo trabajo del equipo de diseño.

Dos decisiones arquitectónicas que `tests/test_engine.py` dejaba
pendientes quedaron resueltas: `StoryEngine` y `SaveEngine`
sobreviven como capas finas con estado sobre `StoryManager`/
`SaveManager` — ningún método reimplementa lo que
`services/story_service.py`/`services/save_service.py` ya resuelven
y ya prueban, solo delegan. Y `decision_engine.py` dejó de ser una
copia de `story_engine.py` (bug real, documentado antes de esta
pieza): ahora formaliza el objeto "decision_tomada" que
`VITA_Game_Design_Document.md` §4 describe, delegando la aplicación
de efectos en `ConsequenceService` — el único con permiso de
escritura sobre `Player` (GDD §5, ver §4 más abajo).

## 3. `ai/` y `database/` — no conectados a la aplicación en ejecución

- **`ai/`** (`ai_manager.py`, `memory.py`, `npc_ai.py`,
  `prompt_builder.py`, `story_generator.py`): no lo importa
  `main.py` ni ninguna capa que sí esté en el camino de ejecución.
  Solo lo usa `tests/test_ai.py`. No depende de ningún SDK externo
  (ni `openai` ni `anthropic` — se verificó con un escaneo de
  imports real al escribir `requirements.txt`).
- **`database/`** (`create_users_db.py`, `users_database.py`,
  `migrations/`): usa `sqlite3` (estándar de Python) para un
  esquema de cuentas de usuario separado del guardado de partidas.
  `main.py` no lo instancia. El guardado real de partidas (`Player`
  + `Story`) pasa por `services/repositories.py` (JSON), no por
  aquí — ver §5.

## 4. Regla de escritura sobre `Player` — el Sistema de Consecuencias

`VITA_Game_Design_Document.md` (§4–5) establece que el Sistema de
Decisiones "no modifica variables directamente" y que el Sistema de
Consecuencias es "el único con permiso de escritura sobre el EP
(Estado de Personaje)". Ese sistema existe hoy:
`services/consequence_service.py::ConsequenceService`.

En la práctica esto significa:

- `models/player.py` expone mutadores auditables
  (`modify_health(amount, reason)`, etc.); el único código que los
  llama es `ConsequenceService.apply_effects()` — ningún otro punto
  de `ui/` ni de `services/` escribe un atributo de `Player`
  directamente.
- `services/story_service.py::choose_option()` (vía `StoryManager`)
  sigue sin tocar ningún atributo de `Player` por sí mismo — eso
  sigue siendo responsabilidad exclusiva de `ConsequenceService`.
  La conexión entre "elegiste la opción B" y "tu disciplina sube 3
  puntos" vive en `ui/screens/story_panel.py::_apply_effects_if_any()`,
  que lee el campo opcional `effects` de la opción elegida (ver
  `docs/content_authoring_guide.md`) y se lo pasa a
  `ConsequenceService` ANTES de llamar a `StoryManager.choose_option()`.
- Alcance actual de `ConsequenceService`: los 10 atributos reales de
  `Player` más `net_worth` — todos comparten la forma
  `modify_x(amount, reason)` (delta simple). `annual_income`
  (`set_annual_income`, valor absoluto) y `debt`
  (`add_debt`/`reduce_debt`, dos verbos) quedan fuera a propósito:
  mezclarlos en un diccionario plano de deltas habría sido ambiguo.
- `ui/` respeta la regla: los paneles de personaje muestran los
  valores reales de `Player`, y sí pueden cambiar tras una decisión
  — `ui/screens/gameplay_screen.py::_handle_story_advanced()`
  refresca el panel de personaje compacto y la ficha completa en
  cada decisión, no solo el historial, precisamente porque ahora
  pueden haber cambiado de verdad.

## 5. Persistencia

`services/repositories.py` (`JSONKeyValueRepository`/
`JSONContentRepository`) sigue siendo el backend que `main.py` usa
de verdad — `Player`+`Story` como JSON en disco
(`config/paths.py::SAVES_DIR`), probado con 70+ pruebas. Es el mismo
que se documenta a sí mismo como **sustituto temporal**.

`database/` (reconstruida en la sesión de deuda técnica — la
anterior tenía un import roto y 3 esquemas sin relación entre sí,
ver `docs/changelog.md`) es la migración real a SQLAlchemy que ese
sustituto temporal anticipaba: `database/models.py` define una tabla
por tipo de dato (`players`, `story_progress`, `inventory_items`,
`player_achievements`, `unlocked_endings`, `account_statistics`,
`save_slots`), y `database/repositories.py` expone 7
repositorios (`PlayerRepository`, `StoryRepository`,
`InventoryRepository`, `AchievementRepository`, `EndingRepository`,
`StatisticsRepository`, `SaveSlotRepository`) con conversión
explícita ida y vuelta a los dataclasses reales — probado con 12
pruebas de ida y vuelta contra un SQLite temporal real
(`tests/test_database.py`).

**Activado para 4 de los 6 services** que reciben un
`KeyValueRepository` (`SaveService`, `StatisticsService`,
`InventoryService`, `AchievementService`) — `main.py` los construye
sobre `database/adapters.py`, que traduce el contrato genérico
`get`/`set`/`delete`/`list_keys` a los métodos tipados de
`database/repositories.py` (`get_player`/`save_player`, etc.). No fue
un cambio de una línea, exactamente por lo dicho arriba: los 4
adaptadores existen justamente para hacer esa traducción, uno por
tipo de dato. `StoryService` y `EndingManager` quedaron fuera de esta
activación (no se pidió) y siguen sobre JSON.

Limitaciones conocidas del puente (documentadas también en
`database/adapters.py`): `save_slots` guarda metadata de una ranura de
guardado (nombre, edad, fecha), no una foto independiente de
`Player`+`Story` en ese momento — a diferencia del sistema JSON, que
sí guarda una foto congelada por cada `save_id`. "Cargar" una ranura
en el esquema relacional devuelve el estado ACTUAL del jugador, no
uno histórico. Además, `database/models.py` no tiene tabla de NPCs
(`SQLSaveRepository` los loguea y no los persiste — hoy nada en el
juego real le pasa NPCs a `SaveManager`) y `inventory_items` no tiene
columna de capacidad de inventario (`Inventory.capacity` siempre
vuelve `None`/ilimitado — hoy nada en el proyecto asigna una
capacidad distinta).

`managers/save_manager.py` expone dos ranuras con nombre fijo,
`QUICKSAVE_SLOT = "quicksave"` y `AUTOSAVE_SLOT = "autosave"`, además
de guardado por `save_id` arbitrario vía `save_now()`/`load()`.

### Postgres remoto (Supabase) y cuentas de usuario

`database/engine.py::create_database_engine()` acepta un `db_url`
opcional: si se pasa (o si `main.py` encuentra `SUPABASE_DB_URL` en el
entorno, cargada vía `python-dotenv` desde un `.env` — ver
`.env.example`), el `Engine` apunta a esa Postgres en vez de al
SQLite local, sin ningún cambio en `database/models.py`/
`repositories.py`/`adapters.py` (SQLAlchemy Core ya es agnóstico de
dialecto). Como `SaveService`/`StatisticsService`/`InventoryService`/
`AchievementService` ya corren sobre ese mismo `Engine`, apuntarlo a
Supabase ya sincroniza esos 4 servicios en la nube — no hay un
mecanismo de sync aparte. `StoryService`/`EndingManager` siguen en
JSON local (mismo límite documentado arriba, no se pidió cambiarlo).

`services/auth_service.py::AuthService` envuelve Supabase Auth
(registro/login/logout), instanciado por `main.py` solo si
`SUPABASE_URL`/`SUPABASE_ANON_KEY` están configuradas; si no, queda en
`None` y `ui/screens/login_screen.py` (`GameScene.LOGIN`, primera
pantalla que ve el jugador) solo ofrece "Seguir sin cuenta" — nunca
bloquea el juego. No existe una tabla `users`/FK de cuenta: se
reutiliza el `user.id` de Supabase Auth directamente como `player_id`
(`managers/player_manager.py::create_player(player_id=...)`), así que
los datos de un jugador logueado ya quedan scoped a su cuenta sin
tocar el esquema.

## 6. Contenido narrativo vs. progreso — separación de datos

- **Contenido** (capítulos, escenas, texto, opciones): JSON de solo
  lectura en `data/scenarios/<story_content_id>.json`, resuelto por
  `services/repositories.py::JSONContentRepository`. Hoy solo existe
  un archivo ahí, `example_ui_fixture.json`, marcado explícitamente
  como fixture técnico de desarrollo (ver `roadmap.md` §"Contenido
  narrativo real").
- **Progreso** (qué escena va, qué eligió el jugador): `models/story.py::Story`,
  mutable, es lo único que cambia en tiempo de ejecución.

`ui/` nunca mezcla ambos ni hardcodea texto narrativo en un
componente — todo lo que se muestra en pantalla llega desde
`StoryService.get_current_scene()`.

## 7. Capa de interfaz (`ui/`)

Construida en PySide6 (`requirements.txt`, no `pygame` — `pygame-ce`
solo cubre audio, ver §8). No existía antes de la sesión de diseño
de interfaz; se construyó completa sobre `services/` + `managers/`
ya funcionales.

```
ui/
├── theme.py            proxy dinámico hacia ui/themes/ (ver §7.2)
├── themes/
│   ├── __init__.py      define Theme + registro THEMES
│   ├── light.py          tema por defecto
│   └── dark.py            tema oscuro
├── widgets/              componentes reutilizables sin lógica de pantalla
│   ├── card.py, stat_bar.py, nav_button.py,
│   └── image_placeholder.py, decision_option.py
├── screens/               pantallas/paneles con conocimiento de qué mostrar
│   ├── main_menu_screen.py
│   ├── gameplay_screen.py         shell de 3 columnas + sidebar interna
│   ├── story_panel.py             columna central de la sección Historia
│   ├── character_summary_panel.py  panel compacto (columna derecha)
│   ├── history_panel.py
│   ├── character_screen.py        ficha completa de personaje
│   ├── statistics_screen.py
│   ├── inventory_screen.py        vacía a propósito, ver §9
│   ├── achievements_screen.py     vacía a propósito, ver §9
│   └── settings_screen.py         audio + idioma, ambos reales
├── windows/
│   └── main_window.py    QMainWindow, aloja MainMenuScreen/GameplayScreen
│                          en un QStackedWidget sincronizado con SceneManager
└── dev_preview.py         SOLO desarrollo — ver §9
```

### 7.1 Navegación: dos niveles distintos, a propósito

- **Nivel de aplicación**: `managers/scene_manager.py::GameScene`
  (`MAIN_MENU`, `GAMEPLAY`, `PAUSE`, `SETTINGS`, `ALBUM`,
  `CHARACTER_CREATION`, `GAME_OVER`, `CREDITS`) — pila con
  push/pop, ya existía antes de `ui/`.
- **Nivel interno de `GameplayScreen`**: un enum local
  (`ui/screens/gameplay_screen.py::_Section`, con `STORY`,
  `CHARACTER`, `STATISTICS`, `INVENTORY`, `ACHIEVEMENTS`,
  `SETTINGS`) para las 6 secciones del sidebar. Es local a ese
  archivo a propósito — no se añadió a `GameScene` para no modificar
  `scene_manager.py`, que no necesitaba cambiar.

### 7.2 Sistema de temas

`ui/theme.py` reenvía cada color estructural (fondo, superficie,
texto, borde, acento) al tema activo en `ui/themes/` vía
`__getattr__` de módulo (PEP 562) — así el resto de `ui/` sigue
haciendo `theme.BACKGROUND` sin saber que existe más de un tema.
`ui.theme.set_theme("dark")` / `toggle_theme()` cambian el tema
activo para los widgets que se construyan **a partir de ese
momento**; no hay repintado en caliente de widgets ya visibles (para
eso haría falta un sistema de suscripción a "tema cambiado" que no
se ha construido). Los colores semánticos (éxito/aviso/error/info,
colores de estadísticas) y los tokens no-color (espaciado,
tipografía) son iguales en ambos temas.

## 8. Audio, imágenes e IA — todas con degradación controlada

Tres dependencias externas se importan de forma **perezosa** (dentro
de una función/método, no al nivel de módulo), con manejo explícito
de su ausencia:

| Import perezoso | Archivo | Si falta |
|---|---|---|
| `pygame` (paquete `pygame-ce`) | `services/audio_service.py::PygameAudioBackend` | Audio deshabilitado, aviso en log, resto del juego funciona (confirmado en pruebas) |
| `PIL` (paquete `Pillow`) | `managers/resource_manager.py`, `services/image_service.py` | `ResourceNotFoundError` controlado al pedir una imagen/fuente |
| `openai` | `services/image_service.py::OpenAIImageProvider` | `ImageGenerationError` controlado, nunca crasha el import |

`PySide6` es la única dependencia que **sí** es obligatoria para que
`main.py` arranque — es la única que se importa a nivel de módulo en
el camino de arranque.

## 9. Código de desarrollo, claramente marcado para borrar

- `ui/dev_preview.py` + `data/scenarios/example_ui_fixture.json`:
  fixture técnico para poder ver la pantalla Historia funcionando
  sin que exista todavía un Sistema de Creación de Personaje ni
  contenido narrativo real. Se llega ahí solo desde "Vista previa de
  interfaz" en el menú principal, nunca desde "Nueva partida".

`ui/screens/inventory_screen.py` y `achievements_screen.py` ya NO
entran en esta categoría: `services/inventory_service.py` y
`achievement_service.py` existen y están conectados (ver §1 más
arriba, y `docs/api.md` para su interfaz completa) — van a seguir
mostrando su estado vacío casi siempre, pero ahora es un vacío
calculado desde datos reales, no una pantalla a la espera de que se
construya su backend.

Ver `roadmap.md` para qué queda pendiente y en qué orden.
