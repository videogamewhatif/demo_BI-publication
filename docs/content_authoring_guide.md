# Guía de autoría de contenido narrativo — What If?

> Para quien escriba historias reales en `data/scenarios/`. Documenta
> el formato exacto que `services/story_service.py` espera —
> verificado contra ese código, no inventado. Los ejemplos de este
> documento están marcados como PLANTILLA a propósito: son
> estructura, no historias reales — eso es trabajo del equipo de
> diseño, no de este documento.

## Antes de escribir: validá lo que ya tengas

```bash
python tools/validate_scenario.py data/scenarios/tu_historia.json
```

Corre automáticamente en cada `pytest` también
(`tests/test_scenario_content.py`), así que un error de estructura
no llega a producción sin que alguien lo vea.

## Estructura del archivo

Un archivo = una historia = un `story_content_id` (el nombre del
archivo sin `.json`). Tres claves son obligatorias; el resto son
opcionales pero recomendadas:

```json
{
  "title": "PLANTILLA: título de la historia",
  "genre": "PLANTILLA: género (opcional)",
  "setting": "PLANTILLA: ambientación (opcional)",
  "objective": "PLANTILLA: qué busca el jugador en esta historia (opcional)",
  "start_scene": "escena_inicial",
  "scenes": {
    "escena_inicial": { "...": "ver abajo" }
  }
}
```

| Clave | Obligatoria | Para qué |
|---|---|---|
| `title` | Sí | Se muestra como encabezado si la escena no trae su propio `title` |
| `start_scene` | Sí | Debe ser una clave real dentro de `scenes` |
| `scenes` | Sí | Objeto con todas las escenas de esta historia |
| `genre`, `setting`, `objective` | No | Metadatos, no se muestran en la UI hoy |

## Una escena

```json
"escena_inicial": {
  "title": "PLANTILLA: título corto de la escena (opcional)",
  "text": "PLANTILLA: el texto narrativo que ve el jugador. Obligatorio en la práctica — si falta, la pantalla se muestra vacía.",
  "image": "PLANTILLA: ruta o id de imagen (opcional — ver nota abajo)",
  "options": [
    { "label": "PLANTILLA: texto del botón A", "next_scene": "otra_escena" },
    { "label": "PLANTILLA: texto del botón B", "next_scene": "otra_escena_2" }
  ]
}
```

- **`options`**: cualquier cantidad (la interfaz no asume 2 — lo
  probamos con 3 en el fixture de desarrollo). Cada una necesita
  `label` (el texto del botón) y `next_scene` (el id de la escena
  siguiente — si falta o apunta a algo que no existe, el validador
  lo marca como ERROR).
- **`image`**: el campo existe y `ui/widgets/image_placeholder.py`
  ya sabe leerlo, pero **no hay ningún sistema que genere o resuelva
  esa imagen todavía** — ver `docs/architecture.md` §8. Poné el
  campo si querés dejarlo listo, o omitilo; en ambos casos la
  interfaz muestra un placeholder mientras tanto.

## Una escena final

```json
"final_ejemplo": {
  "text": "PLANTILLA: texto del cierre de esta rama.",
  "ending": true,
  "ending_id": "nombre-unico-de-este-final"
}
```

- `"options"` se omite (o se deja vacío) en un final — si una escena
  tiene `ending: true` Y opciones, el validador te avisa que las
  opciones nunca se van a mostrar.
- `ending_id` es técnicamente opcional (si falta, `StoryService` le
  pone `"ending-generic"`), pero el validador lo marca como warning:
  sin un id propio, todos los finales que caigan en ese caso son
  indistinguibles entre sí para cualquier sistema que quiera saber
  "¿qué final sacó el jugador?".

## Momentos Clave del Álbum de Vida (opcional)

Un subconjunto curado de escenas puede marcarse como "Momento Clave"
(`What_If_Vision_Document.md` §5.3) — el juego genera una ilustración
y la guarda en el Álbum de Vida del jugador cuando llega ahí. **No
marques todas las escenas**: eso satura la experiencia y devalúa el
impacto visual, exactamente lo que el Vision Document advierte que
hay que evitar.

```json
"trabajo_estable": {
  "title": "Ocho meses en la ferretería",
  "text": "...",
  "memory_moment": { "category": "hito_profesional" },
  "options": [ ... ]
}
```

