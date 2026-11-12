# WHAT IF...?

## Documento de Visión del Proyecto (Project Vision Document)

**Versión:** 1.0 **Estado:** Pre-producción **Tipo de documento:** Vision Document / North Star Document **Audiencia:** Equipo interno (diseño, arte, tecnología, narrativa, producción)


## 0. Cómo usar este documento

Este documento no es un pitch de marketing ni un resumen de una línea. Es el documento de referencia que cualquier persona que se incorpore al equipo —diseñador, programador, artista, escritor, productor— debe poder leer y, al terminar, entender **qué juego estamos haciendo, por qué lo estamos haciendo así, y qué NO estamos haciendo**.

Cuando exista una duda de diseño durante el desarrollo ("¿esto encaja en What If...?"), la respuesta debe poder derivarse de este documento. Si no puede derivarse, este documento está incompleto y debe actualizarse — no se debe improvisar la visión sobre la marcha.


## 1. Visión del Proyecto

**What If...?** es un simulador narrativo de vida impulsado por Inteligencia Artificial, en el que el jugador no controla a un personaje a través de mecánicas de acción, sino a través de **decisiones**. El juego genera una biografía única, coherente y visualmente ilustrada para cada partida, construida en tiempo real a partir de las elecciones del jugador.

La promesa central del producto es simple de enunciar y difícil de lograr:

> *"Cada partida es la vida de una persona que nunca existió, pero que pudo haber existido."*

El jugador no compite, no acumula puntuación, no "gana". El jugador **vive**. El resultado final de cada partida no es un marcador, es un **álbum de recuerdos**: una colección de momentos ilustrados, decisiones tomadas y consecuencias vividas, que cuentan la historia de una vida completa, desde su creación hasta su desenlace (natural, trágico, exitoso, mediocre, extraordinario — el juego no juzga cuál es el "buen" final).

What If...? existe en la intersección de tres categorías que históricamente no se han combinado bien:

1. **Simuladores de vida** (BitLife, The Sims) — fuertes en sistemas, débiles en narrativa y en peso emocional de las decisiones.

2. **Ficción interactiva / novelas visuales** (Reigns, Choice of Games) — fuertes en narrativa y decisiones con peso, débiles en variedad infinita y personalización visual.

3. **Herramientas generativas de IA** (generación de texto e imagen) — fuertes en variedad infinita, débiles en curación, coherencia y diseño de experiencia.

La visión del proyecto es tomar lo mejor de las tres y resolver, mediante diseño e ingeniería, los problemas que impiden que coexistan: coherencia narrativa a largo plazo, consistencia visual del personaje a través de cientos de decisiones, y una sensación de autoría del jugador sobre una historia que en realidad está siendo co-escrita por un modelo de IA.

**Lo que el juego NO es:**

- No es un juego de gestión de recursos con el objetivo de optimizar una puntuación.

- No es un juego de "final correcto" — no existe un final correcto.

- No es un chatbot de texto libre; el jugador elige entre opciones curadas, no escribe prompts.

- No es una demo tecnológica de IA generativa disfrazada de juego. La IA es el motor invisible; el juego es la experiencia.


## 2. Filosofía

### 2.1 Principio rector: "El jugador debe sentir, no calcular"

Todo sistema, toda pantalla, toda decisión de UI debe evaluarse contra una pregunta: *¿esto hace que el jugador sienta que está viviendo una vida, o que está administrando una hoja de cálculo?* Ante la duda, el diseño se inclina siempre hacia lo emocional y lo memorable, no hacia lo óptimo o lo eficiente.

### 2.2 Principio rector: "No hay build óptimo"

En el momento en que exista una combinación de decisiones "correcta" para maximizar algo, el juego habrá fallado en su propósito. No habrá stat a maximizar, no habrá "meta". Las consecuencias deben ser interesantes, no punitivas ni recompensadas en abstracto.

