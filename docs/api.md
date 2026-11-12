# API interna — What If?

> Referencia de la API pública de `services/`, `managers/` y
> `ui.theme`. Las firmas se copiaron directamente del código (no de
> memoria); si algo cambia en el código y no aquí, este documento
> quedó desactualizado — avisa para corregirlo, no asumas que el
> código está mal.
>
> No documenta `engine/` (roto, no importable — ver `architecture.md`
> §2) ni `ai/`/`database/` (no conectados al camino de ejecución).

## Convención general

`ui/` habla con `services/` y `managers/`, nunca con `models/`
directamente para escribir. Todo lo de abajo es seguro de llamar
desde una pantalla.

---

## `services.story_service.StoryService`

Progreso narrativo: iniciar, leer la escena actual, elegir una
opción, cerrar una historia.

```python
start_story(player_id: str, story_content_id: str, started_at_age: int) -> Story
get_current_scene(story: Story) -> Dict[str, Any]
    # {"title"?, "text", "options": [{"label", "next_scene"}], "ending"?, "ending_id"?}
is_current_scene_ending(story: Story) -> bool
choose_option(story: Story, option_index: int) -> Story
    # Valida, registra la decisión, avanza de escena, cierra si aplica, persiste.
    # NO toca ningún atributo de Player — ver architecture.md §4.
finish_story(story: Story, ending_id: str) -> Story
fail_story(story: Story, reason: str = "") -> Story
get_story(story_id: str) -> Story
list_stories_for_player(player_id: str) -> List[Story]
list_active_stories_for_player(player_id: str) -> List[Story]
```

Excepciones: `StoryContentNotFoundError`, `InvalidStoryContentError`,
`SceneNotFoundError`, `InvalidOptionError`, `StoryNotFoundError`.

---

## `services.save_service.SaveService` (vía `managers.save_manager.SaveManager`)

`ui/` debería usar `SaveManager`, no `SaveService` directamente —
mismo patrón que audio e idioma (manager = fachada, service = lógica).

```python
# managers.save_manager
QUICKSAVE_SLOT = "quicksave"
AUTOSAVE_SLOT = "autosave"

SaveManager(save_service: SaveService, autosave_interval_turns: int = 5)

save_now(save_id: str, player: Player, stories: Optional[List[Story]] = None, npcs: Optional[List[NPC]] = None) -> None
autosave_if_due(current_turn: int, player: Player, stories: List[Story]) -> Optional[SaveSlot]
turns_until_next_autosave(current_turn: int) -> int
quick_save(player: Player, stories: List[Story]) -> SaveSlot
quick_load() -> LoadedGame
load(save_id: str) -> LoadedGame
delete_save(save_id: str) -> None
save_exists(save_id: str) -> bool
list_saves() -> List[SaveSlot]
```

`LoadedGame` (dataclass): `player: Player`, `stories: List[Story]`.
`SaveSlot` (dataclass): metadata de una ranura de guardado.

Excepción: `SaveNotFoundError` (capturarla al llamar `quick_load()`
sin partida guardada — ver `ui/screens/main_menu_screen.py` para el
patrón real).

---

## `services.statistics_service.StatisticsService`

Estadísticas de **cuenta** (entre partidas) — distintas de
`player.statistics` (`PlayerStatistics`, de la vida en curso). Ver
`docs/architecture.md` si hace falta más contexto sobre esta
separación.

```python
get_statistics(user_id: str) -> AccountStatistics
record_life_ended(user_id: str, player: Player, died: bool) -> AccountStatistics
record_achievement_unlocked(user_id: str) -> AccountStatistics
reset_statistics(user_id: str) -> AccountStatistics
```

`AccountStatistics` (dataclass): incluye `total_games`,
`total_deaths`, `achievements_unlocked`, entre otros — ver
`to_dict()`/`from_dict()` para la lista completa de campos.

Nota: el proyecto no tiene todavía un sistema de cuentas/login
activo; `user_id` se resuelve hoy con `player.player_id` (ver
`ui/screens/statistics_screen.py`).

---

