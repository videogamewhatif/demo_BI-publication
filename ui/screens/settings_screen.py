"""
ui/screens/settings_screen.py
================================

Qué hace:
    `SettingsScreen`: destino "Configuración" del sidebar. Solo
    incluye lo que tiene un mecanismo real y funcional detrás:
    apariencia (`ui.theme.set_theme()`), volumen
    (`managers.audio_manager.AudioManager`) e idioma
    (`managers.language_manager.LanguageManager`). No incluye
    dificultad ni otras opciones de `config/game_config.py` porque
    no hay ningún lugar en el proyecto que persista o aplique una
    dificultad activa todavía — añadirlo aquí sería un control que
    no hace nada.

Selector de tema:
    El checkbox "Modo oscuro" llama a `ui.theme.set_theme()`, que
    desde esta sesión repinta en caliente toda la ventana (ver
    docstring de `ui/theme.py` y `ui/windows/main_window.py`) — al
    tocarlo, esta misma pantalla se reconstruye desde cero un
    instante después con el tema nuevo, checkbox incluido.

Autor: Korlo (ui/ añadida en esta sesión; selector de tema añadido después)
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QComboBox, QLabel, QSlider, QVBoxLayout, QWidget

from managers.audio_manager import AudioManager
from managers.language_manager import LanguageManager
from ui import theme
from ui.widgets.card import Card


def _volume_row(label_text: str, initial_percent: int, on_change) -> tuple[QWidget, QSlider]:
    row = QWidget()
    layout = QVBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)

    label = QLabel(label_text)
    label.setStyleSheet(f"color: {theme.TEXT_PRIMARY}; font-size: {theme.FONT_SIZE_SMALL}px; font-weight: 600;")

    slider = QSlider(Qt.Horizontal)
    slider.setRange(0, 100)
    slider.setValue(initial_percent)
    slider.valueChanged.connect(on_change)
    slider.setStyleSheet(
        f"""
        QSlider::groove:horizontal {{ height: 6px; background: {theme.BORDER}; border-radius: 3px; }}
        QSlider::handle:horizontal {{
            background: {theme.ACCENT_PURPLE}; width: 16px; height: 16px;
            margin: -5px 0; border-radius: 8px;
        }}
        QSlider::sub-page:horizontal {{ background: {theme.ACCENT_PURPLE}; border-radius: 3px; }}
        """
    )

    layout.addWidget(label)
    layout.addWidget(slider)
    return row, slider


class SettingsScreen(QWidget):
    """Configuración real de apariencia, audio e idioma (nada sin mecanismo real detrás)."""

    def __init__(self, audio_manager: AudioManager, language_manager: LanguageManager, parent=None) -> None:
        super().__init__(parent)
        self._audio_manager = audio_manager
        self._language_manager = language_manager

        layout = QVBoxLayout(self)
        layout.setSpacing(theme.SPACE_MD)

        appearance_card = Card(clickable=True)
        appearance_title = QLabel(self._language_manager.translate("appearance_title") if hasattr(self._language_manager, "translate") else "APARIENCIA")
        appearance_title.setStyleSheet(
            f"color: {theme.ACCENT_PURPLE}; font-size: {theme.FONT_SIZE_SMALL}px; font-weight: 700; letter-spacing: 1px;"
        )
        appearance_card.body_layout.addWidget(appearance_title)

        # Reemplazamos el checkbox por todo el card clicable. Mantenemos
        # un checkbox interno para reflejar el estado visualmente.
        dark_mode_checkbox = QCheckBox("Modo oscuro")
        dark_mode_checkbox.setChecked(theme.current_theme_name() == "dark")
        dark_mode_checkbox.setEnabled(False)
        # Un widget deshabilitado no reenvía el clic a su padre: sin esto,
        # el checkbox "atrapa" el clic y la tarjeta nunca se entera.
        dark_mode_checkbox.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        appearance_card.body_layout.addWidget(dark_mode_checkbox)
        self._dark_mode_checkbox = dark_mode_checkbox

        # Al hacer clic en la tarjeta invertimos el tema.
        def _toggle_theme() -> None:
            checked = theme.current_theme_name() != "dark"
            theme.set_theme("dark" if checked else "light")
            self._dark_mode_checkbox.setChecked(checked)

        appearance_card.clicked.connect(_toggle_theme)

        layout.addWidget(appearance_card)

        audio_card = Card()
        audio_title = QLabel(self._language_manager.translate("audio_title") if hasattr(self._language_manager, "translate") else "AUDIO")
        audio_title.setStyleSheet(
            f"color: {theme.ACCENT_PURPLE}; font-size: {theme.FONT_SIZE_SMALL}px; font-weight: 700; letter-spacing: 1px;"
        )
        audio_card.body_layout.addWidget(audio_title)

        master_row, _ = _volume_row(
            self._language_manager.translate("master_volume") if hasattr(self._language_manager, "translate") else "Volumen maestro",
            int(round(audio_manager.get_master_volume() * 100)),
            lambda v: audio_manager.set_master_volume(v / 100),
        )
        music_row, _ = _volume_row(
            self._language_manager.translate("music") if hasattr(self._language_manager, "translate") else "Música",
            int(round(audio_manager.get_music_volume() * 100)),
            lambda v: audio_manager.set_music_volume(v / 100),
        )
        effects_row, _ = _volume_row(
            self._language_manager.translate("effects") if hasattr(self._language_manager, "translate") else "Efectos",
            int(round(audio_manager.get_effects_volume() * 100)),
            lambda v: audio_manager.set_effects_volume(v / 100),
        )
        audio_card.body_layout.addWidget(master_row)
        audio_card.body_layout.addWidget(music_row)
        audio_card.body_layout.addWidget(effects_row)

        mute_checkbox = QCheckBox("Silenciar todo")
        mute_checkbox.setChecked(audio_manager.is_muted())
        mute_checkbox.toggled.connect(
            lambda checked: audio_manager.mute() if checked else audio_manager.unmute()
        )
        audio_card.body_layout.addWidget(mute_checkbox)

        layout.addWidget(audio_card)

        language_card = Card()
        language_title = QLabel(self._language_manager.translate("language_title") if hasattr(self._language_manager, "translate") else "IDIOMA")
        language_title.setStyleSheet(
            f"color: {theme.ACCENT_PURPLE}; font-size: {theme.FONT_SIZE_SMALL}px; font-weight: 700; letter-spacing: 1px;"
        )
        language_card.body_layout.addWidget(language_title)

        combo = QComboBox()
        available = language_manager.available_languages()
        combo.addItems(available)
        current = language_manager.current_language()
        if current in available:
            combo.setCurrentText(current)
        combo.currentTextChanged.connect(language_manager.change_language)
        language_card.body_layout.addWidget(combo)

        layout.addWidget(language_card)
        layout.addStretch(1)
