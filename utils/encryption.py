"""
utils/encryption.py
====================

Qué hace:
    Utilidades de seguridad basadas ÚNICAMENTE en la librería
    estándar de Python: hash de contraseñas (PBKDF2-HMAC-SHA256, con
    sal y comparación segura ante ataques de tiempo), checksums de
    integridad, y generación de tokens aleatorios seguros.

Alcance y límites (léase antes de usar este archivo):
    `requirements.txt` no incluye ninguna biblioteca de criptografía
    (`cryptography`, `bcrypt`, `argon2-cffi`). Implementar cifrado
    simétrico real (por ejemplo, para "encriptar" archivos de
    partida) sin una biblioteca revisada por la comunidad sería
    criptografía casera — algo que este archivo NO hace, a
    propósito, porque dar una falsa sensación de seguridad es peor
    que no ofrecer ninguna. Lo que SÍ se puede construir con
    seguridad usando solo la librería estándar es hash de
    contraseñas (no reversible, no hace falta "desencriptar") y
    checksums (detectar corrupción, no ocultar contenido).

    Si el proyecto necesita cifrado simétrico real más adelante
    (por ejemplo, para que un jugador no pueda editar su archivo de
    guardado a mano), la recomendación es agregar `cryptography` a
    `requirements.txt` e implementarlo con esa biblioteca — no
    extender este archivo con una implementación propia.

    Nota de integración pendiente: `database/users_database.py` (ver
    análisis inicial del proyecto) guarda contraseñas sin ningún
    hash. Esta entrega no lo modifica (la consolidación de
    `database/` sigue pendiente), pero `hash_password()`/
    `verify_password()` son exactamente lo que debe usarse ahí
    cuando se aborde.

Cómo funciona:
    `hash_password()` genera una sal aleatoria por contraseña
    (`secrets.token_bytes`) y aplica PBKDF2-HMAC-SHA256 con un
    número alto de iteraciones (200 000 por defecto, acorde a las
    recomendaciones vigentes de OWASP para PBKDF2-SHA256). El
    resultado es un único string autocontenido (algoritmo + sal +
    iteraciones + hash), para no tener que guardar la sal en una
    columna aparte. `verify_password()` compara con
    `hmac.compare_digest`, que no revela por temporización cuántos
    caracteres coinciden — comparar con `==` filtraría esa
    información a un atacante suficientemente paciente.

Dependencias:
    - Solo biblioteca estándar (hashlib, hmac, secrets, base64).

Autor: Korlo
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

_ALGORITHM = "pbkdf2_sha256"
_DEFAULT_ITERATIONS = 200_000
_SALT_BYTES = 16


def hash_password(password: str, iterations: int = _DEFAULT_ITERATIONS) -> str:
    """
    Genera un hash seguro de `password`, listo para almacenar.

    Args:
        password: contraseña en texto plano.
        iterations: número de iteraciones de PBKDF2 (más alto =
            más lento de calcular = más resistente a fuerza bruta,
            a costa de más tiempo de CPU en cada login).

    Returns:
        Un string autocontenido con el formato
        `"pbkdf2_sha256$<iteraciones>$<sal_b64>$<hash_b64>"`.

    Raises:
        ValueError: si `password` está vacía.
    """
    if not password:
        raise ValueError("password no puede estar vacía.")

    salt = secrets.token_bytes(_SALT_BYTES)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)

    salt_b64 = base64.b64encode(salt).decode("ascii")
    hash_b64 = base64.b64encode(derived).decode("ascii")
    return f"{_ALGORITHM}${iterations}${salt_b64}${hash_b64}"


def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verifica si `password` corresponde a `stored_hash` (generado
    previamente por `hash_password`).

    Usa `hmac.compare_digest` para la comparación final, en vez de
    `==`, porque una comparación ingenua de strings termina apenas
    encuentra el primer byte distinto — el tiempo que tarda en
    fallar puede filtrarle a un atacante cuántos bytes iniciales
    acertó, permitiendo reconstruir el hash byte a byte a fuerza de
    medir tiempos. `compare_digest` siempre tarda lo mismo,
    sin importar en qué byte difieren.

    Returns:
        True si la contraseña es correcta, False en caso contrario
        (incluyendo si `stored_hash` no tiene el formato esperado —
        no se lanza excepción para no filtrar esa distinción a quien
        llama con fines de enumeración de usuarios).
    """
    try:
        algorithm, iterations_str, salt_b64, hash_b64 = stored_hash.split("$")
        if algorithm != _ALGORITHM:
            return False
        iterations = int(iterations_str)
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
    except (ValueError, TypeError):
        return False

    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)


def checksum(data: bytes) -> str:
    """
    Calcula un checksum SHA-256 de `data`, en hexadecimal.

    Pensado para detectar corrupción o modificación accidental de un
    archivo (por ejemplo, una partida guardada), no para ocultar su
    contenido — esto NO es cifrado.
    """
    return hashlib.sha256(data).hexdigest()


def generate_token(length: int = 32) -> str:
    """
    Genera un token aleatorio criptográficamente seguro, codificado
    en base64 URL-safe (apto para usar en nombres de archivo o URLs).

    Útil para tokens de sesión, identificadores de guardado rápido
    que no deban ser adivinables, etc.

    Raises:
        ValueError: si `length` no es positivo.
    """
    if length <= 0:
        raise ValueError("length debe ser mayor que 0.")
    return secrets.token_urlsafe(length)