# VITA — Simulador de Vida Narrativo
## Game Design Document

*Documento de Diseño de Videojuego — Descripción Funcional de Sistemas*
*Versión 1.0 — Documento Interno de Diseño*

---

## Índice

- [Visión General y Pilares de Diseño](#visión-general-y-pilares-de-diseño)
- [1. Flujo Completo del Juego](#1-flujo-completo-del-juego)
- [2. Creación del Personaje](#2-creacion-del-personaje)
- [3. Variables del Personaje](#3-variables-del-personaje)
- [4. Sistema de Decisiones](#4-sistema-de-decisiones)
- [5. Sistema de Consecuencias](#5-sistema-de-consecuencias)
- [6. Sistema de Tiempo](#6-sistema-de-tiempo)
- [7. Sistema de Edad](#7-sistema-de-edad)
- [8. Sistema Económico](#8-sistema-economico)
- [9. Sistema Educativo](#9-sistema-educativo)
- [10. Profesiones](#10-profesiones)
- [11. Relaciones](#11-relaciones)
- [12. Matrimonio](#12-matrimonio)
- [13. Hijos](#13-hijos)
- [14. Salud](#14-salud)
- [15. Enfermedades](#15-enfermedades)
- [16. Estrés](#16-estres)
- [17. Felicidad](#17-felicidad)
- [18. Reputación](#18-reputacion)
- [19. Patrimonio](#19-patrimonio)
- [20. Jubilación](#20-jubilacion)
- [21. Eventos Especiales](#21-eventos-especiales)
- [22. Eventos Aleatorios](#22-eventos-aleatorios)
- [23. Sistema de IA Narrativa](#23-sistema-de-ia-narrativa)
- [24. Sistema de Generación de Imágenes](#24-sistema-de-generacion-de-imagenes)
- [25. Tipos de Imágenes](#25-tipos-de-imagenes)
- [26. Interfaz](#26-interfaz)
- [27. Guardado](#27-guardado)
- [28. Dificultad](#28-dificultad)
- [29. Condiciones de Derrota](#29-condiciones-de-derrota)
- [30. Finales Posibles](#30-finales-posibles)
- [31. Rejugabilidad](#31-rejugabilidad)
- [32. Estadísticas Finales](#32-estadisticas-finales)
- [Apéndice A — Diccionario Global de Variables del Personaje](#apéndice-a--diccionario-global-de-variables-del-personaje)

---

## Visión General y Pilares de Diseño

VITA es un simulador de vida narrativo en el que la persona jugadora controla el destino completo de un personaje, desde su nacimiento hasta su muerte, tomando decisiones en cada etapa que determinan su salud, su economía, sus relaciones y su legado. El juego combina la profundidad estadística de un simulador de gestión con la fuerza emocional de una herramienta narrativa asistida por Inteligencia Artificial, que redacta eventos únicos en tiempo real y genera imágenes que ilustran la vida del personaje.

El pilar central del diseño es la causalidad visible: ninguna variable cambia sin que la persona jugadora entienda por qué. Cada sistema documentado en este documento expone claramente sus entradas y salidas para que el equipo de programación pueda implementarlos como módulos independientes que se comunican mediante un estado global del personaje (en adelante, el Estado de Personaje o EP).

Pilares de diseño:

1. Consecuencia real — toda decisión relevante dentro del juego dispara efectos verificables, inmediatos y/o diferidos.

2. Vidas irrepetibles — la generación procedural de eventos y el sistema de IA narrativa aseguran que ninguna partida sea idéntica a otra.

3. Lectura emocional — la interfaz y las imágenes generadas priorizan que la persona jugadora sienta empatía por su personaje.

4. Simulación honesta — los sistemas económico, de salud y de envejecimiento se basan en modelos probabilísticos creíbles, no arbitrarios.

5. Rejugabilidad estructural — la variación de punto de partida (familia, país, genética, época) hace que cada partida ofrezca un dilema distinto.

Género: simulación de vida / narrativa generativa. Plataformas objetivo: PC y móvil. Público objetivo: adolescentes desde 16 años y adultos, clasificación orientativa PEGI 16 / ESRB Teen por temas de enfermedad, muerte, adicciones y relaciones adultas.

---

## 1. Flujo Completo del Juego

### Qué hace

Es el sistema orquestador de más alto nivel: define la secuencia macro de una partida, desde la pantalla de creación de personaje hasta la pantalla de estadísticas finales tras la muerte. Actúa como una máquina de estados finita con las fases: Creación → Bucle de Vida (Año/Turno) → Evento de Cierre (muerte o final especial) → Resumen Final → Nueva Partida.

Dentro del Bucle de Vida, el flujo por turno (normalmente un turno = un año, salvo excepciones detalladas en el Sistema de Tiempo) sigue el orden: 1) Actualización de edad y estadísticas base, 2) Resolución de eventos aleatorios asignados al año, 3) Presentación de decisiones activas (educación, trabajo, relaciones, salud, finanzas), 4) Aplicación de consecuencias, 5) Chequeo de condiciones de derrota, 6) Actualización de interfaz y generación de imagen del año si corresponde, 7) Avance de turno.

### Interacción con otros sistemas

Es el único sistema que tiene autoridad para invocar a todos los demás; actúa como despachador (dispatcher) central. Llama al Sistema de Tiempo para avanzar el reloj, al Sistema de Edad para envejecer al personaje, al Sistema de Eventos Aleatorios y Especiales para poblar el turno, al Sistema de Decisiones para recoger la interacción de la persona jugadora, al Sistema de Consecuencias para aplicar los resultados, y a los Sistemas de Condiciones de Derrota y Finales para determinar el cierre de la partida.

### Variables que modifica

- fase_actual (enum: CREACION, BUCLE_VIDA, CIERRE, RESUMEN)
- turno_actual (entero)
- cola_de_eventos_pendientes (lista)
- bandera_partida_activa (booleano)

### Información que recibe (entradas)

- Estado de Personaje (EP) completo al inicio del turno.
- Configuración de dificultad seleccionada.
- Semilla aleatoria de la partida (para reproducibilidad y para el sistema de logros).

### Información que produce (salidas)

- EP actualizado al final del turno.
- Señal de fin de partida con motivo (muerte natural, muerte por evento, derrota, final especial).
- Registro cronológico de la partida (línea de tiempo) que alimentará el Sistema de Estadísticas Finales.

---

## 2. Creación del Personaje

### Qué hace

Genera el punto de partida de la partida. La persona jugadora define parámetros iniciales controlables (nombre, apellido, género, país y época de nacimiento) mientras que el sistema genera de forma procedural los parámetros no controlables que dan variabilidad y rejugabilidad: familia de origen, nivel socioeconómico de nacimiento, genética de salud, rasgos de personalidad iniciales y un 'gancho narrativo' de nacimiento (por ejemplo, nacer en una familia numerosa, ser adoptado, nacer con una condición médica leve, heredar un pequeño patrimonio).

Ofrece un modo 'Aleatorio total' (todos los parámetros generados por el sistema) y un modo 'Personalizado' (la persona jugadora ajusta sliders de dificultad de partida: riqueza inicial, salud genética, entorno familiar), este último pensado como opción de accesibilidad y no como valor de dificultad narrativa por defecto.

### Interacción con otros sistemas

Escribe el EP inicial que consumirán absolutamente todos los demás sistemas. Se apoya en el Sistema Económico para fijar el patrimonio familiar de partida, en el Sistema de Salud para tirar la genética base, en el Sistema de Relaciones para generar a los padres (y hermanos si aplica) como personajes no jugables (PNJ) con sus propias variables, y en el Sistema de IA Narrativa para redactar la escena de nacimiento y la primera imagen del personaje (bebé).

### Variables que modifica

- identidad (nombre, apellido, género, fecha de nacimiento, país)
- genetica_salud (rango 0–100, afecta probabilidades futuras de enfermedad)
- nivel_socioeconomico_origen (Muy bajo / Bajo / Medio / Alto / Muy alto)
- rasgos_personalidad_iniciales (hasta 3 rasgos de una tabla de 20)
- arbol_familiar_inicial (referencias a PNJ padres/hermanos)
- gancho_narrativo_nacimiento (texto/id de evento especial de origen)

### Información que recibe (entradas)

- Selecciones manuales de la persona jugadora (si eligió modo personalizado).
- Semilla aleatoria de la partida.

### Información que produce (salidas)

- EP inicial completo, congelado en el turno 0.
- Lista de PNJ familiares iniciales con sus propias fichas resumidas.
- Primer evento narrativo (nacimiento) e imagen asociada.

---

## 3. Variables del Personaje

### Qué hace

Define y centraliza el Estado de Personaje (EP): la estructura de datos única que representa todo lo que el personaje es en un momento dado. No 'hace' una acción por sí sola, sino que actúa como la fuente única de verdad que todos los demás sistemas leen y escriben. Se divide en categorías: Identidad, Atributos Físicos, Atributos Mentales, Atributos Sociales, Economía, Historial y Relaciones.

Cada variable numérica del EP se mueve normalmente en una escala de 0 a 100 para permitir comparabilidad en interfaz (barras, anillos, semáforos), salvo las variables económicas, que son valores absolutos en la moneda del país de partida.

### Interacción con otros sistemas

Es leído y escrito por todos los sistemas del juego. Ninguna variable se modifica directamente por la interfaz: siempre pasa por el Sistema de Consecuencias, que es el único módulo autorizado a escribir en el EP, para poder mantener un registro auditable de por qué cambió cada valor.

### Variables que modifica

- Salud (0–100), Estrés (0–100), Felicidad (0–100)
- Inteligencia, Disciplina, Carisma, Creatividad, Empatía (0–100 cada uno)
- Reputación (–100 a 100), Apariencia (0–100)
- Patrimonio neto, Ingresos anuales, Deuda (valores absolutos)
- Nivel educativo alcanzado, Profesión actual
- Estado civil, Lista de relaciones activas (referencias a PNJ)
- Edad, Esperanza de vida estimada (recalculada cada turno)

### Información que recibe (entradas)

- Órdenes de escritura provenientes exclusivamente del Sistema de Consecuencias.

### Información que produce (salidas)

- Snapshot del EP bajo demanda para cualquier sistema o para la interfaz.
- Historial de cambios de cada variable (para el Sistema de Estadísticas Finales y para depuración).

---

## 4. Sistema de Decisiones

### Qué hace

Presenta a la persona jugadora las disyuntivas disponibles en cada turno: decisiones estructurales (elegir carrera, casarse, comprar una vivienda), decisiones de evento (respuesta a un evento aleatorio o especial) y decisiones de estilo de vida (hábitos recurrentes como hacer ejercicio, ahorrar, fumar). Filtra qué decisiones están disponibles según edad, patrimonio, nivel educativo y estado de salud actuales, de modo que solo se muestran opciones plausibles.

Cada decisión se presenta con la información necesaria para tomarla de forma informada (costes, riesgos conocidos) pero, deliberadamente, sin revelar probabilidades exactas de resultados inciertos, preservando la tensión narrativa.

### Interacción con otros sistemas

Consulta al EP para filtrar opciones válidas, consulta al Sistema de Dificultad para ajustar cuántas opciones de riesgo se muestran, y entrega la elección tomada al Sistema de Consecuencias para su resolución. También notifica al Sistema de IA Narrativa para que redacte la decisión y su desenlace en prosa.

### Variables que modifica

- No modifica variables directamente; genera el objeto 'decision_tomada' que consume el Sistema de Consecuencias.

### Información que recibe (entradas)

- EP actual (para filtrar opciones elegibles).
- Catálogo de decisiones disponibles por categoría.
- Selección de la persona jugadora (input de interfaz).

### Información que produce (salidas)

- Objeto 'decision_tomada' (id de decisión, opción elegida, contexto).
- Registro en el historial de decisiones de la partida.

---

## 5. Sistema de Consecuencias

### Qué hace

Es el único sistema con permiso de escritura sobre el EP. Traduce cada decisión tomada o evento resuelto en una lista de modificadores de variables, aplicando fórmulas de impacto inmediato (por ejemplo, aceptar un ascenso sube Ingresos y Estrés de inmediato) e impacto diferido (por ejemplo, fumar durante 10 turnos consecutivos incrementa gradualmente la probabilidad de enfermedad pulmonar en el Sistema de Enfermedades).

Gestiona también las 'consecuencias en cadena': un mismo resultado puede disparar efectos secundarios en otros sistemas (perder el trabajo reduce Ingresos, lo que el Sistema Económico traduce en riesgo de deuda, lo que el Sistema de Estrés traduce en una penalización adicional).

### Interacción con otros sistemas

Recibe entradas del Sistema de Decisiones y del Sistema de Eventos (aleatorios y especiales). Escribe en el EP (Sistema de Variables del Personaje). Notifica a los sistemas Económico, de Salud, de Estrés, de Felicidad y de Reputación cuando sus variables se ven afectadas, para que cada uno recalcule sus propios derivados internos (por ejemplo, el Sistema de Salud recalcula la esperanza de vida tras un cambio significativo).

### Variables que modifica

- Puede modificar cualquier variable del EP; mantiene un log de 'causa → efecto' para trazabilidad.

### Información que recibe (entradas)

- Objeto 'decision_tomada' o 'evento_resuelto'.
- Tablas de fórmulas de impacto por tipo de decisión/evento.
- Modificadores de dificultad activa.

### Información que produce (salidas)

- EP actualizado.
- Lista de 'efectos aplicados' (para mostrar en interfaz, ej. '+5 Felicidad, −10 Patrimonio').
- Disparadores hacia otros sistemas cuando se cruzan umbrales (ej. Salud < 20 dispara chequeo del Sistema de Enfermedades).

---

## 6. Sistema de Tiempo

### Qué hace

Gestiona el avance cronológico de la partida. La unidad estándar de turno es un año de vida del personaje, pero el sistema soporta 'micro-turnos' de meses o días para eventos críticos que requieren resolución más granular (por ejemplo, un embarazo, una enfermedad aguda o un juicio). Convierte el turno interno en una fecha de calendario del mundo de juego, permitiendo que los eventos históricos/especiales del país y época elegidos aparezcan en el momento correcto.

Controla también la velocidad de avance solicitada por la persona jugadora (avanzar año a año, o 'saltar' varios años si no hay decisiones pendientes relevantes, una función de conveniencia para etapas de vida con poca interacción como la primera infancia).

### Interacción con otros sistemas

Es invocado por el Flujo Completo del Juego al cierre de cada turno. Informa al Sistema de Edad para que envejezca al personaje y a los PNJ relacionados, y al Sistema de Eventos Aleatorios para que consulte su tabla de probabilidad por franja de edad y por fecha de calendario.

### Variables que modifica

- turno_actual, fecha_calendario_actual, velocidad_de_avance

### Información que recibe (entradas)

- Turno anterior y bandera de si quedan decisiones pendientes sin resolver (bloquea el salto de turno).

### Información que produce (salidas)

- Nuevo turno_actual y fecha_calendario_actual.
- Señal de 'nuevo año' o 'nuevo micro-turno' que otros sistemas escuchan.

---

## 7. Sistema de Edad

### Qué hace

Aplica el envejecimiento biológico del personaje y de todos los PNJ vinculados a él en cada turno. Determina la etapa de vida activa (Infancia 0–5, Niñez 6–12, Adolescencia 13–17, Adultez temprana 18–29, Adultez 30–49, Adultez media 50–64, Vejez 65+), etapa que condiciona qué decisiones, eventos y variables están activos (por ejemplo, el Sistema Educativo solo está activo hasta que se completa o abandona la formación; el Sistema de Jubilación solo se activa a partir de Adultez media).

Recalcula, en cada turno, un valor de 'esperanza de vida estimada' en función de la genética, el historial de salud, el estilo de vida y el patrimonio (acceso a mejor atención médica), valor que se usa como referencia interna para calibrar probabilidades de muerte natural, sin ser mostrado nunca como una cuenta atrás literal en interfaz.

### Interacción con otros sistemas

Recibe la señal de 'nuevo año' del Sistema de Tiempo. Modifica la variable Edad en el EP y notifica al Sistema de Salud (degradación natural asociada a la edad), al Sistema Educativo y de Profesiones (disponibilidad por edad), al Sistema de Relaciones/Matrimonio/Hijos (ventanas de fertilidad, mayoría de edad) y al Sistema de Jubilación.

### Variables que modifica

- Edad, Etapa_de_vida (enum), Esperanza_de_vida_estimada

### Información que recibe (entradas)

- Señal de nuevo turno del Sistema de Tiempo.
- Genética, historial de salud y patrimonio actuales del EP.

### Información que produce (salidas)

- Edad y Etapa_de_vida actualizadas.
- Esperanza_de_vida_estimada recalculada (uso interno).
- Disparo de eventos de transición de etapa (ej. 'Primer día de colegio', 'Mayoría de edad', 'Jubilación disponible').

---

## 8. Sistema Económico

### Qué hace

Modela ingresos, gastos, ahorro, deuda, inversión y patrimonio neto del personaje a lo largo de su vida. Calcula automáticamente gastos recurrentes según etapa de vida y decisiones tomadas (vivienda, alimentación, educación de los hijos, salud), y procesa decisiones financieras activas de la persona jugadora (pedir un préstamo, invertir en bolsa o bienes raíces, montar un negocio, declararse en bancarrota).

Incluye un submodelo de mercado simplificado (ciclos de expansión/recesión aleatorios ligados a la época y país de la partida) que afecta el rendimiento de inversiones y la estabilidad del empleo, dando peso estratégico a decisiones económicas de largo plazo.

### Interacción con otros sistemas

Recibe inputs del Sistema de Profesiones (salario), del Sistema Educativo (coste de matrícula, préstamos estudiantiles), del Sistema de Salud (gasto médico), del Sistema de Hijos (coste de crianza) y del Sistema de Decisiones (compras, inversiones). Escribe en el EP a través del Sistema de Consecuencias. Alimenta al Sistema de Estrés (la precariedad económica es una fuente directa de estrés) y al Sistema de Reputación (bancarrota o gran riqueza afectan percepción social).

### Variables que modifica

- Patrimonio_neto, Ingresos_anuales, Gastos_anuales, Deuda_total, Cartera_de_inversion, Puntaje_crediticio

### Información que recibe (entradas)

- Salario actual (Profesiones), gastos fijos por etapa de vida, decisiones financieras de la persona jugadora, estado del ciclo de mercado.

### Información que produce (salidas)

- Patrimonio_neto y demás variables económicas actualizadas cada turno.
- Alertas de riesgo (deuda excesiva, insolvencia) hacia interfaz y hacia el Sistema de Condiciones de Derrota.

---

## 9. Sistema Educativo

### Qué hace

Modela la trayectoria formativa: educación primaria y secundaria (obligatorias, con decisiones de rendimiento y actividades extracurriculares), y educación superior optativa (formación técnica, universidad, posgrado), cada una con requisitos de acceso (notas previas, patrimonio familiar o becas), coste y duración. El rendimiento académico se resuelve mediante una combinación de Inteligencia, Disciplina y decisiones activas de estudio tomadas por la persona jugadora.

Genera el 'expediente académico' que condiciona qué profesiones estarán disponibles en el Sistema de Profesiones y puede desbloquear eventos especiales propios (beca, expulsión, mención de honor).

### Interacción con otros sistemas

Depende del Sistema de Edad para activarse/desactivarse por etapa. Consume Inteligencia y Disciplina del EP y las incrementa como resultado del esfuerzo invertido. Informa al Sistema Económico del coste de matrícula y al Sistema de Profesiones del nivel educativo alcanzado como prerrequisito de empleabilidad. Interactúa con el Sistema de Estrés (exigencia académica) y el de Relaciones (amistades y primeras relaciones sentimentales en el entorno escolar).

### Variables que modifica

- Nivel_educativo_alcanzado, Rendimiento_academico_historico, Titulos_obtenidos (lista), Deuda_estudiantil

### Información que recibe (entradas)

- Etapa de vida actual, Inteligencia y Disciplina del EP, decisiones de estudio/esfuerzo de la persona jugadora, patrimonio familiar disponible.

### Información que produce (salidas)

- Nivel_educativo_alcanzado y Titulos_obtenidos actualizados.
- Lista de profesiones desbloqueadas hacia el Sistema de Profesiones.
- Coste acumulado hacia el Sistema Económico.

---

## 10. Profesiones

### Qué hace

Ofrece el catálogo de empleos disponibles según nivel educativo, edad, ubicación, atributos (una profesión creativa pondera Creatividad, una profesión de liderazgo pondera Carisma) e historial (experiencia previa, reputación). Modela la progresión de carrera dentro de una misma profesión (ascensos, despidos, cambio de empleo) y las profesiones alternativas de alto riesgo/alta recompensa (emprendimiento, carrera artística, política).

Cada turno en un empleo genera una tirada de eventos laborales propios (ascenso, conflicto con jefatura, oferta de la competencia, agotamiento) que se resuelven mediante el Sistema de Decisiones cuando requieren intervención de la persona jugadora, o de forma automática cuando son menores.

### Interacción con otros sistemas

Depende del Sistema Educativo (requisitos) y del Sistema de Edad (edad mínima/máxima laboral, jubilación). Entrega salario e Ingresos_anuales al Sistema Económico. Consume y modifica Carisma, Disciplina y Reputación. Es una fuente central de eventos para el Sistema de Estrés (carga laboral) y el de Felicidad (satisfacción laboral, propósito).

### Variables que modifica

- Profesion_actual, Nivel_jerarquico, Antiguedad_en_puesto, Historial_laboral (lista), Salario_actual

### Información que recibe (entradas)

- Nivel_educativo_alcanzado, atributos del EP, Reputación, ofertas de empleo generadas proceduralmente.

### Información que produce (salidas)

- Profesion_actual, Salario_actual, Historial_laboral actualizados.
- Eventos laborales enviados al Sistema de Decisiones/Eventos.
- Ingresos_anuales enviados al Sistema Económico.

---

## 11. Relaciones

### Qué hace

Modela vínculos interpersonales con PNJ: familia, amistades, parejas y relaciones profesionales. Cada PNJ tiene su propia ficha simplificada (personalidad, afinidad con el personaje jugador, su propia vida en segundo plano que evoluciona con el tiempo) y una variable de 'Afinidad' (0–100) por relación que sube o baja según interacciones, decisiones y eventos compartidos.

Genera eventos relacionales propios (peleas, reconciliaciones, traiciones, apoyo en momentos difíciles, fallecimiento de un PNJ cercano) y permite a la persona jugadora invertir tiempo/dinero/atención en fortalecer vínculos específicos, con rendimientos decrecientes si se descuidan otras áreas de vida.

### Interacción con otros sistemas

Es la base sobre la que se construyen el Sistema de Matrimonio y el Sistema de Hijos (ambos requieren una relación con Afinidad suficiente y ciertos hitos previos). Afecta al Sistema de Felicidad y de Estrés directamente. Se alimenta del Sistema de Eventos Aleatorios/Especiales para generar encuentros y del Sistema Educativo/Profesiones como contextos donde aparecen nuevos PNJ.

### Variables que modifica

- Lista_de_relaciones (PNJ, tipo_de_vinculo, Afinidad, historial_de_interacciones)

### Información que recibe (entradas)

- Decisiones de interacción de la persona jugadora, eventos generados, paso del tiempo (decaimiento natural de afinidad si no hay interacción).

### Información que produce (salidas)

- Lista_de_relaciones actualizada.
- Disparadores hacia Matrimonio, Hijos, Felicidad y Estrés.
- Eventos relacionales hacia el Sistema de IA Narrativa para su redacción.

---

## 12. Matrimonio

### Qué hace

Gestiona el ciclo completo de una unión formal: propuesta, aceptación/rechazo (probabilística según Afinidad, Reputación y contexto), boda (con coste económico configurable y evento narrativo propio), vida marital (eventos de convivencia, aniversarios, crisis) y posible disolución (separación o divorcio, con reparto de patrimonio según reglas configurables del país de la partida).

La calidad del matrimonio se modela con una variable de 'Satisfacción_marital' independiente de la Afinidad general, que decae con el tiempo si no se invierte en la relación y que es sensible a eventos externos (infidelidad, dificultades económicas, llegada de hijos).

### Interacción con otros sistemas

Requiere una relación de pareja previa gestionada por el Sistema de Relaciones. Interactúa con el Sistema Económico (coste de boda, fusión/reparto de patrimonio), el Sistema de Hijos (habilita ciertas rutas), el de Felicidad/Estrés (fuerte impacto en ambos) y el de Reputación (el divorcio puede penalizar reputación según época/cultura simulada).

### Variables que modifica

- Estado_civil, Conyuge_actual (referencia PNJ), Satisfaccion_marital, Historial_matrimonial (lista)

### Información que recibe (entradas)

- Afinidad de la relación de pareja, decisión de propuesta/aceptación, eventos de vida compartida.

### Información que produce (salidas)

- Estado_civil y Satisfaccion_marital actualizados.
- Movimientos patrimoniales hacia el Sistema Económico.
- Eventos de boda/divorcio hacia IA Narrativa e Imágenes.

---

## 13. Hijos

### Qué hace

Modela la decisión de tener descendencia (biológica o adopción), el proceso de embarazo cuando aplica (con micro-turnos mensuales y riesgos de salud gestionados junto al Sistema de Salud), el nacimiento y la crianza del hijo como nuevo PNJ con su propio EP simplificado que envejece en paralelo. La persona jugadora toma decisiones de crianza (estilo educativo, inversión de tiempo/dinero) que afectan los atributos iniciales del hijo, en un eco reducido del propio Sistema de Creación de Personaje.

Permite, opcionalmente, 'heredar el control' del hijo al fallecer o jubilarse el personaje original (modo legado/dinastía), reiniciando el bucle de vida sobre un nuevo personaje jugable que conserva parte del patrimonio y la reputación familiar.

### Interacción con otros sistemas

Depende del Sistema de Relaciones/Matrimonio (o de decisiones de monoparentalidad/adopción) y del Sistema de Salud (fertilidad, riesgos de embarazo). Genera carga en el Sistema Económico (coste de crianza) y en el de Estrés/Felicidad (ambos direccionales, según narrativa). Alimenta al Sistema Educativo del hijo como nuevo personaje en formación.

### Variables que modifica

- Lista_de_hijos (PNJ con EP simplificado), Estado_de_embarazo, Estilo_de_crianza

### Información que recibe (entradas)

- Decisión de concepción/adopción, Afinidad y Estado_civil, genética combinada de los progenitores.

### Información que produce (salidas)

- Lista_de_hijos actualizada.
- Coste de crianza hacia el Sistema Económico.
- Nuevo personaje jugable disponible para el modo legado (si se activa).

---

## 14. Salud

### Qué hace

Es el sistema fisiológico central: mantiene la variable Salud (0–100) como resultado de genética, edad, estilo de vida (ejercicio, alimentación, sueño, sustancias), acceso a atención médica (dependiente del patrimonio y del país) y eventos aleatorios. Ofrece decisiones activas de cuidado (revisiones médicas, tratamientos preventivos, cirugías electivas) y calcula el recálculo periódico de la Esperanza_de_vida_estimada usado por el Sistema de Edad.

Gestiona lesiones agudas (accidentes) de forma diferenciada de las condiciones crónicas, que se delegan al Sistema de Enfermedades cuando la Salud cae por debajo de umbrales críticos o cuando la genética/estilo de vida acumulan suficiente 'riesgo latente'.

### Interacción con otros sistemas

Recibe inputs de casi todos los sistemas (Edad para degradación natural, Económico para acceso a atención médica, Profesiones para riesgo laboral, Estrés para impacto psicosomático). Alimenta al Sistema de Enfermedades cuando se cruzan umbrales de riesgo, al Sistema de Felicidad (la mala salud reduce felicidad) y al Sistema de Condiciones de Derrota (Salud a 0 es una vía de muerte).

### Variables que modifica

- Salud, Habitos (ejercicio, dieta, sueño, consumo de sustancias — cada uno con su propia escala), Riesgo_latente_por_organo (interno)

### Información que recibe (entradas)

- Genetica_salud, edad, decisiones de estilo de vida y de atención médica, eventos de accidente.

### Información que produce (salidas)

- Salud actualizada.
- Disparo hacia el Sistema de Enfermedades cuando se supera un umbral de riesgo.
- Esperanza_de_vida_estimada recalculada hacia el Sistema de Edad.

---

## 15. Enfermedades

### Qué hace

Gestiona la aparición, progresión y resolución de condiciones médicas específicas (agudas y crónicas), desde un catálogo con distintos niveles de gravedad (leve, moderada, grave, terminal). Cada enfermedad tiene una probabilidad base modulada por genética, edad, hábitos y azar, y una vez activa sigue su propio curso por turnos (mejora, estabilización, empeoramiento) según el tratamiento elegido mediante el Sistema de Decisiones y el acceso económico a dicho tratamiento.

Modela también enfermedades mentales (ansiedad, depresión, adicciones) que se activan preferentemente desde umbrales sostenidos del Sistema de Estrés en lugar de la genética física, y que a su vez retroalimentan negativamente Estrés y Felicidad si no se tratan.

### Interacción con otros sistemas

Se activa por disparo del Sistema de Salud o del Sistema de Estrés. Consume recursos del Sistema Económico (coste de tratamiento) y del tiempo del Sistema de Profesiones (bajas laborales). Es una de las vías directas hacia el Sistema de Condiciones de Derrota (enfermedad terminal no tratada) y genera eventos propios para el Sistema de IA Narrativa (diagnóstico, remisión, despedida).

### Variables que modifica

- Lista_de_enfermedades_activas (id, gravedad, turno_de_inicio, tratamiento_actual, pronostico)

### Información que recibe (entradas)

- Riesgo_latente_por_organo, umbrales de Estrés sostenido, tirada aleatoria modulada por dificultad.

### Información que produce (salidas)

- Lista_de_enfermedades_activas actualizada.
- Penalizaciones a Salud, Estrés y capacidad laboral.
- Señal de muerte por enfermedad hacia Condiciones de Derrota si el pronóstico llega a terminal sin remisión.

---

## 16. Estrés

### Qué hace

Cuantifica la carga psicológica acumulada (0–100) proveniente de fuentes múltiples y simultáneas: presión laboral, dificultades económicas, conflictos relacionales, exigencia académica, problemas de salud propios o de seres queridos, y eventos traumáticos. Se acumula con inercia (no sube ni baja instantáneamente salvo picos por eventos graves) y decae naturalmente con el tiempo si la persona jugadora invierte en actividades de descompresión (ocio, descanso, terapia).

Cuando el Estrés se sostiene por encima de umbrales durante varios turnos consecutivos, incrementa significativamente la probabilidad de activación de enfermedades mentales gestionadas por el Sistema de Enfermedades y reduce el rendimiento en Profesiones y Educación.

### Interacción con otros sistemas

Recibe inputs de Profesiones, Sistema Económico, Relaciones/Matrimonio, Educación y Salud. Alimenta directamente a Enfermedades (umbral sostenido) y a Felicidad (relación inversa fuerte). Sus decisiones de mitigación (terapia, vacaciones, hobbies) pasan por el Sistema de Decisiones y tienen coste económico o de tiempo.

### Variables que modifica

- Estres (0–100), Fuentes_activas_de_estres (lista con peso de cada una)

### Información que recibe (entradas)

- Eventos y decisiones de todos los sistemas listados como fuente, decisiones activas de mitigación.

### Información que produce (salidas)

- Estres actualizado.
- Disparo hacia Enfermedades si se sostiene sobre umbral crítico.
- Penalización hacia Profesiones/Educación (rendimiento) y hacia Felicidad.

---

## 17. Felicidad

### Qué hace

Sintetiza el bienestar subjetivo global del personaje (0–100) como una combinación ponderada de Salud, Estrés (inverso), Satisfacción_marital, calidad de las relaciones activas, satisfacción laboral, logros conseguidos y coherencia entre valores del personaje (rasgos de personalidad) y decisiones tomadas por la persona jugadora. No es una variable que se module directamente por decisiones aisladas, sino un derivado recalculado cada turno.

Sirve como el principal indicador de 'éxito de vida' visible en interfaz junto al patrimonio, y es la variable central sobre la que se evalúan varios de los Finales Posibles (por ejemplo, el final 'vida plena' exige Felicidad sostenida alta durante la vejez, independientemente del patrimonio acumulado).

### Interacción con otros sistemas

Es un derivado que lee de Salud, Estrés, Relaciones, Matrimonio, Profesiones y Reputación. No escribe en otros sistemas de forma directa, pero es leída por el Sistema de Eventos Especiales (algunos eventos solo aparecen con Felicidad baja o alta sostenida) y por el Sistema de Finales/Estadísticas Finales.

### Variables que modifica

- Felicidad (0–100), Felicidad_historica (serie temporal para el resumen final)

### Información que recibe (entradas)

- Snapshot del EP completo cada turno (lectura, no escritura, de Salud, Estrés, Relaciones, etc.).

### Información que produce (salidas)

- Felicidad recalculada cada turno.
- Serie histórica hacia Estadísticas Finales.
- Señales de umbral hacia Eventos Especiales y Finales Posibles.

---

## 18. Reputación

### Qué hace

Mide cómo perciben al personaje su entorno cercano y, si aplica, la sociedad/medios (–100 a 100), a partir de decisiones públicas (comportamiento profesional, escándalos, actos filantrópicos, logros notables) y del cumplimiento o incumplimiento de normas sociales del país/época de la partida. Se subdivide internamente en Reputación_personal (círculo cercano) y Reputación_publica (solo relevante para profesiones de alta visibilidad como política, espectáculo o negocios).

Genera consecuencias de puerta: cierta Reputación mínima es requisito para desbloquear oportunidades (ascensos, matrimonio con ciertos PNJ, cargos públicos) y una Reputación muy negativa puede desbloquear eventos especiales negativos propios (juicio, escándalo mediático, ostracismo social).

### Interacción con otros sistemas

Recibe inputs de Profesiones, Matrimonio, Eventos Especiales y decisiones éticas del Sistema de Decisiones. Es consultada como prerrequisito por Profesiones, Matrimonio y ciertos Eventos Especiales, y contribuye como componente ponderado de Felicidad.

### Variables que modifica

- Reputacion_personal, Reputacion_publica

### Información que recibe (entradas)

- Decisiones públicas/éticas, resultados de eventos especiales, nivel de visibilidad de la profesión actual.

### Información que produce (salidas)

- Reputacion_personal y Reputacion_publica actualizadas.
- Habilitación/bloqueo de oportunidades hacia Profesiones y Matrimonio.

---

## 19. Patrimonio

### Qué hace

Consolida en una única cifra el valor neto total del personaje (activos menos pasivos): efectivo, inversiones, propiedades, negocios, menos deudas pendientes. Es la variable de referencia para clasificar el nivel de vida del personaje en interfaz (categorías: Precariedad, Ajustado, Estable, Acomodado, Rico, Muy rico) y para calcular la herencia disponible en el modo legado/dinastía al fallecer el personaje.

A diferencia de Ingresos_anuales (flujo), el Patrimonio es un acumulado (stock) que el Sistema Económico recalcula cada turno sumando ahorro neto, rendimiento de inversiones y variaciones de valor de activos (por ejemplo, revalorización inmobiliaria simulada por ciclos de mercado).

### Interacción con otros sistemas

Es un derivado directo del Sistema Económico; no tiene lógica propia de cálculo fuera de él, pero se expone como variable independiente porque es consumida por el Sistema de Reputación (percepción de estatus), el de Matrimonio (reparto en divorcio, dote/aporte a la boda), el de Hijos (herencia) y el de Estadísticas Finales.

### Variables que modifica

- Patrimonio_neto (idéntica a la variable homónima del Sistema Económico, expuesta aquí como interfaz de consulta)

### Información que recibe (entradas)

- Snapshot del Sistema Económico cada turno.

### Información que produce (salidas)

- Categoría de nivel de vida hacia interfaz.
- Monto de herencia disponible hacia el Sistema de Hijos/modo legado y hacia Estadísticas Finales.

---

## 20. Jubilación

### Qué hace

Se activa a partir de la etapa Adultez media y ofrece a la persona jugadora la decisión de retirarse de la vida laboral activa, ya sea a la edad estándar del país simulado (con pensión calculada según historial de aportes/Ingresos_anuales acumulados) o de forma anticipada/tardía (con penalización o bonificación respectiva sobre la pensión). Tras la jubilación, el personaje deja de generar Salario_actual y pasa a recibir Ingreso_por_pension, y el Sistema de Profesiones queda inactivo salvo por actividades ocasionales (consultorías, voluntariado) que pueden mantenerse por decisión activa.

La etapa de jubilación introduce su propio catálogo de eventos y decisiones (nuevos hobbies, viajes, tiempo con nietos, voluntariado, deterioro gradual de salud) con menor peso económico y mayor peso en Felicidad y Relaciones.

### Interacción con otros sistemas

Depende del Sistema de Edad (etapa mínima) y del Sistema de Profesiones (historial para calcular pensión). Modifica el Sistema Económico (cambio de fuente de ingresos) y reduce la relevancia de Estrés de origen laboral, mientras puede aumentar el peso de Salud y Relaciones sobre Felicidad.

### Variables que modifica

- Estado_de_jubilacion (booleano), Edad_de_jubilacion, Ingreso_por_pension

### Información que recibe (entradas)

- Historial_laboral y Ingresos_anuales acumulados, decisión de retiro de la persona jugadora, edad actual.

### Información que produce (salidas)

- Estado_de_jubilacion e Ingreso_por_pension hacia el Sistema Económico.
- Desbloqueo del catálogo de eventos/decisiones de vejez activa.

---

## 21. Eventos Especiales

### Qué hace

Catálogo de eventos únicos, no repetibles dentro de una misma partida, ligados a hitos de vida predecibles (graduación, boda, nacimiento de un hijo, jubilación) o a condiciones narrativas específicas del EP (alcanzar cierto patrimonio, cierta Reputación, cierta combinación de rasgos de personalidad). A diferencia de los eventos aleatorios, estos están diseñados a mano por el equipo narrativo como 'grandes momentos' con múltiples opciones de resolución y consecuencias de mayor peso relativo que un evento aleatorio ordinario.

Sirven como principal fuente de contenido para los Finales Posibles: varios finales requieren haber vivido (o evitado) determinados eventos especiales.

### Interacción con otros sistemas

Es consultado por el Flujo Completo del Juego en cada turno junto con Eventos Aleatorios. Lee condiciones de disparo desde el EP completo. Entrega el evento disparado al Sistema de Decisiones para su resolución interactiva y al Sistema de IA Narrativa para su redacción y a Generación de Imágenes para su ilustración.

### Variables que modifica

- No modifica variables directamente; produce el objeto 'evento_especial_disparado' que pasa por Decisiones → Consecuencias.

### Información que recibe (entradas)

- EP completo (para evaluar condiciones de disparo), catálogo de eventos especiales con sus condiciones y banderas de 'ya visto' en la partida actual.

### Información que produce (salidas)

- Evento especial disparado (si corresponde) hacia Decisiones/IA Narrativa/Imágenes.
- Actualización de banderas de eventos ya vistos.

---

## 22. Eventos Aleatorios

### Qué hace

Genera la variabilidad cotidiana de cada turno mediante una tabla ponderada de eventos menores (desde encontrar dinero en la calle hasta un conflicto vecinal) filtrada por etapa de vida, contexto socioeconómico, atributos del EP y Sistema de Dificultad. A diferencia de los Eventos Especiales, son repetibles entre partidas y entre turnos, y su peso individual sobre el EP es menor, pero su repetición constante es la que da 'textura' de vida cotidiana a la simulación.

Incluye eventos completamente triviales sin decisión (solo narrativa/imagen, sin impacto en variables) para dar variedad de tono sin sobrecargar de decisiones a la persona jugadora en cada turno.

### Interacción con otros sistemas

Es consultado en cada turno por el Flujo Completo del Juego. Su tabla de probabilidades está modulada por el Sistema de Dificultad y filtrada por Edad, Salud, Sistema Económico y Relaciones activas. Entrega los eventos disparados a Decisiones (si requieren elección) o directamente a Consecuencias (si son automáticos), y en ambos casos a IA Narrativa/Imágenes para su presentación.

### Variables que modifica

- No modifica variables directamente; produce 0 a N objetos 'evento_aleatorio_disparado' por turno.

### Información que recibe (entradas)

- EP actual, tabla de eventos ponderada por etapa de vida, nivel de dificultad activo, semilla aleatoria del turno.

### Información que produce (salidas)

- Lista de eventos aleatorios disparados en el turno hacia Decisiones/Consecuencias/IA Narrativa.

---

## 23. Sistema de IA Narrativa

### Qué hace

Convierte los datos estructurados producidos por el resto de sistemas (decisiones, eventos, cambios de variables) en prosa legible y emocionalmente coherente: la 'voz' que narra la vida del personaje. Redacta tanto viñetas cortas por turno como escenas extensas para eventos especiales, adaptando tono y vocabulario a la edad del personaje, la época/país de la partida y el rasgo de personalidad dominante, de modo que dos partidas con las mismas cifras de EP puedan leerse de forma distinta si el personaje es, por ejemplo, cínico frente a optimista.

Mantiene coherencia narrativa a lo largo de la partida mediante un resumen persistente de contexto (nombre de PNJ relevantes, hitos ya ocurridos, tono general de la vida hasta el momento) que se inyecta en cada nueva generación para evitar contradicciones (por ejemplo, mencionar a una expareja como si aún estuviera presente).

### Interacción con otros sistemas

Es consumidor de casi todos los sistemas (recibe el objeto de evento/decisión/consecuencia ya resuelto) y proveedor exclusivo de texto hacia la Interfaz. Coordina con el Sistema de Generación de Imágenes para que la escena ilustrada corresponda al mismo evento narrado.

### Variables que modifica

- No modifica variables del EP; mantiene su propio 'resumen_de_contexto_narrativo' interno como memoria de trabajo.

### Información que recibe (entradas)

- Objeto de evento/decisión/consecuencia resuelto, snapshot relevante del EP, resumen_de_contexto_narrativo previo, rasgos de personalidad del personaje.

### Información que produce (salidas)

- Texto narrativo del turno/evento.
- resumen_de_contexto_narrativo actualizado.
- Prompt descriptivo de la escena hacia el Sistema de Generación de Imágenes.

---

## 24. Sistema de Generación de Imágenes

### Qué hace

Produce una ilustración representativa de momentos relevantes de la vida del personaje a partir del prompt descriptivo entregado por la IA Narrativa, manteniendo consistencia visual del personaje a lo largo de la partida (mismo rango de edad aparente, mismos rasgos físicos definidos en la Creación del Personaje, envejecimiento progresivo coherente con la Edad actual) mediante una ficha de apariencia persistente que se referencia en cada generación.

Gestiona la frecuencia de generación (no todos los turnos producen imagen, para evitar coste computacional y fatiga visual: se prioriza hitos de vida, eventos especiales y cambios físicos relevantes) y ofrece control de estilo visual (realista, ilustración, cómic) seleccionable por la persona jugadora al inicio de la partida.

### Interacción con otros sistemas

Recibe el prompt del Sistema de IA Narrativa y la ficha de apariencia persistente derivada de la Creación del Personaje y actualizada por el Sistema de Edad (envejecimiento) y por eventos que alteren la apariencia (accidentes, cambios de estilo de vida). Entrega la imagen final a la Interfaz y al Sistema de Estadísticas Finales para el 'álbum de vida' de cierre de partida.

### Variables que modifica

- No modifica variables del EP; mantiene ficha_de_apariencia_persistente (rasgos físicos base + estado de envejecimiento + estilo visual elegido).

### Información que recibe (entradas)

- Prompt descriptivo de la escena, ficha_de_apariencia_persistente, estilo visual elegido, tipo de imagen requerido (ver Tipos de Imágenes).

### Información que produce (salidas)

- Imagen generada del evento/turno.
- ficha_de_apariencia_persistente actualizada si el evento altera la apariencia.

---

## 25. Tipos de Imágenes

### Qué hace

Define la taxonomía de imágenes que el Sistema de Generación de Imágenes puede producir, cada una con su propio propósito de interfaz y frecuencia esperada: 1) Retrato de etapa — actualización del retrato principal del personaje al entrar en una nueva etapa de vida; 2) Escena de evento especial — ilustración de un hito único (boda, graduación, nacimiento); 3) Viñeta de evento aleatorio — ilustración ligera y de menor detalle para eventos cotidianos; 4) Imagen de PNJ — retrato de un personaje relevante (pareja, hijo) al conocerse o al cambiar significativamente su relación con el jugador; 5) Imagen de cierre — la escena final de la partida (muerte o final especial), usada en el resumen de Estadísticas Finales.

Cada tipo tiene su propio nivel de detalle y coste de generación esperado, priorizando calidad en Retrato de etapa, Escena de evento especial e Imagen de cierre, y velocidad/ligereza en Viñeta de evento aleatorio.

### Interacción con otros sistemas

Es consultado por el Sistema de Generación de Imágenes para decidir el nivel de detalle y el encuadre de cada solicitud, y por la Interfaz para decidir dónde y a qué tamaño mostrar cada imagen (retrato fijo en cabecera, imagen de evento en el cuerpo del turno, álbum de vida en el resumen final).

### Variables que modifica

- No aplica (es una taxonomía de configuración, no un estado del personaje).

### Información que recibe (entradas)

- Tipo de evento/momento que solicita imagen (desde IA Narrativa o Flujo del Juego).

### Información que produce (salidas)

- Parámetros de generación (nivel de detalle, encuadre, prioridad) hacia el Sistema de Generación de Imágenes.

---

## 26. Interfaz

### Qué hace

Es la capa de presentación que traduce el EP y las salidas de todos los sistemas en pantallas comprensibles: pantalla principal de turno (retrato, barras de Salud/Felicidad/Estrés, resumen económico, texto narrativo del turno, imagen asociada, decisiones pendientes como botones/tarjetas), pantalla de ficha completa de personaje (todas las variables detalladas, línea de tiempo de vida), pantalla de relaciones (árbol/lista de PNJ con su Afinidad), y pantalla de resumen final. Prioriza jerarquía visual clara: lo narrativo y emocional en primer plano, lo numérico accesible pero secundario.

Incluye capa de accesibilidad (tamaño de texto, modo de alto contraste, narración por voz opcional del texto generado) y capa de configuración (dificultad, estilo visual de imágenes, velocidad de avance de turno).

### Interacción con otros sistemas

Es puramente consumidora: no modifica el EP directamente, solo captura los inputs de la persona jugadora y los envía al Sistema de Decisiones o de Flujo del Juego. Se suscribe a las salidas de todos los demás sistemas para renderizarlas.

### Variables que modifica

- No modifica variables de personaje; mantiene su propio estado de UI (pantalla activa, elementos expandidos, preferencias de accesibilidad).

### Información que recibe (entradas)

- Snapshot del EP, texto narrativo, imagen del turno, catálogo de decisiones pendientes.

### Información que produce (salidas)

- Input de la persona jugadora (selección de decisión, comandos de navegación, cambios de configuración) hacia Decisiones/Flujo del Juego/Guardado.

---

## 27. Guardado

### Qué hace

Persiste el estado íntegro de la partida (EP completo, historial de decisiones y eventos, resumen_de_contexto_narrativo, ficha_de_apariencia_persistente, configuración de dificultad y semilla aleatoria) para permitir continuar la partida en otra sesión sin pérdida de coherencia narrativa ni estadística. Ofrece guardado automático al cierre de cada turno y guardado manual bajo demanda, con soporte para múltiples ranuras de partida (varias 'vidas' en paralelo).

Incluye un modo de exportación del resumen de una vida finalizada (texto + álbum de imágenes + estadísticas) para compartir fuera del juego, independiente del guardado de partidas activas.

### Interacción con otros sistemas

Se suscribe a la señal de 'fin de turno' del Flujo Completo del Juego para disparar el guardado automático. Es el único sistema, junto al de Consecuencias, con acceso de escritura a almacenamiento persistente; todos los demás sistemas leen desde la partida cargada en memoria.

### Variables que modifica

- No modifica el EP; gestiona metadatos_de_partida (id de partida, fecha de guardado, ranura utilizada).

### Información que recibe (entradas)

- EP completo y estados internos de todos los sistemas al cierre de turno o bajo solicitud manual.

### Información que produce (salidas)

- Archivo/registro de partida guardado.
- Confirmación hacia Interfaz.
- Paquete de exportación de resumen de vida (cuando se solicita).

---

## 28. Dificultad

### Qué hace

Define un conjunto de perfiles (Historia guiada, Estándar, Vida real, Hardcore) que modulan globalmente la severidad de los sistemas probabilísticos: probabilidad base de eventos negativos, dureza de las condiciones económicas de partida, velocidad de degradación de Salud/Estrés, y disponibilidad de 'redes de seguridad' narrativas (por ejemplo, en Historia guiada ciertos eventos catastróficos tienen probabilidad reducida; en Hardcore se eliminan salvaguardas y aumenta la probabilidad de eventos adversos encadenados).

No introduce mecánicas nuevas: actúa como un conjunto de multiplicadores y banderas que otros sistemas (Eventos Aleatorios, Sistema Económico, Salud, Enfermedades) consultan al calcular sus propias probabilidades e impactos.

### Interacción con otros sistemas

Es consultado por Eventos Aleatorios, Eventos Especiales, Sistema Económico, Salud, Enfermedades y Estrés en cada cálculo probabilístico relevante. Se fija una sola vez al crear el personaje pero puede exponerse como ajustable a mitad de partida como opción de accesibilidad, con advertencia de que puede afectar la coherencia de dificultad narrativa.

### Variables que modifica

- Perfil_de_dificultad (enum), tabla_de_multiplicadores asociada

### Información que recibe (entradas)

- Selección de la persona jugadora en Creación del Personaje o en configuración.

### Información que produce (salidas)

- tabla_de_multiplicadores consultada por los sistemas probabilísticos en cada cálculo.

---

## 29. Condiciones de Derrota

### Qué hace

Monitorea continuamente el EP para detectar condiciones de cierre de partida por muerte: muerte natural por vejez (probabilidad creciente sobre la Esperanza_de_vida_estimada), muerte por enfermedad terminal no controlada, muerte por evento (accidente grave, evento especial con desenlace fatal aceptado por la persona jugadora), y, en configuraciones de dificultad alta, muerte por circunstancias extremas derivadas de Salud o Estrés en 0 sostenido. No existe una 'condición de derrota' en el sentido de fracaso obligatorio de partida: la muerte es el cierre natural y esperado de toda vida simulada, y el sistema está diseñado para que llegue con sentido narrativo, no como penalización arbitraria.

Distingue explícitamente entre el cierre 'normal' de partida (muerte) y los Finales Posibles de tono especial, que son variaciones narrativas del mismo cierre según cómo se vivió la partida.

### Interacción con otros sistemas

Es evaluado cada turno por el Flujo Completo del Juego tras aplicar Consecuencias. Recibe señales directas de Salud, Enfermedades y Eventos Especiales/Aleatorios con desenlace fatal. Al activarse, dispara el Sistema de Finales Posibles y congela el EP para el Sistema de Estadísticas Finales.

### Variables que modifica

- bandera_muerte (booleano), causa_de_muerte (enum/texto), turno_de_muerte

### Información que recibe (entradas)

- Salud, Lista_de_enfermedades_activas, Esperanza_de_vida_estimada, eventos con desenlace fatal.

### Información que produce (salidas)

- bandera_muerte y causa_de_muerte hacia Finales Posibles.
- Señal de fin de partida hacia el Flujo Completo del Juego.

---

## 30. Finales Posibles

### Qué hace

Clasifica el cierre de la partida en una de varias 'etiquetas de final' narrativas, evaluadas sobre el EP completo en el momento de la muerte: por ejemplo, Legado Familiar (patrimonio y relaciones altas, hijos con buena trayectoria), Vida Plena (Felicidad sostenida alta pese a patrimonio bajo/medio), Ambición Cumplida (Reputación y logros profesionales altos), Redención (recuperación notable tras un periodo de vida muy negativo), Tragedia Evitable (muerte prematura vinculada directamente a decisiones de riesgo ignoradas), y Vida Anónima (final neutro sin hitos destacados, tratado con el mismo respeto narrativo que los demás).

Cada final tiene su propio cierre narrativo redactado por la IA Narrativa y su imagen de cierre correspondiente, evitando que el juego module la finalidad de una vida como 'buena' o 'mala' de forma simplista: varios finales pueden coexistir como etiquetas (por ejemplo, Legado Familiar + Redención).

### Interacción con otros sistemas

Se dispara tras la Condición de Derrota. Evalúa el EP completo y el historial de decisiones de toda la partida. Entrega la(s) etiqueta(s) de final a la IA Narrativa (cierre) y al Sistema de Estadísticas Finales (clasificación del resumen).

### Variables que modifica

- etiquetas_de_final_obtenidas (lista)

### Información que recibe (entradas)

- EP completo en el momento de la muerte, historial de decisiones y eventos de toda la partida, causa_de_muerte.

### Información que produce (salidas)

- etiquetas_de_final_obtenidas hacia IA Narrativa e Imágenes (cierre) y hacia Estadísticas Finales.

---

## 31. Rejugabilidad

### Qué hace

No es un sistema con estado propio en tiempo de ejecución, sino el conjunto de mecanismos deliberados de diseño que hacen que partidas sucesivas se sientan distintas: variabilidad de la Creación del Personaje (familia, país, época, genética), tablas de Eventos Aleatorios/Especiales lo bastante amplias para no repetirse en pocas partidas, perfiles de Dificultad alternativos, modo legado/dinastía que encadena partidas, y un sistema de 'logros de vida' transversal a partidas (por ejemplo, 'alcanza cierto patrimonio antes de los 30 en 3 partidas distintas') que incentiva explorar rutas diferentes.

Incluye 'desafíos de vida' opcionales seleccionables antes de empezar (por ejemplo, 'nace en pobreza extrema', 'personaje con enfermedad crónica desde la infancia') que restringen deliberadamente el punto de partida para generar dilemas distintos a los de una partida estándar.

### Interacción con otros sistemas

Se apoya en la Creación del Personaje, Eventos Aleatorios/Especiales, Dificultad y el modo legado del Sistema de Hijos para su variabilidad estructural, y en un registro transversal de logros que persiste fuera de una partida individual (a diferencia del Sistema de Guardado, que persiste una partida concreta).

### Variables que modifica

- registro_de_logros_global (persistente fuera de partida), desafios_de_vida_disponibles

### Información que recibe (entradas)

- Historial agregado de partidas jugadas por la persona usuaria.

### Información que produce (salidas)

- Logros desbloqueados hacia Interfaz.
- Nuevos desafíos de vida u opciones de Creación del Personaje desbloqueados.

---

## 32. Estadísticas Finales

### Qué hace

Genera el resumen de cierre de partida tras la muerte del personaje: línea de tiempo completa de hitos, gráficas de evolución de Salud/Felicidad/Estrés/Patrimonio a lo largo de la vida, álbum de imágenes generadas durante la partida, etiquetas de final obtenidas, y comparativas opcionales contra partidas anteriores de la misma persona jugadora (mismo país/época o global). Cierra con la narrativa de cierre redactada por la IA Narrativa y ofrece la opción de exportar el resumen o iniciar una nueva partida (posiblemente en modo legado si hay hijos elegibles).

### Interacción con otros sistemas

Es el consumidor final de todos los sistemas: lee el historial completo del EP, el registro cronológico del Flujo del Juego, las etiquetas de Finales Posibles y el álbum del Sistema de Generación de Imágenes. Entrega su salida a la Interfaz (pantalla de resumen) y opcionalmente al Sistema de Guardado (exportación) y al de Rejugabilidad (actualización del registro de logros global).

### Variables que modifica

- No modifica el EP (la partida ya cerró); produce resumen_final (estructura de solo lectura).

### Información que recibe (entradas)

- Historial completo de la partida (EP a lo largo del tiempo, decisiones, eventos, imágenes), etiquetas_de_final_obtenidas, causa_de_muerte.

### Información que produce (salidas)

- resumen_final estructurado hacia Interfaz.
- Paquete de exportación hacia Guardado (si se solicita).
- Actualización del registro_de_logros_global hacia Rejugabilidad.

---

## Apéndice A — Diccionario Global de Variables del Personaje

Tabla de referencia rápida con las variables centrales del Estado de Personaje (EP), su rango de valores y el sistema que actúa como su fuente principal de verdad. Variables auxiliares internas de cada sistema se detallan en la sección correspondiente de cada sistema.

| Variable | Descripción | Rango | Sistema de origen |
|---|---|---|---|
| Salud | Estado físico general del personaje. | 0–100 | Salud |
| Estres | Carga psicológica acumulada. | 0–100 | Estrés |
| Felicidad | Bienestar subjetivo global, derivado. | 0–100 | Felicidad |
| Inteligencia | Capacidad cognitiva y de aprendizaje. | 0–100 | Creación / Educativo |
| Disciplina | Constancia y autocontrol. | 0–100 | Creación / Educativo |
| Carisma | Habilidad social e influencia. | 0–100 | Creación / Profesiones |
| Creatividad | Capacidad de generar ideas originales. | 0–100 | Creación / Educativo |
| Empatia | Capacidad de conexión emocional con otros. | 0–100 | Creación / Relaciones |
| Reputacion_personal | Percepción del entorno cercano. | -100–100 | Reputación |
| Reputacion_publica | Percepción social/mediática amplia. | -100–100 | Reputación |
| Apariencia | Percepción estética, afecta ciertos eventos sociales. | 0–100 | Salud / Creación |
| Patrimonio_neto | Activos menos pasivos totales. | Valor absoluto | Económico / Patrimonio |
| Ingresos_anuales | Flujo de ingreso anual actual. | Valor absoluto | Económico / Profesiones |
| Deuda_total | Obligaciones financieras pendientes. | Valor absoluto | Económico |
| Nivel_educativo_alcanzado | Máximo grado formativo completado. | Enum | Educativo |
| Profesion_actual | Empleo activo del personaje. | Enum/Texto | Profesiones |
| Estado_civil | Situación marital actual. | Enum | Matrimonio |
| Satisfaccion_marital | Calidad percibida del matrimonio. | 0–100 | Matrimonio |
| Lista_de_relaciones | PNJ vinculados y su Afinidad. | Lista | Relaciones |
| Lista_de_hijos | Descendencia con EP simplificado. | Lista | Hijos |
| Lista_de_enfermedades_activas | Condiciones médicas en curso. | Lista | Enfermedades |
| Edad | Edad actual del personaje en años. | 0–120 | Edad |
| Etapa_de_vida | Fase vital activa. | Enum | Edad |
| Esperanza_de_vida_estimada | Referencia interna de longevidad. | Años | Edad / Salud |
| Estado_de_jubilacion | Indica si el personaje está retirado. | Booleano | Jubilación |
| bandera_muerte / causa_de_muerte | Cierre de partida y su motivo. | Booleano/Enum | Condiciones de Derrota |
| etiquetas_de_final_obtenidas | Clasificación narrativa del cierre. | Lista | Finales Posibles |
