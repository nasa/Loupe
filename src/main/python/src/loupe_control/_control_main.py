import os
import sys
import math
import numpy as np
from scipy import spatial
import functools
import copy
import time
import pandas as pd
import shapely.geometry as sg

from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtWidgets import QColorDialog
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QPainter
from PyQt5.QtGui import QPen
from PyQt5.QtGui import QBrush
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QPoint
from PyQt5.QtCore import QPointF

from matplotlib import cm as mpl_cm
from matplotlib import pyplot as plt

from src import log_parsing
from src import generate_plots
from src import file_IO
from src import poly_ROI
from src.loupe_control import _control_main
from src.loupe_control import _control_norm
from src.loupe_control import _control_false_color
from src.loupe_control import _control_cosmic
from src import roi_class
from src.loupe_view import _tab_main
from src import parse_dat_files



def _updateMainLeftPanel(self):
    log_parsing.log_info(self._view, 'Updating main left panel')
    _populateMetadataTables(self)
    _populateFileListTable(self)
    _populateDimensionListTable(self)
    _populateTableListTable(self)
    #_populateRoiCheckGroup(self)
    _updateSpecProcessing(self)

def _updateMainImgPanel(self):
    log_parsing.log_info(self._view, 'Updating main image panel')
    if self._view.workspace.selectedACIFilename is None and len(self._view.workspace.aciNames) > 0:
        self._view.workspace.selectedACIFilename = os.path.join(self._view.workspace.workingDir, 'img', self._view.workspace.aciNames[0].replace('IMG', 'PNG'))

    if self._view.workspace.selectedACIFilename is not None:
        _parseACI(self)
        _populateImageMetadataList(self)
        self._view.groupboxROI.setEnabled(True)
        self._view.groupboxLaserMain.setEnabled(True)
        #self._view.groupboxRelPosLaserWidget.setEnabled(True)
        self._view.selectionScrollbarMain.setMaximum(self._view.workspace.nSpectra-1)
        self._view.selectionOffsetAzEdit.setText(' ')
        self._view.selectionOffsetElEdit.setText(' ')

        self._view.ROIPolySelectButton.setEnabled(True)
        self._view.ROIAddPointButton.setEnabled(True)
        self._view.ROIDelPointButton.setEnabled(False)
        self._view.ROIClearPointButton.setEnabled(False)
        self._view.ROISaveButton.setEnabled(False)
        self._view.ROIColorButton.setEnabled(True)

    else:
        log_parsing.log_info(self._view, 'No image selected')
        # TODO: add laser shots to blank image
        #_defineLaserShots(self)
        #_addLaserShots(self)
        self._view.groupboxROI.setEnabled(False)
        self._view.groupboxLaserMain.setEnabled(False)

    self._view.groupboxACI.setEnabled(True)
    _populateRoiCheckGroup(self)


def _clearMain(self):
    log_parsing.log_info(self._view, 'Clearing main tab contents')
    self._view.CosmicRayRemovalProcessingItemMain.setChecked(False)
    self._view.LaserNormalizationItemMain.setChecked(False)
    self._view.BaselineSubtractionItemMain.setChecked(False)
    self._view.R1ItemMain.setChecked(True)
    self._view.R2ItemMain.setChecked(True)
    self._view.R3ItemMain.setChecked(True)
    self._view.allItemMain.setChecked(False)
    for _roi_name in self._view.workspace.roiNames:
        _roi_dict_name = self._view.workspace.roiHumanToDictKey[_roi_name]
        if _roi_name == 'Full Map':
            self._view.roiDict[_roi_dict_name].checkboxWidget.setChecked(True)
        else:
            self._view.roiDict[_roi_dict_name].checkboxWidget.setChecked(False)

    for i in reversed(range(self._view.vboxRoi.count())):
        self._view.vboxRoi.itemAt(i).widget().setParent(None)
    self._view.groupboxROIMain.resize(self._view.groupboxROIMain.sizeHint())
    self._view.metadataList.clear()
    self._view.dataFileListTable.clear()
    self._view.dimensionListTable.clear()
    self._view.tableListTable.clear()

    self._view.tempRoi = []
    self._view.tempRoiColor = '#00f2ff'
    self._view.ROIColorBox.setStyleSheet("QCheckBox::indicator{background-color : "+self._view.tempRoiColor+";}")

    self._view.humanReadableRoi.clear()

    # completely removing and re-adding the MPL canvas prevents plotting slow-downs from accumulating after many switches between workspaces
    self._view.LoupeViewMainTabLayout.removeWidget(self._view.toolbarMainPlot1)
    self._view.toolbarMainPlot1.deleteLater()
    self._view.toolbarMainPlot1 = None
    self._view.LoupeViewMainTabLayout.removeWidget(self._view.traceCanvasMainPlot1)
    self._view.traceCanvasMainPlot1.deleteLater()
    self._view.traceCanvasMainPlot1 = None
    self._view.LoupeViewMainTabLayout.removeWidget(self._view._hLineMain)
    self._view._hLineMain.deleteLater()
    self._view._hLineMain = None
    self._view.LoupeViewMainTabLayout.removeWidget(self._view.toolbarMainPlot2)
    self._view.toolbarMainPlot2.deleteLater()
    self._view.toolbarMainPlot2 = None
    self._view.LoupeViewMainTabLayout.removeWidget(self._view.traceCanvasMainPlot2)
    self._view.traceCanvasMainPlot2.deleteLater()
    self._view.traceCanvasMainPlot2 = None
    _tab_main._addMainPlotPanel(self._view)

    self._view.toolbarResizeMain1.triggered.disconnect()
    self._view.toolbarResizeMain2.triggered.disconnect()
    self._view.toolbarResizeMain1.triggered.connect(functools.partial(_control_main._rescaleYMain1, self))
    self._view.toolbarResizeMain2.triggered.connect(functools.partial(_control_main._rescaleYMain2, self))

    self._view._yRangeSPAR = None
    self._view._xRangeSPAR = None
    self._view._axBackgroundSPAR = None

    self._view.traceCanvasMainPlot1.axes.clear()
    self._view.axMainPlot1 = []
    self._view.traceCanvasMainPlot1.draw_idle()
    self._view.traceCanvasMainPlot2.draw_idle()
    self._view.axTopSparMain = None
    self._view.axTopMain = None

    img1_dir = os.path.join(os.path.dirname(sys.modules[__name__].__file__), os.pardir, os.pardir, 'resources', 'ACI_placeholder.png')
    self._view.pixmapACI = QPixmap(img1_dir)
    #self.pixmapACI = self.pixmapACI.scaledToWidth(0.92*self.mainImgScrollContainer.width())
    self._view.imageACI.setPhoto(pixmap = self._view.pixmapACI, zoomSelect=None)

    self._view.groupboxROI.setEnabled(False)
    self._view.groupboxLaserMain.setEnabled(False)

    # clear image metadata table
    self._view.imageMetadataList.setItem(0, 1, QTableWidgetItem('N/A'))
    self._view.imageMetadataList.setItem(0, 2, QTableWidgetItem('N/A'))
    self._view.imageMetadataList.setItem(1, 1, QTableWidgetItem('N/A'))
    self._view.imageMetadataList.setItem(1, 2, QTableWidgetItem('N/A'))
    self._view.imageMetadataList.setItem(2, 1, QTableWidgetItem('N/A'))
    self._view.imageMetadataList.setItem(2, 2, QTableWidgetItem('N/A'))
    self._view.imageMetadataList.setItem(3, 1, QTableWidgetItem('N/A'))
    self._view.imageMetadataList.setItem(3, 2, QTableWidgetItem('N/A'))
    self._view.imageMetadataList.setItem(4, 1, QTableWidgetItem('N/A'))
    self._view.imageMetadataList.setItem(4, 2, QTableWidgetItem('N/A'))
    self._view.imageMetadataList.setItem(5, 1, QTableWidgetItem('N/A'))
    self._view.imageMetadataList.setItem(5, 2, QTableWidgetItem('N/A'))
    self._view.imageMetadataList.setItem(6, 1, QTableWidgetItem('N/A'))
    self._view.imageMetadataList.setItem(6, 2, QTableWidgetItem('N/A'))


def _renameWorkspace(self):
    # add workspace name to translation (go from human readable to dict name) so that workspace may be accessed later using workspaceDict
    # remove previous workspace name from workspaceHumanToDictKey
    _dictKeys = [k for k in self._view.workspaceHumanToDictKey.keys()]
    for key in _dictKeys:
        if self._view.workspaceHumanToDictKey[key] == self._view.workspace.dictName:
            _ = self._view.workspaceHumanToDictKey.pop(key, None)

    _newWorkspaceName = self._view.humanReadableRename.text()
    if _newWorkspaceName in _dictKeys:
        _newWorkspaceName = _newWorkspaceName + str(len(_newWorkspaceName))
    self._view.workspaceHumanToDictKey[_newWorkspaceName] = self._view.workspace.dictName
    self._view.workspace.humanReadableName = _newWorkspaceName

    # update combo box
    # disconnect signal
    self._view.selectedWorkspaceCombo.currentIndexChanged.disconnect()

    self._view.selectedWorkspaceCombo.clear()
    for key in self._view.workspaceHumanToDictKey:
        self._view.selectedWorkspaceCombo.addItem(key)

    # get index of this item
    _workspaceItems = [self._view.selectedWorkspaceCombo.itemText(i) for i in range(self._view.selectedWorkspaceCombo.count())]
    _workspaceIndex = np.argwhere(np.array(_workspaceItems) == _newWorkspaceName)[0][0]
    self._view.selectedWorkspaceCombo.setCurrentIndex(_workspaceIndex)

    # reconnect signal
    self._view.selectedWorkspaceCombo.currentIndexChanged.connect(functools.partial(_control_main._clearMain, self))
    self._view.selectedWorkspaceCombo.currentIndexChanged.connect(self._setCurrentWorkspace)
    self._view.selectedWorkspaceCombo.currentIndexChanged.connect(self._accessSparData)
    self._view.selectedWorkspaceCombo.currentIndexChanged.connect(self._readDataTables)
    self._view.selectedWorkspaceCombo.currentIndexChanged.connect(self._setImgCombo)
    self._view.selectedWorkspaceCombo.currentIndexChanged.connect(functools.partial(_control_main._updateMainLeftPanel, self))
    self._view.selectedWorkspaceCombo.currentIndexChanged.connect(functools.partial(_control_main._updateMainPlotPanel, self))
    self._view.selectedWorkspaceCombo.currentIndexChanged.connect(functools.partial(_control_main._updateMainImgPanel, self))
    self._view.selectedWorkspaceCombo.currentIndexChanged.connect(functools.partial(_control_main._initSparDim1Selection, self))
    self._view.selectedWorkspaceCombo.currentIndexChanged.connect(functools.partial(_control_norm._updateNormLeftPanel, self))
    self._view.selectedWorkspaceCombo.currentIndexChanged.connect(functools.partial(_control_norm._updateNormCentralPanel, self))
    self._view.selectedWorkspaceCombo.currentIndexChanged.connect(functools.partial(_control_false_color._updateRGBLeftPanel, self))
    self._view.selectedWorkspaceCombo.currentIndexChanged.connect(functools.partial(_control_false_color._updateRGBCentralPanel, self))
    self._view.selectedWorkspaceCombo.currentIndexChanged.connect(functools.partial(_control_false_color._clearMap, self))
    self._view.selectedWorkspaceCombo.currentIndexChanged.connect(functools.partial(_control_cosmic._updateCosmicLeftPanel, self))
    self._view.selectedWorkspaceCombo.currentIndexChanged.connect(functools.partial(_control_cosmic._updateCosmicCentralPanel, self))
    self._view.selectedWorkspaceCombo.currentIndexChanged.connect(functools.partial(_control_cosmic._clearCosmic, self))

    self._view.selectedWorkspaceCombo.currentIndexChanged.connect(self._updateEvent)


    _control_norm._updateNormLeftPanel(self)
    _control_false_color._updateRGBLeftPanel(self)
    _control_cosmic._updateCosmicLeftPanel(self)
    self._view.humanReadableRename.clear()

    # add new workspace name to loupe.csv file
    _loupe_file = os.path.join(self._view.workspace.workingDir, 'loupe.csv')
    file_IO.writeLoupeCsv(_loupe_file, self._view)


def _updateMainPlotPanel(self):
    log_parsing.log_info(self._view, 'Updating main plot')
    #for _ax in self._view.axMainPlot1:
        #_ax.remove()
    #self._view.axMainPlot1 = []
    #self._view.traceCanvasMainPlot1.axes.clear()
    _clearPlotMain(self)
    # TODO: determine why this is so slow (without _idle - there mst be lots to draw that isn't obviously displayed)
    self._view.traceCanvasMainPlot1.draw_idle()

    for _ax in self._view.axMainPlot2:
        _ax.remove()
    self._view.axMainPlot2 = []
    self._view.traceCanvasMainPlot2.axes.clear()
    self._view.traceCanvasMainPlot2.draw_idle()

    # if spectral data exists, plot active-dark mean +/- 1 STD areas for each region
    if self._view.workspace.activeSpectraR1['None'] is not None:
        self._view.groupboxRegionsMain.setDisabled(False)
        self._view.groupboxModeMain.setDisabled(False)
        self._view.groupboxDisplayTypeMain.setDisabled(False)
        self._view.groupboxDomainTypeMain.setDisabled(False)
        self._view.darkSubMain.setChecked(True)
        self._view.groupboxIndividualPlotMain.setDisabled(False)
        self._view.meanStdDisplay.setDisabled(False)
        self._view.meanStdDisplay.setChecked(False)
        self._view.medianStdDisplay.setDisabled(False)
        self._view.medianStdDisplay.setChecked(False)

        # need to trigger _plotMainUpdate because signal is clicked. If toggled signal is used, _plotMainUpdate runs twice when user clicks
        _plotMainUpdate(self)

def _plotLowerUpdate(self):
    if len(self._view.axMainPlot2) != 0 or self._view._axBackgroundSPAR is not None:
        _addSelectionPlotMain(self)

def _plotMainUpdate(self):
    _updateSpecProcessing(self)
    if self._view.axMainPlot1 != []:
        for _ax in self._view.axMainPlot1:
            for _line in _ax.lines:
                _line.remove()
            # remove std fill_betweens
            for i in range(len(_ax.collections)):
                _ax.collections[0].remove()
        self._view.traceCanvasMainPlot1.draw_idle()
    self._view.axMainPlot1 = []
    # if no ROIs are selected, or one ROI is selected, plot as normal and use ROI index for mean/median
    if len(self._view.workspace.selectedROI) < 2:
        if self._view.darkSubMain.isChecked():
            _plotMainActiveDark(self)
        elif self._view.darkItemMain.isChecked():
            _plotMainDark(self)
        elif self._view.activeItemMain.isChecked():
            _plotMainActive(self)
        if self._view.workspace.selectedACIFilename is not None:
            if len(self._view.workspace.selectedROI) == 0 or self._view.workspace.selectedROI[0].split('_')[-1] == 'Full Map':
                _addACIImage(self)
            else:
                _addACIMultiRoiImage(self)
    # if multiple ROIs are selected, plot only one region (or all/composite) and use colors and legends to distinguish between ROIs
    else:
        if self._view.darkSubMain.isChecked():
            _plotMainActiveDarkMultiRoi(self)
        elif self._view.darkItemMain.isChecked():
            _plotMainDarkMultiRoi(self)
        elif self._view.activeItemMain.isChecked():
            _plotMainActiveMultiRoi(self)
    #self._view.toolbarMainPlot1.update()
    #self._view.toolbarMainPlot1.push_current()