## `services.localization_service.LocalizationService` (vía `managers.language_manager.LanguageManager`)

```python
# managers.language_manager
subscribe(callback) -> None
unsubscribe(callback) -> None
change_language(locale: str) -> None
current_language() -> str
available_languages() -> List[str]
translate(key: str, **variables: Any) -> str
```

Si `data/localization/` no tiene contenido para un locale, no
falla: usa un diccionario vacío con aviso en el log (confirmado en
pruebas). `available_languages()` puede devolver una lista vacía en
ese caso.

---

## `services.audio_service.AudioService` (vía `managers.audio_manager.AudioManager`)

```python
# managers.audio_manager
AudioManager(audio_service: AudioService, scene_manager: SceneManager)

attach_to_scene_manager(scene_manager: SceneManager) -> None
set_track_for_scene(scene: GameScene, track_id: str) -> None
play_sound_effect(effect_id: str) -> None
set_master_volume(volume: float) -> None      # 0.0 – 1.0
set_music_volume(volume: float) -> None
set_effects_volume(volume: float) -> None
get_master_volume() -> float
get_music_volume() -> float
get_effects_volume() -> float
mute() -> None
unmute() -> None
is_muted() -> bool
```

Los tres getters (`get_master_volume`, `get_music_volume`,
`get_effects_volume`) se añadieron a `AudioManager` durante la
sesión de UI — ya existían en `AudioService` pero faltaban en la
fachada; `ui/screens/settings_screen.py` los necesita para mostrar
el volumen actual, no solo poder fijarlo.

Backend real: `pygame-ce` (import perezoso, con degradación
controlada si no está instalado — ver `architecture.md` §8).

---

## `managers.resource_manager.ResourceManager`

```python
get_image(resource_id: str)          # PIL.Image.Image
get_icon(resource_id: str)           # PIL.Image.Image
preload_images(resource_ids: List[str]) -> None
get_font(resource_id: str, size: int)  # PIL.ImageFont.FreeTypeFont
clear_cache() -> None
cache_size() -> int
```

Import de Pillow perezoso (dentro de cada método) para que el
módulo se pueda importar sin error si Pillow no está instalado.
Excepción: `ResourceNotFoundError`.

---

## `managers.scene_manager.SceneManager`

Nivel de aplicación (menú/gameplay/pausa/...) — no confundir con la
navegación interna de `GameplayScreen` (`_Section`, local a
`ui/screens/gameplay_screen.py`). Ver `architecture.md` §7.1.

```python
class GameScene(Enum):
    MAIN_MENU, CHARACTER_CREATION, GAMEPLAY, PAUSE,
    SETTINGS, ALBUM, GAME_OVER, CREDITS

current_scene() -> GameScene
stack_depth() -> int
is_active(scene: GameScene) -> bool
change_scene(scene: GameScene) -> None    # reemplaza la escena actual
push_scene(scene: GameScene) -> None      # apila (p. ej. Pausa sobre Gameplay)
pop_scene() -> GameScene
on_enter(scene: GameScene, callback) -> None
on_exit(scene: GameScene, callback) -> None
off_enter(scene: GameScene, callback) -> None
off_exit(scene: GameScene, callback) -> None
```

`AudioManager` está suscrito a esto (`attach_to_scene_manager`) para
cambiar de pista al cambiar de escena.

---

## `managers.story_manager.StoryManager`

Primer manager de dominio construido. Fachada delgada, delega 1:1 en
`StoryService` (mismo objeto que devuelve `services.story_service`) —
no añade política propia (a diferencia de `SaveManager`, que sí
decide *cuándo* autoguardar). `ui/` lo usa en vez de `StoryService`
directamente desde esta sesión.

```python
StoryManager(story_service: StoryService)

start_story(player_id: str, story_content_id: str, started_at_age: int) -> Story
get_current_scene(story: Story) -> Dict[str, Any]
is_current_scene_ending(story: Story) -> bool
choose_option(story: Story, option_index: int) -> Story
finish_story(story: Story, ending_id: str) -> Story
fail_story(story: Story, reason: str = "") -> Story
get_story(story_id: str) -> Story
list_stories_for_player(player_id: str) -> List[Story]
list_active_stories_for_player(player_id: str) -> List[Story]
```

