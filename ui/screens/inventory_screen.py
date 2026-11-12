"""
ui/screens/inventory_screen.py
=================================

Qué hace:
    `InventoryScreen`: destino "Inventario" del sidebar. Recibe
    objetos reales vía `set_items()` (`GameplayScreen` los obtiene de
    `InventoryService.get_inventory()`) y, por cada uno, un botón
    "Usar" que emite `use_item_requested(item_id)` —
    `GameplayScreen._handle_use_item()` lo conecta a
    `InventoryManager.use_item()`. `data/items/` sigue vacía hoy, así
    que en la práctica el inventario casi siempre se ve vacío — pero
    ya no por falta de conexión, sino porque nada otorga objetos
    todavía (ningún `effects` de escena mueve inventario, solo
    stats — ver `docs/content_authoring_guide.md`).

    `set_items()` acepta objetos genéricos (duck-typing por `.name`/
    `.item_id`) en vez de importar `models.item.Item` directamente,
    para no acoplar esta pantalla al modelo concreto.

Autor: Korlo (ui/ añadida en esta sesión)
"""

from __future__ import annotations

from typing import Any, List, Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ui import theme
from ui.widgets.card import Card


class InventoryScreen(QWidget):
    """Destino Inventario: objetos reales del jugador, cada uno con un botón 'Usar'."""

    use_item_requested = Signal(str)  # item_id

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)

        card = Card()
        title = QLabel("Inventario")
        title.setStyleSheet(f"font-size: {theme.FONT_SIZE_H2}px; font-weight: 700; color: {theme.TEXT_PRIMARY};")
        self._message = QLabel(
            "Tu inventario está vacío. El sistema ya está conectado de punta a "
            "punta — lo que falta es contenido real en data/items/ que le "
            "otorgue objetos a un personaje."
        )
        self._message.setWordWrap(True)
        self._message.setStyleSheet(f"color: {theme.TEXT_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")

        card.body_layout.addWidget(title)
        card.body_layout.addWidget(self._message)
        layout.addWidget(card)
        layout.addStretch(1)

        self._items_layout = QVBoxLayout()
        layout.addLayout(self._items_layout)

    def set_items(self, items: Optional[List[Any]]) -> None:
        """Refresca la lista con los objetos reales del jugador; cada fila trae un botón 'Usar'."""
        while self._items_layout.count():
            child = self._items_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        items = items or []
        self._message.setVisible(not items)

        for item in items:
            item_id = getattr(item, "item_id", None)
            name = getattr(item, "name", str(item))

            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)

            label = QLabel(f"• {name}")
            row_layout.addWidget(label, stretch=1)

            use_button = QPushButton("Usar")
            if item_id is not None:
                use_button.clicked.connect(
                    lambda _checked, iid=item_id: self.use_item_requested.emit(iid)
                )
            else:
                use_button.setEnabled(False)
            row_layout.addWidget(use_button)

            self._items_layout.addWidget(row)
