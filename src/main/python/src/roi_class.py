import os
import functools

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QCheckBox

from src.loupe_control import _control_main


class roiClass():
    def __init__(self):
        self.humanReadableName = ''
        self.dictName = ''
        self.checkboxWidget = None
        self.checkboxWidgetRoi = None
        self.checkboxWidgetCosmic = None
        self.color = '#ffffff' #white, '#00f2ff' #cyan
        self.specIndexList = []

    def defineFull(self, roiName, workspace):
        self.dictName = workspace.dictName+'_'+roiName
        self.humanReadableName = roiName
        self.checkboxWidget = QCheckBox(roiName)
        # checkboxWidgetRoi is for the map tab
        self.checkboxWidgetRoi = QCheckBox(roiName)
        self.checkboxWidgetCosmic = QCheckBox(roiName)
        #self.checkboxWidget.clicked.connect(functools.partial(_control_main._roiSelectMainUpdate, self))
        self.color = '#ffffff'
        self.specIndexList = list(range(workspace.nSpectra))

    def defineSelectedRoi(self, roiName, workspace, indexList, color = '#ffffff'):
        self.dictName = workspace.dictName+'_'+roiName
        self.humanReadableName = roiName
        self.checkboxWidget = QCheckBox(roiName)
        self.checkboxWidgetRoi = QCheckBox(roiName)
        self.checkboxWidgetCosmic = QCheckBox(roiName)
        #self.checkboxWidget.clicked.connect(functools.partial(_control_main._roiSelectMainUpdate, self))
        self.color = color
        self.specIndexList = indexList