def _plotMainUpdateRegion1(self):
    # if the checkbox is checked:
    if self._view.R1ItemMain.isChecked():
        # if there are more than 2 ROIs selected:
        if len(self._view.workspace.selectedROI) > 1:
            if self._view.axMainPlot1 != []:
                for _ax in self._view.axMainPlot1:
                    for _line in _ax.lines:
                        _line.remove()
                    # remove std fill_betweens
                    for i in range(len(_ax.collections)):
                        _ax.collections[0].remove()
                self._view.traceCanvasMainPlot1.draw_idle()
            self._view.axMainPlot1 = []

            self._view.R2ItemMain.setChecked(False)
            self._view.R3ItemMain.setChecked(False)
            self._view.allItemMain.setChecked(False)
            if self._view.darkSubMain.isChecked():
                _plotMainActiveDarkMultiRoi(self)
            elif self._view.activeItemMain.isChecked():
                _plotMainActiveMultiRoi(self)
            else:
                _plotMainDarkMultiRoi(self)

        else:
            _add_plot_flag = True
            # loop through all axes, check if the line label name R1 exists, if not add it
            for _ax in self._view.axMainPlot1:
                for _line in _ax.lines:
                    if _line._label == 'R1':
                        log_parsing.log_info(self._view, 'R1 trace already present in plot')
                        _add_plot_flag = False
            if self._view.workspace.selectedROI == []:
                _ROIindex = list(range(self._view.workspace.nSpectra))
            else:
                _ROIindex = self._view.roiDict[self._view.workspace.selectedROI[0]].specIndexList

            _yR1_std = None
            if self._view.meanDisplayMain.isChecked():
                if self._view.darkSubMain.isChecked():
                    _yR1 = self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].mean()
                    if self._view.meanStdDisplay.isChecked():
                        _yR1_std = self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].std()
                elif self._view.activeItemMain.isChecked():
                    _yR1 = self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].mean()
                    if self._view.meanStdDisplay.isChecked():
                        _yR1_std = self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].std()
                else:
                    _yR1 = self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].mean()
                    if self._view.meanStdDisplay.isChecked():
                        _yR1_std = self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].std()
            elif self._view.medianDisplayMain.isChecked():
                if self._view.darkSubMain.isChecked():
                    _yR1 = np.median(self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
                    if self._view.medianStdDisplay.isChecked():
                        _yR1_std = self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].std()
                elif self._view.activeItemMain.isChecked():
                    _yR1 = np.median(self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
                    if self._view.medianStdDisplay.isChecked():
                        _yR1_std = self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].std()
                else:
                    _yR1 = np.median(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
                    if self._view.medianStdDisplay.isChecked():
                        _yR1_std = self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].std()
            else:
                if self._view.darkSubMain.isChecked():
                    _yR1 = self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].loc[self.indexList].values
                elif self._view.activeItemMain.isChecked():
                    _yR1 = self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].loc[self.indexList].values
                else:
                    _yR1 = self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].loc[self.indexList].values

            if self._view.waveDomainMain.isChecked():
                _x = self._view.workspace.wavelength
            else:
                _x = list(range(self._view.workspace.nChannels))
            _color = self._view.workspace.colorR1
            if len(_yR1) == self._view.workspace.nChannels:
                _plotMainSingle(self, _x, _yR1, _color, label='R1', y_std = _yR1_std)
            else:
                _plotMainMulti(self, _x, _yR1, _color, label='R1', y_std = _yR1_std)
            log_parsing.log_info(self._view, 'added R1 trace')
            if len(self._view.workspace.selectedROI) == 0 or self._view.workspace.selectedROI[0].split('_')[-1] == 'Full Map':
                _addACIImage(self)
            else:
                _addACIMultiRoiImage(self)

    # if the checkbox is unchecked:
    else:
        # loop through all axes, check if the line label name R1 exists, if so, remove it
        for _ax in self._view.axMainPlot1:
            for _line in _ax.lines:
                if _line._label == 'R1':
                    log_parsing.log_info(self._view, 'removed trace R1')
                    _line.remove()
            # remove std fill_betweens
            for _coll in _ax.collections:
                if _coll._label == 'R1' or _coll._label == '_R1':
                    _coll.remove()
        if self._view.axMainPlot2 != []:
            for _ax in self._view.axMainPlot2:
                if _ax.get_color() == '#0099FF':
                    _ax.remove()
                    self._view.axMainPlot2.remove(_ax)
            self._view.traceCanvasMainPlot2.draw_idle()

    self._view.traceCanvasMainPlot1.draw_idle()
    _updateSelectionPlotMain(self)
    #self._view.toolbarMainPlot1.update()
    #self._view.toolbarMainPlot1.push_current()


def _plotMainUpdateRegion2(self):
    # if the checkbox is checked:
    if self._view.R2ItemMain.isChecked():
        # if there are more than 2 ROIs selected:
        if len(self._view.workspace.selectedROI) > 1:
            if self._view.axMainPlot1 != []:
                for _ax in self._view.axMainPlot1:
                    for _line in _ax.lines:
                        _line.remove()
                    # remove std fill_betweens
                    for i in range(len(_ax.collections)):
                        _ax.collections[0].remove()
                self._view.traceCanvasMainPlot1.draw_idle()
            self._view.axMainPlot1 = []

            self._view.R1ItemMain.setChecked(False)
            self._view.R3ItemMain.setChecked(False)
            self._view.allItemMain.setChecked(False)
            if self._view.darkSubMain.isChecked():
                _plotMainActiveDarkMultiRoi(self)
            elif self._view.activeItemMain.isChecked():
                _plotMainActiveMultiRoi(self)
            else:
                _plotMainDarkMultiRoi(self)

        else:
            _add_plot_flag = True
            # loop through all axes, check if the line label name R2 exists, if not add it
            for _ax in self._view.axMainPlot1:
                for _line in _ax.lines:
                    if _line._label == 'R2':
                        log_parsing.log_info(self._view, 'R2 trace already present in plot')
                        _add_plot_flag = False

            if self._view.workspace.selectedROI == []:
                _ROIindex = list(range(self._view.workspace.nSpectra))
            else:
                _ROIindex = self._view.roiDict[self._view.workspace.selectedROI[0]].specIndexList

            #if _add_plot_flag:
            _yR2_std = None
            if self._view.meanDisplayMain.isChecked():
                if self._view.darkSubMain.isChecked():
                    _yR2 = self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].mean()
                    if self._view.meanStdDisplay.isChecked():
                        _yR2_std = self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].std()
                elif self._view.activeItemMain.isChecked():
                    _yR2 = self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].mean()
                    if self._view.meanStdDisplay.isChecked():
                        _yR2_std = self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].std()
                else:
                    _yR2 = self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].mean()
                    if self._view.meanStdDisplay.isChecked():
                        _yR2_std = self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].std()
            elif self._view.medianDisplayMain.isChecked():
                if self._view.darkSubMain.isChecked():
                    _yR2 = np.median(self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
                    if self._view.medianStdDisplay.isChecked():
                        _yR2_std = self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].std()
                elif self._view.activeItemMain.isChecked():
                    _yR2 = np.median(self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
                    if self._view.medianStdDisplay.isChecked():
                        _yR2_std = self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].std()
                else:
                    _yR2 = np.median(self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
                    if self._view.medianStdDisplay.isChecked():
                        _yR2_std = self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].std()
            else:
                if self._view.darkSubMain.isChecked():
                    _yR2 = self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].loc[self.indexList].values
                elif self._view.activeItemMain.isChecked():
                    _yR2 = self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].loc[self.indexList].values
                else:
                    _yR2 = self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].loc[self.indexList].values

            if self._view.waveDomainMain.isChecked():
                _x = self._view.workspace.wavelength
            else:
                _x = list(range(self._view.workspace.nChannels))
            _color = self._view.workspace.colorR2
            if len(_yR2) == self._view.workspace.nChannels:
                _plotMainSingle(self, _x, _yR2, _color, label='R2', y_std = _yR2_std)
            else:
                _plotMainMulti(self, _x, _yR2, _color, label='R2', y_std = _yR2_std)
            log_parsing.log_info(self._view, 'added R2 trace')
            if len(self._view.workspace.selectedROI) == 0 or self._view.workspace.selectedROI[0].split('_')[-1] == 'Full Map':
                _addACIImage(self)
            else:
                _addACIMultiRoiImage(self)

    # if the checkbox is unchecked:
    else:
        # loop through all axes, check if the line label name R1 exists, if so, remove it
        for _ax in self._view.axMainPlot1:
            for _line in _ax.lines:
                if _line._label == 'R2':
                    log_parsing.log_info(self._view, 'removed trace R2')
                    _line.remove()
            # remove std fill_betweens
            for _coll in _ax.collections:
                if _coll._label == 'R2' or _coll._label == '_R2':
                    _coll.remove()
        if self._view.axMainPlot2 != []:
            for _ax in self._view.axMainPlot2:
                if _ax.get_color() == '#00FF00':
                    _ax.remove()
                    self._view.axMainPlot2.remove(_ax)
            self._view.traceCanvasMainPlot2.draw_idle()

    self._view.traceCanvasMainPlot1.draw_idle()
    _updateSelectionPlotMain(self)
    #self._view.toolbarMainPlot1.update()
    #self._view.toolbarMainPlot1.push_current()

def _plotMainUpdateRegion3(self):
    # if the checkbox is checked:
    if self._view.R3ItemMain.isChecked():
        # if there are more than 2 ROIs selected:
        if len(self._view.workspace.selectedROI) > 1:
            if self._view.axMainPlot1 != []:
                for _ax in self._view.axMainPlot1:
                    for _line in _ax.lines:
                        _line.remove()
                    # remove std fill_betweens
                    for i in range(len(_ax.collections)):
                        _ax.collections[0].remove()
                self._view.traceCanvasMainPlot1.draw_idle()
            self._view.axMainPlot1 = []

            self._view.R1ItemMain.setChecked(False)
            self._view.R2ItemMain.setChecked(False)
            self._view.allItemMain.setChecked(False)
            if self._view.darkSubMain.isChecked():
                _plotMainActiveDarkMultiRoi(self)
            elif self._view.activeItemMain.isChecked():
                _plotMainActiveMultiRoi(self)
            else:
                _plotMainDarkMultiRoi(self)
        else:
            _add_plot_flag = True
            # loop through all axes, check if the line label name R3 exists, if not add it
            for _ax in self._view.axMainPlot1:
                for _line in _ax.lines:
                    if _line._label == 'R3':
                        log_parsing.log_info(self._view, 'R3 trace already present in plot')
                        _add_plot_flag = False

            if self._view.workspace.selectedROI == []:
                _ROIindex = list(range(self._view.workspace.nSpectra))
            else:
                _ROIindex = self._view.roiDict[self._view.workspace.selectedROI[0]].specIndexList

            #if _add_plot_flag:
            _yR3_std = None
            if self._view.meanDisplayMain.isChecked():
                if self._view.darkSubMain.isChecked():
                    _yR3 = self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].mean()
                    if self._view.meanStdDisplay.isChecked():
                        _yR3_std = self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].std()
                elif self._view.activeItemMain.isChecked():
                    _yR3 = self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].mean()
                    if self._view.meanStdDisplay.isChecked():
                        _yR3_std = self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].std()
                else:
                    _yR3 = self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].mean()
                    if self._view.meanStdDisplay.isChecked():
                        _yR3_std = self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].std()
            elif self._view.medianDisplayMain.isChecked():
                if self._view.darkSubMain.isChecked():
                    _yR3 = np.median(self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
                    if self._view.medianStdDisplay.isChecked():
                        _yR3_std = self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].std()
                elif self._view.activeItemMain.isChecked():
                    _yR3 = np.median(self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
                    if self._view.medianStdDisplay.isChecked():
                        _yR3_std = self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].std()
                else:
                    _yR3 = np.median(self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
                    if self._view.medianStdDisplay.isChecked():
                        _yR3_std = self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].std()
            else:
                if self._view.darkSubMain.isChecked():
                    _yR3 = self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].loc[self.indexList].values
                elif self._view.activeItemMain.isChecked():
                    _yR3 = self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].loc[self.indexList].values
                else:
                    _yR3 = self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].loc[self.indexList].values

            if self._view.waveDomainMain.isChecked():
                _x = self._view.workspace.wavelength
            else:
                _x = list(range(self._view.workspace.nChannels))
            _color = self._view.workspace.colorR3
            if len(_yR3) == self._view.workspace.nChannels:
                _plotMainSingle(self, _x, _yR3, _color, label='R3', y_std = _yR3_std)
            else:
                _plotMainMulti(self, _x, _yR3, _color, label='R3', y_std = _yR3_std)
            log_parsing.log_info(self._view, 'added R3 trace')
            if len(self._view.workspace.selectedROI) == 0 or self._view.workspace.selectedROI[0].split('_')[-1] == 'Full Map':
                _addACIImage(self)
            else:
                _addACIMultiRoiImage(self)

    # if the checkbox is unchecked:
    else:
        # loop through all axes, check if the line label name R1 exists, if so, remove it
        for _ax in self._view.axMainPlot1:
            for _line in _ax.lines:
                if _line._label == 'R3':
                    log_parsing.log_info(self._view, 'removed trace R3')
                    _line.remove()
            # remove std fill_betweens
            for _coll in _ax.collections:
                if _coll._label == 'R3' or _coll._label == '_R3':
                    _coll.remove()
        if self._view.axMainPlot2 != []:
            for _ax in self._view.axMainPlot2:
                if _ax.get_color() == '#FF0000':
                    _ax.remove()
                    self._view.axMainPlot2.remove(_ax)
            self._view.traceCanvasMainPlot2.draw_idle()

    self._view.traceCanvasMainPlot1.draw_idle()
    _updateSelectionPlotMain(self)
    #self._view.toolbarMainPlot1.update()
    #self._view.toolbarMainPlot1.push_current()

def _plotMainUpdateRegionAll(self):
    # if the checkbox is checked:
    if self._view.allItemMain.isChecked():
        # if there are more than 2 ROIs selected:
        if len(self._view.workspace.selectedROI) > 1:
            if self._view.axMainPlot1 != []:
                for _ax in self._view.axMainPlot1:
                    for _line in _ax.lines:
                        _line.remove()
                    # remove std fill_betweens
                    for i in range(len(_ax.collections)):
                        _ax.collections[0].remove()
                self._view.traceCanvasMainPlot1.draw_idle()
            self._view.axMainPlot1 = []

            self._view.R1ItemMain.setChecked(False)
            self._view.R2ItemMain.setChecked(False)
            self._view.R3ItemMain.setChecked(False)
            if self._view.darkSubMain.isChecked():
                _plotMainActiveDarkMultiRoi(self)
            elif self._view.activeItemMain.isChecked():
                _plotMainActiveMultiRoi(self)
            else:
                _plotMainDarkMultiRoi(self)
        else:
            _add_plot_flag = True
            # loop through all axes, check if the line label name R1 exists, if not add it
            for _ax in self._view.axMainPlot1:
                for _line in _ax.lines:
                    if _line._label == 'composite':
                        log_parsing.log_info(self._view, 'composite trace already present in plot')
                        _add_plot_flag = False
            #if _add_plot_flag:
            _yAll_std = None
            if self._view.meanDisplayMain.isChecked():
                if self._view.darkSubMain.isChecked():
                    _yAll = (self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].mean().values + \
                             self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].mean().values + \
                             self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].mean().values)
                    if self._view.meanStdDisplay.isChecked():
                        _yAll_std = (self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].std().values +
                                     self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].std().values +
                                     self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].std().values)
                elif self._view.activeItemMain.isChecked():
                    _yAll = (self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].mean().values +
                             self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].mean().values +
                             self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].mean().values)
                    if self._view.meanStdDisplay.isChecked():
                        _yAll_std = (self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].std().values +
                                     self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].std().values +
                                     self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].std().values)
                else:
                    _yAll = (self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].mean().values +
                             self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].mean().values +
                             self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].mean().values)
                    if self._view.meanStdDisplay.isChecked():
                        _yAll_std = (self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].std().values +
                                     self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].std().values +
                                     self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].std().values)
            elif self._view.medianDisplayMain.isChecked():
                if self._view.darkSubMain.isChecked():
                    _yAll = (np.median(self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected], axis=0) + \
                             np.median(self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected], axis=0) + \
                             np.median(self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected], axis=0))
                    if self._view.medianStdDisplay.isChecked():
                        _yAll_std = (self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].std().values +
                                     self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].std().values +
                                     self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].std().values)
                elif self._view.activeItemMain.isChecked():
                    _yAll = (np.median(self._view.workspace.activeSpectraR1[self._view.specProcessingSelected], axis=0) +
                             np.median(self._view.workspace.activeSpectraR2[self._view.specProcessingSelected], axis=0) +
                             np.median(self._view.workspace.activeSpectraR3[self._view.specProcessingSelected], axis=0))
                    if self._view.medianStdDisplay.isChecked():
                        _yAll_std = (self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].std().values +
                                     self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].std().values +
                                     self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].std().values)
                else:
                    _yAll = (np.median(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected], axis=0) +
                             np.median(self._view.workspace.darkSpectraR2[self._view.specProcessingSelected], axis=0) +
                             np.median(self._view.workspace.darkSpectraR3[self._view.specProcessingSelected], axis=0))
                    if self._view.medianStdDisplay.isChecked():
                        _yAll_std = (self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].std().values +
                                     self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].std().values +
                                     self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].std().values)
            else:
                if self._view.darkSubMain.isChecked():
                    _yAll = (self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].loc[self.indexList].values + \
                             self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].loc[self.indexList].values + \
                             self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].loc[self.indexList].values)
                elif self._view.activeItemMain.isChecked():
                    _yAll = (self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].loc[self.indexList].values +
                             self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].loc[self.indexList].values +
                             self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].loc[self.indexList].values)
                else:
                    _yAll = (self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].loc[self.indexList].values +
                             self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].loc[self.indexList].values +
                             self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].loc[self.indexList].values)

            if self._view.waveDomainMain.isChecked():
                _x = self._view.workspace.wavelength
            else:
                _x = list(range(self._view.workspace.nChannels))
            _color = self._view.workspace.colorComposite
            if len(_yAll) == self._view.workspace.nChannels:
                _plotMainSingle(self, _x, _yAll, _color, label='composite', y_std = _yAll_std)
            else:
                _plotMainMulti(self, _x, _yAll, _color, label='composite', y_std = _yAll_std)
            log_parsing.log_info(self._view, 'added composite trace')

    # if the checkbox is unchecked:
    else:
        # loop through all axes, check if the line label name R1 exists, if so, remove it
        for _ax in self._view.axMainPlot1:
            for _line in _ax.lines:
                if _line._label == 'composite':
                    log_parsing.log_info(self._view, 'removed composite trace')
                    _line.remove()
                    # remove std fill_betweens
            for _coll in _ax.collections:
                if _coll._label == 'composite' or _coll._label == '_composite':
                    _coll.remove()
        if self._view.axMainPlot2 != []:
            for _ax in self._view.axMainPlot2:
                if _ax.get_color() == 'w':
                    _ax.remove()
                    self._view.axMainPlot2.remove(_ax)
            self._view.traceCanvasMainPlot2.draw_idle()

    self._view.traceCanvasMainPlot1.draw_idle()
    _updateSelectionPlotMain(self)

