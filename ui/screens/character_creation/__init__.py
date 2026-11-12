"""
ui/screens/character_creation/
================================

Flujo de creación de personaje en 3 pasos:

    Paso 1 (identity_step.py)  — nombre, apellido, género
    Paso 2 (origin_step.py)    — país, ciudad
    Paso 3 (attributes_step.py)— distribución de 20 puntos entre
                                  los 10 atributos de Player

El widget orquestador (character_creation_screen.py) recibe los tres
pasos y emite `creation_complete(Player)` cuando el jugador termina
el paso 3. La pantalla en sí no crea el Player — llama a
`PlayerManager.create_player()` con los datos recogidos.

Autor: Korlo
"""
