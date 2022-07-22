import os
import sys
import numpy as np
import functools
from scipy import spatial

from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QImage
from PyQt5.QtGui import QPainter
from PyQt5.QtGui import QTransform
from PyQt5.QtGui import QPen
from PyQt5.QtGui import QBrush
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QPoint
from PyQt5.QtCore import QRect
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QApplication

from matplotlib import pyplot as plt

from src import log_parsing
from src import generate_images
from src import generate_plots
from src import file_IO
from src.loupe_view import _tab_false_color
from src.loupe_control import _control_false_color



def _updateRGBLeftPanel(self):
    log_parsing.log_info(self._view, 'Updating false color map left panel')
    _populateWorkspaceName(self)
    _populateRoiCheckGroup(self)
    # enable button and groupboxes


def _updateRGBCentralPanel(self):
    log_parsing.log_info(self._view, 'Updating false color map plot panel')
    if self._view.workspace.selectedACIFilename is not None:
        _displayRGBACI(self)
    _roiSelectMapUpdate(self)
    _calculateSpec(self)

def _populateWorkspaceName(self):
    self._view.workspaceLabelMap.setText('Workspace: {0}'.format(self._view.workspace.humanReadableName))


def _clearMap(self):
    log_parsing.log_info(self._view, 'Clearing false color map tab contents')
    _resetGroupboxEnable(self)

    for _roi_name in self._view.workspace.roiNames:
        _roi_dict_name = self._view.workspace.roiHumanToDictKey[_roi_name]
        if _roi_name == 'Full Map':
            self._view.roiDict[_roi_dict_name].checkboxWidgetRoi.setChecked(True)
        else:
            self._view.roiDict[_roi_dict_name].checkboxWidgetRoi.setChecked(False)

    for i in reversed(range(self._view.vboxRoiRGB.count())):
        self._view.vboxRoiRGB.itemAt(i).widget().setParent(None)
    self._view.groupboxROIRGB.resize(self._view.groupboxROIRGB.sizeHint())

    #self._view.tempRoiRGB = []

    # completely removing and re-adding the MPL canvas prevents plotting slow-downs from accumulating after many switches between workspaces
    self._view.LoupeViewRGBTabLayout.removeWidget(self._view.imageACIMap)
    self._view.imageACIMap.deleteLater()
    self._view.imageACIMap = None
    self._view.LoupeViewRGBTabLayout.removeWidget(self._view.toolbarMapPlot1)
    self._view.toolbarMapPlot1.deleteLater()
    self._view.toolbarMapPlot1 = None
    self._view.LoupeViewRGBTabLayout.removeWidget(self._view.traceCanvasMapPlot1)
    self._view.traceCanvasMapPlot1.deleteLater()
    self._view.traceCanvasMapPlot1 = None
    self._view.LoupeViewRGBTabLayout.removeWidget(self._view.toolbarMapPlot2)
    self._view.toolbarMapPlot2.deleteLater()
    self._view.toolbarMapPlot2 = None
    self._view.LoupeViewRGBTabLayout.removeWidget(self._view.traceCanvasMapPlot2)
    self._view.traceCanvasMapPlot2.deleteLater()
    self._view.traceCanvasMapPlot2 = None
    _tab_false_color._addFalseColorCenterPanel(self._view)

    self._view.toolbarResizeMap1.triggered.disconnect()
    self._view.toolbarResizeMap2.triggered.disconnect()
    self._view.toolbarResizeMap1.triggered.connect(functools.partial(_control_false_color._rescaleYMap1, self))
    self._view.toolbarResizeMap2.triggered.connect(functools.partial(_control_false_color._rescaleYMap2, self))

    self._view._axBackgroundRGB = None

    self._view.traceCanvasMapPlot1.axes[0].clear()
    self._view.traceCanvasMapPlot1.axes[0].tick_params(axis='x', colors='#FF3B3B')
    self._view.traceCanvasMapPlot1.axes[1].clear()
    self._view.traceCanvasMapPlot1.axes[1].tick_params(axis='x', colors='#01FF24')
    self._view.traceCanvasMapPlot1.axes[2].clear()
    self._view.traceCanvasMapPlot1.axes[2].tick_params(axis='x', colors='#3CD0FF')
    self._view.axMapPlot1 = []
    self._view.traceCanvasMapPlot1.draw_idle()
    self._view.traceCanvasMapPlot2.draw_idle()
    self._view.axTopMap = None
    self._view.axTopTopMap = None

    img1_dir = os.path.join(os.path.dirname(sys.modules[__name__].__file__), os.pardir, os.pardir, 'resources', 'ACI_placeholder.png')
    self._view.pixmapACIMap = QPixmap(img1_dir)
    self._view.imageACIMap.setPhoto(pixmap = self._view.pixmapACIMap, zoomSelect=None)

    self._view.specRGB = None
    self._view.imageArrayRGB = None
    self._view.redRGB = None
    self._view.greenRGB = None
    self._view.blueRGB = None
    self._view.interpolateRGB_r = None
    self._view.interpolateRGB_g = None
    self._view.interpolateRGB_b = None
    self._view.currentInterpol = None

    self._view.redHistHighRGB.setText('')
    self._view.redHistLowRGB.setText('')
    self._view.greenHistHighRGB.setText('')
    self._view.greenHistLowRGB.setText('')
    self._view.blueHistHighRGB.setText('')
    self._view.blueHistLowRGB.setText('')

    self._view.RGBExportButton.setEnabled(False)

    if self._view.workspace.xPix is not None:
        # reducing the size of this significantly speeds up processing. Aim for 150x150
        x_spacing = int(max(self._view.workspace.xPix))-int(min(self._view.workspace.xPix))
        y_spacing = int(max(self._view.workspace.yPix))-int(min(self._view.workspace.yPix))
        x_grid_spacing = round(x_spacing/100)
        y_grid_spacing = round(y_spacing/100)
        if x_grid_spacing < 1 or y_grid_spacing < 1:
            x_grid_spacing = 1
            y_grid_spacing = 1
        self._view.workspace.grid_x, self._view.workspace.grid_y = np.mgrid[int(min(self._view.workspace.xPix)):int(max(self._view.workspace.xPix)):x_grid_spacing, int(min(self._view.workspace.yPix)):int(max(self._view.workspace.yPix)):y_grid_spacing]
        self._view.workspace.coords = np.array([[self._view.workspace.xPix[i], self._view.workspace.yPix[i]] for i in range(len(self._view.workspace.xPix))])


def _resetGroupboxEnable(self):
    self._view.groupboxRegionsRGB.setEnabled(True)
    self._view.groupboxRegionsRGB.setEnabled(True)
    self._view.R1ItemRGB.setChecked(True)
    self._view.R2ItemRGB.setChecked(True)
    self._view.R3ItemRGB.setChecked(True)
    self._view.allItemRGB.setChecked(False)
    self._view.groupboxDisplayTypeRGB.setEnabled(True)
    self._view.meanDisplayRGB.setEnabled(True)
    self._view.medianDisplayRGB.setEnabled(True)
    self._view.indexDisplayRGB.setEnabled(True)
    self._view.indexSpecRGB.setEnabled(True)
    self._view.meanDisplayRGB.setChecked(True)
    self._view.groupboxRGBSelection.setEnabled(True)
    self._view.redCheckRGB.setChecked(False)
    self._view.greenCheckRGB.setChecked(False)
    self._view.blueCheckRGB.setChecked(False)

    self._view.groupboxImageRGB.setEnabled(True)
    self._view.groupboxImageModeRGB.setEnabled(True)
    self._view.groupboxImageInterpolationRGB.setEnabled(True)
    self._view.RGBInterpolatedNearest.setChecked(True)



