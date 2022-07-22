import os
import sys

import PyQt5
# import QApplication and required widgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QSlider
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QRadioButton
from PyQt5.QtWidgets import QHBoxLayout # horizontal layout
from PyQt5.QtWidgets import QVBoxLayout # vertical layout
from PyQt5.QtWidgets import QGridLayout # grid layout
# from PyQt5.QtWidgets import QFormLayout # form layout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QScrollArea
from PyQt5.QtWidgets import QSpacerItem
from PyQt5.QtWidgets import QSizePolicy

from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT


from src import MPL_plots
from src import image_viewer



###################################################
###################################################
#  FALSE COLOR Left Panel
###################################################
###################################################
def _addFalseColorLeftPanel(self):
    # define grid layout for labels and lists
    mapLeftScrollContainer = QScrollArea()
    mapLeftScrollContainer.setFixedWidth(300)
    mapLeftScrollContainer.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
    mapLeftScrollContainer.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    mapLeftScrollContainer.setWidgetResizable(True)

    mapLeftWidgetContainer = QWidget()
    mapLeftScrollContainer.setWidget(mapLeftWidgetContainer)
    mapLeftLayout = QGridLayout(mapLeftWidgetContainer)

    # workspace
    _workspaceLabelWidget = QWidget()
    gridMode = QGridLayout()
    _workspaceLabelWidget.setLayout(gridMode)
    self.workspaceLabelMap = QLabel()
    self.workspaceLabelMap.setText('Workspace: {0}'.format(self.workspace.humanReadableName))
    gridMode.addWidget(self.workspaceLabelMap)
    mapLeftLayout.addWidget(_workspaceLabelWidget)


    # spectrum groupbox:
    self.groupboxSpectrumRGB = QGroupBox('Spectrum Configuration')
    vboxModeSpec = QVBoxLayout()
    self.groupboxSpectrumRGB.setLayout(vboxModeSpec)

    # Region Selection
    self.groupboxRegionsRGB = QGroupBox('SCCD Region Selection')
    #groupbox.setCheckable(True)
    hboxRegion = QHBoxLayout()
    self.groupboxRegionsRGB.setLayout(hboxRegion)
    self.R1ItemRGB = QCheckBox('R1')
    hboxRegion.addWidget(self.R1ItemRGB)
    self.R2ItemRGB = QCheckBox('R2')
    hboxRegion.addWidget(self.R2ItemRGB)
    self.R3ItemRGB = QCheckBox('R3')
    hboxRegion.addWidget(self.R3ItemRGB)
    self.allItemRGB = QCheckBox('all')
    hboxRegion.addWidget(self.allItemRGB)
    self.groupboxRegionsRGB.setDisabled(True)
    self.R1ItemRGB.setChecked(True)
    self.R2ItemRGB.setChecked(True)
    self.R3ItemRGB.setChecked(True)
    self.allItemRGB.setChecked(False)
    self.groupboxRegionsRGB.setMaximumHeight(68)
    vboxModeSpec.addWidget(self.groupboxRegionsRGB)

    # Spectrum Display
    self.groupboxDisplayTypeRGB = QGroupBox('Select Display Type')
    #groupbox.setCheckable(True)
    vboxMode = QVBoxLayout()
    self.groupboxDisplayTypeRGB.setLayout(vboxMode)
    self.meanDisplayRGB = QRadioButton('Mean')
    vboxMode.addWidget(self.meanDisplayRGB)
    self.medianDisplayRGB = QRadioButton('Median')
    vboxMode.addWidget(self.medianDisplayRGB)
    self.indexDisplayRGB = QRadioButton('Spectrum Index')
    vboxMode.addWidget(self.indexDisplayRGB)
    self.indexSpecRGB = QLineEdit()
    self.indexSpecRGB.setPlaceholderText('Index: 1, 4:10, 15')
    vboxMode.addWidget(self.indexSpecRGB)
    self.groupboxDisplayTypeRGB.setDisabled(True)
    self.meanDisplayRGB.setChecked(True)
    vboxModeSpec.addWidget(self.groupboxDisplayTypeRGB)

    self.groupboxROIRGB = QGroupBox('ROI Selection: ')
    self.vboxRoiRGB = QVBoxLayout()
    self.groupboxROIRGB.setLayout(self.vboxRoiRGB)
    for _roiName in self.workspace.roiNames:
        _roiDictKey = self.workspace.roiHumanToDictKey[_roiName]
        if self.roiDict[_roiDictKey].checkboxWidgetRoi is None:
            _checkboxRoi = QCheckBox(self.roiDict[_roiDictKey].humanReadableName)
            self.roiDict[_roiDictKey].checkboxWidgetRoi = _checkboxRoi
        self.vboxRoiRGB.addWidget(self.roiDict[_roiDictKey].checkboxWidgetRoi)
        if len(self.roiDict) < 2:
            _checkboxRoi.setDisabled(True)
        else:
            _checkboxRoi.setDisabled(False)
    vboxModeSpec.addWidget(self.groupboxROIRGB)


    self.groupboxRGBSelection = QGroupBox('RGB Selection: ')
    self.gridRGBSelection = QGridLayout()
    self.groupboxRGBSelection.setLayout(self.gridRGBSelection)
    self.redCheckRGB = QCheckBox('Red')
    self.redCheckRGB.setChecked(False)
    self.gridRGBSelection.addWidget(self.redCheckRGB, 0,0,1,1)
    self.redPosRGB = QLineEdit()
    self.redPosRGB.setPlaceholderText('Center')
    self.gridRGBSelection.addWidget(self.redPosRGB, 0,1,1,1)
    self.redWidthRGB = QLineEdit()
    self.redWidthRGB.setPlaceholderText('Width')
    self.gridRGBSelection.addWidget(self.redWidthRGB, 0,2,1,1)

    self.greenCheckRGB = QCheckBox('Green')
    self.greenCheckRGB.setChecked(False)
    self.gridRGBSelection.addWidget(self.greenCheckRGB, 1,0,1,1)
    self.greenPosRGB = QLineEdit()
    self.greenPosRGB.setPlaceholderText('Center')
    self.gridRGBSelection.addWidget(self.greenPosRGB, 1,1,1,1)
    self.greenWidthRGB = QLineEdit()
    self.greenWidthRGB.setPlaceholderText('Width')
    self.gridRGBSelection.addWidget(self.greenWidthRGB, 1,2,1,1)

    self.blueCheckRGB = QCheckBox('Blue')
    self.blueCheckRGB.setChecked(False)
    self.gridRGBSelection.addWidget(self.blueCheckRGB, 2,0,1,1)
    self.bluePosRGB = QLineEdit()
    self.bluePosRGB.setPlaceholderText('Center')
    self.gridRGBSelection.addWidget(self.bluePosRGB, 2,1,1,1)
    self.blueWidthRGB = QLineEdit()
    self.blueWidthRGB.setPlaceholderText('Width')
    self.groupboxRGBSelection.setDisabled(True)
    self.gridRGBSelection.addWidget(self.blueWidthRGB, 2,2,1,1)

    vboxModeSpec.addWidget(self.groupboxRGBSelection)


    # not displayed:
    self.redHistHighRGB = QLineEdit()
    self.redHistLowRGB = QLineEdit()
    self.greenHistHighRGB = QLineEdit()
    self.greenHistLowRGB = QLineEdit()
    self.blueHistHighRGB = QLineEdit()
    self.blueHistLowRGB = QLineEdit()


    mapLeftLayout.addWidget(self.groupboxSpectrumRGB)
    self.groupboxDisplayTypeRGB.setMaximumHeight(135)


    # image groupbox:
    self.groupboxImageRGB = QGroupBox('Image Configuration')
    gboxMode = QGridLayout()
    self.groupboxImageRGB.setLayout(gboxMode)
    _laserMapImgLabel = QLabel()
    _laserMapImgLabel.setText('Select ACI Image')
    gboxMode.addWidget(_laserMapImgLabel, 0, 0, 1, 3)
    # ACI file select dropdown
    if self.workspace.selectedACIFilename is None:
        self.selectedACIComboRGB = QComboBox()
    else:
        self.selectedACIComboRGB = QComboBox(self.workspace.selectedACIFilename)
    self.selectedACIComboRGB.setFixedHeight(30)
    self.selectedACIComboRGB.setMinimumWidth(50)
    gboxMode.addWidget(self.selectedACIComboRGB, 0, 3, 1, 7)
    self.selectedACIComboRGB.setMaximumHeight(100)

    # image opacity
    _OpacityLabel = QLabel()
    _OpacityLabel.setText('Image Opacity')
    gboxMode.addWidget(_OpacityLabel, 1, 0, 1, 2)
    self.opacityACIRGB = QSlider(Qt.Horizontal)
    self.opacityACIRGB.setMinimum(0)
    self.opacityACIRGB.setMaximum(100)
    self.opacityACIRGB.setValue(100)
    gboxMode.addWidget(self.opacityACIRGB, 1, 2, 1, 8)

    # RGB map opacity
    _OpacityLabel = QLabel()
    _OpacityLabel.setText('Map Opacity')
    gboxMode.addWidget(_OpacityLabel, 2, 0, 1, 2)
    self.opacityMapRGB = QSlider(Qt.Horizontal)
    self.opacityMapRGB.setMinimum(0)
    self.opacityMapRGB.setMaximum(100)
    self.opacityMapRGB.setValue(100)
    gboxMode.addWidget(self.opacityMapRGB, 2, 2, 1, 8)

    # toggle between spots and integrated map
    self.groupboxImageModeRGB = QGroupBox('RGB Map Display Mode')
    hboxMode = QVBoxLayout()
    self.groupboxImageModeRGB.setLayout(hboxMode)
    self.RGBDiscrete = QRadioButton('Discrete Points')
    hboxMode.addWidget(self.RGBDiscrete)
    self.RGBInterpolatedNearest = QRadioButton('Interpolated - Nearest')
    hboxMode.addWidget(self.RGBInterpolatedNearest)
    self.RGBInterpolatedCubic = QRadioButton('Interpolated - Cubic')
    hboxMode.addWidget(self.RGBInterpolatedCubic)
    self.RGBInterpolatedNearest.setChecked(True)
    self.opacityMapRGB.setEnabled(False)
    self.opacityACIRGB.setEnabled(False)
    self.groupboxImageModeRGB.setEnabled(False)
    gboxMode.addWidget(self.groupboxImageModeRGB, 3, 0, 1, 10)

    # toggle between spots and integrated map
    self.groupboxImageInterpolationRGB = QGroupBox('RGB Map Selection Type')
    hboxMode = QVBoxLayout()
    self.groupboxImageInterpolationRGB.setLayout(hboxMode)
    self.RGBMax = QRadioButton('Maximum')
    hboxMode.addWidget(self.RGBMax)
    self.RGBMedian = QRadioButton('Median')
    hboxMode.addWidget(self.RGBMedian)
    self.RGBMean = QRadioButton('Mean')
    hboxMode.addWidget(self.RGBMean)
    self.RGBIntegratedIntensity = QRadioButton('Integrated Intensity')
    hboxMode.addWidget(self.RGBIntegratedIntensity)
    self.RGBIntegratedIntensity.setChecked(True)
    self.groupboxImageInterpolationRGB.setEnabled(False)
    gboxMode.addWidget(self.groupboxImageInterpolationRGB, 4, 0, 1, 10)

    self.RGBExportButton = QPushButton()
    self.RGBExportButton.setText('Export RGB Map')
    self.RGBExportButton.setEnabled(False)
    gboxMode.addWidget(self.RGBExportButton, 5, 0, 1, 4)

    self.groupboxImageRGB.setEnabled(False)

    mapLeftLayout.addWidget(self.groupboxImageRGB)


    mapLeftLayout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
    self.LoupeViewRGBTabLayout.addWidget(mapLeftScrollContainer)