Reexporta las excepciones de `story_service` (`StoryContentNotFoundError`,
`InvalidStoryContentError`, `SceneNotFoundError`, `InvalidOptionError`,
`StoryNotFoundError`) para no tener que importar de dos módulos distintos.

---

## `managers.player_manager.PlayerManager`

Segundo manager de dominio. Crea, persiste y recupera `Player`. A
diferencia de `StoryManager`, sí añade lógica propia: calcula
`birth_year` desde la edad de inicio, y valida la distribución de
puntos de atributos antes de crear el personaje.

```python
CURRENT_GAME_YEAR = 2024          # año de referencia del universo del juego
POINTS_TO_DISTRIBUTE = 20         # puntos extra sobre los valores por defecto de Player
DISTRIBUTABLE_ATTRS: List[str]    # los 10 atributos numéricos de Player, en orden de UI

PlayerManager(repository: Optional[KeyValueRepository] = None)

validate_distribution(deltas: Dict[str, int]) -> Tuple[bool, str]
create_player(*, first_name, last_name, gender, starting_age, country, city,
              socioeconomic_origin=SocioeconomicLevel.MEDIUM,
              attr_deltas=None, aspiration=None) -> Player
get_player(player_id: str) -> Player
save_player(player: Player) -> None     # persiste el estado actual (útil tras ConsequenceService)
player_exists(player_id: str) -> bool
```

Excepciones: `PlayerCreationError`, `PlayerNotFoundError`.

---

## `managers.time_manager.TimeManager`

Tercer manager de dominio — el "futuro Sistema de Edad" que
`Player.advance_age()` ya mencionaba en su propio docstring antes de
que este archivo existiera. Dos responsabilidades: avanzar el tiempo
y decidir cuándo (y por qué) termina una vida.

```python
RANDOM_DEATH_CAUSES = ("accidente", "enfermedad repentina")

TimeManager(random_seed: Optional[int] = None)   # seed solo para pruebas deterministas

advance_time(player: Player, years: int = 1) -> None
    # 1 año por defecto (una decisión = un año, decisión explícita
    # para esta primera versión — el contenido no lo controla).
    # Usa el mutador real Player.advance_age(), no lo reimplementa.

check_life_status(player: Player) -> Optional[LifeEndResult]
    # None si el personaje sigue con vida. Si no, LifeEndResult(cause, age_at_end).
    # Se comprueba en este orden — el primero que se cumple gana:
    #   1. "salud"    — player.is_alive es False (health llegó a 0)
    #   2. "vejez"    — player.age >= player.life_expectancy
    #   3. uno de RANDOM_DEATH_CAUSES — con probabilidad
    #      config.game_config.RANDOM_DEATH_CHANCE_PER_YEAR (0.01),
    #      independiente de salud/edad
```

`LifeEndResult` (dataclass frozen): `cause: str`, `age_at_end: int`.

**Alcance dejado fuera a propósito**: no recalcula salud/estrés por
envejecimiento (aunque el propio docstring de `advance_age()` lo
anticipa) — definir esa curva es una decisión de balance de juego
que no se pidió en esta sesión. Ver `docs/roadmap.md`.

Consumidor real: `ui/screens/story_panel.py`, que llama a
`advance_time()` + `check_life_status()` después de aplicar
`effects` (si los hay) y antes de avanzar la historia — si la vida
terminó, no se avanza la historia, se emite `life_ended` y
`GameplayScreen`/`MainWindow` llevan a `GameOverScreen`.

---

## `services.inventory_service.InventoryService`

Resuelve "el inventario del jugador X" — un documento `Inventory`
por `player_id` (mismo patrón que `StatisticsService`). No inventa
qué objetos existen en el juego, solo persiste la colección que otro
sistema (todavía inexistente) le entregue.

```python
get_inventory(player_id: str) -> Inventory
has_item(player_id: str, item_id: str) -> bool
add_item(player_id: str, item: Item) -> Inventory
remove_item(player_id: str, item_id: str) -> Inventory
clear_inventory(player_id: str) -> Inventory
```

