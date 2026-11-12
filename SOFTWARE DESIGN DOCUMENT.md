# SOFTWARE DESIGN DOCUMENT (SDD)

# Proyecto: What If?

Versión: 1.0 Estado: En desarrollo Autor: Equipo What If? Fecha: Agosto 2026


# Índice

1. Introducción

2. Objetivos del Diseño

3. Filosofía Arquitectónica

4. Principios SOLID

5. Arquitectura General

6. Capas del Sistema

7. Flujo General del Juego

8. Diagrama General

9. Módulos del Sistema

10. Diseño de Datos

11. Gestión de IA

12. Motor Narrativo

13. Sistema de Eventos

14. Sistema de Guardado

15. Gestión de Memoria

16. Manejo de Errores

17. Seguridad

18. Escalabilidad

19. Rendimiento

20. Convenciones

21. Dependencias


# 1. Introducción

Este documento describe el diseño interno del videojuego **What If?**.

Su propósito es servir como guía técnica para todos los desarrolladores del proyecto, estableciendo la arquitectura, responsabilidades, comunicación entre módulos y decisiones de diseño.

No describe reglas del juego, sino cómo el software está construido.


# 2. Objetivos del Diseño

La arquitectura fue diseñada para cumplir los siguientes objetivos:

- Alta mantenibilidad.

- Escalabilidad.

- Bajo acoplamiento.

- Alta cohesión.

- Fácil incorporación de nuevas historias.

- Soporte para IA.

- Separación entre lógica y contenido.

- Compatibilidad multiplataforma.

- Fácil depuración.


# 3. Filosofía Arquitectónica

El proyecto utiliza una arquitectura híbrida basada en:

- Clean Architecture

- MVC Adaptado

- Component Based Design

- Data Driven Design

El código nunca contendrá historias escritas directamente.

Todo el contenido será leído desde archivos JSON.

La lógica únicamente interpretará esos datos.

Esto permite añadir cientos de historias sin modificar el código fuente.


# 4. Principios SOLID

El proyecto sigue estrictamente los principios SOLID.

## Single Responsibility

Cada clase tiene una sola responsabilidad.

Ejemplo:

Player ↓

Sólo administra información del jugador.

Nunca controla historias.

Nunca controla IA.


## Open / Closed

Los módulos pueden extenderse sin modificar el código existente.

Ejemplo:

Agregar un nuevo sistema de logros.

No modifica GameEngine.

Sólo registra un nuevo AchievementManager.


## Liskov

Todas las clases derivadas podrán sustituir a sus clases padre sin alterar el comportamiento.


## Interface Segregation

Las clases sólo implementarán las interfaces que realmente utilizan.


## Dependency Inversion

Los módulos importantes nunca dependerán de implementaciones concretas.

Siempre dependerán de abstracciones.


# 5. Arquitectura General

La arquitectura está dividida en capas.

```
                 UI  
  
                 ↓  
  
           Game Engine  
  
                 ↓  
  
        Story Engine  
  
                 ↓  
  
     Decision / Event Engine  
  
                 ↓  
  
      AI Manager / Memory  
  
                 ↓  
  
      Models + Database  
  
                 ↓  
  
        JSON + SQLite
```

Cada capa sólo conoce la inmediatamente inferior.

Nunca salta niveles.


# 6. Capas del Sistema

## Presentación

Responsabilidad:

- Menús

- Botones

- Pantallas

- HUD

- Animaciones

Nunca contiene lógica del juego.


## Engine

Contiene toda la lógica principal.

Aquí viven:

GameEngine

StoryEngine

DecisionEngine

EndingEngine

InventoryEngine

AchievementEngine

TimeEngine

SaveEngine


## IA

Responsable de:

- construir prompts

- recordar decisiones

- generar NPC

- adaptar historias


## Datos

Representa:

Player

Story

Question

Ending

NPC

Inventory

Achievements

Events


## Persistencia

SQLite

JSON

Archivos de configuración


# 7. Flujo General

Inicio

↓

Carga Configuración

↓

Carga Historias

↓

Carga Usuario

↓

Carga Save

↓

GameEngine

↓

StoryEngine

↓

Pregunta

↓

Jugador responde

↓

DecisionEngine

↓

Evento

↓

Actualización IA

↓

Guardar progreso

↓

Siguiente historia


# 8. Diagrama General

```
                 UI  
  
                  │  
  
                  ▼  
  
          GameEngine  
  
        /      │      \\  
  
Story   Save   Inventory  
  
  │  
  
Decision Engine  
  
  │  
  
Event Engine  
  
  │  
  
Ending Engine  
  
  │  
  
AI Manager  
  
  │  
  
Memory  
  
  │  
  
SQLite  
  
JSON
```


# 9. Módulos

