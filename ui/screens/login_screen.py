"""
ui/screens/login_screen.py
=============================

Qué hace:
    `LoginScreen`: la pantalla `GameScene.LOGIN`, primera que ve el
    jugador al abrir el juego. Permite iniciar sesión o registrarse
    con `services.auth_service.AuthService` (Supabase Auth), o seguir
    sin cuenta — el juego sigue siendo 100% jugable en modo local en
    ese caso, no es un muro de pago ni un requisito real.

Cómo funciona:
    Si `auth_service` es `None` (no hay `SUPABASE_URL`/
    `SUPABASE_ANON_KEY` configuradas en el entorno, ver `main.py`),
    el formulario de email/contraseña queda deshabilitado con una
    nota explicativa — "Seguir sin cuenta" sigue siempre disponible,
    para que la ausencia de configuración de Supabase nunca bloquee
    el juego.

    Un mismo formulario alterna entre "Iniciar sesión" y
    "Registrarse" (`self._sign_up_mode`) en vez de duplicar los
    campos — mismo espíritu que el flujo de pasos de
    `ui/screens/character_creation/`.

Autor: Korlo
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from services.auth_service import AuthError, AuthService
from ui import theme
from ui.widgets.card import Card


class LoginScreen(QWidget):
    """Pantalla de login/registro con salida honesta a modo invitado."""

    authenticated = Signal(str)  # user_id
    continue_as_guest = Signal()

    def __init__(self, auth_service: Optional[AuthService], parent=None) -> None:
        super().__init__(parent)
        self._auth_service = auth_service
        self._sign_up_mode = False

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignHCenter)
        layout.setSpacing(theme.SPACE_MD)
        layout.addStretch(1)

        title = QLabel("WHAT IF?")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"font-size: 40px; font-weight: 800; color: {theme.TEXT_PRIMARY};")
        layout.addWidget(title)

        card = Card()
        card.setFixedWidth(360)

        self._card_title = QLabel("Iniciar sesión")
        self._card_title.setStyleSheet(
            f"font-size: {theme.FONT_SIZE_H2}px; font-weight: 700; color: {theme.TEXT_PRIMARY};"
        )
        card.body_layout.addWidget(self._card_title)

        self._email_field = self._labeled_input("Email", card)
        self._password_field = self._labeled_input("Contraseña", card)
        self._password_field.setEchoMode(QLineEdit.Password)

        self._error_label = QLabel("")
        self._error_label.setWordWrap(True)
        self._error_label.setStyleSheet(f"color: {theme.ERROR}; font-size: {theme.FONT_SIZE_SMALL}px;")
        self._error_label.hide()
        card.body_layout.addWidget(self._error_label)

        self._primary_button = QPushButton("Iniciar sesión")
        self._primary_button.setFixedHeight(44)
        self._primary_button.setStyleSheet(
            f"QPushButton {{ background-color: {theme.ACCENT_PURPLE}; color: {theme.TEXT_WHITE}; "
            f"border-radius: {theme.RADIUS_SM}px; font-weight: 700; }}"
            f"QPushButton:hover {{ background-color: {theme.ACCENT_PRIMARY_HOVER}; }}"
            f"QPushButton:disabled {{ background-color: {theme.BORDER}; color: {theme.TEXT_DISABLED}; }}"
        )
        self._primary_button.clicked.connect(self._handle_primary_action)
        card.body_layout.addWidget(self._primary_button)

        self._toggle_button = QPushButton("¿No tienes cuenta? Regístrate")
        self._toggle_button.setFlat(True)
        self._toggle_button.setStyleSheet(
            f"QPushButton {{ color: {theme.ACCENT_PURPLE}; border: none; background: transparent; }}"
        )
        self._toggle_button.clicked.connect(self._handle_toggle_mode)
        card.body_layout.addWidget(self._toggle_button)

        if self._auth_service is None:
            note = QLabel("Cuenta en la nube no configurada — puedes jugar sin ella.")
            note.setWordWrap(True)
            note.setStyleSheet(f"color: {theme.TEXT_DISABLED}; font-size: {theme.FONT_SIZE_TINY}px;")
            card.body_layout.addWidget(note)
            self._email_field.setEnabled(False)
            self._password_field.setEnabled(False)
            self._primary_button.setEnabled(False)
            self._toggle_button.setEnabled(False)

        layout.addWidget(card)

        guest_button = QPushButton("Seguir sin cuenta")
        guest_button.setFixedHeight(40)
        guest_button.setMinimumWidth(200)
        guest_button.setStyleSheet(
            f"QPushButton {{ background-color: {theme.SURFACE}; color: {theme.TEXT_PRIMARY}; "
            f"border: 1px solid {theme.BORDER_STRONG}; border-radius: {theme.RADIUS_SM}px; }}"
            f"QPushButton:hover {{ background-color: {theme.BACKGROUND}; }}"
        )
        guest_button.clicked.connect(self.continue_as_guest.emit)
        layout.addWidget(guest_button, alignment=Qt.AlignHCenter)

        layout.addStretch(2)

    def _labeled_input(self, label_text: str, parent_card: Card) -> QLineEdit:
        label = QLabel(label_text)
        label.setStyleSheet(
            f"color: {theme.TEXT_PRIMARY}; font-size: {theme.FONT_SIZE_SMALL}px; font-weight: 600;"
        )
        field = QLineEdit()
        field.setStyleSheet(
            f"QLineEdit {{ border: 1px solid {theme.BORDER_STRONG}; border-radius: {theme.RADIUS_SM}px; "
            f"padding: 8px 12px; font-size: {theme.FONT_SIZE_BODY}px; "
            f"background: {theme.SURFACE}; color: {theme.TEXT_PRIMARY}; }}"
        )
        parent_card.body_layout.addWidget(label)
        parent_card.body_layout.addWidget(field)
        return field

    def _handle_toggle_mode(self) -> None:
        self._sign_up_mode = not self._sign_up_mode
        self._error_label.hide()
        if self._sign_up_mode:
            self._card_title.setText("Crear cuenta")
            self._primary_button.setText("Registrarse")
            self._toggle_button.setText("¿Ya tienes cuenta? Inicia sesión")
        else:
            self._card_title.setText("Iniciar sesión")
            self._primary_button.setText("Iniciar sesión")
            self._toggle_button.setText("¿No tienes cuenta? Regístrate")

    def _handle_primary_action(self) -> None:
        if self._auth_service is None:
            return

        email = self._email_field.text().strip()
        password = self._password_field.text()
        if not email or not password:
            self._show_error("Completa email y contraseña.")
            return

        try:
            if self._sign_up_mode:
                result = self._auth_service.sign_up(email, password)
            else:
                result = self._auth_service.sign_in(email, password)
        except AuthError as error:
            self._show_error(str(error))
            return

        self._error_label.hide()
        self.authenticated.emit(result.user_id)

    def _show_error(self, message: str) -> None:
        self._error_label.setText(message)
        self._error_label.show()

    def reset(self) -> None:
        """Limpia el formulario (llamado al reconstruir la pantalla por cambio de tema)."""
        self._email_field.setText("")
        self._password_field.setText("")
        self._error_label.hide()