### 2.3 Principio rector: "Consistencia por encima de sorpresa técnica"

Es preferible una ilustración ligeramente menos espectacular que sea consistente con las anteriores, a una ilustración impresionante que rompa la continuidad visual del personaje. La confianza del jugador en que "esa persona en la imagen soy yo" es un activo narrativo más valioso que la calidad puntual de un frame.

### 2.4 Principio rector: "La IA escribe, el diseño cura"

La IA generativa (texto e imagen) es un motor de contenido, no un motor de diseño. Las reglas de qué tipo de eventos pueden ocurrir, con qué frecuencia, bajo qué condiciones y con qué tono, están definidas por sistemas de diseño determinísticos. La IA rellena esos sistemas; no los reemplaza. Esto es lo que separa a What If...? de "un chatbot con imágenes".

### 2.5 Principio rector: "Cada vida merece ser recordada, no todas merecen ser felices"

El juego debe estar dispuesto a contar historias de fracaso, pérdida, enfermedad, pobreza o muerte temprana con la misma honestidad narrativa que las historias de éxito. Suavizar sistemáticamente las consecuencias negativas mataría la credibilidad emocional del producto. (Ver sección 9, Riesgos, para el tratamiento responsable de estos temas.)


## 3. Público Objetivo

### 3.1 Perfil primario

- Jugadores de 16–35 años, con fuerte presencia femenina (histórico de BitLife y simuladores de vida muestra ~55-60% audiencia femenina).

- Jugadores de dispositivos móviles y PC casual que disfrutan de historias personales, generación de contenido, y "coleccionar momentos" (paralelo directo con el consumo de contenido tipo Sims, Animal Crossing, journaling apps).

- Usuarios activos de redes sociales que comparten capturas de pantalla y momentos narrativos — el "álbum de recuerdos" está diseñado explícitamente para ser compartible.

### 3.2 Perfil secundario

- Aficionados a la ficción interactiva y novelas visuales que buscan mayor rejugabilidad y variedad que las historias de ramificación manual tradicional.

- Early adopters de herramientas de IA generativa curiosos por ver una aplicación pulida y "productizada" de estas tecnologías en un contexto lúdico, no utilitario.

### 3.3 A quién NO apunta este juego (en su versión inicial)

- Jugadores hardcore de simulación de gestión profunda (Football Manager, Dwarf Fortress) que esperan sistemas numéricos complejos y optimización.

- Jugadores que buscan multijugador competitivo o social síncrono.

- Audiencias que buscan un juego de "alta habilidad mecánica" (reflejos, puntería, combate).


## 4. Experiencia del Jugador

### 4.1 La fantasía central

La fantasía que vendemos no es "ser poderoso" ni "ganar". Es **la fantasía de la posibilidad**: *"¿Qué hubiera pasado si...?"* — de ahí el nombre del proyecto. Cada partida es una respuesta distinta a esa pregunta, y el jugador siente curiosidad genuina por descubrir cómo se desarrolla "esta versión" de una vida.

### 4.2 El arco emocional de una sesión

1. **Creación (curiosidad y proyección):** el jugador construye a alguien — puede ser un alter ego, un opuesto radical, o un experimento social ("¿qué tal si nazco en la pobreza extrema y con un talento artístico?").

2. **Primeros años (familiaridad y ternura):** decisiones de bajo riesgo (infancia, colegio) que generan apego emocional antes de que las decisiones importen de verdad.

3. **Bifurcación (tensión):** las decisiones empiezan a tener consecuencias visibles y el jugador siente el peso de estar cerrando puertas al abrir otras.

4. **Consolidación (identidad):** la vida del personaje adquiere una "forma" reconocible — una carrera, una familia, una reputación — y el jugador empieza a sentir que está protegiendo o cultivando algo.

5. **Cierre (reflexión):** el desenlace, sea cual sea, se presenta como el álbum completo. El jugador hojea su propia historia antes de decidir empezar una nueva.