- **`category`** (obligatoria dentro de `memory_moment`): una de
  `nacimiento`, `hito_educativo`, `hito_profesional`,
  `hito_relacional`, `hito_salud`, `consecuencia_extrema`,
  `desenlace_final` (`models/memory_moment.py::VALID_MEMORY_CATEGORIES`
  — misma lista curada del Vision Document §5.3). El validador avisa
  si usás una categoría distinta.
- El **título y el texto** del momento se toman directo de `title`/
  `text` de la escena — no inventes contenido nuevo acá, reutilizá lo
  que ya escribiste.
- `nacimiento` (creación de personaje) y `desenlace_final` (fin de
  vida) NO se marcan en escenas: se disparan solos desde
  `ui/windows/main_window.py`, porque no dependen de una historia
  concreta.

## Lo que el validador atrapa por vos


| Problema | Nivel |
|---|---|
| Falta `title`/`start_scene`/`scenes` | Error |
| `start_scene` no existe en `scenes` | Error |
| Una opción no tiene `next_scene` | Error |
| `next_scene` apunta a una escena que no existe | Error |
| Una escena sin opciones y sin `ending: true` (callejón sin salida) | Warning |
| Una escena `ending: true` que además tiene opciones | Warning |
| Un final sin `ending_id` propio | Warning |
| Una escena que ninguna otra referencia (contenido muerto) | Warning |
| Ningún final alcanzable desde `start_scene` (la historia no termina nunca) | Warning |
| Falta `text` en una escena | Warning |
| `effects` usa una clave que `ConsequenceService` no reconoce | Error |
| `effects` tiene un valor no numérico | Error |
| `memory_moment` sin `category`, o con una categoría no reconocida | Warning |

## Lo que el validador NO puede evaluar

Calidad de la escritura, tono, si una decisión "se siente" real, si
el texto respeta el pilar de diseño de "no juzgar las decisiones del
jugador" (ver `What_If_Vision_Document.md`). Eso sigue siendo
criterio humano — el validador solo protege la estructura.

## Nota sobre consecuencias en estadísticas

`StoryService.choose_option()` no aplica efectos por sí mismo — pero
el campo `effects` de una opción SÍ se aplica de verdad, vía
`ConsequenceService` (el único sistema con permiso de escribir en
`Player`, según el GDD §5), conectado en
`ui/screens/story_panel.py` justo antes de avanzar la historia:

```json
{
  "label": "PLANTILLA: aceptar el trabajo estable",
  "next_scene": "oficina",
  "effects": { "happiness": -5, "discipline": 3, "net_worth": 1500 }
}
```

`effects` es un objeto `{atributo: delta}` — un número a sumar (o
restar, si es negativo) al valor actual del jugador. Es opcional: si
una opción no lo trae, simplemente no cambia ninguna estadística
(la mayoría de las opciones hoy no lo necesitan).

**Claves válidas** (deben coincidir exactamente con
`services/consequence_service.py::VALID_EFFECT_KEYS` — el validador
te avisa si usás una que no está en esta lista):

`health`, `appearance`, `intelligence`, `discipline`, `creativity`,
`stress`, `happiness`, `charisma`, `empathy`, `reputation`,
`net_worth`.

**Lo que NO cubre `effects` todavía**: `annual_income` y `debt`. Se
excluyeron a propósito porque sus mutadores en `Player` no son un
simple delta (`set_annual_income()` fija un valor absoluto;
`add_debt()`/`reduce_debt()` son dos verbos distintos) — meterlos en
un diccionario plano de deltas habría sido ambiguo. Si hace falta
cubrirlos, es una extensión aparte con su propio formato.

**Magnitudes de referencia** (`config/game_config.py`, no aplicadas
ni validadas automáticamente — son solo para no inventar un número
distinto cada vez que se escribe un `effects`):

| Constante | Valor | Para qué |
|---|---|---|
| `SMALL_IMPACT` | 5 | Un matiz — casi no se nota en el momento, pero se acumula |
| `MEDIUM_IMPACT` | 10 | Una decisión con peso real |
| `LARGE_IMPACT` | 20 | Un punto de inflexión |
| `EXTREME_IMPACT` | 40 | Algo que cambia el rumbo de la historia |

Los valores ya vienen acotados por los mismos límites que usa el
resto del juego (0-100 para la mayoría, -100..100 para reputación) —
si un `effects` intenta pasarse, `Player` lo recorta solo y lo avisa
en el log, no hace falta que el contenido se cuide de eso.
