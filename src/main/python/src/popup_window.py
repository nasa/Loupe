from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QGridLayout # grid layout

import functools

from src import log_parsing

class ROI_export_selection_popup(QDialog):

    def __init__(self, radio_button_state, spacing, parent=None):
        super().__init__(parent)
        self.setWindowTitle('ROI Export Settings')
        self.LoupePopupLayout = QGridLayout()
        #_titleText = 'ROI Export Settings'
        #self.labelTitle = QLabel(_titleText, self)
        #self.LoupePopupLayout.addWidget(self.labelTitle, 0, 2, 1, 2)
        _text = 'ASCII Export: Enable this checkbox to export\nASCII-formatted spectra in addition to CSV files'
        self.label = QLabel(_text, self)
        self.LoupePopupLayout.addWidget(self.label, 1, 0, 1, 4)
        self.LoupePopupLayout.addWidget(radio_button_state, 2, 0, 1, 2)
        self.labelSpacing = QLabel('Shift Sampling:', self)
        self.LoupePopupLayout.addWidget(self.labelSpacing, 2, 2, 1, 1)
        self.LoupePopupLayout.addWidget(spacing, 2, 3, 1, 1)
        self.closeButton = QPushButton('Close')
        self.LoupePopupLayout.addWidget(self.closeButton, 3, 1, 1, 2)
        self.setLayout(self.LoupePopupLayout)
        self.closeButton.clicked.connect(self.closeWindow)

    def closeWindow(self):
        self.close()