### 4.3 El "álbum de recuerdos" como experiencia central

El juego debe tratarse visualmente y estructuralmente como un álbum, no como un dashboard de stats. La metáfora de interfaz dominante es la de un **libro/álbum fotográfico viviente**: páginas, fotografías, anotaciones a mano, marcas de tiempo ("18 años", "Ciudad de México", "3 años después"), en lugar de barras de progreso, iconos de stats flotantes o HUDs de videojuego tradicional.

### 4.4 Consistencia visual del personaje (requisito de experiencia, no solo técnico)

El jugador debe poder mirar la ilustración del momento 40 y reconocer inequívocamente al mismo personaje que vio en el momento 2, con el envejecimiento, cambios de peinado, ropa o contexto socioeconómico reflejados de forma creíble. Esto es innegociable para la experiencia: es la diferencia entre "estoy viendo mi vida" y "estoy viendo imágenes al azar con un texto relacionado".


## 5. Mecánicas Principales

### 5.1 Creación de personaje

El jugador define, al inicio de cada partida, un conjunto de parámetros fundacionales:

- **Identidad:** nombre, edad inicial, género/presentación (opcional).

- **Contexto geográfico:** país y ciudad — determina el trasfondo cultural, económico e idiomático de los eventos generados.

- **Contexto socioeconómico:** nivel económico familiar de origen.

- **Salud:** condición de salud inicial (general, o condiciones específicas relevantes).

- **Familia:** estructura familiar (padres, hermanos, dinámica familiar).

- **Educación:** punto de partida educativo (o proyectado, si el personaje inicia siendo niño).

- **Rasgos de personalidad:** un conjunto acotado de rasgos (ej. modelo simplificado tipo Big Five o un set propio de 8–10 rasgos) que influyen en qué tipo de opciones se presentan y cómo reacciona el mundo del juego.

- **Talentos:** predisposiciones (artístico, analítico, físico, social, etc.) que desbloquean líneas narrativas específicas.

- **Aspiraciones:** un objetivo de vida declarado por el jugador (no garantizado, pero que orienta el tono de los eventos generados y habilita arcos narrativos de largo plazo relacionados con perseguirlo, alcanzarlo o fallarlo).

Estos parámetros no son "stats a subir" — son la **semilla narrativa** que el sistema generativo utiliza como contexto persistente en cada generación de evento.

### 5.2 El evento (unidad mínima de juego)

Cada momento de juego es un **Evento**, compuesto por:

- Un contexto narrativo (texto generado, coherente con el estado actual del personaje).

- Entre 3 y 4 opciones de decisión, mutuamente excluyentes.

- Consecuencias asociadas a cada opción (cambios de estado, no necesariamente inmediatos ni obvios para el jugador).

Los eventos se clasifican internamente en:

- **Eventos de progresión** (edad, etapas de vida — escuela, primer empleo, jubilación).

- **Eventos derivados de estado** (generados porque una variable cruzó un umbral: salud baja, riqueza alta, relación en riesgo).

- **Eventos de aspiración** (relacionados directamente con el objetivo de vida declarado).

- **Eventos aleatorios de color** (eventos menores que añaden textura sin gran consecuencia, evitando que el juego se sienta como una cadena ininterrumpida de decisiones trascendentales).

### 5.3 Momentos Ilustrados (Memory Moments)

No todos los eventos generan una ilustración — eso saturaría la experiencia y devaluaría el impacto visual. Un subconjunto curado de eventos, los **Momentos Clave**, dispara la generación de una ilustración:

- Nacimiento / creación del personaje.

- Hitos educativos y profesionales (graduación, primer empleo, ascensos importantes, jubilación).

- Hitos relacionales (primer amor, matrimonio, nacimiento de hijos, rupturas significativas).

- Hitos de salud (enfermedad grave, recuperación, accidentes).

- Consecuencias extremas de decisiones de alto riesgo (éxito o fracaso rotundo de una apuesta narrativa importante).