## GameEngine

Responsable de controlar todo el ciclo del juego.

Funciones:

- iniciar partida

- cargar partida

- cerrar partida

- reiniciar

Nunca conoce detalles de historias.


## StoryEngine

Responsable de:

- cargar historias

- validar historias

- controlar capítulos

No conoce interfaz.


## DecisionEngine

Recibe:

Pregunta

↓

Respuesta

↓

Consecuencia

Actualiza:

- karma

- inventario

- estadísticas


## EventEngine

Controla eventos dinámicos.

Ejemplo:

Lluvia

Terremoto

Encuentro NPC

Peleas

Viajes

Eventos aleatorios


## EndingEngine

Calcula:

Final correcto.

No usa valores fijos.

Analiza:

- karma

- relaciones

- decisiones

- inventario

- tiempo

- logros


## InventoryEngine

Controla:

Objetos

Equipamiento

Dinero

Coleccionables


## AchievementEngine

Desbloquea logros.

No modifica historias.

Sólo escucha eventos.


## SaveEngine

Convierte el estado del juego a SQLite.

Puede:

Guardar

Cargar

Exportar

Respaldar


## TimeEngine

Controla:

Hora

Día

Calendario

Tiempo restante

Eventos temporales


# 10. Diseño de Datos

Todo el contenido del juego está desacoplado del código fuente.

## JSON

Contiene:

Historias

NPC

Eventos

Preguntas

Finales

Objetos

Idiomas

Configuraciones


## SQLite

Contiene:

Usuarios

Partidas

Inventario

Configuraciones

Estadísticas

Logros

Historial


# 11. Gestión de IA

La IA nunca controla el juego.

Sólo propone contenido.

El GameEngine decide si acepta o no.

Flujo:

Jugador

↓

Prompt Builder

↓

IA

↓

Respuesta

↓

Validador

↓

Story Engine


# 12. Memoria

La memoria se divide en:

## Memoria permanente

Datos importantes.

Ejemplo:

Nombre

Edad

Relaciones

Objetos


## Memoria narrativa

Eventos recientes.

Últimas decisiones.

Conversaciones.


## Memoria contextual

Información necesaria para generar prompts.


# 13. Motor Narrativo

El StoryEngine funciona como una máquina de estados.

Estado actual

↓

Pregunta

↓

Respuesta

↓

Transición

↓

Nuevo estado

Cada nodo puede producir:

- evento

- NPC

- recompensa

- combate

- final


# 14. Sistema de Guardado

El juego utiliza guardado incremental.

No guarda únicamente el archivo completo.

Sólo registra cambios.

Beneficios:

Menor tamaño.

Mayor velocidad.

Menor riesgo de corrupción.


# 15. Manejo de Errores

Todos los módulos deben capturar excepciones.

Nunca finalizar abruptamente.

Errores críticos:

- JSON corrupto

- Save inválido

- Historia inexistente

Todos los errores serán registrados mediante Logger.


# 16. Seguridad

Validaciones:

JSON

SQLite

Entradas usuario

Prompts IA

Nunca ejecutar contenido generado por IA.

Toda salida será validada.


# 17. Escalabilidad

La arquitectura soporta:

Miles de historias.

Miles de NPC.

Decenas de idiomas.

Nuevos motores IA.

Nuevos sistemas de combate.

Multiplayer futuro.

Nuevos DLC.

Sin modificar GameEngine.


# 18. Rendimiento

Objetivos:

Carga inicial \< 3 segundos

Cambio entre escenas \< 300 ms

Guardado \< 150 ms

Uso RAM \< 500 MB

FPS objetivo:

60 FPS


# 19. Convenciones

PEP8

Typing obligatorio.

Docstrings Google Style.

Clases:

PascalCase

Funciones:

snake\_case

Constantes:

UPPER\_CASE

Archivos:

snake\_case.py


# 20. Dependencias

Python 3.12+

SQLite

PySide6

OpenAI API

python-dotenv

Pydantic

Requests

Loguru

pytest


# 21. Estrategia de Pruebas

Pruebas Unitarias

Cada Engine debe tener cobertura superior al 90%.

Pruebas de Integración

Validar comunicación entre motores.

Pruebas Narrativas

Verificar que cada historia tenga:

inicio

desarrollo

ramificaciones

final

sin nodos muertos.


# Conclusión

La arquitectura de What If? está diseñada para ser modular, mantenible y escalable. La separación estricta entre lógica, contenido y persistencia permite que el proyecto evolucione sin afectar componentes existentes, facilitando la incorporación de nuevas historias, sistemas y tecnologías. Esta base técnica busca garantizar un desarrollo sostenible y una experiencia de juego flexible, preparada para futuras expansiones y para la integración de capacidades avanzadas de inteligencia artificial.

