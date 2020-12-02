# SPDX-License-Identifier: GPL-2.0-or-later

from collections import defaultdict

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout

from clickable_label import ClickableLabel
from keyboard_widget import KeyboardWidget
from keycodes import keycode_label, keycode_tooltip, keycode_is_mask
from constants import LAYER_BTN_STYLE, ACTIVE_LAYER_BTN_STYLE
from util import tr


class KeyboardContainer(QWidget):

    number_layers_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout_layers = QHBoxLayout()
        layer_label = QLabel(tr("KeyboardContainer", "Layer"))

        layout_labels_container = QHBoxLayout()
        layout_labels_container.addWidget(layer_label)
        layout_labels_container.addLayout(self.layout_layers)
        layout_labels_container.addStretch()

        # contains the actual keyboard
        self.container = KeyboardWidget()
        self.container.clicked.connect(self.on_key_clicked)

        layout = QVBoxLayout()
        layout.addLayout(layout_labels_container)
        layout.addWidget(self.container)
        layout.setAlignment(self.container, Qt.AlignHCenter)
        self.setLayout(layout)

        self.keys = []
        self.layer_labels = []
        self.rowcol = defaultdict(list)
        self.selected_row = -1
        self.selected_col = -1
        self.selected_mask = False
        self.keyboard = None
        self.current_layer = 0

    def rebuild_layers(self):
        self.number_layers_changed.emit()

        # delete old layer labels
        for label in self.layer_labels:
            label.deleteLater()
        self.layer_labels = []

        # create new layer labels
        for x in range(self.keyboard.layers):
            label = ClickableLabel(str(x))
            label.setAlignment(Qt.AlignCenter)
            label.clicked.connect(lambda idx=x: self.switch_layer(idx))
            self.layout_layers.addWidget(label)
            self.layer_labels.append(label)

    def rebuild(self, keyboard):
        self.keyboard = keyboard

        # delete current layout
        for key in self.keys:
            key.deleteLater()
        self.keys = []

        # get number of layers
        self.rebuild_layers()

        # prepare for fetching keymap
        self.rowcol = defaultdict(list)

        self.container.set_keys(keyboard.keys)
        for key in self.container.keys:
            if key.desc.row is not None:
                self.rowcol[(key.desc.row, key.desc.col)].append(key)

        self.current_layer = 0
        self.refresh_layer_display()

    def refresh_layer_display(self):
        """ Refresh text on key widgets to display data corresponding to current layer """

        for label in self.layer_labels:
            label.setStyleSheet(LAYER_BTN_STYLE)
        self.layer_labels[self.current_layer].setStyleSheet(ACTIVE_LAYER_BTN_STYLE)

        for (row, col), widgets in self.rowcol.items():
            code = self.keyboard.layout[(self.current_layer, row, col)]
            text = keycode_label(code)
            tooltip = keycode_tooltip(code)
            mask = keycode_is_mask(code)
            mask_text = keycode_label(code & 0xFF)
            if mask:
                text = text.split("\n")[0]
            for widget in widgets:
                widget.masked = mask
                widget.setText(text)
                widget.setMaskText(mask_text)
                widget.setToolTip(tooltip)
        self.container.update()
        self.container.updateGeometry()

    def switch_layer(self, idx):
        self.container.deselect()
        self.current_layer = idx
        self.selected_row = -1
        self.selected_col = -1
        self.refresh_layer_display()

    def set_key(self, keycode):
        """ Change currently selected key to provided keycode """

        l, r, c = self.current_layer, self.selected_row, self.selected_col

        if r >= 0 and c >= 0:
            # if masked, ensure that this is a byte-sized keycode
            if self.selected_mask:
                if keycode > 0xFF:
                    return
                keycode = (self.keyboard.layout[(l, r, c)] & 0xFF00) | keycode

            self.keyboard.set_key(l, r, c, keycode)
            self.refresh_layer_display()

    def on_key_clicked(self, widget, is_mask):
        """ Change which key is currently selected """

        self.selected_mask = is_mask

        for (row, col), widgets in self.rowcol.items():
            if widget in widgets:
                self.selected_row = row
                self.selected_col = col
                break
        self.refresh_layer_display()

    def save_layout(self):
        return self.keyboard.save_layout()

    def restore_layout(self, data):
        self.keyboard.restore_layout(data)
        self.refresh_layer_display()