- El desenlace final de la partida.

Cada Momento Clave generado se almacena automáticamente en el **Álbum**, junto con su texto, fecha narrativa y la decisión que lo originó.

### 5.4 Consistencia del personaje en la ilustración

Mecánicamente, esto se resuelve mediante un **perfil visual persistente del personaje** (ficha de rasgos físicos derivada en la creación de personaje + evolución controlada por reglas de edad/contexto), que se inyecta como referencia en cada generación de imagen, junto con el contexto del evento específico. El jugador nunca ve ni edita esta ficha directamente — es infraestructura invisible que garantiza continuidad.

### 5.5 El Álbum de Vida

Interfaz central de "meta-progresión" (no hay progresión de poder, hay progresión de historia). El Álbum es navegable en cualquier momento durante la partida y funciona como:

- Registro cronológico de decisiones y momentos ilustrados.

- Elemento de compartición social (exportable como imagen o secuencia).

- Ancla emocional que refuerza la inversión del jugador en "esta" vida particular.

### 5.6 Lo que el juego NO incluye en su mecánica central (por diseño, no por limitación)

- No hay sistema de combate ni habilidad mecánica de reflejos.

- No hay "puntuación de vida" ni ranking global de partidas.

- No hay micro-gestión de inventario o recursos al estilo simulador de gestión.

- No hay opción de "reintentar" una decisión pasada dentro de la misma partida (la permanencia de las consecuencias es central a la filosofía del juego).


## 6. Loop Principal del Juego (Core Loop)

```
 ┌─────────────────────────────────────────────────────────────┐  
 │                                                               │  
 │   1. CREAR PERSONAJE (una vez por partida)                   │  
 │              │                                               │  
 │              ▼                                               │  
 │   2. EL JUEGO PRESENTA UNA SITUACIÓN                         │  
 │      (texto generado con contexto de estado actual)          │  
 │              │                                               │  
 │              ▼                                               │  
 │   3. EL JUGADOR ELIGE ENTRE 2 OPCIONES                     │  
 │              │                                               │  
 │              ▼                                               │  
 │   4. EL SISTEMA ACTUALIZA EL ESTADO DEL PERSONAJE            │  
 │      (salud, relaciones, economía, educación, reputación...) │  
 │              │                                               │  
 │              ▼                                               │  
 │   5. ¿ES UN MOMENTO CLAVE?  ──NO──►  volver al paso 2         │  
 │              │ SÍ                                            │  
 │              ▼                                               │  
 │   6. SE GENERA UNA ILUSTRACIÓN CONSISTENTE                   │  
 │      Y SE AÑADE AL ÁLBUM DE VIDA                             │  
 │              │                                               │  
 │              ▼                                               │  
 │   7. ¿EL PERSONAJE MURIÓ / LLEGÓ A UN CIERRE NARRATIVO?      │  
 │              │                                               │  
 │       NO ◄───┴───► SÍ                                        │  
 │       │                    │                                 │  
 │  vuelve al paso 2      8. SE PRESENTA EL ÁLBUM COMPLETO       │  
 │                            (resumen de vida, compartible)     │  
 │                                    │                          │  
 │                                    ▼                          │  
 │                          9. NUEVA PARTIDA (nueva vida)        │  
 │                                                               │  
 └─────────────────────────────────────────────────────────────┘
```

El loop está diseñado para funcionar en sesiones cortas  y en sesiones largas (30+ minutos, varias etapas de vida en una sesión). Ninguna decisión individual debería tardar al jugador más de unos segundos en tomar — la fricción está en el peso emocional, no en la complejidad de la interfaz.


## 7. Diferenciadores