def _plotMainActiveDark(self):
    if self._view.workspace.selectedROI == []:
        _ROIindex = list(range(self._view.workspace.nSpectra))
    else:
        _ROIindex = self._view.roiDict[self._view.workspace.selectedROI[0]].specIndexList
    _yR1_std = None
    _yR2_std = None
    _yR3_std = None
    _yAll_std = None
    if self._view.meanDisplayMain.isChecked():
        _yR1 = self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].mean()
        _yR2 = self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].mean()
        _yR3 = self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].mean()
        _yAll = self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].mean().values + \
                self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].mean().values + \
                self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].mean().values
        if self._view.meanStdDisplay.isChecked():
            _yR1_std = self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].std()
            _yR2_std = self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].std()
            _yR3_std = self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].std()
            _yAll_std = self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].std().values + \
                        self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].std().values + \
                        self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].std().values
    elif self._view.medianDisplayMain.isChecked():
        # using numpy is slightly faster than using pandas.median
        _yR1 = np.median(self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
        _yR2 = np.median(self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
        _yR3 = np.median(self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
        _yAll = (np.median(self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0) +
                 np.median(self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0) +
                 np.median(self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0))
        if self._view.medianStdDisplay.isChecked():
            _yR1_std = self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].std()
            _yR2_std = self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].std()
            _yR3_std = self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].std()
            _yAll_std = self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].std().values + \
                        self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].std().values + \
                        self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].std().values
    else:
        # read textbox
        # if empty, use index 0
        if self._view.indexSpecMain.text() == '':
            log_parsing.log_warning(self._view, 'No spectral index entered. Using index 0')
            self._view.indexSpecMain.setText('0')
        _indexText = self._view.indexSpecMain.text()
        log_parsing.log_info(self._view, 'Adding traces for spectral indices: '+_indexText)
        _indexStrList = _indexText.split(',')
        self.indexList = []
        for i in _indexStrList:
            if ':' not in i:
                self.indexList.append(int(i))
            else:
                _iList = list(range(int(i.split(':')[0]), int(i.split(':')[1])+1))
                for j in _iList:
                    self.indexList.append(int(j))
        _yR1 = self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].loc[self.indexList].values
        _yR2 = self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].loc[self.indexList].values
        _yR3 = self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].loc[self.indexList].values
        _yAll = (self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].loc[self.indexList].values +
                 self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].loc[self.indexList].values +
                 self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].loc[self.indexList].values)


    if self._view.waveDomainMain.isChecked():
        _x = self._view.workspace.wavelength
    else:
        _x = list(range(self._view.workspace.nChannels))

    if self._view.R1ItemMain.isChecked():
        _color = self._view.workspace.colorR1
        if len(_yR1) == self._view.workspace.nChannels:
            _plotMainSingle(self, _x, _yR1, _color, label='R1', y_std =_yR1_std)
        else:
            _plotMainMulti(self, _x, _yR1, _color, label='R1', y_std =_yR1_std)
    if self._view.R2ItemMain.isChecked():
        _color = self._view.workspace.colorR2
        if len(_yR2) == self._view.workspace.nChannels:
            _plotMainSingle(self, _x, _yR2, _color, label='R2', y_std = _yR2_std)
        else:
            _plotMainMulti(self, _x, _yR2, _color, label='R2', y_std = _yR2_std)
    if self._view.R3ItemMain.isChecked():
        _color = self._view.workspace.colorR3
        if len(_yR3) == self._view.workspace.nChannels:
            _plotMainSingle(self, _x, _yR3, _color, label='R3', y_std =_yR3_std)
        else:
            _plotMainMulti(self, _x, _yR3, _color, label='R3', y_std = _yR3_std)
    if self._view.allItemMain.isChecked():
        _color = self._view.workspace.colorComposite
        if len(_yAll) == self._view.workspace.nChannels:
            _plotMainSingle(self, _x, _yAll, _color, label='composite', y_std = _yAll_std)
        else:
            _plotMainMulti(self, _x, _yAll, _color, label='composite', y_std = _yAll_std)

    if self._view.traceCanvasMainPlot1.axes.xaxis.label._text == '' or True:
        _plotMainFormat(self)
    self._view.traceCanvasMainPlot1.draw_idle()

def _plotMainActiveDarkMultiRoi(self):
    _ROIindex = [self._view.roiDict[_roiList].specIndexList for _roiList in self._view.workspace.selectedROI]
    _yR1_std = None
    _yR2_std = None
    _yR3_std = None
    _yAll_std = None
    if self._view.meanDisplayMain.isChecked():
        _yR1 = [self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_indexList].mean() for _indexList in _ROIindex]
        _yR2 = [self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_indexList].mean() for _indexList in _ROIindex]
        _yR3 = [self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_indexList].mean() for _indexList in _ROIindex]
        _yAll = [(self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_indexList].mean().values +
                  self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_indexList].mean().values +
                  self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_indexList].mean().values) for _indexList in _ROIindex]
        if self._view.meanStdDisplay.isChecked():
            _yR1_std = [self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_indexList].std() for _indexList in _ROIindex]
            _yR2_std = [self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_indexList].std() for _indexList in _ROIindex]
            _yR3_std = [self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_indexList].std() for _indexList in _ROIindex]
            _yAll_std = [(self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_indexList].std().values +
                          self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_indexList].std().values +
                          self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_indexList].std().values) for _indexList in _ROIindex]
    elif self._view.medianDisplayMain.isChecked():
        # using numpy is slightly faster than using pandas.median
        _yR1 = [np.median(self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yR2 = [np.median(self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yR3 = [np.median(self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yAll = [(np.median(self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_indexList], axis=0) +
                  np.median(self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_indexList], axis=0) +
                  np.median(self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_indexList], axis=0)) for _indexList in _ROIindex]
        if self._view.medianStdDisplay.isChecked():
            _yR1_std = [self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_indexList].std() for _indexList in _ROIindex]
            _yR2_std = [self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_indexList].std() for _indexList in _ROIindex]
            _yR3_std = [self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_indexList].std() for _indexList in _ROIindex]
            _yAll_std = [(self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_indexList].std().values +
                          self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_indexList].std().values +
                          self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_indexList].std().values) for _indexList in _ROIindex]
    else:
        log_parsing.log_error(self._view, 'Cannot display subset of selected indices with multiple ROIs selected')

    if self._view.waveDomainMain.isChecked():
        _x = self._view.workspace.wavelength
    else:
        _x = list(range(self._view.workspace.nChannels))

    #cmap = mpl_cm.get_cmap('hsv')
    #_color = [cmap(i/(len(_yR1))) for i in range(len(_yR1))]
    _color = [self._view.roiDict[_roiDictName].color for _roiDictName in self._view.workspace.selectedROI]
    #cmap = mpl_cm.get_cmap('viridis')
    #_color = [cmap(i/(len(_yR1)-1)) for i in range(len(_yR1))]
    _legend = [self._view.roiDict[_roiDictName].humanReadableName for _roiDictName in self._view.workspace.selectedROI]
    if self._view.R1ItemMain.isChecked():
        _plotMainMulti(self, _x, _yR1, _color, label=_legend, legend = True, y_std = _yR1_std)
    elif self._view.R2ItemMain.isChecked():
        _plotMainMulti(self, _x, _yR2, _color, label=_legend, legend = True, y_std = _yR2_std)
    elif self._view.R3ItemMain.isChecked():
        _plotMainMulti(self, _x, _yR3, _color, label=_legend, legend = True, y_std = _yR3_std)
    elif self._view.allItemMain.isChecked():
        _plotMainMulti(self, _x, _yAll, _color, label=_legend, legend = True, y_std = _yAll_std)

    # add the upper axis for wavenumbers
    if self._view.traceCanvasMainPlot1.axes.xaxis.label._text == '' or True:
        _plotMainFormat(self)
    self._view.traceCanvasMainPlot1.draw_idle()
    _addACIMultiRoiImage(self)


def _plotMainActive(self):
    if self._view.workspace.selectedROI == []:
        _ROIindex = list(range(self._view.workspace.nSpectra))
    else:
        _ROIindex = self._view.roiDict[self._view.workspace.selectedROI[0]].specIndexList
    _yR1_std = None
    _yR2_std = None
    _yR3_std = None
    _yAll_std = None
    if self._view.meanDisplayMain.isChecked():
        _yR1 = self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].mean()
        _yR2 = self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].mean()
        _yR3 = self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].mean()
        _yAll = self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].mean().values + \
                self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].mean().values + \
                self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].mean().values
        if self._view.meanStdDisplay.isChecked():
            _yR1_std = self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].mean()
            _yR2_std = self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].mean()
            _yR3_std = self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].mean()
            _yAll_std = self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].mean().values + \
                        self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].mean().values + \
                        self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].mean().values
    elif self._view.medianDisplayMain.isChecked():
        # using numpy is slightly faster than using pandas.median
        _yR1 = np.median(self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
        _yR2 = np.median(self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
        _yR3 = np.median(self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
        _yAll = np.median(self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0) + \
                np.median(self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0) + \
                np.median(self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
        if self._view.medianStdDisplay.isChecked():
            _yR1_std = self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].mean()
            _yR2_std = self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].mean()
            _yR3_std = self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].mean()
            _yAll_std = self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].mean().values + \
                        self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].mean().values + \
                        self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].mean().values
    else:
        # read textbox
        # if empty, use index 0
        if self._view.indexSpecMain.text() == '':
            log_parsing.log_warning(self._view, 'No spectral index entered. Using index 0')
            self._view.indexSpecMain.setText('0')
        _indexText = self._view.indexSpecMain.text()
        log_parsing.log_info(self._view, 'Adding traces for spectral indices: '+_indexText)
        _indexStrList = _indexText.split(',')
        self.indexList = []
        for i in _indexStrList:
            if ':' not in i:
                self.indexList.append(int(i))
            else:
                _iList = list(range(int(i.split(':')[0]), int(i.split(':')[1])+1))
                for j in _iList:
                    self.indexList.append(int(j))
        _yR1 = self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].loc[self.indexList].values
        _yR2 = self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].loc[self.indexList].values
        _yR3 = self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].loc[self.indexList].values
        _yAll = self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].loc[self.indexList].values + \
                self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].loc[self.indexList].values + \
                self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].loc[self.indexList].values


    if self._view.waveDomainMain.isChecked():
        _x = self._view.workspace.wavelength
    else:
        _x = list(range(self._view.workspace.nChannels))

    if self._view.R1ItemMain.isChecked():
        _color = self._view.workspace.colorR1
        if len(_yR1) == self._view.workspace.nChannels:
            _plotMainSingle(self, _x, _yR1, _color, label='R1', y_std = _yR1_std)
        else:
            _plotMainMulti(self, _x, _yR1, _color, label='R1', y_std = _yR1_std)
    if self._view.R2ItemMain.isChecked():
        _color = self._view.workspace.colorR2
        if len(_yR2) == self._view.workspace.nChannels:
            _plotMainSingle(self, _x, _yR2, _color, label='R2', y_std = _yR2_std)
        else:
            _plotMainMulti(self, _x, _yR2, _color, label='R2', y_std = _yR2_std)
    if self._view.R3ItemMain.isChecked():
        _color = self._view.workspace.colorR3
        if len(_yR3) == self._view.workspace.nChannels:
            _plotMainSingle(self, _x, _yR3, _color, label='R3', y_std = _yR3_std)
        else:
            _plotMainMulti(self, _x, _yR3, _color, label='R3', y_std = _yR3_std)
    if self._view.allItemMain.isChecked():
        _color = self._view.workspace.colorComposite
        if len(_yAll) == self._view.workspace.nChannels:
            _plotMainSingle(self, _x, _yAll, _color, label='composite', y_std = _yAll_std)
        else:
            _plotMainMulti(self, _x, _yAll, _color, label='composite', y_std = _yAll_std)

    if self._view.traceCanvasMainPlot1.axes.xaxis.label._text == '' or True:
        _plotMainFormat(self)
    self._view.traceCanvasMainPlot1.draw_idle()

def _plotMainActiveMultiRoi(self):
    _ROIindex = [self._view.roiDict[_roiList].specIndexList for _roiList in self._view.workspace.selectedROI]
    _yR1_std  = None
    _yR2_std  = None
    _yR3_std  = None
    _yAll_std = None
    if self._view.meanDisplayMain.isChecked():
        _yR1 = [self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_indexList].mean() for _indexList in _ROIindex]
        _yR2 = [self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_indexList].mean() for _indexList in _ROIindex]
        _yR3 = [self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_indexList].mean() for _indexList in _ROIindex]
        _yAll = [self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_indexList].mean().values + \
                 self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_indexList].mean().values + \
                 self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_indexList].mean().values for _indexList in _ROIindex]
        if self._view.meanStdDisplay.isChecked():
            _yR1_std = [self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_indexList].std() for _indexList in _ROIindex]
            _yR2_std = [self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_indexList].std() for _indexList in _ROIindex]
            _yR3_std = [self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_indexList].std() for _indexList in _ROIindex]
            _yAll_std = [self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_indexList].std().values + \
                         self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_indexList].std().values + \
                         self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_indexList].std().values for _indexList in _ROIindex]

    elif self._view.medianDisplayMain.isChecked():
        # using numpy is slightly faster than using pandas.median
        _yR1 = [np.median(self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yR2 = [np.median(self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yR3 = [np.median(self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yAll = [np.median(self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_indexList], axis=0) + \
                 np.median(self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_indexList], axis=0) + \
                 np.median(self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_indexList], axis=0) for _indexList in _ROIindex]
        if self._view.medianStdDisplay.isChecked():
            _yR1_std = [self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_indexList].std() for _indexList in _ROIindex]
            _yR2_std = [self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_indexList].std() for _indexList in _ROIindex]
            _yR3_std = [self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_indexList].std() for _indexList in _ROIindex]
            _yAll_std = [self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_indexList].std().values + \
                         self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_indexList].std().values + \
                         self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_indexList].std().values for _indexList in _ROIindex]

    else:
        log_parsing.log_error(self._view, 'Cannot display subset of selected indices with multiple ROIs selected')

    if self._view.waveDomainMain.isChecked():
        _x = self._view.workspace.wavelength
    else:
        _x = list(range(self._view.workspace.nChannels))

    #cmap = mpl_cm.get_cmap('hsv')
    #_color = [cmap(i/(len(_yR1))) for i in range(len(_yR1))]
    _color = [self._view.roiDict[_roiDictName].color for _roiDictName in self._view.workspace.selectedROI]
    _legend = [self._view.roiDict[_roiDictName].humanReadableName for _roiDictName in self._view.workspace.selectedROI]
    if self._view.R1ItemMain.isChecked():
        _plotMainMulti(self, _x, _yR1, _color, label=_legend, legend = True, y_std = _yR1_std)
    elif self._view.R2ItemMain.isChecked():
        _plotMainMulti(self, _x, _yR2, _color, label=_legend, legend = True, y_std = _yR2_std)
    elif self._view.R3ItemMain.isChecked():
        _plotMainMulti(self, _x, _yR3, _color, label=_legend, legend = True, y_std = _yR3_std)
    elif self._view.allItemMain.isChecked():
        _plotMainMulti(self, _x, _yAll, _color, label=_legend, legend = True, y_std = _yAll_std)

    if self._view.traceCanvasMainPlot1.axes.xaxis.label._text == '' or True:
        _plotMainFormat(self)
    self._view.traceCanvasMainPlot1.draw_idle()
    _addACIMultiRoiImage(self)


