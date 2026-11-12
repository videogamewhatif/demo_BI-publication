"""
services/auth_service.py
==========================

Qué hace:
    Envuelve Supabase Auth (registro, inicio de sesión, cierre de
    sesión) detrás de una interfaz mínima que no expone tipos de
    `supabase-py` a quien lo use (`ui/screens/login_screen.py`):
    entra email/password, sale un `AuthResult` (o `AuthError`).

Cómo funciona:
    Importa el paquete `supabase` de forma perezosa (dentro de
    `__init__`), igual que `OpenAIImageProvider` en
    `services/image_service.py`, para que este módulo se pueda
    importar sin error en un entorno donde el paquete no esté
    instalado. Exige `url`/`key` explícitos en el constructor —
    nunca los lee de `os.environ` él mismo; eso es responsabilidad de
    quien lo instancia (`main.py`, vía `python-dotenv`).

Dependencias:
    - supabase (opcional, solo si se instancia AuthService).

Autor: Korlo
"""

from __future__ import annotations

from dataclasses import dataclass


class AuthError(Exception):
    """Se lanza cuando Supabase Auth rechaza un registro/inicio de sesión."""


@dataclass(frozen=True)
class AuthResult:
    """Resultado mínimo de una autenticación exitosa."""

    user_id: str
    email: str


class AuthService:
    """
    Fachada delgada sobre Supabase Auth. No mantiene sesión propia
    más allá de la que ya guarda el cliente de `supabase-py`
    internamente.
    """

    def __init__(self, url: str, key: str) -> None:
        """
        Args:
            url: URL del proyecto de Supabase (Project Settings > API > Project URL).
            key: clave anónima pública del proyecto (Project Settings >
                API > Project API keys > anon public). Se exige
                explícita a propósito: nunca debe venir hardcodeada en
                el código fuente (cárgala con python-dotenv desde una
                variable de entorno).

        Raises:
            ValueError: si `url` o `key` están vacíos.
            AuthError: si el paquete `supabase` no está instalado.
        """
        if not url or not key:
            raise ValueError(
                "url y key no pueden estar vacíos. No los hardcodees: cárgalos "
                "con python-dotenv desde variables de entorno."
            )
        try:
            from supabase import create_client
        except ImportError as error:
            raise AuthError(
                "El paquete 'supabase' no está instalado (ver requirements.txt)."
            ) from error

        self._client = create_client(url, key)

    def sign_up(self, email: str, password: str) -> AuthResult:
        """Registra una cuenta nueva y la deja autenticada."""
        return self._handle(
            lambda: self._client.auth.sign_up({"email": email, "password": password})
        )

    def sign_in(self, email: str, password: str) -> AuthResult:
        """Inicia sesión con una cuenta existente."""
        return self._handle(
            lambda: self._client.auth.sign_in_with_password({"email": email, "password": password})
        )

    def sign_out(self) -> None:
        """Cierra la sesión activa, si había una."""
        try:
            self._client.auth.sign_out()
        except Exception as error:  # noqa: BLE001 (relanzada como AuthError propia)
            raise AuthError(str(error)) from error

    def _handle(self, call) -> AuthResult:
        try:
            response = call()
        except Exception as error:  # noqa: BLE001 (supabase-py lanza varios tipos propios)
            raise AuthError(str(error)) from error

        user = getattr(response, "user", None)
        if user is None or not getattr(user, "id", None):
            raise AuthError("Supabase no devolvió un usuario válido.")
        return AuthResult(user_id=user.id, email=user.email or "")