| Diferenciador | Por qué importa |
| - | - |
| **Consistencia visual del personaje a lo largo de toda la partida** | Ningún competidor directo (BitLife, simuladores similares) ofrece esto hoy con calidad de ilustración real; es la barrera técnica/de diseño más difícil de replicar. |
| **Narrativa generativa contextual, no plantillas fijas** | BitLife y similares usan bloques de texto predefinidos con variables; What If...? genera contenido nuevo coherente con el historial completo del personaje. |
| **El "Álbum de Vida" como objeto central, no un log de eventos** | Convierte el historial de decisiones en un artefacto emocional y compartible, no en una lista de texto. |
| **Ausencia deliberada de condición de victoria** | Diferencia al juego de la categoría "simulador de gestión" y lo acerca a la categoría "experiencia narrativa", ampliando el atractivo a audiencias no gamers. |
| **Personalización profunda desde el origen (país, ciudad, nivel económico)** | Da relevancia cultural y verosimilitud global, no un "default" cultural único (evita el sesgo anglocéntrico típico del género). |



## 8. Inspiraciones

**Simuladores de vida y decisión:**

- *BitLife* — estructura de eventos y decisiones, ritmo de sesión corta.

- *Reigns* — el peso dramático de decisiones binarias/simples repetidas indefinidamente.

- *The Sims* — fantasía de vida y personalización de personaje (referencia de tono, no de mecánica).

**Ficción interactiva y narrativa de consecuencias:**

- *Choice of Games* / *Fallen London* — ramificación narrativa basada en estado acumulado, no en árboles fijos.

- *80 Days* (Inkle) — generación de variedad narrativa combinatoria con coherencia de tono.

**Objetos y formatos emocionales (referencias fuera del videojuego):**

- Álbumes fotográficos familiares y "libros de vida" — la referencia formal para la interfaz del Álbum.

- Documentales biográficos y formato "This Is Your Life" — la estructura de "revivir momentos clave" al final de una etapa.

**Referencias técnicas (generación de imagen consistente de personaje):**

- Herramientas de generación de personajes consistentes mediante referencia de identidad (LoRA / IP-Adapter y técnicas equivalentes) — como referencia de la capacidad técnica que el equipo de tecnología deberá evaluar e implementar, no como producto a imitar.


## 9. Riesgos

### 9.1 Riesgos de diseño

- **Riesgo de "sopa narrativa":** que la IA genere eventos genéricos, repetitivos o desconectados del historial del personaje, rompiendo la ilusión de continuidad. *Mitigación:* sistema de memoria narrativa estructurada (no solo "historial de texto crudo" sino un estado de personaje resumido y versionado que se inyecta en cada generación); curación editorial de un banco base de arquetipos de eventos.

- **Riesgo de pérdida de agencia percibida:** si el jugador siente que sus decisiones no importan realmente (los eventos "parecen" personalizados pero convergen siempre a resultados similares), la promesa central del juego se rompe. *Mitigación:* testing constante de "divergencia narrativa" — métricas internas que midan cuánto varían las historias entre partidas con decisiones distintas desde el mismo punto de partida.

### 9.2 Riesgos técnicos

- **Riesgo de inconsistencia visual del personaje:** es, con diferencia, el mayor riesgo técnico del proyecto. Si el personaje "cambia de cara" entre ilustraciones, se rompe la experiencia central descrita en la sección 4.4. *Mitigación:* investigación y prototipado temprano (spike técnico) de la solución de identidad visual persistente antes de comprometer el resto del pipeline de producción; esto debe validarse en la fase de preproducción, no asumirse como resuelto.

- **Riesgo de costo y latencia de generación (texto + imagen) a escala:** generar contenido único por jugador y por decisión tiene un costo variable por partida, a diferencia de un juego con contenido fijo. *Mitigación:* diseño híbrido — banco de contenido pre-generado y curado para eventos comunes/tempranos, generación en vivo reservada para momentos de alto valor narrativo; caching de ilustraciones por combinación de rasgos cuando sea posible.