###################################################
###################################################
#  FALSE COLOR Central Panel
###################################################
###################################################

def _addFalseColorCenterPanel(self):
    # ACI / false color map overlay
    _vertScaleIconPath = self._appctxt.get_resource('rescale_vertical_40px.png')
    mapPlotLayout = QGridLayout()

    imageWidget = QWidget()
    imageLayout = QHBoxLayout(imageWidget)
    imageLayout.setContentsMargins(0, 0, 0, 0)

    img1_dir = self._appctxt.get_resource('ACI_placeholder.png')
    self.pixmapACIMap = QPixmap(img1_dir)
    self.pixmapACIMap = self.pixmapACIMap.scaledToWidth(0.90*imageWidget.width())

    self.imageACIMap = image_viewer.imageViewer(self)
    self.imageACIMap.setMinimumHeight(420)
    self.imageACIMap.setPhoto(pixmap = self.pixmapACIMap, zoomSelect=1)

    imageLayout.addWidget(self.imageACIMap)
    # row, col, row span, col span
    mapPlotLayout.addWidget(imageWidget, 0, 0, 2, 1)


    # RGB histogram plot
    self.traceCanvasMapPlot1 = MPL_plots.MplCanvas(self, width=5, height=4, dpi=100, subplots=3)
    self.traceCanvasMapPlot1.axes[0].plot([0], [0])
    self.traceCanvasMapPlot1.axes[1].plot([0], [0])
    self.traceCanvasMapPlot1.axes[2].plot([0], [0])

    # list of axes in the plot
    self.axMapPlot1 = []

    # Create toolbar, passing canvas as first parameter, parent (self, the MainWindow) as second.
    self.toolbarMapPlot1 = NavigationToolbar2QT(self.traceCanvasMapPlot1, self)
    self.toolbarMapPlot1.setMaximumHeight(25)
    self.toolbarResizeMap1 = QAction(QIcon(_vertScaleIconPath), 'Autoscale vertical axis', self.toolbarMapPlot1)
    self.toolbarMapPlot1.insertAction(self.toolbarMapPlot1.actions()[5], self.toolbarResizeMap1)
    self.toolbarMapPlot1.removeAction(self.toolbarMapPlot1.actions()[7])
    self.toolbarMapPlot1.setStyleSheet("QToolBar { border: 0px }")

    mapPlotLayout.addWidget(self.toolbarMapPlot1, 0, 1, 1, 1)
    mapPlotLayout.addWidget(self.traceCanvasMapPlot1, 1, 1, 1, 1)


    # spectrum selection plot
    self.traceCanvasMapPlot2 = MPL_plots.MplCanvas(self, width=5, height=4, dpi=100)
    self.traceCanvasMapPlot2.axes.plot([0], [0])

    # list of axes in the plot
    self.axMapPlot2 = []

    # Create toolbar, passing canvas as first parameter, parent (self, the MainWindow) as second.
    self.toolbarMapPlot2 = NavigationToolbar2QT(self.traceCanvasMapPlot2, self)
    self.toolbarMapPlot2.setMaximumHeight(25)
    self.toolbarResizeMap2 = QAction(QIcon(_vertScaleIconPath), 'Autoscale vertical axis', self.toolbarMapPlot2)
    self.toolbarMapPlot2.insertAction(self.toolbarMapPlot2.actions()[5], self.toolbarResizeMap2)
    self.toolbarMapPlot2.removeAction(self.toolbarMapPlot2.actions()[7])
    self.toolbarMapPlot2.setStyleSheet("QToolBar { border: 0px }")

    mapPlotLayout.addWidget(self.toolbarMapPlot2, 2, 0, 1, 2)
    mapPlotLayout.addWidget(self.traceCanvasMapPlot2, 3, 0, 1, 2)


    #mapPlotLayout.addStretch()
    self.LoupeViewRGBTabLayout.addLayout(mapPlotLayout, 0, 3, 4, 7)