def _roiSelectMapUpdate(self):
    # determine which ROI checkboxes are selected
    _roiSelected = []
    self._view.workspace.selectedROIRGB = []
    for _roiName in self._view.workspace.roiNames:
        _roiKey = self._view.workspace.roiHumanToDictKey[_roiName]
        if self._view.roiDict[_roiKey].checkboxWidgetRoi.isChecked():
            _roiSelected.append(_roiKey)
            self._view.workspace.selectedROIRGB.append(_roiKey)

    if len(_roiSelected) == 1 and _roiSelected[0].split('_')[-1] == 'Full Map':
        self._view.indexDisplayRGB.setEnabled(True)
        self._view.indexSpecRGB.setEnabled(True)
        _plotMapUpdate(self)
    elif len(_roiSelected) == 1:
        _plotMapUpdate(self)
    else:
        self._view.R1ItemRGB.setChecked(False)
        self._view.R2ItemRGB.setChecked(False)
        self._view.R3ItemRGB.setChecked(False)
        self._view.allItemRGB.setChecked(True)
        self._view.indexDisplayRGB.setEnabled(False)
        self._view.indexSpecRGB.setEnabled(False)
        if self._view.indexDisplayRGB.isChecked():
            self._view.meanDisplayRGB.setChecked(True)
        _plotMapUpdate(self)

# if this gets called anywhere else, remove the last conditional statement that sets the checkboxes and add them to a new function called when switching workspaces
def _populateRoiCheckGroup(self):
    # clear group box
    for _checkboxIndex in reversed(range(self._view.vboxRoiRGB.count())):
        self._view.vboxRoiRGB.itemAt(_checkboxIndex).widget().setParent(None)
    # add each roi checkbox widget to the groupbox
    for _roi_name in self._view.workspace.roiNames:
        _roi_dict_name = self._view.workspace.roiHumanToDictKey[_roi_name]
        # get ROI class
        #_roiDictName = self._view.workspace.roiHumanToDictKey[_roi_name]
        _checkboxRoi = self._view.roiDict[_roi_dict_name].checkboxWidgetRoi
        _checkboxRoi.clicked.connect(functools.partial(_roiSelectMapUpdate, self))
        self._view.vboxRoiRGB.addWidget(_checkboxRoi)
        if len(self._view.workspace.roiNames) < 2:
            _checkboxRoi.setDisabled(True)
        else:
            _checkboxRoi.setDisabled(False)
        if _roi_name == 'Full Map':
            self._view.roiDict[_roi_dict_name].checkboxWidgetRoi.setChecked(True)
        else:
            self._view.roiDict[_roi_dict_name].checkboxWidgetRoi.setChecked(False)


def _displayRGBACI(self):
    # check if image format is IMG or PNG
    if self._view.workspace.selectedACIFilename.endswith('IMG') or self._view.workspace.selectedACIFilename.endswith('PNG') or self._view.workspace.selectedACIFilename.endswith('png'):
        _addACIImageRGB(self)
        # fitinview will not set the zoom correctly unless the image is already loaded
        self._view.imageACIMap.fitInView()#self._view.imageACINorm._scene.sceneRect())
        if not self._view.mapTabOpened:
            self._view.imageACIMap.setTransform(QTransform.fromScale(5.70, 5.70), True)
        else:
            self._view.imageACIMap.setTransform(QTransform.fromScale(5.70, 5.70), True)
        QApplication.processEvents()

        # enable other buttons
        self._view.opacityMapRGB.setEnabled(True)
        self._view.opacityACIRGB.setEnabled(True)

    else:
        log_parsing.log_warning(self._view, 'Selected ACI file {0} does not have the expected PNG or IMG extension'.format(self._view.workspace.selectedACIFilename))


# intial display of laser points and ACI
def _updateACIMapPlot(self, x, y):
    self._view.workspace.SelectedAciIndexMap = []
    _laserSelectionAciMap(self, x, y)
    #_addACIImage(self)

def _laserSelectionAciMap(self, pix_x, pix_y):
    # find closest spectrum to position, display it in lower plot
    _laserShots = [(self._view.workspace.xPix[i], self._view.workspace.yPix[i]) for i in range(self._view.workspace.nSpectra)]
    _dist, _closestIndex = spatial.KDTree(_laserShots).query([pix_x, pix_y])

    self._view.workspace.SelectedAciIndexMap = [_closestIndex]
    # if mulltiple ROIs, disable ROIs, enable Full Map
    self._view.workspace.selectedROIRGB = []
    for _roiName in self._view.workspace.roiNames:
        _roiKey = self._view.workspace.roiHumanToDictKey[_roiName]
        if self._view.roiDict[_roiKey].checkboxWidgetRoi.isChecked() and _roiName != 'Full Map':
            self._view.roiDict[_roiKey].checkboxWidgetRoi.setChecked(False)
    self._view.indexDisplayRGB.setEnabled(True)
    self._view.indexSpecRGB.setEnabled(True)

    # add _closestIndex to spectrum index
    self._view.indexSpecRGB.setText(str(_closestIndex))
    # select spectrum index radio button
    self._view.indexDisplayRGB.setChecked(True)
    # trigger plot update
    _plotMapUpdate(self)


def _addACIImageRGB(self):
    self._view.pixmapACIMap = QPixmap(self._view.workspace.selectedACIFilename)

    if self._view.imageArrayRGB is not None:
        if self._view.RGBDiscrete.isChecked():
            _addDiscretePointsRGB(self)
        else:
            _addInterpolatedPointsRGB(self)

    self._view.imageACIMap.setPhoto(pixmap = self._view.pixmapACIMap, zoomSelect = self._view.imageACIMap._zoom)
    self._view.imageACIMap.mouseDoubleClickEvent = self._getAciMapPos
    self._view.RGBExportButton.setEnabled(True)

def _updateMapContrast(self, red=False, green=False, blue=False):
    if red:
        self._view.interpolateRGB_r = None
    if green:
        self._view.interpolateRGB_g = None
    if blue:
        self._view.interpolateRGB_b = None
    _addACIImageRGB(self)


# add point selection capability? (isolate view of a single spectrum)
def _addDiscretePointsRGB(self, pixMapSave = None, customOpacity = None):
    if self._view.imageArrayRGB is not None:
        if pixMapSave is not None:
            pixMap = pixMapSave
        else:
            pixMap = self._view.pixmapACIMap
        # check if full ROI is displayed:
        # commented out - display all points for now, regardless of ROI selected
        #if len(self._view.workspace.selectedROI) == 0 or self._view.workspace.selectedROI[0].split('_')[-1] == 'Full Map':
        self._view.OverlayMap = QPainter(pixMap)
        self._view.OverlayMap.setPen(QPen(Qt.black, 1, Qt.SolidLine))
        self._view.OverlayMap.setBrush(QBrush(Qt.black, Qt.SolidPattern))
        if customOpacity is not None:
            opacity = customOpacity
        else:
            opacity = self._view.opacityMapRGB.value()
        self._view.OverlayMap.setOpacity(1 - float(self._view.opacityACIRGB.value())/100.0)
        self._view.OverlayMap.drawRect(0, 0, pixMap.width(), pixMap.height())
        self._view.OverlayMap.end()

        # add points
        self._view.laserPainterInstanceMap = QPainter(pixMap)
        self._view.laserPainterInstanceMap.setOpacity(float(opacity)/100.0)
        clip_low_red, clip_high_red = _get_clip(self, red=True)
        clip_low_green, clip_high_green = _get_clip(self, green=True)
        clip_low_blue, clip_high_blue = _get_clip(self, blue=True)
        data_red = self._view.imageArrayRGB[0].copy()
        if len(self._view.imageArrayRGB[0]) > 0 and clip_low_red is not None and clip_high_red is not None:
            data_red = np.clip(self._view.imageArrayRGB[0], clip_low_red, clip_high_red)
        data_green = self._view.imageArrayRGB[1].copy()
        if len(self._view.imageArrayRGB[1]) > 0 and clip_low_green is not None and clip_high_green is not None:
            data_green = np.clip(self._view.imageArrayRGB[1], clip_low_green, clip_high_green)
        data_blue = self._view.imageArrayRGB[2].copy()
        if len(self._view.imageArrayRGB[2]) > 0 and clip_low_blue is not None and clip_high_blue is not None:
            data_blue = np.clip(self._view.imageArrayRGB[2], clip_low_blue, clip_high_blue)

        #_width = self._view.laserPainterInstanceMap.window().size().width()
        #_height = self._view.laserPainterInstanceMap.window().size().height()
        for i in range(len(self._view.workspace.xPix)):
            if len(self._view.imageArrayRGB[0]) > 0:
                if self._view.imageArrayRGB[0].min() == self._view.imageArrayRGB[0].max():
                    _r = 127
                else:
                    _r = int(255*(data_red[i]-data_red.min())/(data_red.max()-data_red.min()))
            else:
                _r = 0
            if len(self._view.imageArrayRGB[1]) > 0:
                if self._view.imageArrayRGB[1].min() == self._view.imageArrayRGB[1].max():
                    _g = 127
                else:
                    _g = int(255*(data_green[i]-data_green.min())/(data_green.max()-data_green.min()))
            else:
                _g = 0
            if len(self._view.imageArrayRGB[2]) > 0:
                if self._view.imageArrayRGB[2].min() == self._view.imageArrayRGB[2].max():
                    _b = 127
                else:
                    _b = int(255*(data_blue[i]-data_blue.min())/(data_blue.max()-data_blue.min()))
            else:
                _b = 0
            self._view.laserPainterInstanceMap.setPen(QPen(QColor(_r, _g, _b), 1, Qt.SolidLine))
            self._view.laserPainterInstanceMap.setBrush(QBrush(QColor(_r, _g, _b), Qt.SolidPattern))
            _x = self._view.workspace.xPix[i]
            _y = self._view.workspace.yPix[i]
            self._view.laserPainterInstanceMap.drawEllipse(QPoint(_x, _y), self._view.workspace.laserPix/2.0, self._view.workspace.laserPix/2.0)

        self._view.laserPainterInstanceMap.end()