- **Riesgo de moderación de contenido generado:** al ser contenido generado dinámicamente (texto e imagen), existe riesgo de outputs inapropiados, especialmente considerando que el juego trata temas de salud, muerte, relaciones y dificultades de vida. *Mitigación:* capas de filtrado y validación de contenido antes de mostrarlo al jugador; límites de diseño explícitos sobre qué temas pueden generarse y con qué nivel de detalle (ver 9.3).

### 9.3 Riesgos de sensibilidad temática y responsabilidad

- El juego aborda temas potencialmente sensibles: enfermedad, muerte, pobreza, fracaso, dinámicas familiares difíciles. *Mitigación:* un documento de lineamientos de tono editorial (separado de este documento) que defina explícitamente qué se puede narrar, con qué nivel de gráficidad, y qué se evita por completo (contenido explícito de autolesión, violencia gráfica, contenido sexual con menores, discurso de odio, etc.). Estos lineamientos deben revisarse con el equipo de confianza y seguridad antes de producción de contenido a escala. *Nota:* el manejo de temas como salud mental o duelo dentro del juego debe hacerse con cuidado narrativo — el objetivo es honestidad emocional, no explotación del drama por impacto.

### 9.4 Riesgos de mercado

- **Riesgo de categorización confusa:** el producto no encaja limpiamente en una categoría de tienda existente (¿simulador? ¿narrativa? ¿casual?), lo que puede dificultar descubribilidad. *Mitigación:* estrategia de posicionamiento y marketing clara desde preproducción, apoyada en el "álbum compartible" como gancho viral distintivo.

- **Riesgo de percepción de "juego de IA genérico":** el mercado está saturado de productos que usan IA generativa como gancho superficial; existe riesgo de que el público asuma que el juego es un wrapper simple sobre un modelo de lenguaje. *Mitigación:* el pulido de producto (interfaz de álbum, dirección de arte, curación de momentos clave) debe comunicar claramente que la IA es infraestructura invisible al servicio de una experiencia diseñada, no el producto en sí mismo.


## 10. Alcance Inicial (MVP / Vertical Slice)

El alcance inicial busca validar el mayor riesgo del proyecto —consistencia visual del personaje combinada con narrativa generativa coherente— con el menor scope posible.

**Incluido en el MVP:**

- Creación de personaje con el set completo de parámetros descritos en la sección 5.1, con opciones acotadas y curadas (no texto libre) para simplificar el control de calidad narrativa.

- Un motor de eventos con un banco inicial curado de entre 150–250 eventos base (con variantes generativas sobre ellos), cubriendo desde la niñez hasta una etapa adulta temprana/media (no se requiere cubrir el ciclo de vida completo hasta la vejez en el MVP).

- Entre 3–4 opciones por evento, con lógica de consecuencias sobre un set acotado de variables de estado (salud, economía, educación, relaciones, felicidad/satisfacción, reputación).

- Sistema de Momentos Clave con generación de ilustración para un conjunto definido y limitado de hitos (8–12 tipos de hitos cubiertos en el MVP).

- Solución técnica validada de consistencia visual del personaje (spike de preproducción, ver 9.2), aplicada de forma funcional aunque no perfecta.

- Álbum de Vida navegable dentro de la partida, con exportación básica (captura/compartir) de al menos un formato.

- Un solo idioma y una región cultural de partida cuidadosamente curada (para controlar calidad narrativa antes de expandir a más países/idiomas).

**Explícitamente fuera del MVP:**

- Cobertura del ciclo de vida completo (vejez, muerte por edad avanzada) — puede simularse con un cierre narrativo genérico temporal.

- Múltiples idiomas y localización cultural profunda por país.

- Funciones sociales/multijugador (comparar vidas entre jugadores, retos, etc.).

- Personalización visual manual del personaje por parte del jugador (edición de apariencia más allá de lo que el sistema deriva de los parámetros de creación).

- Monetización final (el modelo de negocio se define en un documento aparte, no es objeto de este Vision Document).


## 11. Roadmap General