Excepciones: `ItemNotFoundError`, `InventoryFullError`.

---

## `services.achievement_service.AchievementService`

Resuelve "los logros del jugador X" — igual patrón, sin catálogo de
qué logros existen (eso sería contenido de diseño). Solo administra
qué `Achievement` tiene otorgados un jugador y cuáles están
desbloqueados.

```python
list_achievements(player_id: str) -> List[Achievement]
list_unlocked(player_id: str) -> List[Achievement]
has_achievement(player_id: str, achievement_id: str) -> bool
grant_achievement(player_id: str, achievement: Achievement) -> Achievement
unlock_achievement(player_id: str, achievement_id: str) -> Achievement
```

Excepciones: `AchievementNotFoundError`, `DuplicateAchievementError`.

---

## `services.consequence_service.ConsequenceService`

"El único sistema con permiso de escritura sobre el EP" (GDD §5).
Sin estado propio: opera directamente sobre el `Player` que se le
pase, usando sus mutadores auditables (`modify_health()`, etc.) —
nunca escritura directa de atributo. Quien lo llama es responsable
de persistir el `Player` después (ya lo hace
`ui/screens/gameplay_screen.py` en cada guardado tras una decisión).

```python
VALID_EFFECT_KEYS: FrozenSet[str]   # health, appearance, intelligence, discipline,
                                     # creativity, stress, happiness, charisma, empathy,
                                     # reputation, net_worth (NO annual_income/debt — ver docstring)

ConsequenceService()

apply_effects(player: Player, effects: Dict[str, int | float], reason: str) -> List[str]
```

`apply_effects` no hace nada si `effects` está vacío/`None`. Valida
TODO el diccionario antes de aplicar nada (para no dejar al jugador
a medio modificar si hay un error a mitad de camino). Los valores se
acotan solos vía la lógica interna de `Player` (`_clamp_stat`) — este
servicio no reimplementa ese acotado.

Excepción: `InvalidEffectsError` (clave desconocida o valor no numérico).

Consumidor real: `ui/screens/story_panel.py`, que lee `effects` de
la opción elegida (ver `docs/content_authoring_guide.md`) y lo aplica
antes de avanzar la historia.

---

## `managers.event_manager.EventManager`

Catálogo de eventos (`data/events/<id>.json`) + disparo con
comprobación de requisitos, aplicando efectos vía
`ConsequenceService`. Catálogo real pero vacío hoy — construir
contenido de eventos es trabajo de diseño.

```python
EventManager(repository: Optional[ContentRepository] = None,
             consequence_service: Optional[ConsequenceService] = None,
             rng: Optional[random.Random] = None)

get_event(event_id: str) -> Optional[Dict[str, Any]]
get_random_event(category: Optional[str] = None) -> Optional[Tuple[str, Dict[str, Any]]]
    # selección ponderada por el campo "weight" de cada definición,
    # vía utils.random_utils.weighted_choice (1.0 si no lo trae)
list_events() -> List[str]
can_trigger(player: Player, event: Dict[str, Any]) -> bool
trigger_event(player: Player, event_id: str) -> Tuple[Dict[str, Any], List[str]]
```

Excepciones: `EventNotFoundError`, `EventRequirementsNotMetError`.

---

## `managers.ending_manager.EndingManager`

Catálogo de finales de VIDA (`data/endings/<id>.json`) — distinto
del `ending_id` de una `Story` individual, ver `docs/architecture.md`
§6 — más qué finales tiene desbloqueados cada jugador.

```python
EndingManager(content_repository: Optional[ContentRepository] = None,
              progress_repository: Optional[KeyValueRepository] = None)

get_ending(ending_id: str) -> Optional[Dict[str, Any]]
list_endings() -> List[str]
determine_ending(player: Player, ending_ids: Optional[List[str]] = None) -> Optional[str]
    # primer id (en orden) cuyos requisitos cumple `player`
unlock_ending(player_id: str, ending_id: str) -> None
has_ending(player_id: str, ending_id: str) -> bool
list_unlocked(player_id: str) -> List[str]
```