def _plotMainDark(self):
    if self._view.workspace.selectedROI == []:
        _ROIindex = list(range(self._view.workspace.nSpectra))
    else:
        _ROIindex = self._view.roiDict[self._view.workspace.selectedROI[0]].specIndexList
    _yR1_std  = None
    _yR2_std  = None
    _yR3_std  = None
    _yAll_std = None
    if self._view.meanDisplayMain.isChecked():
        _yR1 = self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].mean()
        _yR2 = self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].mean()
        _yR3 = self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].mean()
        _yAll = (self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].mean().values +
                 self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].mean().values +
                 self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].mean().values)
        if self._view.meanStdDisplay.isChecked():
            _yR1_std = self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].std()
            _yR2_std = self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].std()
            _yR3_std = self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].std()
            _yAll_std = (self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].std().values +
                         self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].std().values +
                         self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].std().values)

    elif self._view.medianDisplayMain.isChecked():
        # using numpy is slightly faster than using pandas.median
        _yR1 = np.median(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
        _yR2 = np.median(self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
        _yR3 = np.median(self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
        _yAll = (np.median(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0) +
                 np.median(self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0) +
                 np.median(self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0))
        if self._view.medianStdDisplay.isChecked():
            _yR1_std = self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].std()
            _yR2_std = self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].std()
            _yR3_std = self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].std()
            _yAll_std = (self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].std().values +
                         self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].std().values +
                         self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].std().values)
    else:
        # read textbox
        # if empty, use index 0
        if self._view.indexSpecMain.text() == '':
            log_parsing.log_warning(self._view, 'No spectral index entered. Using index 0')
            self._view.indexSpecMain.setText('0')
        _indexText = self._view.indexSpecMain.text()
        log_parsing.log_info(self._view, 'Adding traces for spectral indices: '+_indexText)
        _indexStrList = _indexText.split(',')
        self.indexList = []
        for i in _indexStrList:
            if ':' not in i:
                self.indexList.append(int(i))
            else:
                _iList = list(range(int(i.split(':')[0]), int(i.split(':')[1])+1))
                for j in _iList:
                    self.indexList.append(int(j))
        _yR1 = self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].loc[self.indexList].values
        _yR2 = self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].loc[self.indexList].values
        _yR3 = self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].loc[self.indexList].values
        _yAll = self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].loc[self.indexList].values + \
                self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].loc[self.indexList].values + \
                self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].loc[self.indexList].values


    if self._view.waveDomainMain.isChecked():
        _x = self._view.workspace.wavelength
    else:
        _x = list(range(self._view.workspace.nChannels))

    if self._view.R1ItemMain.isChecked():
        _color = self._view.workspace.colorR1
        if len(_yR1) == self._view.workspace.nChannels:
            _plotMainSingle(self, _x, _yR1, _color, label='R1', y_std = _yR1_std)
        else:
            _plotMainMulti(self, _x, _yR1, _color, label='R1', y_std = _yR1_std)
    if self._view.R2ItemMain.isChecked():
        _color = self._view.workspace.colorR2
        if len(_yR2) == self._view.workspace.nChannels:
            _plotMainSingle(self, _x, _yR2, _color, label='R2', y_std = _yR2_std)
        else:
            _plotMainMulti(self, _x, _yR2, _color, label='R2', y_std = _yR2_std)
    if self._view.R3ItemMain.isChecked():
        _color = self._view.workspace.colorR3
        if len(_yR3) == self._view.workspace.nChannels:
            _plotMainSingle(self, _x, _yR3, _color, label='R3', y_std = _yR3_std)
        else:
            _plotMainMulti(self, _x, _yR3, _color, label='R3', y_std = _yR3_std)
    if self._view.allItemMain.isChecked():
        _color = self._view.workspace.colorComposite
        if len(_yAll) == self._view.workspace.nChannels:
            _plotMainSingle(self, _x, _yAll, _color, label='composite', y_std = _yAll_std)
        else:
            _plotMainMulti(self, _x, _yAll, _color, label='composite', y_std = _yAll_std)

    if self._view.traceCanvasMainPlot1.axes.xaxis.label._text == '' or True:
        _plotMainFormat(self)
    self._view.traceCanvasMainPlot1.draw_idle()

def _plotMainDarkMultiRoi(self):
    _ROIindex = [self._view.roiDict[_roiList].specIndexList for _roiList in self._view.workspace.selectedROI]
    _yR1_std  = None
    _yR2_std  = None
    _yR3_std  = None
    _yAll_std = None
    if self._view.meanDisplayMain.isChecked():
        _yR1 = [self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_indexList].mean() for _indexList in _ROIindex]
        _yR2 = [self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_indexList].mean() for _indexList in _ROIindex]
        _yR3 = [self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_indexList].mean() for _indexList in _ROIindex]
        _yAll = [(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_indexList].mean().values +
                  self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_indexList].mean().values +
                  self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_indexList].mean().values) for _indexList in _ROIindex]
        if self._view.meanStdDisplay.isChecked():
            _yR1_std = [self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_indexList].std() for _indexList in _ROIindex]
            _yR2_std = [self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_indexList].std() for _indexList in _ROIindex]
            _yR3_std = [self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_indexList].std() for _indexList in _ROIindex]
            _yAll_std = [(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_indexList].std().values +
                          self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_indexList].std().values +
                          self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_indexList].std().values) for _indexList in _ROIindex]

    elif self._view.medianDisplayMain.isChecked():
        # using numpy is slightly faster than using pandas.median
        _yR1 = [np.median(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yR2 = [np.median(self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yR3 = [np.median(self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yAll = [(np.median(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_indexList], axis=0) +
                  np.median(self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_indexList], axis=0) +
                  np.median(self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_indexList], axis=0)) for _indexList in _ROIindex]
        if self._view.medianStdDisplay.isChecked():
            _yR1_std = [self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_indexList].std() for _indexList in _ROIindex]
            _yR2_std = [self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_indexList].std() for _indexList in _ROIindex]
            _yR3_std = [self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_indexList].std() for _indexList in _ROIindex]
            _yAll_std = [(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_indexList].std().values +
                          self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_indexList].std().values +
                          self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_indexList].std().values) for _indexList in _ROIindex]

    else:
        log_parsing.log_error(self._view, 'Cannot display subset of selected indices with multiple ROIs selected')

    if self._view.waveDomainMain.isChecked():
        _x = self._view.workspace.wavelength
    else:
        _x = list(range(self._view.workspace.nChannels))

    #cmap = mpl_cm.get_cmap('hsv')
    #_color = [cmap(i/(len(_yR1))) for i in range(len(_yR1))]
    _color = [self._view.roiDict[_roiDictName].color for _roiDictName in self._view.workspace.selectedROI]
    _legend = [self._view.roiDict[_roiDictName].humanReadableName for _roiDictName in self._view.workspace.selectedROI]
    if self._view.R1ItemMain.isChecked():
        _plotMainMulti(self, _x, _yR1, _color, label=_legend, legend = True, y_std = _yR1_std)
    elif self._view.R2ItemMain.isChecked():
        _plotMainMulti(self, _x, _yR2, _color, label=_legend, legend = True, y_std = _yR2_std)
    elif self._view.R3ItemMain.isChecked():
        _plotMainMulti(self, _x, _yR3, _color, label=_legend, legend = True, y_std = _yR3_std)
    elif self._view.allItemMain.isChecked():
        _plotMainMulti(self, _x, _yAll, _color, label=_legend, legend = True, y_std = _yAll_std)

    if self._view.traceCanvasMainPlot1.axes.xaxis.label._text == '' or True:
        _plotMainFormat(self)
    self._view.traceCanvasMainPlot1.draw_idle()
    _addACIMultiRoiImage(self)


def _roiSelectMainUpdate(self):
    # determine which ROI checkboxes are selected
    _roiSelected = []
    self._view.workspace.selectedROI = []
    for _roiName in self._view.workspace.roiNames:
        _roiKey = self._view.workspace.roiHumanToDictKey[_roiName]
        if self._view.roiDict[_roiKey].checkboxWidget.isChecked():
            _roiSelected.append(_roiKey)
            self._view.workspace.selectedROI.append(_roiKey)

    if len(_roiSelected) == 1 and _roiSelected[0].split('_')[-1] == 'Full Map':
        self._view.indexDisplayMain.setEnabled(True)
        self._view.indexSpecMain.setEnabled(True)
        _plotMainUpdate(self)
    elif len(_roiSelected) == 1:
        _plotMainUpdate(self)
    else:
        self._view.R1ItemMain.setChecked(False)
        self._view.R2ItemMain.setChecked(False)
        self._view.R3ItemMain.setChecked(False)
        self._view.allItemMain.setChecked(True)
        self._view.indexDisplayMain.setEnabled(False)
        self._view.indexSpecMain.setEnabled(False)
        if self._view.indexDisplayMain.isChecked():
            self._view.meanDisplayMain.setChecked(True)
        _plotMainUpdate(self)
        # TODO: this causes the lower plot to reset zoom/home each time a new ROI is checked, but solves an issue with the incorrect regions being displayed
        if self._view.selectionScrollbarEdit.text() != '':
            self._view._axBackgroundSPAR = None
            _addSelectionPlotMain(self)



def _plotMainSingle(self, x, y, color, alpha=0.9, label='', y_std = None):
    _ax = generate_plots.plotMainTrace(self._view, x, y, color, alpha=alpha, label=label, std = y_std)
    _legend = _ax.get_legend()
    if _legend is not None:
        _legend.remove()
    #if _ax not in self._view.axMainPlot1:
        #self._view.axMainPlot1.append(_ax)
    self._view.axMainPlot1.append(_ax)
    #self._view.axMainPlot1 = [_ax]

def _plotMainMulti(self, x, y, color, label='', legend = False, y_std = None):
    _alpha = 0.6-0.0006*len(y)
    # all lines are not removed with this method:
    #_ax = generate_plots.plotMainTrace(self._view, x, y.T, color, alpha=_alpha, label=label)
    #self._view.axMainPlot1.append(_ax)
    # TODO: fix the calling sequences so that a list is always passed, rather than converting to the right type here
    if type(color) == type(''):
        color = [color]*len(y)
    if type(label) == type(''):
        label = [label]*len(y)

    i = 0
    for _y_i, c_i, _label in zip(y, color, label):
        if y_std is not None:
            _ystd_i = y_std[i]
        else:
            _ystd_i = None
        _ax = generate_plots.plotMainTrace(self._view, x, _y_i, c_i, alpha=_alpha, label=_label, std = _ystd_i)
        if legend:
            _ax.legend()
        else:
            _legend = _ax.get_legend()
            if _legend is not None:
                _legend.remove()
        self._view.axMainPlot1.append(_ax)
        i+=1


def _plotMainFormat(self):
    #self._view.toolbarResizeMain1.triggered.disconnect()
    if self._view.axTopMain is None or (self._view.waveDomainMain.isChecked() and self._view.axTopMain.xaxis.label._text == ''):
        if self._view.axTopMain is not None:
            plotMainFormatReset(self)
        _x1 = self._view.workspace.wavelength
        _laser = self._view.workspace.laserWavelength
        _ax, self._view.axTopMain = generate_plots.formatWavelengthWavenumber(self._view, _x1, x_range = [50, 2098], laser=_laser)
        #self._view.axMainPlot1.append(_ax)
    elif (self._view.ccdDomainMain.isChecked() and self._view.axTopMain.xaxis.label._text != ''):
        plotMainFormatReset(self)
        _x1 = list(range(self._view.workspace.nChannels))
        _ax, self._view.axTopMain = generate_plots.formatCCDPixel(self._view, _x1, x_range = [50, 2098])
        #self._view.axMainPlot1.append(_ax)
    #self._view.toolbarResizeMain1.triggered.connect(functools.partial(_control_main._rescaleYMain1, self))
    #self._view.toolbarMainPlot1.update()
    #self._view.toolbarMainPlot1.push_current()


def plotMainFormatReset(self):
    self._view.axTopMain.set_xticks([])
    self._view.axTopMain.set_xticklabels([])
    self._view.axTopMain.xaxis.set_minor_locator(plt.FixedLocator([]))
    self._view.axTopMain.set_xlabel('', fontsize=10)
    try:
        self._view.axTopMain.remove()
    except:
        pass


def _plotSparFormat(self, x_range_channel = [50, 2098], x_range = False, y_range = False):
    if self._view.axTopSparMain is None or (self._view.waveDomainMain.isChecked() and self._view.axTopSparMain.xaxis.label._text == ''):
        if self._view.axTopSparMain is not None:
            _plotSparFormatReset(self)
        _x1 = self._view.workspace.wavelength
        _laser = self._view.workspace.laserWavelength
        _ax, self._view.axTopSparMain = generate_plots.formatSparWavelengthWavenumber(self._view, _x1, laser=_laser, x_range = x_range, y_range = y_range)
    elif (self._view.ccdDomainMain.isChecked() and self._view.axTopSparMain.xaxis.label._text != ''):
        _plotSparFormatReset(self)
        _x1 = list(range(self._view.workspace.nChannels))
        _ax, self._view.axTopSparMain = generate_plots.formatSparCCDPixel(self._view, _x1, x_range = x_range_channel)
    self._view.toolbarMainPlot2.update()

def _plotSparFormatReset(self):
    #_ax = generate_plots.formatSparReset(self._view)
    self._view.axTopSparMain.set_xticks([])
    self._view.axTopSparMain.set_xticklabels([])
    self._view.axTopSparMain.xaxis.set_minor_locator(plt.FixedLocator([]))
    self._view.axTopSparMain.set_xlabel('', fontsize=10)
    try:
        self._view.axTopSparMain.remove()
    except:
        pass


def _rescaleYMain1(self):
    generate_plots.autoscale_y(self._view.traceCanvasMainPlot1.axes, margin=0.1)
    self._view.traceCanvasMainPlot1.draw_idle()

def _rescaleYMain2(self):
    generate_plots.autoscale_y(self._view.traceCanvasMainPlot2.axes, margin=0.1)
    self._view.traceCanvasMainPlot2.draw_idle()


def _populateRoiCheckGroup(self):
    # clear group box
    for _checkboxIndex in reversed(range(self._view.vboxRoi.count())):
        self._view.vboxRoi.itemAt(_checkboxIndex).widget().setParent(None)
    # clear combobox
    self._view.selectedROICombo.clear()
    self._view.deleteROICombo.clear()
    self._view.exportROICombo.clear()

    self._view.ROIEditButton.setEnabled(False)
    self._view.ROIDeleteButton.setEnabled(False)
    self._view.ROIExportButton.setEnabled(True)

    # add each roi checkbox widget to the groupbox
    for _roi_name in self._view.workspace.roiNames:
        _roi_dict_name = self._view.workspace.roiHumanToDictKey[_roi_name]
        # get ROI class
        #_roiDictName = self._view.workspace.roiHumanToDictKey[_roi_name]
        _checkboxRoi = self._view.roiDict[_roi_dict_name].checkboxWidget
        _checkboxRoi.clicked.connect(functools.partial(_roiSelectMainUpdate, self))
        self._view.vboxRoi.addWidget(_checkboxRoi)
        if len(self._view.workspace.roiNames) < 2:
            _checkboxRoi.setDisabled(True)
        else:
            _checkboxRoi.setDisabled(False)
        _roiComboItems = [self._view.selectedROICombo.itemText(i) for i in range(self._view.selectedROICombo.count())]
        self._view.exportROICombo.addItem(_roi_name)
        if _roi_name not in _roiComboItems and _roi_name != 'Full Map':
            self._view.selectedROICombo.addItem(_roi_name)
            self._view.deleteROICombo.addItem(_roi_name)
            self._view.ROIEditButton.setEnabled(True)
            self._view.ROIDeleteButton.setEnabled(True)