**Fase 0 — Preproducción / Spikes técnicos (validación de riesgo)** Objetivo: probar que el mayor riesgo del proyecto (consistencia visual del personaje + coherencia narrativa de largo plazo) es técnicamente viable con la calidad y el costo requeridos. Entregable: prototipo no jugable que demuestre 10–15 ilustraciones consecutivas del mismo personaje a través de distintas edades/contextos, y una cadena de 20–30 eventos generados coherentes entre sí.

**Fase 1 — Vertical Slice** Objetivo: una porción jugable de principio a fin (creación de personaje → varias decisiones → al menos 3 Momentos Clave ilustrados → cierre narrativo de ejemplo), con calidad de producción representativa del producto final. Entregable: build jugable internamente, usada para validar la experiencia de jugador descrita en la sección 4 con testers reales.

**Fase 2 — MVP (según sección 10)** Objetivo: producto completo según el alcance definido, listo para testing cerrado (closed beta). Entregable: build de beta cerrada.

**Fase 3 — Beta abierta y pulido** Objetivo: ampliar banco de eventos, pulir dirección de arte del álbum, ajustar balance de sistemas de estado con datos reales de testers, endurecer moderación de contenido. Entregable: build de beta pública / soft launch en mercados limitados.

**Fase 4 — Lanzamiento 1.0** Objetivo: lanzamiento comercial del alcance validado en Fases 2–3, con el idioma y región curados en el MVP, posiblemente ampliado según resultados de la beta.

*(Este roadmap es deliberadamente agnóstico de fechas: los tiempos dependen de los resultados de los spikes técnicos de la Fase 0, que son la variable de mayor incertidumbre del proyecto.)*


## 12. Posibles Expansiones Futuras

*(Fuera de alcance para la versión 1.0, listadas aquí para que el equipo diseñe con extensibilidad en mente, no para comprometer trabajo actual.)*

- **Expansión de ciclo de vida completo:** cobertura de vejez, herencia narrativa (posibilidad de iniciar una nueva partida como hijo/a del personaje anterior, heredando contexto).

- **Localización profunda multi-país:** expansión del sistema de generación contextual a más países y ciudades con verosimilitud cultural específica (no solo traducción de idioma, sino de contexto social, educativo y económico).

- **Modo social/comparativo:** posibilidad de comparar álbumes de vida entre jugadores (amigos), sin convertir el juego en competitivo — la comparación sería de curiosidad narrativa, no de ranking.

- **Personalización visual asistida:** permitir al jugador ajustar o guiar aspectos de la apariencia del personaje dentro de los límites de la consistencia del sistema.

- **"Vidas cruzadas":** eventos generados que reflejan el contexto histórico/temporal (por ejemplo, ambientar partidas en distintas décadas), añadiendo una capa de profundidad narrativa e histórica.

- **Herramientas de creación/exportación avanzada del Álbum:** generación automática de un video-resumen o "biopic" corto de la partida, pensado explícitamente para compartir en redes sociales.

- **Modo "editor de aspiraciones" ampliado:** aspiraciones compuestas o cambiantes a lo largo de la vida del personaje, en lugar de una sola aspiración fija desde la creación.


## Cierre

Este documento debe tratarse como un organismo vivo durante la preproducción: se espera que evolucione a medida que los spikes técnicos (Fase 0) confirmen o refuten supuestos de diseño, especialmente en torno a la consistencia visual del personaje (el riesgo \#1 del proyecto, ver sección 9.2). Cualquier cambio sustancial a la visión aquí descrita debe documentarse como una revisión versionada de este mismo archivo, no como decisiones dispersas en canales de comunicación informales.

**Recuérdese siempre la pregunta rectora del proyecto:** *¿esta decisión de diseño ayuda a que el jugador sienta que está viviendo una vida única, o lo convierte en un administrador de sistemas?* Si la respuesta apunta a lo segundo, se ha desviado del propósito de What If...?