Excepción: `EndingNotFoundError`.

---

## `managers.achievement_manager.AchievementManager`

Envuelve `AchievementService` (no lo duplica) y añade un catálogo de
DEFINICIONES con requisitos (`data/achievements/<id>.json`) para
poder comprobar automáticamente qué logros corresponde desbloquear.

```python
AchievementManager(achievement_service: AchievementService,
                    catalog_repository: Optional[ContentRepository] = None,
                    statistics_service: Optional[StatisticsService] = None)

get_achievement_definition(achievement_id: str) -> Optional[Dict[str, Any]]
list_catalog() -> List[str]
unlock(player_id: str, achievement_id: str) -> bool   # False si ya lo tenía
is_unlocked(player_id: str, achievement_id: str) -> bool
get_unlocked(player_id: str) -> List[Achievement]
check(player: Player, achievement_id: str) -> bool
check_all(player: Player) -> List[str]                 # desbloquea y devuelve los nuevos
get_progress(player_id: str) -> Dict[str, Any]          # {"unlocked", "total", "percentage"}
```

Con `statistics_service` configurado, cada desbloqueo real llama a
`record_achievement_unlocked()` — reutiliza ese contador de cuenta,
no lleva uno propio.

---

## `managers.inventory_manager.InventoryManager`

Envuelve `InventoryService` (no lo duplica) y añade un catálogo de
definiciones de objeto (`data/items/<id>.json`) para poder "usar"
uno con efecto vía `ConsequenceService`.

```python
InventoryManager(inventory_service: InventoryService,
                  catalog_repository: Optional[ContentRepository] = None,
                  consequence_service: Optional[ConsequenceService] = None)

get_item_definition(item_id: str) -> Optional[Dict[str, Any]]
add_item(player_id: str, item_id: str, quantity: int = 1) -> Inventory
remove_item(player_id: str, item_id: str) -> Inventory
has_item(player_id: str, item_id: str) -> bool
get_inventory(player_id: str) -> Inventory
clear_inventory(player_id: str) -> Inventory
use_item(player: Player, item_id: str) -> bool
    # False (sin lanzar excepción) si no existe la definición o el
    # jugador no lo tiene — no es un error de programación
```

---

## `database/` — backend SQLAlchemy (no activo por defecto)

Ver `docs/architecture.md` §5 antes de usar: infraestructura real,
pero `main.py` sigue usando `services/repositories.py` con JSON.

```python
# database.engine
create_database_engine(db_path: Optional[Path] = None, echo: bool = False) -> Engine
create_all(engine: Engine) -> None   # crea las tablas de database/models.py

# database.repositories — construcción uniforme: Repo(engine)
PlayerRepository(engine).save_player(player: Player) -> None
PlayerRepository(engine).get_player(player_id: str) -> Player            # PlayerNotFoundError
PlayerRepository(engine).player_exists(player_id: str) -> bool

StoryRepository(engine).save_story(story: Story) -> None
StoryRepository(engine).get_story(story_id: str) -> Story                # StoryNotFoundError
StoryRepository(engine).list_stories_for_player(player_id: str) -> List[Story]

InventoryRepository(engine).get_items(player_id: str) -> List[Item]
InventoryRepository(engine).add_item(player_id: str, item: Item) -> None
InventoryRepository(engine).remove_item(player_id: str, item_id: str) -> bool
InventoryRepository(engine).clear_inventory(player_id: str) -> None

AchievementRepository(engine).list_achievements(player_id: str) -> List[Achievement]
AchievementRepository(engine).grant_achievement(player_id: str, achievement: Achievement) -> None
AchievementRepository(engine).unlock_achievement(player_id: str, achievement_id: str, unlocked_at: str) -> bool

EndingRepository(engine).unlock_ending(player_id: str, ending_id: str, unlocked_at: str) -> None
EndingRepository(engine).has_ending(player_id: str, ending_id: str) -> bool
EndingRepository(engine).list_unlocked(player_id: str) -> List[str]

StatisticsRepository(engine).get_statistics(user_id: str) -> AccountStatistics
StatisticsRepository(engine).save_statistics(user_id: str, stats: AccountStatistics) -> None

SaveSlotRepository(engine).save_slot(save_id: str, player: Player, saved_at: str) -> None
SaveSlotRepository(engine).list_slots() -> List[dict]
SaveSlotRepository(engine).delete_slot(save_id: str) -> None
```