def _populateMetadataTables(self):
    self._view.metadataList.clear()
    _collectSOH = QTreeWidgetItem(['COLLECT SOH', ''])
    self._view.metadataList.addTopLevelItem(_collectSOH)
    _collectSOH.addChild(QTreeWidgetItem(['C&DH PCB Temp.', str(self._view.workspace.CNDH_PCB_TEMP_STAT_REG[-1])]))
    _collectSOH.addChild(QTreeWidgetItem(['C&DH 1.2 V', str(self._view.workspace.CNDH_1_2_V_STAT_REG[-1])]))
    _collectSOH.addChild(QTreeWidgetItem(['C&DH 1.5 V', str(self._view.workspace.CNDH_1_5_V_STAT_REG[-1])]))
    _collectSOH.addChild(QTreeWidgetItem(['C&DH 3.3 V', str(self._view.workspace.CNDH_3_3_V_STAT_REG[-1])]))
    _collectSOH.addChild(QTreeWidgetItem(['C&DH 5 V DAC', str(self._view.workspace.CNDH_5_V_DAC_STAT_REG[-1])]))
    _collectSOH.addChild(QTreeWidgetItem(['C&DH 5 V ADC', str(self._view.workspace.CNDH_5_V_ADC_STAT_REG[-1])]))
    _collectSOH.addChild(QTreeWidgetItem(['C&DH -15 V', str(self._view.workspace.CNDH_NEG_15_V_STAT_REG[-1])]))
    _collectSOH.addChild(QTreeWidgetItem(['C&DH +15 V', str(self._view.workspace.CNDH_15_V_STAT_REG[-1])]))
    _collectSOH.addChild(QTreeWidgetItem(['Total Laser Shots', str(self._view.workspace.laser_shot_counter[-1])]))
    _collectSOH.addChild(QTreeWidgetItem(['Total Laser Misfires', str(self._view.workspace.laser_misfire_counter[-1])]))
    _collectSOH.addChild(QTreeWidgetItem(['Total Arc Events', str(self._view.workspace.arc_event_counter[-1])]))

    _SE_collectSOH = QTreeWidgetItem(['SE COLLECT SOH', ''])
    self._view.metadataList.addTopLevelItem(_SE_collectSOH)
    _SE_collectSOH.addChild(QTreeWidgetItem(['CCD ID', str(self._view.workspace.SE_CCD_ID_STAT_REG[-1])]))
    _SE_collectSOH.addChild(QTreeWidgetItem(['CCD Temp.', str(self._view.workspace.SE_CCD_TEMP_STAT_REG[-1])]))
    _SE_collectSOH.addChild(QTreeWidgetItem(['PCB Temp.', str(self._view.workspace.SE_PCB_TEMP_STAT_REG[-1])]))
    _SE_collectSOH.addChild(QTreeWidgetItem(['SE 1.5 V', str(self._view.workspace.SE_V_1_5_STAT_REG[-1])]))
    _SE_collectSOH.addChild(QTreeWidgetItem(['Laser PRT 1', str(self._view.workspace.SE_LASER_PRT1_STAT_REG[-1])]))
    _SE_collectSOH.addChild(QTreeWidgetItem(['Laser PRT 2', str(self._view.workspace.SE_LASER_PRT2_STAT_REG[-1])]))
    _SE_collectSOH.addChild(QTreeWidgetItem(['LPS PRT 1', str(self._view.workspace.SE_LPS_PRT1_STAT_REG[-1])]))
    _SE_collectSOH.addChild(QTreeWidgetItem(['LPS PRT 2', str(self._view.workspace.SE_LPS_PRT2_STAT_REG[-1])]))
    _SE_collectSOH.addChild(QTreeWidgetItem(['TPRB Housing Temp.', str(self._view.workspace.SE_TPRB_HOUSING_PRT_STAT_REG[-1])]))
    _SE_collectSOH.addChild(QTreeWidgetItem(['Spare PRT', str(self._view.workspace.SE_SPARE1_PRT_STAT_REG[-1])]))

    _CCD_vert = QTreeWidgetItem(['CCD Vert Config', ''])
    self._view.metadataList.addTopLevelItem(_CCD_vert)
    _CCD_vert.addChild(QTreeWidgetItem(['Col 1 Low', str(self._view.workspace.CCD_VERT_COL1_LOW[-1])]))
    _CCD_vert.addChild(QTreeWidgetItem(['Col 1 High', str(self._view.workspace.CCD_VERT_COL1_HIGH[-1])]))
    _CCD_vert.addChild(QTreeWidgetItem(['Col 2 Low', str(self._view.workspace.CCD_VERT_COL2_LOW[-1])]))
    _CCD_vert.addChild(QTreeWidgetItem(['Col 2 High', str(self._view.workspace.CCD_VERT_COL2_HIGH[-1])]))
    _CCD_vert.addChild(QTreeWidgetItem(['Col 3 Low', str(self._view.workspace.CCD_VERT_COL3_LOW[-1])]))
    _CCD_vert.addChild(QTreeWidgetItem(['Col 3 High', str(self._view.workspace.CCD_VERT_COL3_HIGH[-1])]))

    _CCD_horz = QTreeWidgetItem(['CCD Horz Config', ''])
    self._view.metadataList.addTopLevelItem(_CCD_horz)
    _CCD_horz.addChild(QTreeWidgetItem(['Clock Limit', str(self._view.workspace.CCD_HORZ_CLOCK_LIM[-1])]))
    _CCD_horz.addChild(QTreeWidgetItem(['Col 1 Low', str(self._view.workspace.CCD_HORZ_R1_CLOCK_Low[-1])]))
    _CCD_horz.addChild(QTreeWidgetItem(['Col 1 High', str(self._view.workspace.CCD_HORZ_R1_CLOCK_HIGH[-1])]))
    _CCD_horz.addChild(QTreeWidgetItem(['Col 2 Low', str(self._view.workspace.CCD_HORZ_R2_CLOCK_Low[-1])]))
    _CCD_horz.addChild(QTreeWidgetItem(['Col 2 High', str(self._view.workspace.CCD_HORZ_R2_CLOCK_HIGH[-1])]))
    _CCD_horz.addChild(QTreeWidgetItem(['Col 3 Low', str(self._view.workspace.CCD_HORZ_R3_CLOCK_Low[-1])]))
    _CCD_horz.addChild(QTreeWidgetItem(['Col 3 High', str(self._view.workspace.CCD_HORZ_R3_CLOCK_HIGH[-1])]))

    _CCD_config = QTreeWidgetItem(['CCD Config', ''])
    self._view.metadataList.addTopLevelItem(_CCD_config)
    _CCD_config.addChild(QTreeWidgetItem(['Mode 2D', str(self._view.workspace.MODE_2D[-1])]))
    _CCD_config.addChild(QTreeWidgetItem(['Gain 2D', str(self._view.workspace.CCD_GAIN_2D[-1])]))
    _CCD_config.addChild(QTreeWidgetItem(['Gain Enable', str(self._view.workspace.GAIN_ENABLE[-1])]))
    _CCD_config.addChild(QTreeWidgetItem(['Region Enable', str(self._view.workspace.REGION_ENABLE[-1])]))
    _CCD_config.addChild(QTreeWidgetItem(['HORZ Enable', str(self._view.workspace.HORZ_ENABLE[-1])]))
    _CCD_config.addChild(QTreeWidgetItem(['Skip 1', str(self._view.workspace.SKIP_1[-1])]))
    _CCD_config.addChild(QTreeWidgetItem(['Sum 1', str(self._view.workspace.SUM_1[-1])]))
    _CCD_config.addChild(QTreeWidgetItem(['Skip 2', str(self._view.workspace.SKIP_2[-1])]))
    _CCD_config.addChild(QTreeWidgetItem(['Sum 2', str(self._view.workspace.SUM_2[-1])]))
    _CCD_config.addChild(QTreeWidgetItem(['Skip 3', str(self._view.workspace.SKIP_3[-1])]))
    _CCD_config.addChild(QTreeWidgetItem(['Sum 3', str(self._view.workspace.SUM_3[-1])]))
    _CCD_config.addChild(QTreeWidgetItem(['Skip 4', str(self._view.workspace.SKIP_4[-1])]))
    _CCD_config.addChild(QTreeWidgetItem(['Sum 4', str(self._view.workspace.SUM_4[-1])]))
    _CCD_config.addChild(QTreeWidgetItem(['Skip 5', str(self._view.workspace.SKIP_5[-1])]))
    _CCD_config.addChild(QTreeWidgetItem(['Sum 6', str(self._view.workspace.SUM_5[-1])]))
    _CCD_config.addChild(QTreeWidgetItem(['Last Skip', str(self._view.workspace.LAST_SKIP[-1])]))

    _laser_config = QTreeWidgetItem(['Laser Config', ''])
    self._view.metadataList.addTopLevelItem(_laser_config)
    _laser_config.addChild(QTreeWidgetItem(['Integration Time', str(self._view.workspace.LASER_INT_TIME[-1])]))
    _laser_config.addChild(QTreeWidgetItem(['On Time', str(self._view.workspace.LASER_ON_TIME[-1])]))
    _laser_config.addChild(QTreeWidgetItem(['Rep Rate', str(self._view.workspace.LASER_REP_RATE[-1])]))
    _laser_config.addChild(QTreeWidgetItem(['Pulse Width', str(self._view.workspace.PULSE_WIDTH[-1])]))
    _laser_config.addChild(QTreeWidgetItem(['Current', str(self._view.workspace.LASER_CURRENT[-1])]))
    _laser_config.addChild(QTreeWidgetItem(['Shots', str(self._view.workspace.LASER_SHOTS[-1])]))

    self._view.metadataList.expandAll()
    self._view.metadataList.resizeColumnToContents(0)


def _populateFileListTable(self):
    self._view.dataFileListTable.clear()
    for file in self._view.fileNames:
        self._view.dataFileListTable.addItem(file)

def _populateDimensionListTable(self):
    # add the dimensions (grouped by class) to dimensionList
    for dClass in self._view.dimensionClassDict:
        if dClass != 'Discovered':
            # to add parent item:
            dimensionClass = QTreeWidgetItem([dClass, ''])
            self._view.dimensionListTable.addTopLevelItem(dimensionClass)
            # to add child item
            for dID in self._view.dimensionClassDict[dClass]:
                dimensionClass.addChild(QTreeWidgetItem([dID, str(self._view.dimensionDict[dID]['size'])]))
    self._view.dimensionListTable.expandAll()
    self._view.dimensionListTable.resizeColumnToContents(0)

def _populateTableListTable(self):
    # add the tables to tableList
    for tab in self._view.tableDict:
        _dim0 = self._view.tableDict[tab]['dimension_ids'][0]
        if 'DiscoveredDimension' not in _dim0:
            # to add parent item:
            tableEntry = QTreeWidgetItem([tab, ''])
            self._view.tableListTable.addTopLevelItem(tableEntry)
            # to add child item
            for i, tabDim in enumerate(self._view.tableDict[tab]['dimension_ids']):
                tableEntry.addChild(QTreeWidgetItem([tabDim, str(self._view.tableDict[tab]['size'][i])]))
    self._view.tableListTable.expandAll()
    self._view.tableListTable.resizeColumnToContents(0)


def _initSparDim1Selection(self):
    # clear combo boxes
    self._view.selectedXDimCombo.clear()
    self._view.selectedYDimCombo.clear()
    # add each dimension option to the combo box
    for dim in self._view.dimensionDict:
        if 'DiscoveredDimension' not in dim:
            self._view.selectedXDimCombo.addItem(dim)
    if len(self._view.dimensionDict) > 0:
        self._view.selectedXDimCombo.setEnabled(True)
        _initSparDim2Selection(self, list(self._view.dimensionDict.keys())[0])
        self._view.selectedYDimCombo.setEnabled(True)


# determine the matching 2nd dimensions to use in the plot (and the corresponding table names)
def _initSparDim2Selection(self, dimName):
    self._view.addTraceButtonMain.setEnabled(False)
    self._view.selectedXDimCombo.setEnabled(True)
    self._view.selectedYDimCombo.clear()
    # add the dimension (y axis) options to dimension2Tab1Combo
    _dim2Items = []
    for tab in self._view.tableDict:
        if dimName in self._view.tableDict[tab]['dimension_ids']:
            _dims = [d for d in self._view.tableDict[tab]['dimension_ids'] if d != dimName]
            for dim in _dims:
                _dimText = dim + ' (' + tab + ')'
                _dim2Items.append(_dimText)
            if len(_dims) == 0:
                _dimText = 'None (' + tab + ')'
                _dim2Items.append(_dimText)


    for _dim in _dim2Items:
        if 'DiscoveredDimension' not in _dim:
            self._view.selectedYDimCombo.addItem(_dim)
    if len(_dim2Items) > 0:
        _selectSparPlotDim2(self)
    else:
        self._view.cursorSpecMain.setEnabled(False)

def _selectSparPlotDim2(self):
    self._view.cursorSpecMain.setEnabled(True)
    self._view.cursorSpecMain.clear()
    self._view.cursorSpecMain.setPlaceholderText('e.g.: 1,2,8:10')
    self._view.addTraceButtonMain.setEnabled(False)

def _selectSparPlotCursor(self):
    self._view.addTraceButtonMain.setEnabled(True)

# The user defines the first dimension (x axis)
def _init1DSparDim1(self):
    _intial_xBounds = self._view.traceCanvasMainPlot2.axes.get_xbound()
    _clearSparPlotMain(self)
    # identify the dimension selected
    dimName = self._view.selectedXDimCombo.currentText()
    # populate selectedYDimCombo with available dimensions
    _initSparDim2Selection(self, dimName)


def _clearPlotMain(self):
    # remove top axis and wavenumber ticks, if they are present
    if self._view.axTopMain is not None and self._view.axTopMain.xaxis.label != '':
        self._view.axTopMain.set_xticks([])
        self._view.axTopMain.set_xticklabels([])
        self._view.axTopMain.xaxis.set_minor_locator(plt.FixedLocator([]))
        self._view.axTopMain.set_xlabel('', fontsize=10)
    for _ax in self._view.axMainPlot1:
        _ax.remove()
    self._view.axMainPlot1 = []
    #self._view.traceCanvasMainPlot1.axes.clear()
    self._view.traceCanvasMainPlot1.draw_idle()


def _clearSparPlotMain(self):
    # remove top axis and wavenumber ticks, if they are present
    if self._view.axTopSparMain is not None and self._view.axTopSparMain.xaxis.label != '':
        self._view.axTopSparMain.set_xticks([])
        self._view.axTopSparMain.set_xticklabels([])
        self._view.axTopSparMain.xaxis.set_minor_locator(plt.FixedLocator([]))
        self._view.axTopSparMain.set_xlabel('', fontsize=10)

        #_plotSparFormatReset(self)
        #self._view.traceCanvasMainPlot2.axes.clear()
        #self._view.traceCanvasMainPlot2.axes.tick_params(top=False, labeltop=False)
        #self._view.traceCanvasMainPlot2.axes.get_xaxis().set_visible(False)

    for _ax in self._view.axMainPlot2:
        #for _line in _ax.lines:
            #_line.remove()
        _ax.remove()
    self._view.axMainPlot2 = []
    self._view.traceCanvasMainPlot2.axes.clear()
    if self._view.traceCanvasMainPlot2.axes.get_legend() is not None:
        self._view.traceCanvasMainPlot2.axes.get_legend().remove()
    self._view.traceCanvasMainPlot2.draw_idle()

def _addSparTrace(self):
    self._view._axBackgroundSPAR = None
    # add plot trace items to the tableFileListTab1:
    _dim1 = self._view.selectedXDimCombo.currentText()
    _dim2 = self._view.selectedYDimCombo.currentText().split(' (')[0]
    _table = self._view.selectedYDimCombo.currentText().split('(')[-1].split(')')[0]
    _indexText = self._view.cursorSpecMain.text()
    _indexStrList = _indexText.split(',')
    _indexList = []
    for i in _indexStrList:
        if ':' not in i:
            _indexList.append(str(i))
        else:
            _iList = list(range(int(i.split(':')[0]), int(i.split(':')[1])+1))
            for j in _iList:
                _indexList.append(str(j))
    _lineNames = [_axIndex._label for _axIndex in self._view.axMainPlot2]
    for _index in _indexList:
        # get all legend items
        # TODO: replace index number with index name, if one exists
        _legendName = _table + ': ' + _dim2 + ' (index '+ _index.strip() + ') vs ' + _dim1
        if _legendName not in _lineNames:
            # add the trace to the canvas
            if _dim2 != 'None':
                _yDim = self._view.SPARProd.getDimension(self._view.dimensionDict[_dim2]['index'])
                if int(_index) >= _yDim.getSize() or int(_index) < 0:
                    log_parsing.log_warning(self._view, 'Selected index outside range. Select again.')
                    break
            _xData, _yData = _get1DData(self, _dim1, _dim2, _table, int(_index)+1)
            _ax = self._view.traceCanvasMainPlot2.axes.plot(_xData, _yData, label=_legendName, alpha=0.5)[0]
            self._view.traceCanvasMainPlot2.axes.set_xlabel(_dim1)
            if len(_indexList) < 10:
                self._view.traceCanvasMainPlot2.axes.legend(loc=0, ncol=1, fancybox=False, fontsize=8, frameon = False, framealpha=0.5)
            self._view.traceCanvasMainPlot2.axes.relim()
            self._view.traceCanvasMainPlot2.axes.autoscale_view()
            self._view.traceCanvasMainPlot2.draw_idle()
            self._view.axMainPlot2.append(_ax)

def _get1DData(self, _dim1, _dim2, _table, _index):
    _itemTableIndex = self._view.tableDict[_table]['index']
    _itemTable = self._view.SPARProd.getTable(_itemTableIndex+1)

    _xDim = self._view.SPARProd.getDimension(self._view.dimensionDict[_dim1]['index'])
    _xDimIndex = _itemTable.getIndexForDimension(_xDim)
    _xDimLen = _itemTable.getSize(_xDimIndex)

    if _dim2 != 'None':
        _yDim = self._view.SPARProd.getDimension(self._view.dimensionDict[_dim2]['index'])
        _yDimIndex = _itemTable.getIndexForDimension(_yDim)
        _yDimLen = _itemTable.getSize(_yDimIndex)
        _itemCursor = _itemTable.createCursor(_yDimIndex)

    else:
        _itemCursor = _itemTable.createCursor(2)

    _dataSlice = _itemTable.readData(_itemCursor, int(_index))
    _yData = [_dataSlice.getDouble(j+1)[1] for j in range(_xDimLen)]
    return range(_xDimLen), _yData



#################### Imaging
# ACI
def _populateImageMetadataList(self):
    self._view.imageMetadataList.setItem(0, 1, QTableWidgetItem(str(self._view.workspace.WATSONAttributes['pixelScale'])))
    self._view.imageMetadataList.setItem(0, 2, QTableWidgetItem(str(self._view.workspace.ACIAttributes['pixelScale'])))

    self._view.imageMetadataList.setItem(1, 1, QTableWidgetItem(str(self._view.workspace.WATSONAttributes['range'])))
    self._view.imageMetadataList.setItem(1, 2, QTableWidgetItem(str(self._view.workspace.ACIAttributes['range'])))

    self._view.imageMetadataList.setItem(2, 1, QTableWidgetItem(str(self._view.workspace.WATSONAttributes['CDPID'])))
    self._view.imageMetadataList.setItem(2, 2, QTableWidgetItem(str(self._view.workspace.ACIAttributes['CDPID'])))

    self._view.imageMetadataList.setItem(3, 1, QTableWidgetItem(str(self._view.workspace.WATSONAttributes['motor_pos'])))
    self._view.imageMetadataList.setItem(3, 2, QTableWidgetItem(str(self._view.workspace.ACIAttributes['motor_pos'])))

    self._view.imageMetadataList.setItem(4, 1, QTableWidgetItem(str(self._view.workspace.WATSONAttributes['exp_time'])))
    self._view.imageMetadataList.setItem(4, 2, QTableWidgetItem(str(self._view.workspace.ACIAttributes['exp_time'])))

    self._view.imageMetadataList.setItem(5, 1, QTableWidgetItem(str(self._view.workspace.WATSONAttributes['product_ID'])))
    self._view.imageMetadataList.setItem(5, 2, QTableWidgetItem(str(self._view.workspace.ACIAttributes['product_ID'])))

    self._view.imageMetadataList.setItem(6, 1, QTableWidgetItem(str(self._view.workspace.WATSONAttributes['led_flag'])))
    self._view.imageMetadataList.setItem(6, 2, QTableWidgetItem(str(self._view.workspace.ACIAttributes['led_flag'])))

    _populateACILaserSpotParameters(self)