def _get_clip(self, red=False, green = False, blue = False):
    if red:
        if self._view.redHistLowRGB.text() != '' or self._view.redHistHighRGB.text() != '':
            clip_low = self._view.redHistLowRGB.text()
            clip_high = self._view.redHistHighRGB.text()
            if clip_low == '':
                clip_low = self._view.imageArrayRGB[0].min()-1
            if clip_high == '':
                clip_high = self._view.imageArrayRGB[0].max()+1
        else:
            clip_low = None
            clip_high = None
    if green:
        if self._view.greenHistLowRGB.text() != '' or self._view.greenHistHighRGB.text() != '':
            clip_low = self._view.greenHistLowRGB.text()
            clip_high = self._view.greenHistHighRGB.text()
            if clip_low == '':
                clip_low = self._view.imageArrayRGB[1].min()-1
            if clip_high == '':
                clip_high = self._view.imageArrayRGB[1].max()+1
        else:
            clip_low = None
            clip_high = None

    if blue:
        if self._view.blueHistLowRGB.text() != '' or self._view.blueHistHighRGB.text() != '':
            clip_low = self._view.blueHistLowRGB.text()
            clip_high = self._view.blueHistHighRGB.text()
            if clip_low == '':
                clip_low = self._view.imageArrayRGB[2].min()-1
            if clip_high == '':
                clip_high = self._view.imageArrayRGB[2].max()+1
        else:
            clip_low = None
            clip_high = None

    if clip_low is not None:
        clip_low = float(clip_low)
    if clip_high is not None:
        clip_high = float(clip_high)

    return clip_low, clip_high

def _addInterpolatedPointsRGB(self, pixMapSave = None, customOpacity = None):
    if self._view.RGBInterpolatedNearest.isChecked():
        method = 'nearest'
        if self._view.currentInterpol != 'nearest':
            self._view.interpolateRGB_r = None
            self._view.interpolateRGB_g = None
            self._view.interpolateRGB_b = None
        self._view.currentInterpol = 'nearest'
    elif self._view.RGBInterpolatedCubic.isChecked():
        method = 'cubic'
        if self._view.currentInterpol != 'cubic':
            self._view.interpolateRGB_r = None
            self._view.interpolateRGB_g = None
            self._view.interpolateRGB_b = None
        self._view.currentInterpol = 'cubic'

    if pixMapSave is not None:
        pixMap = pixMapSave
    else:
        pixMap = self._view.pixmapACIMap
    if customOpacity is not None:
        opacity = customOpacity
    else:
        opacity = self._view.opacityMapRGB.value()


    # check if full ROI is displayed:
    #if len(self._view.workspace.selectedROI) == 0 or self._view.workspace.selectedROI[0].split('_')[-1] == 'Full Map':
    self._view.OverlayMap = QPainter(pixMap)
    self._view.OverlayMap.setPen(QPen(Qt.black, 1, Qt.SolidLine))
    self._view.OverlayMap.setBrush(QBrush(Qt.black, Qt.SolidPattern))
    self._view.OverlayMap.setOpacity(1 - float(self._view.opacityACIRGB.value())/100.0)
    self._view.OverlayMap.drawRect(0, 0, pixMap.width(), pixMap.height())
    self._view.OverlayMap.end()

    # generate interpolated RGB map
    if self._view.interpolateRGB_r is None:
        if len(self._view.imageArrayRGB[0]) > 0:
            clip_low, clip_high = _get_clip(self, red=True)
            self._view.interpolateRGB_r = generate_images.color_image_interpolate(self._view.workspace.grid_x, self._view.workspace.grid_y, self._view.workspace.coords, self._view.imageArrayRGB[0], method=method, clip_low=clip_low, clip_high = clip_high)
        else:
            if self._view.interpolateRGB_g is not None:
                self._view.interpolateRGB_r = np.zeros(self._view.interpolateRGB_g.shape).astype(np.int8)
            elif self._view.interpolateRGB_b is not None:
                self._view.interpolateRGB_r = np.zeros(self._view.interpolateRGB_b.shape).astype(np.int8)
            else:
                self._view.interpolateRGB_r = generate_images.color_image_interpolate(self._view.workspace.grid_x, self._view.workspace.grid_y, self._view.workspace.coords, np.ones(self._view.workspace.nSpectra), method=method, clip_low=None, clip_high = None)
                self._view.interpolateRGB_r = np.zeros(self._view.interpolateRGB_r.shape).astype(np.int8)

    if self._view.interpolateRGB_g is None:
        if len(self._view.imageArrayRGB[1]) > 0:
            clip_low, clip_high = _get_clip(self, green=True)
            self._view.interpolateRGB_g = generate_images.color_image_interpolate(self._view.workspace.grid_x, self._view.workspace.grid_y, self._view.workspace.coords, self._view.imageArrayRGB[1], method=method, clip_low=clip_low, clip_high = clip_high)
        else:
            if self._view.interpolateRGB_r is not None:
                self._view.interpolateRGB_g = np.zeros(self._view.interpolateRGB_r.shape).astype(np.int8)
            elif self._view.interpolateRGB_b is not None:
                self._view.interpolateRGB_g = np.zeros(self._view.interpolateRGB_b.shape).astype(np.int8)
            else:
                self._view.interpolateRGB_g = generate_images.color_image_interpolate(self._view.workspace.grid_x, self._view.workspace.grid_y, self._view.workspace.coords, np.ones(self._view.workspace.nSpectra), method=method, clip_low=None, clip_high = None)
                self._view.interpolateRGB_g = np.zeros(self._view.interpolateRGB_g.shape).astype(np.int8)

    if self._view.interpolateRGB_b is None:
        if len(self._view.imageArrayRGB[2]) > 0:
            clip_low, clip_high = _get_clip(self, blue=True)
            self._view.interpolateRGB_b = generate_images.color_image_interpolate(self._view.workspace.grid_x, self._view.workspace.grid_y, self._view.workspace.coords, self._view.imageArrayRGB[2], method=method, clip_low=clip_low, clip_high = clip_high)
        else:
            if self._view.interpolateRGB_r is not None:
                self._view.interpolateRGB_b = np.zeros(self._view.interpolateRGB_r.shape).astype(np.int8)
            elif self._view.interpolateRGB_g is not None:
                self._view.interpolateRGB_b = np.zeros(self._view.interpolateRGB_g.shape).astype(np.int8)
            else:
                self._view.interpolateRGB_b = generate_images.color_image_interpolate(self._view.workspace.grid_x, self._view.workspace.grid_y, self._view.workspace.coords, np.ones(self._view.workspace.nSpectra), method=method, clip_low=None, clip_high = None)
                self._view.interpolateRGB_b = np.zeros(self._view.interpolateRGB_b.shape).astype(np.int8)

    self._view.RGBinterpolateImageArray = np.dstack((self._view.interpolateRGB_r, self._view.interpolateRGB_g, self._view.interpolateRGB_b))
    _pixmap = QPixmap(QImage(self._view.RGBinterpolateImageArray, self._view.interpolateRGB_r.shape[1], self._view.interpolateRGB_r.shape[0], 3*self._view.interpolateRGB_r.shape[1], QImage.Format_RGB888))
    self._view.laserPainterInstanceMap = QPainter(pixMap)
    self._view.laserPainterInstanceMap.setOpacity(float(opacity)/100.0)
    _width = max(self._view.workspace.xPix) - min(self._view.workspace.xPix)
    _height = max(self._view.workspace.yPix) - min(self._view.workspace.yPix)
    self._view.laserPainterInstanceMap.drawPixmap(QRect(min(self._view.workspace.xPix), min(self._view.workspace.yPix), _width, _height), _pixmap)
    self._view.laserPainterInstanceMap.end()