---

## `ui.theme` — tokens visuales

```python
set_theme(name: str) -> None          # "light" | "dark"; ValueError si no existe
toggle_theme() -> str                  # alterna, devuelve el nombre resultante
get_active_theme() -> Theme            # objeto completo (ui.themes.Theme)
current_theme_name() -> str
stat_color(stat_name: str) -> str      # color por campo real de Player
base_stylesheet() -> str               # QSS global para el tema activo EN ESTE MOMENTO
on_theme_changed(callback: Callable[[str], None]) -> None   # suscripción para repintado en caliente
off_theme_changed(callback: Callable[[str], None]) -> None  # cancela una suscripción
```

Atributos de color reenviados al tema activo (`BACKGROUND`,
`SURFACE`, `CARD`, `SIDEBAR_BG`, `TEXT_PRIMARY`, `TEXT_SECONDARY`,
`TEXT_DISABLED`, `TEXT_WHITE`, `BORDER`, `BORDER_STRONG`,
`ACCENT_PRIMARY`, `ACCENT_PRIMARY_HOVER`, `ACCENT_PRIMARY_LIGHT`,
`ACCENT_PURPLE`, `ACCENT_PURPLE_SOFT`, `INPUT_BACKGROUND`,
`INPUT_BORDER`) — se leen como `theme.BACKGROUND`, no como función.

Constantes iguales en cualquier tema: `SUCCESS`, `WARNING`, `ERROR`,
`INFO`, `STAT_COLORS`, `SPACE_XS..XL`, `RADIUS_SM..LG`,
`FONT_FAMILY`, `FONT_SIZE_H1..TINY`.

**Alcance de `set_theme()`**: desde esta sesión, SÍ repinta en
caliente lo que ya está en pantalla —
`ui/windows/main_window.py::MainWindow` es el único suscriptor de
`on_theme_changed()` y reconstruye `MainMenuScreen`/`GameplayScreen`
desde cero al cambiar de tema, conservando la sesión activa
(`Player`/`Story`) y qué pantalla estaba visible. No conserva la
sub-sección interna de `GameplayScreen` (vuelve a "Historia").
Selector visible en `ui/screens/settings_screen.py` ("Modo oscuro").

---

## Referencia rápida de campos — `models.player.Player`

Atributos reales (no confundir con los de la imagen de referencia
del diseño de interfaz, que eran solo ejemplos visuales):

- Físicos: `health`, `appearance` (0–100)
- Mentales: `intelligence`, `discipline`, `creativity`, `stress`, `happiness` (0–100)
- Sociales: `charisma`, `empathy` (0–100), `reputation` (-100–100, `config.constant.MIN_REPUTATION`/`MAX_REPUTATION`)
- Económicos: `net_worth`, `annual_income`, `debt`
- Identidad: `age`, `aspiration`, `civil_status`, `education_level`, `current_profession`, `socioeconomic_origin`, `country`, `city`
- Meta: `statistics` (`PlayerStatistics`: `turns_played`, `decisions_made`, `key_moments_unlocked`)

Mutadores auditables (`modify_health(amount, reason)`, etc.):
uso exclusivo de `services.consequence_service.ConsequenceService`
— ningún otro punto de `ui/` los llama directamente. Ver
`architecture.md` §4 y la sección de `ConsequenceService` más arriba.

## Referencia rápida de campos — `models.story.Story`

- `chapter: int`, `current_scene_id: str`, `status` (`StoryStatus`),
  `story_content_id: str`, `important_choices: List[str]`,
  `events: List[str]`, `ending_id: Optional[str]`
- `is_finished` / `is_active`: propiedades derivadas de `status`