def _populateACILaserSpotParameters(self):
    # update Laser - ACI parameters
    # if parameters are equivalent to "old" parameters, highlight in red
    if int(self._view.workspace.laserCenter[0]) == 809 and int(self._view.workspace.laserCenter[1]) == 658 and self._view.workspace.azScale == 0.643 and self._view.workspace.elScale == 0.455:
        self._view.xPosLaser.setStyleSheet('color: rgb(255,0,0);')
        self._view.yPosLaser.setStyleSheet('color: rgb(255,0,0);')
        self._view.azScaleLaser.setStyleSheet('color: rgb(255,0,0);')
        self._view.elScaleLaser.setStyleSheet('color: rgb(255,0,0);')
        self._view.rotLaser.setStyleSheet('color: rgb(255,0,0);')
        # use new parameters to make is easier for user to update to new values
        self._view.xPosLaser.setText(str(int(809)))
        self._view.yPosLaser.setText(str(int(664)))
        self._view.azScaleLaser.setText('{0:.5f}'.format(0.628154699))
        self._view.elScaleLaser.setText('{0:.5f}'.format(0.422441487))
        self._view.rotLaser.setText('{0:.5f}'.format(20.6793583))
    else:
        self._view.xPosLaser.setStyleSheet('color: rgb(255,255,255);')
        self._view.yPosLaser.setStyleSheet('color: rgb(255,255,255);')
        self._view.azScaleLaser.setStyleSheet('color: rgb(255,255,255);')
        self._view.elScaleLaser.setStyleSheet('color: rgb(255,255,255);')
        self._view.rotLaser.setStyleSheet('color: rgb(255,255,255);')
        self._view.xPosLaser.setText(str(int(self._view.workspace.laserCenter[0])))
        self._view.yPosLaser.setText(str(int(self._view.workspace.laserCenter[1])))
        self._view.azScaleLaser.setText('{0:.5f}'.format(self._view.workspace.azScale))
        self._view.elScaleLaser.setText('{0:.5f}'.format(self._view.workspace.elScale))
        self._view.rotLaser.setText('{0:.5f}'.format(self._view.workspace.rotation))

    self._view.resetLaserSpotMain.setEnabled(True)


def _recalculateLaserSpots(self):
    log_parsing.log_info(self._view, 'Recalculating ACI laser shot positions.')
    # save textbox entries to workspace
    self._view.workspace.laserCenter = (int(self._view.xPosLaser.text()), int(self._view.yPosLaser.text()))
    self._view.workspace.azScale = float(self._view.azScaleLaser.text())
    self._view.workspace.elScale = float(self._view.elScaleLaser.text())
    self._view.workspace.rotation = float(self._view.rotLaser.text())

    #update textbox entry (change colors if necessary)
    _populateACILaserSpotParameters(self)

    # re-calculate laser spot positions
    _tableX, _tableY, _pix_x, _pix_y, _pix_x_float, _pix_y_float = parse_dat_files.calculate_positions(self._view.workspace.az, self._view.workspace.el, self._view, az_scale=self._view.workspace.azScale, el_scale=self._view.workspace.elScale, center=self._view.workspace.laserCenter, pix_um = 10.1, rotation=self._view.workspace.rotation)
    self._view.workspace.x = _tableX
    self._view.workspace.y = _tableY
    self._view.workspace.xyTable = pd.DataFrame(np.array([self._view.workspace.x, self._view.workspace.y]).T, columns = ['x', 'y'])

    # update spatial.csv file
    _spatial_file = os.path.join(self._view.workspace.workingDir, 'spatial.csv')
    file_IO.writeTable(_spatial_file, self._view, self._view.workspace.scannerTable, self._view.workspace.scannerTableCommanded, self._view.workspace.xyTable, self._view.workspace.xyTableCommanded, self._view.workspace.scannerTableErr, self._view.workspace.scannerCurrent)

    # update loupe.csv file
    _loupe_file = os.path.join(self._view.workspace.workingDir, 'loupe.csv')
    file_IO.writeLoupeCsv(_loupe_file, self._view)

    # update SOFF file (byte offset changes - no it does not)
    #self._view.workspace.writeDataCsv(self._view, SOFF_only = True)

    # update laser spot map
    _defineLaserShots(self)
    _addACIImage(self)
    _control_norm._updateNormCentralPanel(self)



# if the Open ACI button is selected
def _openACI(self):
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    if self._view._test:
        self._view.workspace.selectedACIFilename = os.path.join(os.sep, 'Users', '[user_name]', 'Documents', 'Loupe', 'Loupe', 'test_data', 'sol_0059', 'rawDps', 'maze_1', 'SC3_0059_0672191316_445ECM_N0032046SRLC15041_0000LUJ01.IMG')

    else:
        self._view.workspace.selectedACIFilename, _ = QFileDialog.getOpenFileName(self._view,"QFileDialog.getOpenFileName()", "","All Files (*);;IMG (*.IMG);;PNG (*.png)", options = options)

    _parseACI(self)
    _control_norm._updateNormLeftPanel(self)
    _control_norm._updateNormCentralPanel(self)
    _control_false_color._updateRGBLeftPanel(self)
    _control_false_color._clearMap(self)

def _parseACI(self):
    # check if image format is IMG or PNG
    if self._view.workspace.selectedACIFilename.endswith('IMG') or self._view.workspace.selectedACIFilename.endswith('PNG') or self._view.workspace.selectedACIFilename.endswith('png'):
        # If IMG, read metadata from label
        log_parsing.log_warning(self._view, 'Opening ACI image file {0}'.format(self._view.workspace.selectedACIFilename))
        im_arr, self._view.workspace.selectedACIFilename = file_IO.parseImgFile(self._view, self._view.workspace.selectedACIFilename, self._view.workspace)
        # populate table
        _populateImageMetadataList(self)
        self._view.imageMetadataList.setEnabled(True)
        # NOTE: if stitching points together and an error is thrown here, it means you didn't update the byte offset in the SOFF files
        _defineLaserShots(self)
        _addACIImage(self)
        self._view.imageACI.fitInView()
        #self._view.mainImgScrollContainer.installEventFilter(self._view.mainImgScrollContainer)
        # enable other buttons
        self._view.groupboxROI.setEnabled(True)
        self._view.groupboxLaserMain.setEnabled(True)
        #self._view.groupboxRelPosLaserWidget.setEnabled(True)
        self._view.selectionScrollbarMain.setMaximum(self._view.workspace.nSpectra-1)
        # show spec in lower plot when hovering over laser spots

    else:
        log_parsing.log_warning(self._view, 'Selected ACI file {0} does not have the expected PNG or IMG extension'.format(self._view.workspace.selectedACIFilename))

def _defineLaserShots(self):
    # laser spot locations
    _, self._view.workspace.x = _get1DData(self, 'Points', 'None', 'Spatial Table XY', 1)
    _, self._view.workspace.y = _get1DData(self, 'Points', 'None', 'Spatial Table XY', 2)
    # scale laser pulse positions to image width
    # don't scale image to avoid pixelation artifacts
    #_w = self._view.pixmapACI.width()
    #_h = self._view.pixmapACI.height()
    #_wOrig = im_arr.shape[1]
    #_hOrig = im_arr.shape[0]
    #_scaleFactor = np.mean([(_w/_wOrig), (_h/_hOrig)])
    _scaleFactor = 1.0

    self._view.workspace.xPix = [self._view.workspace.laserCenter[0]*_scaleFactor - x*_scaleFactor*1000/float(self._view.workspace.ACIAttributes['pixelScale']) for x in self._view.workspace.x]
    self._view.workspace.yPix = [self._view.workspace.laserCenter[1]*_scaleFactor - y*_scaleFactor*1000/float(self._view.workspace.ACIAttributes['pixelScale']) for y in self._view.workspace.y]
    # laser spot size
    # laser spot size: 100 um
    self._view.workspace.laserPix = 100*_scaleFactor/float(self._view.workspace.ACIAttributes['pixelScale'])


def _addACIImage(self):
    # add image to right frame
    #self._view.imageACI.clearImage()
    self._view.pixmapACI = QPixmap(self._view.workspace.selectedACIFilename)
    #self._view.pixmapACI = self._view.pixmapACI.scaledToWidth(self._view.imageACI.width())
    if len(self._view.workspace.selectedROI) == 0 or (len(self._view.workspace.selectedROI) == 1 and self._view.workspace.selectedROI[0].split('_')[-1] == 'Full Map'):
        _addLaserShots(self)
    else:
        _addLaserShotsMultiRoi(self)
    #self._view.imageACIScene.addPixmap(pixmap1)
    self._view.imageACI.setPhoto(pixmap = self._view.pixmapACI, zoomSelect = self._view.imageACI._zoom)

    self._view.imageACI.mouseDoubleClickEvent = self._getAciPos


def _addACIMultiRoiImage(self):
    # add image to right frame
    self._view.pixmapACI = QPixmap(self._view.workspace.selectedACIFilename)
    _addLaserShotsMultiRoi(self)
    self._view.imageACI.setPhoto(pixmap = self._view.pixmapACI, zoomSelect = self._view.imageACI._zoom)



def _addLaserShots(self):
    self._view.Overlay = QPainter(self._view.pixmapACI)
    self._view.Overlay.setPen(QPen(Qt.black, 1, Qt.SolidLine))
    self._view.Overlay.setBrush(QBrush(Qt.black, Qt.SolidPattern))
    self._view.Overlay.setOpacity(1 - float(self._view.opacityACIMain.value())/100.0)
    self._view.Overlay.drawRect(0, 0, self._view.pixmapACI.width(), self._view.pixmapACI.height())
    self._view.Overlay.end()

    # add laser shots
    self._view.laserPainterInstance = QPainter(self._view.pixmapACI)
    self._view.laserPainterInstance.setPen(QPen(Qt.red, 1, Qt.SolidLine))
    if self._view.pointFillMain.isChecked():
        self._view.laserPainterInstance.setBrush(QBrush(Qt.red, Qt.SolidPattern))
    self._view.laserPainterInstance.setOpacity(float(self._view.opacityLaserMain.value())/100.0)
    for i in range(len(self._view.workspace.xPix)):
        self._view.laserPainterInstance.drawEllipse(QPoint(self._view.workspace.xPix[i], self._view.workspace.yPix[i]), self._view.workspace.laserPix/2.0, self._view.workspace.laserPix/2.0)
        #self._view.laserPainterInstance.drawPoint(self._view.workspace.xPix[i], self._view.workspace.yPix[i])
    for i in self._view.tempRoi:
        self._view.laserPainterInstance.setPen(QPen(QColor(self._view.tempRoiColor), 1, Qt.SolidLine))
        if self._view.pointFillMain.isChecked():
            self._view.laserPainterInstance.setBrush(QBrush(QColor(self._view.tempRoiColor), Qt.SolidPattern))
        self._view.laserPainterInstance.setOpacity(float(self._view.opacityLaserMain.value())/100.0)
        self._view.laserPainterInstance.drawEllipse(QPoint(self._view.workspace.xPix[i], self._view.workspace.yPix[i]), self._view.workspace.laserPix/2.0, self._view.workspace.laserPix/2.0)
    for i in self._view.workspace.SelectedAciIndex:
        self._view.laserPainterInstance.setPen(QPen(QColor('#002fff'), 1, Qt.SolidLine))
        if self._view.pointFillMain.isChecked():
            self._view.laserPainterInstance.setBrush(QBrush(QColor('#002fff'), Qt.SolidPattern))
        self._view.laserPainterInstance.setOpacity(float(self._view.opacityLaserMain.value())/100.0)
        self._view.laserPainterInstance.drawEllipse(QPoint(self._view.workspace.xPix[i], self._view.workspace.yPix[i]), self._view.workspace.laserPix/2.0, self._view.workspace.laserPix/2.0)
        #self._view.laserPainterInstance.drawPoint(self._view.workspace.xPix[i], self._view.workspace.yPix[i])

    self._view.laserPainterInstance.end()


def _addLaserShotsMultiRoi(self):
    # list of spectrum index for each ROI - skip full_map ROI
    _sub_ROI_selection = [_roi for _roi in self._view.workspace.selectedROI if _roi.split('_')[-1] != 'Full Map']
    _ROIindex = [self._view.roiDict[_roiList].specIndexList for _roiList in _sub_ROI_selection]
    _color = [self._view.roiDict[_roiDictName].color for _roiDictName in _sub_ROI_selection]
    _alphaMultiplier = 1.0/len(_color)

    # create list of all points in _ROIindex, count number of instances in each point
    # set alpha value for multiple points accordingly
    _allPoints = [item for sublist in _ROIindex for item in sublist]

    self._view.Overlay = QPainter(self._view.pixmapACI)
    self._view.Overlay.setPen(QPen(Qt.black, 1, Qt.SolidLine))
    self._view.Overlay.setBrush(QBrush(Qt.black, Qt.SolidPattern))
    self._view.Overlay.setOpacity(1 - float(self._view.opacityACIMain.value())/100.0)
    self._view.Overlay.drawRect(0, 0, self._view.pixmapACI.width(), self._view.pixmapACI.height())
    self._view.Overlay.end()

    # add laser shots
    self._view.laserPainterInstance = QPainter(self._view.pixmapACI)
    self._view.laserPainterInstance.setPen(QPen(Qt.red, 1, Qt.SolidLine))
    if self._view.pointFillMain.isChecked():
        self._view.laserPainterInstance.setBrush(QBrush(Qt.red, Qt.SolidPattern))
    self._view.laserPainterInstance.setOpacity(float(self._view.opacityLaserMain.value())/100.0)
    for i in range(len(self._view.workspace.xPix)):
        if i not in _allPoints:
            self._view.laserPainterInstance.drawEllipse(QPoint(self._view.workspace.xPix[i], self._view.workspace.yPix[i]), self._view.workspace.laserPix/2.0, self._view.workspace.laserPix/2.0)

    for _indexList, _c in zip(_ROIindex, _color):
        for i in _indexList:
            _alphaMultiplier = 1.0/_allPoints.count(i)
            self._view.laserPainterInstance.setPen(QPen(QColor(_c), 1, Qt.SolidLine))
            if self._view.pointFillMain.isChecked():
                self._view.laserPainterInstance.setBrush(QBrush(QColor(_c), Qt.SolidPattern))
            self._view.laserPainterInstance.setOpacity(float(_alphaMultiplier*self._view.opacityLaserMain.value())/100.0)
            self._view.laserPainterInstance.drawEllipse(QPoint(self._view.workspace.xPix[i], self._view.workspace.yPix[i]), self._view.workspace.laserPix/2.0, self._view.workspace.laserPix/2.0)
    for i in self._view.workspace.SelectedAciIndex:
        self._view.laserPainterInstance.setPen(QPen(QColor('#002fff'), 1, Qt.SolidLine))
        if self._view.pointFillMain.isChecked():
            self._view.laserPainterInstance.setBrush(QBrush(QColor('#002fff'), Qt.SolidPattern))
        self._view.laserPainterInstance.setOpacity(float(self._view.opacityLaserMain.value())/100.0)
        self._view.laserPainterInstance.drawEllipse(QPoint(self._view.workspace.xPix[i], self._view.workspace.yPix[i]), self._view.workspace.laserPix/2.0, self._view.workspace.laserPix/2.0)
        #self._view.laserPainterInstance.drawPoint(self._view.workspace.xPix[i], self._view.workspace.yPix[i])
    self._view.laserPainterInstance.end()


# intial display of laser points and ACI
def _updateACIPlot(self, x, y):
    self._view.workspace.SelectedAciIndex = []
    _laserSelectionAci(self, x, y)
    #_addACIImage(self)


def _laserSelectionAci(self, pix_x, pix_y):
    # find closest spectrum to position, display it in lower plot
    _laserShots = [(self._view.workspace.xPix[i], self._view.workspace.yPix[i]) for i in range(self._view.workspace.nSpectra)]
    _dist, _closestIndex = spatial.KDTree(_laserShots).query([pix_x, pix_y])

    self._view.workspace.SelectedAciIndex = [_closestIndex]
    self._view.selectionScrollbarMain.setValue(_closestIndex)
    #_addSelectionPlotMain(self)

def _roiSelectionAci(self, pix_x, pix_y):
    # find closest spectrum to position, display it in lower plot
    _laserShots = [(self._view.workspace.xPix[i], self._view.workspace.yPix[i]) for i in range(self._view.workspace.nSpectra)]
    _dist, _closestIndex = spatial.KDTree(_laserShots).query([pix_x, pix_y])
    # when a point is clicked
    # if it is not in the tempRoi list, add it
    if _closestIndex not in self._view.tempRoi:
        self._view.tempRoi.append(_closestIndex)
    # if it is in the tempRoi list, remove it
    else:
        self._view.tempRoi.remove(_closestIndex)

    self._view.workspace.SelectedAciIndex = [_closestIndex]
    self._view.selectionScrollbarMain.setValue(_closestIndex)
    self._view.imageACI.mouseDoubleClickEvent = self._clickAddRoiPointMain