def _plotHistUpdate(self, red=True, green=True, blue=True):
    # determine which RGB boxes are checked
    if self._view.redRGB is not None and red:
        # loop through all axes, check if the line label name R1 exists, if so, remove it
        for _ax in self._view.axMapPlot1:
            if _ax.get_label() == '_redHist':
                # remove std fill_betweens
                for i in range(len(_ax.axes.collections)):
                    _ax.axes.collections[0].remove()
                _ax.remove()
                self._view.axMapPlot1.remove(_ax)
        #self._view.axMapPlot1 = []

        # calculate histogram for each RGB based on intensity distribution
        #_redBins = np.arange(self._view.redRGB.min(), self._view.redRGB.max(), (self._view.redRGB.max()-self._view.redRGB.min())/50)
        _redHist = np.histogram(self._view.redRGB, bins=20)
        _ax = generate_plots.plotRGBHistogram(self._view.traceCanvasMapPlot1.axes[0], _redHist, 'r', alpha=0.5, label='_redHist')
        self._view.axMapPlot1.append(_ax[0])
        _ybounds = (0, max(_redHist[0]))
        self._view.redHistParams = [[_redHist[1][0], _ybounds[0], 0.5*(_redHist[1][1]-_redHist[1][0]), _ybounds[1]-_ybounds[0]],
                                    [_redHist[1][-1], _ybounds[0], 0.5*(_redHist[1][1]-_redHist[1][0]), _ybounds[1]-_ybounds[0]]]

        # add movable rectangles to clip interpolated region
        self._view.traceCanvasMapPlot1.plotDraggablePointsHist(self._view, self._view.redHistParams, None, None)
        self._view.axMapPlot1[-1].axes.relim()
        self._view.axMapPlot1[-1].axes.autoscale()

    if self._view.greenRGB is not None and green:
        # loop through all axes, check if the line label name R1 exists, if so, remove it
        for _ax in self._view.axMapPlot1:
            if _ax.get_label() == '_greenHist':
                # remove std fill_betweens
                for i in range(len(_ax.axes.collections)):
                    _ax.axes.collections[0].remove()
                _ax.remove()
                self._view.axMapPlot1.remove(_ax)
        #self._view.axMapPlot1 = []

        # calculate histogram for each RGB based on intensity distribution
        #_redBins = np.arange(self._view.redRGB.min(), self._view.redRGB.max(), (self._view.redRGB.max()-self._view.redRGB.min())/50)
        _greenHist = np.histogram(self._view.greenRGB, bins=20)
        _ax = generate_plots.plotRGBHistogram(self._view.traceCanvasMapPlot1.axes[1], _greenHist, 'g', alpha=0.5, label='_greenHist')
        self._view.axMapPlot1.append(_ax[0])
        _ybounds = (0, max(_greenHist[0]))
        self._view.greenHistParams = [[_greenHist[1][0], _ybounds[0], 0.5*(_greenHist[1][1]-_greenHist[1][0]), _ybounds[1]-_ybounds[0]],
                                    [_greenHist[1][-1], _ybounds[0], 0.5*(_greenHist[1][1]-_greenHist[1][0]), _ybounds[1]-_ybounds[0]]]

        # add movable rectangles to clip interpolated region
        self._view.traceCanvasMapPlot1.plotDraggablePointsHist(self._view, None, self._view.greenHistParams, None)
        self._view.axMapPlot1[-1].axes.relim()
        self._view.axMapPlot1[-1].axes.autoscale()

    if self._view.blueRGB is not None and blue:
        # loop through all axes, check if the line label name R1 exists, if so, remove it
        for _ax in self._view.axMapPlot1:
            if _ax.get_label() == '_blueHist':
                # remove std fill_betweens
                for i in range(len(_ax.axes.collections)):
                    _ax.axes.collections[0].remove()
                _ax.remove()
                self._view.axMapPlot1.remove(_ax)
        #self._view.axMapPlot1 = []

        # calculate histogram for each RGB based on intensity distribution
        #_redBins = np.arange(self._view.redRGB.min(), self._view.redRGB.max(), (self._view.redRGB.max()-self._view.redRGB.min())/50)
        _blueHist = np.histogram(self._view.blueRGB, bins=20)
        _ax = generate_plots.plotRGBHistogram(self._view.traceCanvasMapPlot1.axes[2], _blueHist, 'b', alpha=0.5, label='_blueHist')
        self._view.axMapPlot1.append(_ax[0])
        _ybounds = (0, max(_blueHist[0]))
        self._view.blueHistParams = [[_blueHist[1][0], _ybounds[0], 0.5*(_blueHist[1][1]-_blueHist[1][0]), _ybounds[1]-_ybounds[0]],
                                    [_blueHist[1][-1], _ybounds[0], 0.5*(_blueHist[1][1]-_blueHist[1][0]), _ybounds[1]-_ybounds[0]]]

        # add movable rectangles to clip interpolated region
        self._view.traceCanvasMapPlot1.plotDraggablePointsHist(self._view, None, None, self._view.blueHistParams)
        self._view.axMapPlot1[-1].axes.relim()
        self._view.axMapPlot1[-1].axes.autoscale()


    # add signal to change map when rectangles are moved
    self._view.traceCanvasMapPlot1.draw_idle()


def _plotMapUpdate(self):
    if self._view.axMapPlot2 != []:
        for _ax in self._view.axMapPlot2:
            for _line in _ax.lines:
                _line.remove()
            #plt.delaxes(_ax)
        self._view.traceCanvasMapPlot2.draw_idle()
    self._view.axMapPlot2 = []
    # always display active-dark
    # if no ROIs are selected, or one ROI is selected, plot as normal and use ROI index for mean/median
    if len(self._view.workspace.selectedROIRGB) < 2:
        _plotMapActiveDark(self)
    # if multiple ROIs are selected, plot only one region (or all composite) and use colors and legends to distinguish between ROIs
    else:
        _plotMapActiveDarkMultiRoi(self)