def _roiSelectionAciRemove(self, pix_x, pix_y):
    # find closest spectrum to position, display it in lower plot
    _laserShots = [(self._view.workspace.xPix[i], self._view.workspace.yPix[i]) for i in range(self._view.workspace.nSpectra)]
    _dist, _closestIndex = spatial.KDTree(_laserShots).query([pix_x, pix_y])
    # when a point is clicked
    # if it is in the tempRoi list, remove it
    if _closestIndex in self._view.tempRoi:
        self._view.tempRoi.remove(_closestIndex)

    self._view.workspace.SelectedAciIndex = [_closestIndex]
    self._view.selectionScrollbarMain.setValue(_closestIndex)
    self._view.imageACI.mouseDoubleClickEvent = self._clickDelRoiPointMain



def _updateLaserSelectionLineEdit(self):
    self._view.workspace.SelectedAciIndex = [self._view.selectionScrollbarMain.value()]
    self._view.selectionScrollbarEdit.setText(str(self._view.workspace.SelectedAciIndex[0]))
    _updateAzElOffset(self)
    if len(self._view.workspace.selectedROI) ==0 or (len(self._view.workspace.selectedROI) > 0 and self._view.workspace.selectedROI[0].split('_')[-1] == 'Full Map'):
        _addACIImage(self)
    else:
        _addACIMultiRoiImage(self)
    _addSelectionPlotMain(self)


def _updateLaserSelectionScrollbar(self):
    self._view.workspace.SelectedAciIndex = [int(self._view.selectionScrollbarEdit.text())]
    self._view.selectionScrollbarMain.setValue(self._view.workspace.SelectedAciIndex[0])

def _updateSelectionPlotMain(self):
    #_clearSparPlotMain(self)
    _addSelectionPlotMain(self)

# TODO: update workspace scheme and loupe.csv to include az/el origin values? No - for off-home scans, still want to use typical az/el origin? (origin just describes origin to assign az/el values relative to table values)
def _updateAzElOffset(self):
    _azOrigin = 32767
    _elOrigin = 32767
    _fmScannerScaleFactor = -0.699438202247191
    _az = self._view.workspace.az[self._view.workspace.SelectedAciIndex[0]]
    _el = self._view.workspace.el[self._view.workspace.SelectedAciIndex[0]]
    self._view.selectionOffsetAzEdit.setText(str(int(_az / _fmScannerScaleFactor + _azOrigin)))
    self._view.selectionOffsetElEdit.setText(str(int(_el / _fmScannerScaleFactor + _elOrigin)))

def _addSelectionPlotMain(self):
    if len(self._view.workspace.SelectedAciIndex) > 0:
        _i = self._view.workspace.SelectedAciIndex[0]
        _x = self._view.workspace.wavelength
        _y = []
        _color = []
        if self._view.R1ItemMain.isChecked():
            if self._view.activeItemMain.isChecked():
                _y.append(self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].loc[_i].values)
            elif self._view.darkItemMain.isChecked():
                _y.append(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].loc[_i].values)
            else:
                _y.append(self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].loc[_i].values)
            _color.append(self._view.workspace.colorR1)
        if self._view.R2ItemMain.isChecked():
            if self._view.activeItemMain.isChecked():
                _y.append(self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].loc[_i].values)
            elif self._view.darkItemMain.isChecked():
                _y.append(self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].loc[_i].values)
            else:
                _y.append(self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].loc[_i].values)
            _color.append(self._view.workspace.colorR2)
        if self._view.R3ItemMain.isChecked():
            if self._view.activeItemMain.isChecked():
                _y.append(self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].loc[_i].values)
            elif self._view.darkItemMain.isChecked():
                _y.append(self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].loc[_i].values)
            else:
                _y.append(self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].loc[_i].values)
            _color.append(self._view.workspace.colorR3)
        if self._view.allItemMain.isChecked():
            if self._view.activeItemMain.isChecked():
                _y.append(self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].loc[_i].values + self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].loc[_i].values + self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].loc[_i].values)
            elif self._view.darkItemMain.isChecked():
                _y.append(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].loc[_i].values + self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].loc[_i].values + self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].loc[_i].values)
            else:
                _y.append(self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].loc[_i].values + self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].loc[_i].values + self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].loc[_i].values)
            _color.append(self._view.workspace.colorComposite)

        # determine if the user zoomed in on the plot
        if len(self._view.axMainPlot2) > 0 and ((self._view._xRangeSPAR is not None and self._view.axMainPlot2[0].axes.get_xbound() != self._view._xRangeSPAR) or (self._view._yRangeSPAR is not None and self._view.axMainPlot2[0].axes.get_ybound() != self._view._yRangeSPAR)):
            print('updating axis background')
            self._view._xRangeSPAR = self._view.axMainPlot2[0].axes.get_xbound()
            self._view._yRangeSPAR = self._view.axMainPlot2[0].axes.get_ybound()
            _clearSparPlotMain(self)
            for _yi, _ci in zip(_y, _color):
                _ax = generate_plots.plotMainSingleTrace(self._view, _x, _yi, _ci, alpha=0.0, label=str(_i), x_range = self._view._xRangeSPAR, y_range = self._view._yRangeSPAR)
                self._view.axMainPlot2.append(_ax)
            if self._view.axTopSparMain is None or self._view.axTopSparMain.xaxis.label._text == '':
                _plotSparFormat(self, x_range = self._view._xRangeSPAR, y_range = self._view._yRangeSPAR)
            self._view.traceCanvasMainPlot2.draw()
            self._view._axBackgroundSPAR = self._view.traceCanvasMainPlot2.fig.canvas.copy_from_bbox(_ax.axes.bbox)

        elif len(self._view.axMainPlot2) == 0 or self._view._axBackgroundSPAR is None or len(_color) != len(self._view.axMainPlot2):
            print('updating axis background')
            _clearSparPlotMain(self)
            for _yi, _ci in zip(_y, _color):
                _ax = generate_plots.plotMainSingleTrace(self._view, _x, _yi, _ci, alpha=0.0, label=str(_i))
                self._view.axMainPlot2.append(_ax)
            if self._view.axTopSparMain is None or self._view.axTopSparMain.xaxis.label._text == '':
                _plotSparFormat(self)
            self._view.traceCanvasMainPlot2.axes.relim()
            _rescaleYMain2(self)
            self._view.traceCanvasMainPlot2.draw()
            self._view._axBackgroundSPAR = self._view.traceCanvasMainPlot2.fig.canvas.copy_from_bbox(_ax.axes.bbox)
            self._view._xRangeSPAR = self._view.axMainPlot2[-1].axes.get_xbound()
            self._view._yRangeSPAR = self._view.axMainPlot2[-1].axes.get_ybound()
            #_ax.set_alpha(0.9)
            #_updateLaserSelectionLineEdit(self)
        # this is not needed?
        elif False and self._view.axMainPlot2[-1].axes.get_ybound() != self._view._yRangeSPAR and self._view.axMainPlot2[-1].axes.get_xbound() != self._view._xRangeSPAR:
            print('updating axis background (after zoom)')
            self._view._yRangeSPAR = self._view.axMainPlot2[-1].axes.get_ybound()
            self._view._xRangeSPAR = self._view.axMainPlot2[-1].axes.get_xbound()
            _xx = self._view.axMainPlot2[-1]._x
            _yy = self._view.axMainPlot2[-1]._y
            for _ax in self._view.axMainPlot2:
                _ax.remove()
                try:
                    self._view.traceCanvasMainPlot2.axes._remove_legend(self._view.traceCanvasMainPlot2.axes.get_legend())
                except:
                    pass
            self._view.axMainPlot2 = []
            _ax = generate_plots.plotMainSingleTrace(self._view, _xx, _yy, 'w', alpha=0.0, x_range=self._view._xRangeSPAR, y_range=self._view._yRangeSPAR)
            self._view.traceCanvasMainPlot2.draw_idle()
            self._view.axMainPlot2.append(_ax)
            self._view._axBackgroundSPAR = self._view.traceCanvasMainPlot2.fig.canvas.copy_from_bbox(_ax.axes.bbox)

        # restore background
        self._view.traceCanvasMainPlot2.fig.canvas.restore_region(self._view._axBackgroundSPAR)
        # define the new data
        for _yi, _ci in zip(_y, _color):
            _ax_list = [self._view.axMainPlot2[i] for i in range(len(self._view.axMainPlot2)) if self._view.axMainPlot2[i].get_color() == _ci]
            if len(_ax_list) > 0:
                _ax = _ax_list[0]
                _ax.set_alpha(0.9)
                _ax.set_color(_ci)
                _ax.set_data(_x, _yi)
                # redraw just the points
                _ax.axes.draw_artist(_ax)
                # fill in the axis
                self._view.traceCanvasMainPlot2.fig.canvas.blit(_ax.axes.bbox)
            else:
                print()
        #self._view.traceCanvasMainPlot2.draw_idle()
        self._view.traceCanvasMainPlot2.flush_events()
        #self._view.toolbarMainPlot2.update()





# ROI functions
def _roiBoxSelection(self):
    if self._view.ROIPolySelectButton.isChecked():
        log_parsing.log_info(self._view, 'Define a polygon around desired ROI points')
        # allow user to draw box in ACI image
        _hex = self._view.tempRoiColor[1:]
        _rgbColor = tuple(int(_hex[i:i+2], 16) for i in (0, 2, 4))
        _polygonRoiItem = poly_ROI.PolygonAnnotation(_rgbColor)
        self._view.imageACI._scene.addItem(_polygonRoiItem)
        self._view._sceneRoiItems = [_polygonRoiItem]
        r = 100
        sides = 8

        for i in range(sides):
            angle = 2 * math.pi * i / sides
            x = r * math.cos(angle)
            y = r * math.sin(angle)
            p = QPointF(x, y) + QPointF(200, 200)
            _item = _polygonRoiItem.addPoint(p)
            self._view._sceneRoiItems.append(_item)

        self._view.ROIPolySelectButton.setText('Finished Selection')
        self._view.ROIAddPointButton.setEnabled(False)
        self._view.ROIDelPointButton.setEnabled(False)
        self._view.ROIClearPointButton.setEnabled(False)
        self._view.ROIColorButton.setEnabled(False)
        self._view.ROISaveButton.setEnabled(False)
        self._view.ROIEditButton.setEnabled(False)
        self._view.ROIDeleteButton.setEnabled(False)
        self._view.ROIExportButton.setEnabled(False)

    else:
        # get points contained within polygon
        _laserShots = [(self._view.workspace.xPix[i], self._view.workspace.yPix[i]) for i in range(self._view.workspace.nSpectra)]

        # moving the whole poly does not update the point positions using the below line
        #_polygonPoints = [(self._view._sceneRoiItems[0].m_points[i].x(), self._view._sceneRoiItems[0].m_points[i].y()) for i in range(len(self._view._sceneRoiItems[0].m_points))]
        _polygonPoints = [(self._view._sceneRoiItems[0].m_items[i].x(), self._view._sceneRoiItems[0].m_items[i].y()) for i in range(len(self._view._sceneRoiItems[0].m_points))]
        _polygon = sg.polygon.Polygon(_polygonPoints)
        _points = [sg.Point(_shot) for _shot in _laserShots]
        _inPoly = [_polygon.contains(_p) for _p in _points]
        # add points to temp ROI (add to ROI in workspace once saved)
        if any(_inPoly):
            _selectedShots = [i for i in range(len(_laserShots)) if _inPoly[i]]
            for _s in _selectedShots:
                if _s not in self._view.tempRoi:
                    self._view.tempRoi.append(_s)

        for _item in self._view._sceneRoiItems:
            self._view.imageACI._scene.removeItem(_item)

        # highlight selected points
        _addACIImage(self)

        log_parsing.log_info(self._view, 'Finished selecting ROI points via polygon')
        self._view.ROIPolySelectButton.setText('Polynomial Selection')
        self._view.ROIAddPointButton.setEnabled(True)
        self._view.ROIColorButton.setEnabled(True)
        if len(self._view.tempRoi) > 0:
            self._view.ROIDelPointButton.setEnabled(True)
            self._view.ROIClearPointButton.setEnabled(True)
            self._view.ROISaveButton.setEnabled(True)
        if self._view.selectedROICombo.count() > 0:
            self._view.ROIEditButton.setEnabled(True)
            self._view.ROIDeleteButton.setEnabled(True)
        else:
            self._view.ROIEditButton.setEnabled(False)
            self._view.ROIDeleteButton.setEnabled(False)
        self._view.ROIExportButton.setEnabled(True)

def _roiAddSelection(self):
    if self._view.ROIAddPointButton.isChecked():
        log_parsing.log_info(self._view, 'Selecting ROI points (double-click)')
        self._view.imageACI.mouseDoubleClickEvent = self._clickAddRoiPointMain

        self._view.ROIPolySelectButton.setEnabled(False)
        self._view.ROIAddPointButton.setText('Finished Adding Point(s)')
        self._view.ROIDelPointButton.setEnabled(False)
        self._view.ROIClearPointButton.setEnabled(False)
        self._view.ROISaveButton.setEnabled(False)
        self._view.ROIColorButton.setEnabled(False)
        self._view.ROIEditButton.setEnabled(False)
        self._view.ROIDeleteButton.setEnabled(False)
        self._view.ROIExportButton.setEnabled(False)

    else:
        log_parsing.log_info(self._view, 'Finished selecting ROI points')
        self._view.imageACI.mouseDoubleClickEvent = self._getAciPos
        self._view.ROIPolySelectButton.setEnabled(True)
        self._view.ROIAddPointButton.setText('Add Point(s)')
        self._view.ROIColorButton.setEnabled(True)
        if len(self._view.tempRoi) > 0:
            self._view.ROIDelPointButton.setEnabled(True)
            self._view.ROIClearPointButton.setEnabled(True)
            self._view.ROISaveButton.setEnabled(True)
        if self._view.selectedROICombo.count() > 0:
            self._view.ROIEditButton.setEnabled(True)
            self._view.ROIDeleteButton.setEnabled(True)
        else:
            self._view.ROIEditButton.setEnabled(False)
            self._view.ROIDeleteButton.setEnabled(False)
        self._view.ROIExportButton.setEnabled(True)

def _roiDelSelection(self):
    if self._view.ROIDelPointButton.isChecked():
        log_parsing.log_info(self._view, 'Removing ROI points (double-click)')
        self._view.imageACI.mouseDoubleClickEvent = self._clickDelRoiPointMain

        self._view.ROIPolySelectButton.setEnabled(False)
        self._view.ROIAddPointButton.setEnabled(False)
        self._view.ROIDelPointButton.setText('Finished Deleting Point(s)')
        self._view.ROIClearPointButton.setEnabled(False)
        self._view.ROISaveButton.setEnabled(False)
        self._view.ROIColorButton.setEnabled(False)
        self._view.ROIEditButton.setEnabled(False)
        self._view.ROIDeleteButton.setEnabled(False)
        self._view.ROIExportButton.setEnabled(False)

    else:
        log_parsing.log_info(self._view, 'Finished removing ROI points')
        self._view.imageACI.mouseDoubleClickEvent = self._getAciPos

        self._view.ROIPolySelectButton.setEnabled(True)
        self._view.ROIAddPointButton.setEnabled(True)
        self._view.ROIDelPointButton.setText('Delete Point(s)')
        if len(self._view.tempRoi) > 0:
            self._view.ROIClearPointButton.setEnabled(True)
            self._view.ROISaveButton.setEnabled(True)
            self._view.ROIColorButton.setEnabled(True)
        else:
            self._view.ROIDelPointButton.setEnabled(False)
        if self._view.selectedROICombo.count() > 0:
            self._view.ROIEditButton.setEnabled(True)
            self._view.ROIDeleteButton.setEnabled(True)
        else:
            self._view.ROIEditButton.setEnabled(False)
            self._view.ROIDeleteButton.setEnabled(False)
        self._view.ROIExportButton.setEnabled(True)

def _roiClear(self):
    self._view.tempRoi = []
    _addACIImage(self)

    self._view.ROIPolySelectButton.setEnabled(True)
    self._view.ROIAddPointButton.setEnabled(True)
    self._view.ROIDelPointButton.setEnabled(False)
    self._view.ROIClearPointButton.setEnabled(False)
    self._view.ROISaveButton.setEnabled(False)
    self._view.ROIColorButton.setEnabled(True)
    if self._view.selectedROICombo.count() > 0:
        self._view.ROIEditButton.setEnabled(True)
        self._view.ROIDeleteButton.setEnabled(True)
    else:
        self._view.ROIEditButton.setEnabled(False)
        self._view.ROIDeleteButton.setEnabled(False)
    self._view.ROIExportButton.setEnabled(True)

# generates an instance of the ROI class and adds it to the dictionary
def _roiSave(self):
    if len(self._view.tempRoi) == 0:
        log_parsing.log_warning(self._view, 'No points to save.')
        self._view.ROIPolySelectButton.setEnabled(True)
        self._view.ROIAddPointButton.setEnabled(True)
        self._view.ROIDelPointButton.setEnabled(False)
        self._view.ROIClearPointButton.setEnabled(False)
        self._view.ROISaveButton.setEnabled(False)
        self._view.ROIColorButton.setEnabled(True)

    else:
        _roiName = self._view.humanReadableRoi.text()
        if _roiName == '':
            _roiName = 'ROI'
        if _roiName in self._view.workspace.roiHumanToDictKey.keys():
            #_roiName = _roiName+'_'+str(len(self._view.roiDict.keys()))
            log_parsing.log_warning(self._view, 'Overwriting ROI: {0}'.format(_roiName))
        _roi = roi_class.roiClass()
        _roi.defineSelectedRoi(_roiName, self._view.workspace, self._view.tempRoi, self._view.tempRoiColor)
        self._view.roiDict[_roi.dictName] = _roi
        if _roiName not in self._view.workspace.roiNames:
            self._view.workspace.roiNames.append(_roiName)
            self._view.workspace.roiHumanToDictKey[_roiName] = _roi.dictName
        self._view.roiDict[_roi.dictName].color = self._view.tempRoiColor
        # regenerate roi.csv with all ROIs
        _roi_file = os.path.join(self._view.workspace.workingDir, 'roi.csv')
        file_IO.writeRoiCsv(_roi_file, self._view)
        # add ROI to dropdown, checkbox, and workspace
        file_IO.parse_roi_csv(self._view)
        _populateRoiCheckGroup(self)
        # remove highlighted points
        self._view.tempRoi = []
        self._view.tempRoiColor = '#00f2ff'
        _addACIImage(self)
        self._view.ROIPolySelectButton.setEnabled(True)
        self._view.ROIAddPointButton.setEnabled(True)
        self._view.ROIDelPointButton.setEnabled(True)
        self._view.ROIClearPointButton.setEnabled(True)
        self._view.ROISaveButton.setEnabled(True)
        self._view.ROIColorButton.setEnabled(True)

    if self._view.selectedROICombo.count() > 0:
        self._view.ROIEditButton.setEnabled(True)
        self._view.ROIDeleteButton.setEnabled(True)
    else:
        self._view.ROIEditButton.setEnabled(False)
        self._view.ROIDeleteButton.setEnabled(False)
    self._view.ROIExportButton.setEnabled(True)


def _roiColorSelect(self):
    # color picker
    _Qcolor = QColorDialog.getColor()
    _rgba = _Qcolor.getRgb()
    _colorHex = '#{0:02x}{1:02x}{2:02x}'.format(_rgba[0], _rgba[1], _rgba[2])
    self._view.tempRoiColor = _colorHex
    self._view.ROIColorBox.setStyleSheet("QCheckBox::indicator{background-color : "+_colorHex+";}")
    _addACIImage(self)


# set points in temporary index list
# highlight points currently selected
def _roiEdit(self):
    _roiName = self._view.selectedROICombo.currentText()
    _roiDictName = self._view.workspace.roiHumanToDictKey[_roiName]
    _roi = self._view.roiDict[_roiDictName]
    self._view.tempRoi = _roi.specIndexList
    self._view.tempRoiColor = _roi.color
    self._view.ROIColorBox.setStyleSheet("QCheckBox::indicator{background-color : "+_roi.color+";}")
    # highlight selected points
    _addACIImage(self)
    self._view.humanReadableRoi.setText(_roiName)
    log_parsing.log_info(self._view, 'Added ROI: {0} points for editing'.format(_roiName))
    self._view.tempRoiColor = _roi.color
    self._view.ROIPolySelectButton.setEnabled(True)
    self._view.ROIAddPointButton.setEnabled(True)
    self._view.ROIDelPointButton.setEnabled(True)
    self._view.ROIClearPointButton.setEnabled(True)
    self._view.ROISaveButton.setEnabled(True)
    self._view.ROIColorButton.setEnabled(True)
    self._view.ROIEditButton.setEnabled(True)
    self._view.ROIDeleteButton.setEnabled(True)
    self._view.ROIExportButton.setEnabled(True)


def _roiDelete(self):
    _roiName = self._view.deleteROICombo.currentText()
    _roiNameFull = self._view.workspace.dictName+'_'+_roiName
    log_parsing.log_warning(self._view, 'Deleting ROI: {0}'.format(_roiName))
    del self._view.roiDict[_roiNameFull]
    self._view.workspace.roiNames.remove(_roiName)
    del self._view.workspace.roiHumanToDictKey[_roiName]

    # regenerate roi.csv with all ROIs
    _roi_file = os.path.join(self._view.workspace.workingDir, 'roi.csv')
    file_IO.writeRoiCsv(_roi_file, self._view)
    # add ROI to dropdown, checkbox, and workspace
    file_IO.parse_roi_csv(self._view)
    _populateRoiCheckGroup(self)
    # remove highlighted points
    self._view.tempRoi = []
    self._view.tempRoiColor = '#00f2ff'
    _addACIImage(self)
    self._view.ROIPolySelectButton.setEnabled(True)
    self._view.ROIAddPointButton.setEnabled(True)
    self._view.ROIDelPointButton.setEnabled(False)
    self._view.ROIClearPointButton.setEnabled(False)
    self._view.ROISaveButton.setEnabled(False)
    self._view.ROIColorButton.setEnabled(True)
    if self._view.selectedROICombo.count() > 0:
        self._view.ROIEditButton.setEnabled(True)
        self._view.ROIDeleteButton.setEnabled(True)
    else:
        self._view.ROIEditButton.setEnabled(False)
        self._view.ROIDeleteButton.setEnabled(False)
    self._view.ROIExportButton.setEnabled(True)

def _roiExport(self):
    _roiName = self._view.exportROICombo.currentText()
    _roiNameFull = self._view.workspace.dictName+'_'+_roiName
    _roiDictName = self._view.workspace.roiHumanToDictKey[_roiName]
    _roi = self._view.roiDict[_roiDictName]

    log_parsing.log_info(self._view, 'Exporting ROI: {0}'.format(_roiName))
    _tempSelectedIndex = self._view.workspace.SelectedAciIndex
    self._view.workspace.SelectedAciIndex = []

    if _roiName != 'Full Map':
        _tempSelected = self._view.workspace.selectedROI
        self._view.workspace.selectedROI = [_roiNameFull]
        _tempRoi = self._view.tempRoi
        self._view.tempRoi = _roi.specIndexList
        self._view.tempRoiColor = _roi.color
        _roiColor = self._view.tempRoiColor
        self._view.ROIColorBox.setStyleSheet("QCheckBox::indicator{background-color : "+_roi.color+";}")
        # highlight selected points
        self._view.pixmapACI = QPixmap(self._view.workspace.selectedACIFilename)
        _addLaserShots(self)
        self._view.imageACI.setPhoto(pixmap = self._view.pixmapACI, zoomSelect = self._view.imageACI._zoom)
    else:
        _tempSelected = self._view.workspace.selectedROI
        self._view.workspace.selectedROI = []
        # highlight selected points
        self._view.pixmapACI = QPixmap(self._view.workspace.selectedACIFilename)
        _addLaserShots(self)
        self._view.imageACI.setPhoto(pixmap = self._view.pixmapACI, zoomSelect = self._view.imageACI._zoom)

    file_IO.exportRoiBundle(_roiName, _roi.specIndexList, self._view)

    if _roiName != 'Full Map':
        self._view.tempRoi = _tempRoi
        self._view.workspace.selectedROI =_tempSelected
        self._view.tempRoiColor = _roiColor
        self._view.ROIColorBox.setStyleSheet("QCheckBox::indicator{background-color : "+_roi.color+";}")
    else:
        self._view.workspace.selectedROI =_tempSelected
    self._view.workspace.SelectedAciIndex = _tempSelectedIndex
    _addACIImage(self)



def _updateSpecProcessing(self):
    # update checkboxes on main tab
    if self._view.workspace.specProcessingApplied != 'None':
        if 'N' in self._view.workspace.specProcessingApplied:
            self._view.LaserNormalizationItemMain.setEnabled(True)
        if 'C' in self._view.workspace.specProcessingApplied:
            self._view.CosmicRayRemovalProcessingItemMain.setEnabled(True)
        if 'B' in self._view.workspace.specProcessingApplied:
            self._view.BaselineSubtractionItemMain.setEnabled(True)

    if self._view.workspace.specProcessingApplied == 'None':
        self._view.CosmicRayRemovalProcessingItemMain.setEnabled(False)
        self._view.CosmicRayRemovalProcessingItemMain.setChecked(False)
        self._view.BaselineSubtractionItemMain.setEnabled(False)
        self._view.BaselineSubtractionItemMain.setChecked(False)
        self._view.LaserNormalizationItemMain.setEnabled(False)
        self._view.LaserNormalizationItemMain.setChecked(False)

    elif len(self._view.workspace.specProcessingApplied) == 1:
        if self._view.workspace.specProcessingApplied == 'N':
            self._view.CosmicRayRemovalProcessingItemMain.setEnabled(False)
            self._view.CosmicRayRemovalProcessingItemMain.setChecked(False)
            self._view.BaselineSubtractionItemMain.setEnabled(False)
            self._view.BaselineSubtractionItemMain.setChecked(False)
        elif self._view.workspace.specProcessingApplied == 'C':
            self._view.LaserNormalizationItemMain.setEnabled(False)
            self._view.LaserNormalizationItemMain.setChecked(False)
            self._view.BaselineSubtractionItemMain.setEnabled(False)
            self._view.BaselineSubtractionItemMain.setChecked(False)
        else:
            self._view.CosmicRayRemovalProcessingItemMain.setEnabled(False)
            self._view.CosmicRayRemovalProcessingItemMain.setChecked(False)
            self._view.LaserNormalizationItemMain.setEnabled(False)
            self._view.LaserNormalizationItemMain.setChecked(False)

    elif len(self._view.workspace.specProcessingApplied) == 2:
        if 'N' not in self._view.workspace.specProcessingApplied:
            self._view.BaselineSubtractionItemMain.setEnabled(True)
            self._view.CosmicRayRemovalProcessingItemMain.setEnabled(True)
            self._view.LaserNormalizationItemMain.setEnabled(False)
            self._view.LaserNormalizationItemMain.setChecked(False)
        elif 'B' not in self._view.workspace.specProcessingApplied:
            self._view.CosmicRayRemovalProcessingItemMain.setEnabled(True)
            self._view.LaserNormalizationItemMain.setEnabled(True)
            self._view.BaselineSubtractionItemMain.setEnabled(False)
            self._view.BaselineSubtractionItemMain.setChecked(False)
        elif 'C' not in self._view.workspace.specProcessingApplied:
            self._view.BaselineSubtractionItemMain.setEnabled(True)
            self._view.LaserNormalizationItemMain.setEnabled(True)
            self._view.CosmicRayRemovalProcessingItemMain.setEnabled(False)
            self._view.CosmicRayRemovalProcessingItemMain.setChecked(False)
        if self._view.workspace.specProcessingApplied[1] == 'N' and self._view.LaserNormalizationItemMain.isChecked():
            if self._view.workspace.specProcessingApplied[0] == 'B' and self._view.workspace.darkSubSpectraR1['BN'] is not None:
                self._view.BaselineSubtractionItemMain.setChecked(True)
            elif self._view.workspace.specProcessingApplied[0] == 'C' and self._view.workspace.darkSubSpectraR1['CN'] is not None:
                self._view.CosmicRayRemovalProcessingItemMain.setChecked(True)
        elif self._view.workspace.specProcessingApplied[1] == 'B' and self._view.BaselineSubtractionItemMain.isChecked():
            if self._view.workspace.specProcessingApplied[0] == 'N' and self._view.workspace.darkSubSpectraR1['NB'] is not None:
                self._view.LaserNormalizationItemMain.setChecked(True)
            elif self._view.workspace.specProcessingApplied[0] == 'C' and self._view.workspace.darkSubSpectraR1['CB'] is not None:
                self._view.CosmicRayRemovalProcessingItemMain.setChecked(True)
        elif self._view.workspace.specProcessingApplied[1] == 'C' and self._view.CosmicRayRemovalProcessingItemMain.isChecked():
            if self._view.workspace.specProcessingApplied[0] == 'N' and self._view.workspace.darkSubSpectraR1['NC'] is not None:
                self._view.LaserNormalizationItemMain.setChecked(True)
            elif self._view.workspace.specProcessingApplied[0] == 'B' and self._view.workspace.darkSubSpectraR1['BC'] is not None:
                self._view.BaselineSubtractionItemMain.setChecked(True)

    # TODO: check this when baseline removal is available
    elif len(self._view.workspace.specProcessingApplied) == 3:
        self._view.CosmicRayRemovalProcessingItemMain.setEnabled(False)
        self._view.BaselineSubtractionItemMain.setEnabled(False)
        self._view.LaserNormalizationItemMain.setEnabled(False)
        if self._view.workspace.specProcessingApplied[2] == 'N' and self._view.LaserNormalizationItemMain.isChecked():
            self._view.BaselineSubtractionItemMain.setChecked(True)
            self._view.CosmicRayRemovalProcessingItemMain.setChecked(True)
        elif self._view.workspace.specProcessingApplied[2] == 'N' and not self._view.LaserNormalizationItemMain.isChecked():
            if self._view.workspace.specProcessingApplied[1] == 'B' and self._view.BaselineSubtractionItemMain.isChecked():
                self._view.CosmicRayRemovalProcessingItemMain.setChecked(True)
            elif self._view.workspace.specProcessingApplied[1] == 'C' and self._view.CosmicRayRemovalProcessingItemMain.isChecked():
                self._view.BaselineSubtractionItemMain.setChecked(True)
        elif self._view.workspace.specProcessingApplied[2] == 'B' and self._view.BaselineSubtractionItemMain.isChecked():
            self._view.LaserNormalizationItemMain.setChecked(True)
            self._view.CosmicRayRemovalProcessingItemMain.setChecked(True)
        elif self._view.workspace.specProcessingApplied[2] == 'B' and not self._view.BaselineSubtractionItemMain.isChecked():
            if self._view.workspace.specProcessingApplied[1] == 'N' and self._view.LaserNormalizationItemMain.isChecked():
                self._view.CosmicRayRemovalProcessingItemMain.setChecked(True)
            elif self._view.workspace.specProcessingApplied[1] == 'C' and self._view.CosmicRayRemovalProcessingItemMain.isChecked():
                self._view.LaserNormalizationItemMain.setChecked(True)
        elif self._view.workspace.specProcessingApplied[2] == 'C' and self._view.CosmicRayRemovalProcessingItemMain.isChecked():
            self._view.LaserNormalizationItemMain.setChecked(True)
            self._view.BaselineSubtractionItemMain.setChecked(True)
        elif self._view.workspace.specProcessingApplied[2] == 'C' and not self._view.CosmicRayRemovalProcessingItemMain.isChecked():
            if self._view.workspace.specProcessingApplied[1] == 'N' and self._view.LaserNormalizationItemMain.isChecked():
                self._view.BaselineSubtractionItemMain.setChecked(True)
            elif self._view.workspace.specProcessingApplied[1] == 'B' and self._view.BaselineSubtractionItemMain.isChecked():
                self._view.CosmicRayRemovalProcessingItemMain.setChecked(True)

    if not self._view.CosmicRayRemovalProcessingItemMain.isChecked() and not self._view.BaselineSubtractionItemMain.isChecked():
        self._view.activeItemMain.setEnabled(True)
        self._view.darkItemMain.setEnabled(True)
    else:
        self._view.activeItemMain.setEnabled(False)
        self._view.darkItemMain.setEnabled(False)

    self._view.specProcessingSelected = 'None'
    if self._view.workspace.specProcessingApplied != 'None':
        for _i in self._view.workspace.specProcessingApplied:
            if _i == 'N' and self._view.LaserNormalizationItemMain.isChecked():
                if self._view.specProcessingSelected == 'None':
                    self._view.specProcessingSelected = ''
                self._view.specProcessingSelected += 'N'
            elif _i == 'B' and self._view.BaselineSubtractionItemMain.isChecked():
                if self._view.specProcessingSelected == 'None':
                    self._view.specProcessingSelected = ''
                self._view.specProcessingSelected += 'B'
            elif _i == 'C' and self._view.CosmicRayRemovalProcessingItemMain.isChecked():
                if self._view.specProcessingSelected == 'None':
                    self._view.specProcessingSelected = ''
                self._view.specProcessingSelected += 'C'


# TODO: check this when baseline removal is available
def _updateProcessingFlagsMain(self):
    if len(self._view.workspace.specProcessingApplied) == 2:
        if self._view.LaserNormalizationItemMain.isChecked():
            if self._view.workspace.darkSubSpectraR1['BN'] is None and self._view.workspace.darkSubSpectraR1['NB'] is None:
                self._view.BaselineSubtractionItemMain.setEnabled(False)
            if self._view.workspace.darkSubSpectraR1['CN'] is None and self._view.workspace.darkSubSpectraR1['NC'] is None:
                self._view.CosmicRayRemovalProcessingItemMain.setEnabled(False)
        elif self._view.CosmicRayRemovalProcessingItemMain.isChecked():
            if self._view.workspace.darkSubSpectraR1['BC'] is None and self._view.workspace.darkSubSpectraR1['CB'] is None:
                self._view.BaselineSubtractionItemMain.setEnabled(False)
            if self._view.workspace.darkSubSpectraR1['CN'] is None and self._view.workspace.darkSubSpectraR1['NC'] is None:
                self._view.LaserNormalizationItemMain.setEnabled(False)
        elif self._view.BaselineSubtractionItemMain.isChecked():
            if self._view.workspace.darkSubSpectraR1['BC'] is None and self._view.workspace.darkSubSpectraR1['CB'] is None:
                self._view.CosmicRayRemovalProcessingItemMain.setEnabled(False)
            if self._view.workspace.darkSubSpectraR1['BN'] is None and self._view.workspace.darkSubSpectraR1['NB'] is None:
                self._view.LaserNormalizationItemMain.setEnabled(False)