# read location and width
# place matplotlib box objects
# connect object to signal to enable dragging and updating
def _plotMapUpdateBoxSelect(self):
    # if needed, get height of box
    _ybounds = self._view.traceCanvasMapPlot2.axes.get_ybound()
    # x, y - lower left corner, width, height
    self._view.redBoxParams = None
    self._view.greenBoxParams = None
    self._view.blueBoxParams = None
    self._view.redHistParams = None
    self._view.greenHistParams = None
    self._view.blueHistParams = None
    self._view.redRGB = None
    self._view.greenRGB = None
    self._view.blueRGB = None
    self._view.interpolateRGB_r = None
    self._view.interpolateRGB_g = None
    self._view.interpolateRGB_b = None

    try:
        self._view.redHistLowRGB.textChanged.disconnect()
        self._view.redHistHighRGB.textChanged.disconnect()
        self._view.greenHistLowRGB.textChanged.disconnect()
        self._view.greenHistHighRGB.textChanged.disconnect()
        self._view.blueHistLowRGB.textChanged.disconnect()
        self._view.blueHistHighRGB.textChanged.disconnect()
    except:
        print('could not disconnect *HistHighRGB.textChanged')

    self._view.redHistHighRGB.setText('')
    self._view.redHistLowRGB.setText('')
    self._view.greenHistHighRGB.setText('')
    self._view.greenHistLowRGB.setText('')
    self._view.blueHistHighRGB.setText('')
    self._view.blueHistLowRGB.setText('')
    _redFlag = False
    _blueFlag = False
    _greenFlag = False

    if self._view.redCheckRGB.isChecked():
        self._view.redPosRGB.textChanged.disconnect()
        self._view.redWidthRGB.textChanged.disconnect()
        # determine center and width positions
        _redCenter = self._view.redPosRGB.text()
        if _redCenter == '':
            _redCenter = '254'
            self._view.redPosRGB.setText(_redCenter)
        _redCenter = float(_redCenter)
        _redWidth = self._view.redWidthRGB.text()
        if _redWidth == '':
            _redWidth = '1'
            self._view.redWidthRGB.setText(_redWidth)
        _redWidth = float(_redWidth)
        # convert to pixel positions
        _redLower = _redCenter -_redWidth/2.0
        self._view.redBoxParams = [_redLower, _ybounds[0], _redWidth, _ybounds[1]-_ybounds[0]]
        self._view.redPosRGB.textChanged.connect(functools.partial(_updateRedValue, self))
        self._view.redWidthRGB.textChanged.connect(functools.partial(_updateRedValue, self))
        _updateRedValue(self, update_img = False)
        _redFlag = True
    if self._view.greenCheckRGB.isChecked():
        self._view.greenPosRGB.textChanged.disconnect()
        self._view.greenWidthRGB.textChanged.disconnect()
        # determine center and width positions
        _greenCenter = self._view.greenPosRGB.text()
        if _greenCenter == '':
            _greenCenter = '261'
            self._view.greenPosRGB.setText(_greenCenter)
        _greenCenter = float(_greenCenter)
        _greenWidth = self._view.greenWidthRGB.text()
        if _greenWidth == '':
            _greenWidth = '1.5'
            self._view.greenWidthRGB.setText(_greenWidth)
        _greenWidth = float(_greenWidth)
        # convert to pixel positions
        _greenLower = _greenCenter -_greenWidth/2.0
        self._view.greenBoxParams = [_greenLower, _ybounds[0], _greenWidth, _ybounds[1]-_ybounds[0]]
        self._view.greenPosRGB.textChanged.connect(functools.partial(_updateGreenValue, self))
        self._view.greenWidthRGB.textChanged.connect(functools.partial(_updateGreenValue, self))
        _updateGreenValue(self, update_img = False)
        _greenFlag = True
    if self._view.blueCheckRGB.isChecked():
        self._view.bluePosRGB.textChanged.disconnect()
        self._view.blueWidthRGB.textChanged.disconnect()
        # determine center and width positions
        _blueCenter = self._view.bluePosRGB.text()
        if _blueCenter == '':
            _blueCenter = '300'
            self._view.bluePosRGB.setText(_blueCenter)
        _blueCenter = float(_blueCenter)
        _blueWidth = self._view.blueWidthRGB.text()
        if _blueWidth == '':
            _blueWidth = '10'
            self._view.blueWidthRGB.setText(_blueWidth)
        _blueWidth = float(_blueWidth)
        # convert to pixel positions
        _blueLower = _blueCenter -_blueWidth/2.0
        self._view.blueBoxParams = [_blueLower, _ybounds[0], _blueWidth, _ybounds[1]-_ybounds[0]]
        self._view.bluePosRGB.textChanged.connect(functools.partial(_updateBlueValue, self))
        self._view.blueWidthRGB.textChanged.connect(functools.partial(_updateBlueValue, self))
        _updateBlueValue(self, update_img = False)
        _blueFlag = True

    _calculateRGBImage(self, red=_redFlag, green=_greenFlag, blue=_blueFlag)
    # add vertical box (with alpha) to plot
    # connect signal to enable user movement, read center and width of each box, and calculate integrated intensity (and update ACI image)
    self._view.traceCanvasMapPlot2.plotDraggablePoints(self._view, self._view.redBoxParams, self._view.greenBoxParams, self._view.blueBoxParams)
    self._view.redHistLowRGB.textChanged.connect(functools.partial(_control_false_color._updateMapContrast, self, red=True))
    self._view.redHistHighRGB.textChanged.connect(functools.partial(_control_false_color._updateMapContrast, self, red=True))
    self._view.greenHistLowRGB.textChanged.connect(functools.partial(_control_false_color._updateMapContrast, self, green=True))
    self._view.greenHistHighRGB.textChanged.connect(functools.partial(_control_false_color._updateMapContrast, self, green=True))
    self._view.blueHistLowRGB.textChanged.connect(functools.partial(_control_false_color._updateMapContrast, self, blue=True))
    self._view.blueHistHighRGB.textChanged.connect(functools.partial(_control_false_color._updateMapContrast, self, blue=True))



def _updateRedValue(self, update_img = True):
    self._view.redRGB = None
    if self._view.redCheckRGB.isChecked():
        self._view.interpolateRGB_r = None
        _redCenter = float(self._view.redPosRGB.text())
        _redWidth = float(self._view.redWidthRGB.text())
        if _redCenter > 100 and _redCenter < 400 and _redWidth > 0:
            # convert to pixel positions
            _redLower = _redCenter -_redWidth
            _redLowerIndex = np.argmin(np.abs([_w - _redLower for _w in self._view.workspace.wavelength]))
            _redUpper = _redCenter +_redWidth
            _redUpperIndex = np.argmin(np.abs([_w - _redUpper for _w in self._view.workspace.wavelength]))
            self._view.redMapPixRange = [_redLowerIndex, _redUpperIndex]
            if self._view.redMapPixRange[0] == 0 and self._view.redMapPixRange[1] == 0:
                self._view.redMapPixRange[1] = 1
            if self._view.redMapPixRange[0] == self._view.workspace.nChannels and self._view.redMapPixRange[1] == self._view.workspace.nChannels:
                self._view.redMapPixRange[0] = self._view.workspace.nChannels-1

            # recalculate red component of image
            if self._view.RGBMax.isChecked():
                self._view.redRGB = self._view.specRGB[:, self._view.redMapPixRange[0]:self._view.redMapPixRange[1]].max(axis=1)
            elif self._view.RGBMedian.isChecked():
                self._view.redRGB = np.median(self._view.specRGB[:, self._view.redMapPixRange[0]:self._view.redMapPixRange[1]], axis=1)
            elif self._view.RGBMean.isChecked():
                self._view.redRGB = np.mean(self._view.specRGB[:, self._view.redMapPixRange[0]:self._view.redMapPixRange[1]], axis=1)
            else:
                self._view.redRGB = self._view.specRGB[:, self._view.redMapPixRange[0]:self._view.redMapPixRange[1]].sum(axis=1)

            # call function to regenerate image from all three RGB components (if they all exist)
            # this function will need to be able to clip values based on the RGB plot in the upper right
            if update_img:
                _calculateRGBImage(self, red=True, green=False, blue=False)



def _updateGreenValue(self, update_img = True):
    self._view.greenRGB = None
    if self._view.greenCheckRGB.isChecked():
        self._view.interpolateRGB_g = None
        _greenCenter = float(self._view.greenPosRGB.text())
        _greenWidth = float(self._view.greenWidthRGB.text())
        if _greenCenter > 100 and _greenCenter < 400 and _greenWidth > 0:
            # convert to pixel positions
            _greenLower = _greenCenter -_greenWidth
            _greenLowerIndex = np.argmin(np.abs([_w - _greenLower for _w in self._view.workspace.wavelength]))
            _greenUpper = _greenCenter +_greenWidth
            _greenUpperIndex = np.argmin(np.abs([_w - _greenUpper for _w in self._view.workspace.wavelength]))
            self._view.greenMapPixRange = [_greenLowerIndex, _greenUpperIndex]
            if self._view.greenMapPixRange[0] == 0 and self._view.greenMapPixRange[1] == 0:
                self._view.greenMapPixRange[1] = 1
            if self._view.greenMapPixRange[0] == self._view.workspace.nChannels and self._view.greenMapPixRange[1] == self._view.workspace.nChannels:
                self._view.greenMapPixRange[0] = self._view.workspace.nChannels-1

            # recalculate green component of image
            if self._view.RGBMax.isChecked():
                self._view.greenRGB = self._view.specRGB[:, self._view.greenMapPixRange[0]:self._view.greenMapPixRange[1]].max(axis=1)
            elif self._view.RGBMedian.isChecked():
                self._view.greenRGB = np.median(self._view.specRGB[:, self._view.greenMapPixRange[0]:self._view.greenMapPixRange[1]], axis=1)
            elif self._view.RGBMean.isChecked():
                self._view.greenRGB = np.mean(self._view.specRGB[:, self._view.greenMapPixRange[0]:self._view.greenMapPixRange[1]], axis=1)
            else:
                self._view.greenRGB = self._view.specRGB[:, self._view.greenMapPixRange[0]:self._view.greenMapPixRange[1]].sum(axis=1)
            if update_img:
                _calculateRGBImage(self, red=False, green=True, blue=False)


def _updateBlueValue(self, update_img = False):
    self._view.blueRGB = None
    if self._view.blueCheckRGB.isChecked():
        self._view.interpolateRGB_b = None
        _blueCenter = float(self._view.bluePosRGB.text())
        _blueWidth = float(self._view.blueWidthRGB.text())
        if _blueCenter > 100 and _blueCenter < 400 and _blueWidth > 0:
            # convert to pixel positions
            _blueLower = _blueCenter -_blueWidth
            _blueLowerIndex = np.argmin(np.abs([_w - _blueLower for _w in self._view.workspace.wavelength]))
            _blueUpper = _blueCenter +_blueWidth
            _blueUpperIndex = np.argmin(np.abs([_w - _blueUpper for _w in self._view.workspace.wavelength]))
            self._view.blueMapPixRange = [_blueLowerIndex, _blueUpperIndex]
            if self._view.blueMapPixRange[0] == 0 and self._view.blueMapPixRange[1] == 0:
                self._view.blueMapPixRange[1] = 1
            if self._view.blueMapPixRange[0] == self._view.workspace.nChannels and self._view.blueMapPixRange[1] == self._view.workspace.nChannels:
                self._view.blueMapPixRange[0] = self._view.workspace.nChannels-1

            # recalculate blue component of image
            if self._view.RGBMax.isChecked():
                self._view.blueRGB = self._view.specRGB[:, self._view.blueMapPixRange[0]:self._view.blueMapPixRange[1]].max(axis=1)
            elif self._view.RGBMedian.isChecked():
                self._view.blueRGB = np.median(self._view.specRGB[:, self._view.blueMapPixRange[0]:self._view.blueMapPixRange[1]], axis=1)
            elif self._view.RGBMean.isChecked():
                self._view.blueRGB = np.mean(self._view.specRGB[:, self._view.blueMapPixRange[0]:self._view.blueMapPixRange[1]], axis=1)
            else:
                self._view.blueRGB = self._view.specRGB[:, self._view.blueMapPixRange[0]:self._view.blueMapPixRange[1]].sum(axis=1)
            if update_img:
                _calculateRGBImage(self, red=False, green=False, blue=True)


def _calculateRGBImage(self, red=True, green=True, blue=True):
    # generate RGB array
    self._view.imageArrayRGB = None
    if self._view.redRGB is not None or self._view.greenRGB is not None or self._view.blueRGB is not None:
        self._view.imageArrayRGB = []
        if self._view.redRGB is None:
            self._view.imageArrayRGB.append([])
        else:
            self._view.imageArrayRGB.append(self._view.redRGB)
        if self._view.greenRGB is None:
            self._view.imageArrayRGB.append([])
        else:
            self._view.imageArrayRGB.append(self._view.greenRGB)
        if self._view.blueRGB is None:
            self._view.imageArrayRGB.append([])
        else:
            self._view.imageArrayRGB.append(self._view.blueRGB)

    # call image function to add it to the image
    _addACIImageRGB(self)
    _plotHistUpdate(self, red=red, green=green, blue=blue)


def _calculateSpec(self):
    # for now, calculate/display all points in map, regardless of which ROIs are selected
    """"""
    if self._view.allItemRGB.isChecked():
        self._view.specRGB = self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].values.copy() + \
                             self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].values.copy() + \
                             self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].values.copy()
    elif self._view.R1ItemRGB.isChecked():
        self._view.specRGB = self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].values.copy()
        if self._view.R2ItemRGB.isChecked():
            self._view.specRGB += self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].values.copy()
        if self._view.R3ItemRGB.isChecked():
            self._view.specRGB += self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].values.copy()
    elif self._view.R2ItemRGB.isChecked():
        self._view.specRGB = self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].values.copy()
        if self._view.R3ItemRGB.isChecked():
            self._view.specRGB += self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].values.copy()
    elif self._view.R3ItemRGB.isChecked():
        self._view.specRGB = self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].values.copy()


def _plotMapActiveDark(self):
    if self._view.workspace.selectedROIRGB == []:
        _ROIindex = list(range(self._view.workspace.nSpectra))
    else:
        _ROIindex = self._view.roiDict[self._view.workspace.selectedROIRGB[0]].specIndexList
    _yR1_std = None
    _yR2_std = None
    _yR3_std = None
    _yAll_std = None
    if self._view.meanDisplayRGB.isChecked():
        _yR1 = self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].mean()
        _yR2 = self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].mean()
        _yR3 = self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].mean()
        _yAll = self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].mean().values + \
                self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].mean().values + \
                self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].mean().values
    elif self._view.medianDisplayRGB.isChecked():
        # using numpy is slightly faster than using pandas.median
        _yR1 = np.median(self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
        _yR2 = np.median(self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
        _yR3 = np.median(self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
        _yAll = (np.median(self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0) +
                 np.median(self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0) +
                 np.median(self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0))
    else:
        # read textbox
        # if empty, use index 0
        if self._view.indexSpecRGB.text() == '':
            log_parsing.log_warning(self._view, 'No spectral index entered. Using index 0')
            self._view.indexSpecRGB.setText('0')
        _indexText = self._view.indexSpecRGB.text()
        log_parsing.log_info(self._view, 'Adding traces for spectral indices: '+_indexText)
        _indexStrList = _indexText.split(',')
        self.indexListMap = []
        for i in _indexStrList:
            if ':' not in i:
                self.indexListMap.append(int(i))
            else:
                _iList = list(range(int(i.split(':')[0]), int(i.split(':')[1])+1))
                for j in _iList:
                    self.indexListMap.append(int(j))
        _yR1 = self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].loc[self.indexListMap].values
        _yR2 = self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].loc[self.indexListMap].values
        _yR3 = self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].loc[self.indexListMap].values
        _yAll = (self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].loc[self.indexListMap].values +
                 self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].loc[self.indexListMap].values +
                 self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].loc[self.indexListMap].values)


    _x = self._view.workspace.wavelength

    if self._view.R1ItemRGB.isChecked():
        _color = self._view.workspace.colorR1
        if len(_yR1) == self._view.workspace.nChannels:
            _plotMapSingle(self, _x, _yR1, _color, label='R1', y_std =_yR1_std)
        else:
            _plotMapMulti(self, _x, _yR1, _color, label='R1', y_std =_yR1_std)
    if self._view.R2ItemRGB.isChecked():
        _color = self._view.workspace.colorR2
        if len(_yR2) == self._view.workspace.nChannels:
            _plotMapSingle(self, _x, _yR2, _color, label='R2', y_std = _yR2_std)
        else:
            _plotMapMulti(self, _x, _yR2, _color, label='R2', y_std = _yR2_std)
    if self._view.R3ItemRGB.isChecked():
        _color = self._view.workspace.colorR3
        if len(_yR3) == self._view.workspace.nChannels:
            _plotMapSingle(self, _x, _yR3, _color, label='R3', y_std =_yR3_std)
        else:
            _plotMapMulti(self, _x, _yR3, _color, label='R3', y_std = _yR3_std)
    if self._view.allItemRGB.isChecked():
        _color = self._view.workspace.colorComposite
        if len(_yAll) == self._view.workspace.nChannels:
            _plotMapSingle(self, _x, _yAll, _color, label='composite', y_std = _yAll_std)
        else:
            _plotMapMulti(self, _x, _yAll, _color, label='composite', y_std = _yAll_std)

    if self._view.traceCanvasMapPlot2.axes.xaxis.label._text == '' or True:
        _plotMapFormat(self)
    self._view.traceCanvasMapPlot2.draw_idle()

def _plotMapActiveDarkMultiRoi(self):
    _ROIindex = [self._view.roiDict[_roiList].specIndexList for _roiList in self._view.workspace.selectedROIRGB]
    _yR1_std = None
    _yR2_std = None
    _yR3_std = None
    _yAll_std = None
    if self._view.meanDisplayRGB.isChecked():
        _yR1 = [self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_indexList].mean() for _indexList in _ROIindex]
        _yR2 = [self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_indexList].mean() for _indexList in _ROIindex]
        _yR3 = [self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_indexList].mean() for _indexList in _ROIindex]
        _yAll = [(self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_indexList].mean().values +
                  self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_indexList].mean().values +
                  self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_indexList].mean().values) for _indexList in _ROIindex]
    elif self._view.medianDisplayRGB.isChecked():
        # using numpy is slightly faster than using pandas.median
        _yR1 = [np.median(self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yR2 = [np.median(self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yR3 = [np.median(self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yAll = [(np.median(self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_indexList], axis=0) +
                  np.median(self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_indexList], axis=0) +
                  np.median(self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_indexList], axis=0)) for _indexList in _ROIindex]
    else:
        log_parsing.log_error(self._view, 'Cannot display subset of selected indices with multiple ROIs selected')

    _x = self._view.workspace.wavelength

    _color = [self._view.roiDict[_roiDictName].color for _roiDictName in self._view.workspace.selectedROIRGB]
    _legend = [self._view.roiDict[_roiDictName].humanReadableName for _roiDictName in self._view.workspace.selectedROIRGB]
    if self._view.R1ItemRGB.isChecked():
        _plotMapMulti(self, _x, _yR1, _color, label=_legend, legend = True, y_std = _yR1_std)
    elif self._view.R2ItemRGB.isChecked():
        _plotMapMulti(self, _x, _yR2, _color, label=_legend, legend = True, y_std = _yR2_std)
    elif self._view.R3ItemRGB.isChecked():
        _plotMapMulti(self, _x, _yR3, _color, label=_legend, legend = True, y_std = _yR3_std)
    elif self._view.allItemRGB.isChecked():
        _plotMapMulti(self, _x, _yAll, _color, label=_legend, legend = True, y_std = _yAll_std)

    # add the upper axis for wavenumbers
    if self._view.traceCanvasMapPlot2.axes.xaxis.label._text == '' or True:
        _plotMapFormat(self)
    self._view.traceCanvasMapPlot2.draw_idle()
    #_addACIMultiRoiImage(self)


def _plotMapUpdateRegion1(self):
    # if the checkbox is checked:
    if self._view.R1ItemRGB.isChecked():
        # if there are more than 2 ROIs selected:
        if len(self._view.workspace.selectedROIRGB) > 1:
            if self._view.axMapPlot2 != []:
                for _ax in self._view.axMapPlot2:
                    for _line in _ax.lines:
                        _line.remove()
                self._view.traceCanvasMapPlot2.draw_idle()
            self._view.axMapPlot2 = []

            self._view.R2ItemRGB.setChecked(False)
            self._view.R3ItemRGB.setChecked(False)
            self._view.allItemRGB.setChecked(False)
            _plotMapActiveDarkMultiRoi(self)

        else:
            _add_plot_flag = True
            # loop through all axes, check if the line label name R1 exists, if not add it
            for _ax in self._view.axMapPlot2:
                for _line in _ax.lines:
                    if _line._label == 'R1':
                        log_parsing.log_info(self._view, 'R1 trace already present in plot')
                        _add_plot_flag = False
            if self._view.workspace.selectedROIRGB == []:
                _ROIindex = list(range(self._view.workspace.nSpectra))
            else:
                _ROIindex = self._view.roiDict[self._view.workspace.selectedROIRGB[0]].specIndexList

            _yR1_std = None
            if self._view.meanDisplayRGB.isChecked():
                _yR1 = self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].mean()
            elif self._view.medianDisplayRGB.isChecked():
                _yR1 = np.median(self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
            else:
                _yR1 = self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].loc[self.indexListMap].values

            _x = self._view.workspace.wavelength
            _color = self._view.workspace.colorR1
            if len(_yR1) == self._view.workspace.nChannels:
                _plotMapSingle(self, _x, _yR1, _color, label='R1', y_std = _yR1_std)
            else:
                _plotMapMulti(self, _x, _yR1, _color, label='R1', y_std = _yR1_std)
            log_parsing.log_info(self._view, 'added R1 trace')
            _addACIImageRGB(self)

    # if the checkbox is unchecked:
    else:
        # loop through all axes, check if the line label name R1 exists, if so, remove it
        for _ax in self._view.axMapPlot2:
            for _line in _ax.lines:
                if _line._label == 'R1':
                    log_parsing.log_info(self._view, 'removed trace R1')
                    _line.remove()

    self._view.traceCanvasMapPlot2.draw_idle()
    _calculateSpec(self)
    _plotMapUpdateBoxSelect(self)


def _plotMapUpdateRegion2(self):
    # if the checkbox is checked:
    if self._view.R2ItemRGB.isChecked():
        # if there are more than 2 ROIs selected:
        if len(self._view.workspace.selectedROIRGB) > 1:
            if self._view.axMapPlot2 != []:
                for _ax in self._view.axMapPlot2:
                    for _line in _ax.lines:
                        _line.remove()
                self._view.traceCanvasMapPlot2.draw_idle()
            self._view.axMapPlot2 = []

            self._view.R1ItemRGB.setChecked(False)
            self._view.R3ItemRGB.setChecked(False)
            self._view.allItemRGB.setChecked(False)
            _plotMapActiveDarkMultiRoi(self)

        else:
            _add_plot_flag = True
            # loop through all axes, check if the line label name R1 exists, if not add it
            for _ax in self._view.axMapPlot2:
                for _line in _ax.lines:
                    if _line._label == 'R2':
                        log_parsing.log_info(self._view, 'R2 trace already present in plot')
                        _add_plot_flag = False
            if self._view.workspace.selectedROIRGB == []:
                _ROIindex = list(range(self._view.workspace.nSpectra))
            else:
                _ROIindex = self._view.roiDict[self._view.workspace.selectedROIRGB[0]].specIndexList

            _yR2_std = None
            if self._view.meanDisplayRGB.isChecked():
                _yR2 = self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].mean()
            elif self._view.medianDisplayRGB.isChecked():
                _yR2 = np.median(self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
            else:
                _yR2 = self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].loc[self.indexListMap].values

            _x = self._view.workspace.wavelength
            _color = self._view.workspace.colorR2
            if len(_yR2) == self._view.workspace.nChannels:
                _plotMapSingle(self, _x, _yR2, _color, label='R2', y_std = _yR2_std)
            else:
                _plotMapMulti(self, _x, _yR2, _color, label='R2', y_std = _yR2_std)
            log_parsing.log_info(self._view, 'added R2 trace')
            _addACIImageRGB(self)

    # if the checkbox is unchecked:
    else:
        # loop through all axes, check if the line label name R1 exists, if so, remove it
        for _ax in self._view.axMapPlot2:
            for _line in _ax.lines:
                if _line._label == 'R2':
                    log_parsing.log_info(self._view, 'removed trace R2')
                    _line.remove()

    self._view.traceCanvasMapPlot2.draw_idle()
    _calculateSpec(self)
    _plotMapUpdateBoxSelect(self)


def _plotMapUpdateRegion3(self):
    # if the checkbox is checked:
    if self._view.R3ItemRGB.isChecked():
        # if there are more than 2 ROIs selected:
        if len(self._view.workspace.selectedROIRGB) > 1:
            if self._view.axMapPlot2 != []:
                for _ax in self._view.axMapPlot2:
                    for _line in _ax.lines:
                        _line.remove()
                self._view.traceCanvasMapPlot2.draw_idle()
            self._view.axMapPlot2 = []

            self._view.R1ItemRGB.setChecked(False)
            self._view.R2ItemRGB.setChecked(False)
            self._view.allItemRGB.setChecked(False)
            _plotMapActiveDarkMultiRoi(self)

        else:
            _add_plot_flag = True
            # loop through all axes, check if the line label name R1 exists, if not add it
            for _ax in self._view.axMapPlot2:
                for _line in _ax.lines:
                    if _line._label == 'R3':
                        log_parsing.log_info(self._view, 'R3 trace already present in plot')
                        _add_plot_flag = False
            if self._view.workspace.selectedROIRGB == []:
                _ROIindex = list(range(self._view.workspace.nSpectra))
            else:
                _ROIindex = self._view.roiDict[self._view.workspace.selectedROIRGB[0]].specIndexList

            _yR3_std = None
            if self._view.meanDisplayRGB.isChecked():
                _yR3 = self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].mean()
            elif self._view.medianDisplayRGB.isChecked():
                _yR3 = np.median(self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
            else:
                _yR3 = self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].loc[self.indexListMap].values

            _x = self._view.workspace.wavelength
            _color = self._view.workspace.colorR3
            if len(_yR3) == self._view.workspace.nChannels:
                _plotMapSingle(self, _x, _yR3, _color, label='R3', y_std = _yR3_std)
            else:
                _plotMapMulti(self, _x, _yR3, _color, label='R3', y_std = _yR3_std)
            log_parsing.log_info(self._view, 'added R3 trace')
            _addACIImageRGB(self)

    # if the checkbox is unchecked:
    else:
        # loop through all axes, check if the line label name R1 exists, if so, remove it
        for _ax in self._view.axMapPlot2:
            for _line in _ax.lines:
                if _line._label == 'R3':
                    log_parsing.log_info(self._view, 'removed trace R3')
                    _line.remove()

    self._view.traceCanvasMapPlot2.draw_idle()
    _calculateSpec(self)
    _plotMapUpdateBoxSelect(self)


def _plotMapUpdateRegionAll(self):
    # if the checkbox is checked:
    if self._view.allItemRGB.isChecked():
        # if there are more than 2 ROIs selected:
        if len(self._view.workspace.selectedROIRGB) > 1:
            if self._view.axMapPlot2 != []:
                for _ax in self._view.axMapPlot2:
                    for _line in _ax.lines:
                        _line.remove()
                self._view.traceCanvasMapPlot2.draw_idle()
            self._view.axMapPlot2 = []

            self._view.R1ItemRGB.setChecked(False)
            self._view.R2ItemRGB.setChecked(False)
            self._view.R3ItemRGB.setChecked(False)
            _plotMapActiveDarkMultiRoi(self)

        else:
            _add_plot_flag = True
            # loop through all axes, check if the line label name R1 exists, if not add it
            for _ax in self._view.axMapPlot2:
                for _line in _ax.lines:
                    if _line._label == 'composite':
                        log_parsing.log_info(self._view, 'composite trace already present in plot')
                        _add_plot_flag = False
            if self._view.workspace.selectedROIRGB == []:
                _ROIindex = list(range(self._view.workspace.nSpectra))
            else:
                _ROIindex = self._view.roiDict[self._view.workspace.selectedROIRGB[0]].specIndexList

            _yAll_std = None
            if self._view.meanDisplayRGB.isChecked():
                _yAll = (self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].mean().values +
                         self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].mean().values +
                         self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].mean().values)
            elif self._view.medianDisplayRGB.isChecked():
                _yAll = (np.median(self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected], axis=0) +
                         np.median(self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected], axis=0) +
                         np.median(self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected], axis=0))
            else:
                _yAll = (self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].loc[self.indexListMap].values +
                         self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].loc[self.indexListMap].values +
                         self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].loc[self.indexListMap].values)

            _x = self._view.workspace.wavelength
            _color = self._view.workspace.colorComposite
            if len(_yAll) == self._view.workspace.nChannels:
                _plotMapSingle(self, _x, _yAll, _color, label='composite', y_std = _yAll_std)
            else:
                _plotMapMulti(self, _x, _yAll, _color, label='composite', y_std = _yAll_std)
            log_parsing.log_info(self._view, 'added composite trace')
            _addACIImageRGB(self)

    # if the checkbox is unchecked:
    else:
        # loop through all axes, check if the line label name R1 exists, if so, remove it
        for _ax in self._view.axMapPlot2:
            for _line in _ax.lines:
                if _line._label == 'composite':
                    log_parsing.log_info(self._view, 'removed trace composite')
                    _line.remove()

    self._view.traceCanvasMapPlot2.draw_idle()
    _calculateSpec(self)
    _plotMapUpdateBoxSelect(self)




def _plotMapSingle(self, x, y, color, alpha=0.9, label='', y_std = None):
    _ax = generate_plots.plotMapTrace(self._view, x, y, color, alpha=alpha, label=label, std = y_std)
    _legend = _ax.get_legend()
    if _legend is not None:
        _legend.remove()
    #if _ax not in self._view.axMainPlot1:
        #self._view.axMainPlot1.append(_ax)
    self._view.axMapPlot2.append(_ax)
    #self._view.axMainPlot1 = [_ax]

def _plotMapMulti(self, x, y, color, label='', legend = False, y_std = None):
    _alpha = 0.6-0.0006*len(y)
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
        _ax = generate_plots.plotMapTrace(self._view, x, _y_i, c_i, alpha=_alpha, label=_label, std = _ystd_i)
        if legend:
            _ax.legend()
        else:
            _legend = _ax.get_legend()
            if _legend is not None:
                _legend.remove()
        self._view.axMapPlot2.append(_ax)
        i+=1


def _plotMapFormat(self):
    #self._view.toolbarResizeMain1.triggered.disconnect()
    if self._view.axTopMap is None or self._view.axTopMap.xaxis.label._text == '':
        if self._view.axTopMap is not None:
            plotMapFormatReset(self)
        _x1 = self._view.workspace.wavelength
        _laser = self._view.workspace.laserWavelength
        _ax, self._view.axTopMap, self._view.axTopTopMap = generate_plots.formatWavelengthWavenumberMap(self._view, _x1, x_range = [50, 2098], laser=_laser)


def plotMapFormatReset(self):
    self._view.axTopMap.set_xticks([])
    self._view.axTopMap.set_xticklabels([])
    self._view.axTopMap.xaxis.set_minor_locator(plt.FixedLocator([]))
    self._view.axTopMap.set_xlabel('', fontsize=10)
    try:
        self._view.axTopMap.remove()
    except:
        pass


def _exportImageRGB(self):
    # dialog box to get filename
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    _rgbName, _ = QFileDialog.getSaveFileName(self._view,"Define ACI False Color Map File Name", "","All Files (*)", options = options)
    if not _rgbName.endswith('.png') or not _rgbName.endswith('.PNG'):
        _rgbName = _rgbName.split('.')[0]+'.png'

    log_parsing.log_info(self._view, 'Exporting ROI: {0}'.format(_rgbName))
    # save current image with annotations
    self._view.pixmapACIMap.save(_rgbName)
    log_parsing.log_info(self._view, 'Exported ROI: {0}'.format(_rgbName))
    _rgbGifName = _rgbName.replace('.png', '.gif')

    _pixmapACIMapSave = QPixmap(self._view.workspace.selectedACIFilename)
    _tmp_dir = os.path.join(self._view.workspace.workingDir, 'tmp')
    file_IO.mkdir(_tmp_dir)

    if self._view.imageArrayRGB is not None:
        _imgList = []
        for _i, opacity in enumerate(list(range(16))):
            _tmpImageSave = os.path.join(_tmp_dir, 'RGB_'+str(_i)+'.png')
            if self._view.RGBDiscrete.isChecked():
                _addDiscretePointsRGB(self, pixMapSave = _pixmapACIMapSave, customOpacity = opacity*3.3)
            else:
                _addInterpolatedPointsRGB(self, pixMapSave = _pixmapACIMapSave, customOpacity = opacity*3.3)
            # save image to tmp folder
            _pixmapACIMapSave.save(_tmpImageSave)
            _imgList.append(_tmpImageSave)
        # generate gif
        _imgList = _imgList + list(reversed(_imgList))
        generate_images.gif_from_pngs(_rgbGifName, _imgList)
        # clear tmp folder
        file_IO.rmFiles(_imgList)
        log_parsing.log_info(self._view, 'Exported ROI Animation: {0}'.format(_rgbGifName))

def _rescaleYMap1(self):
    # if some plots are not populated, this will raise an error (but can be safely ignored)
    try:
        generate_plots.autoscale_y(self._view.traceCanvasMapPlot1.axes[0], margin=0.1)
        generate_plots.autoscale_y(self._view.traceCanvasMapPlot1.axes[1], margin=0.1)
        generate_plots.autoscale_y(self._view.traceCanvasMapPlot1.axes[2], margin=0.1)
        self._view.traceCanvasMapPlot1.draw_idle()
    except:
        pass

def _rescaleYMap2(self):
    generate_plots.autoscale_y(self._view.traceCanvasMapPlot2.axes, margin=0.1)
    _plotMapUpdateBoxSelect(self)
    self._view.traceCanvasMapPlot2.draw_idle()
