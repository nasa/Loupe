import os
import sys

import PyQt5
# import QApplication and required widgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QProgressBar
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QScrollBar
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QRadioButton
from PyQt5.QtWidgets import QHBoxLayout # horizontal layout
from PyQt5.QtWidgets import QVBoxLayout # vertical layout
from PyQt5.QtWidgets import QGridLayout # grid layout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QScrollArea
from PyQt5.QtWidgets import QSpacerItem
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QFrame

from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT


from src import log_parsing
from src import MPL_plots
from src import file_IO
from src import workspace_class
from src import roi_class
from src import image_viewer
from src import QScrollAreaImage

###################################################
###################################################
#  COSMIC RAY REMOVAL Left Panel
###################################################
###################################################
def _addCosmicLeftPanel(self):
    # define grid layout for labels and lists
    cosmicLeftScrollContainer = QScrollArea()
    cosmicLeftScrollContainer.setFixedWidth(300)
    cosmicLeftScrollContainer.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
    cosmicLeftScrollContainer.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    cosmicLeftScrollContainer.setWidgetResizable(True)

    cosmicLeftWidgetContainer = QWidget()
    cosmicLeftScrollContainer.setWidget(cosmicLeftWidgetContainer)
    #cosmicLeftLayout = QGridLayout(cosmicLeftWidgetContainer)
    cosmicLeftLayout = QVBoxLayout(cosmicLeftWidgetContainer)

    # workspace
    _workspaceLabelWidget = QWidget()
    gridMode = QGridLayout()
    _workspaceLabelWidget.setLayout(gridMode)
    self.workspaceLabelCosmic = QLabel()
    self.workspaceLabelCosmic.setText('Workspace: {0}'.format(self.workspace.humanReadableName))
    gridMode.addWidget(self.workspaceLabelCosmic)
    cosmicLeftLayout.addWidget(_workspaceLabelWidget)


    # histogram groupbox:
    self.groupboxHistogramCosmic = QGroupBox('Histogram Display')
    vboxModeSpec = QVBoxLayout()
    self.groupboxHistogramCosmic.setLayout(vboxModeSpec)

    # Region Selection
    self.groupboxRegionsHistCosmic = QGroupBox('SCCD Region Selection')
    #groupbox.setCheckable(True)
    hboxRegion = QHBoxLayout()
    self.groupboxRegionsHistCosmic.setLayout(hboxRegion)
    self.R1ItemHistCosmic = QRadioButton('R1')
    hboxRegion.addWidget(self.R1ItemHistCosmic)
    self.R2ItemHistCosmic = QRadioButton('R2')
    hboxRegion.addWidget(self.R2ItemHistCosmic)
    self.R3ItemHistCosmic = QRadioButton('R3')
    hboxRegion.addWidget(self.R3ItemHistCosmic)
    self.R1ItemHistCosmic.setChecked(True)
    self.R2ItemHistCosmic.setChecked(False)
    self.R3ItemHistCosmic.setChecked(False)
    self.groupboxRegionsHistCosmic.setMaximumHeight(68)
    vboxModeSpec.addWidget(self.groupboxRegionsHistCosmic)

    # active, dark selection
    self.groupboxModeHistCosmic = QGroupBox('Select Mode')
    vboxMode = QHBoxLayout()
    self.groupboxModeHistCosmic.setLayout(vboxMode)
    self.activeItemHistCosmic = QRadioButton('Active')
    vboxMode.addWidget(self.activeItemHistCosmic)
    self.darkItemHistCosmic = QRadioButton('Dark')
    vboxMode.addWidget(self.darkItemHistCosmic)
    self.groupboxModeHistCosmic.setMaximumHeight(100)
    self.activeItemHistCosmic.setChecked(True)
    vboxModeSpec.addWidget(self.groupboxModeHistCosmic)


    # channel selection
    self.groupboxChannelCosmic = QGroupBox('Select Channel Index')
    #groupbox.setCheckable(True)
    vboxMode = QGridLayout()
    self.groupboxChannelCosmic.setLayout(vboxMode)

    _labelChannelDisplayCosmic = QLabel('Channel Index:')
    vboxMode.addWidget(_labelChannelDisplayCosmic, 0, 0, 1, 6)
    self.indexChannelCosmic = QLineEdit()
    self.indexChannelCosmic.setText('0')
    self.indexChannelCosmic.setMaximumWidth(60)
    vboxMode.addWidget(self.indexChannelCosmic, 0, 7, 1, 2)
    self.selectionScrollbarChannelCosmic = QScrollBar(Qt.Horizontal)
    self.selectionScrollbarChannelCosmic.setMinimum(0)
    self.selectionScrollbarChannelCosmic.setMaximum(1)
    self.selectionScrollbarChannelCosmic.setValue(100)
    vboxMode.addWidget(self.selectionScrollbarChannelCosmic, 1, 0, 1, 9)

    vboxModeSpec.addWidget(self.groupboxChannelCosmic)
    #self.groupboxChannelCosmic.setMaximumHeight(1575)

    self.groupboxHistogramCosmic.setEnabled(False)
    cosmicLeftLayout.addWidget(self.groupboxHistogramCosmic)



    # spectrum groupbox:
    self.groupboxSpectrumCosmic = QGroupBox('Spectrum Display')
    vboxModeSpec = QVBoxLayout()
    self.groupboxSpectrumCosmic.setLayout(vboxModeSpec)

    # Region Selection
    self.groupboxRegionsCosmic = QGroupBox('SCCD Region Selection')
    #groupbox.setCheckable(True)
    hboxRegion = QHBoxLayout()
    self.groupboxRegionsCosmic.setLayout(hboxRegion)
    self.R1ItemCosmic = QCheckBox('R1')
    hboxRegion.addWidget(self.R1ItemCosmic)
    self.R2ItemCosmic = QCheckBox('R2')
    hboxRegion.addWidget(self.R2ItemCosmic)
    self.R3ItemCosmic = QCheckBox('R3')
    hboxRegion.addWidget(self.R3ItemCosmic)
    self.allItemCosmic = QCheckBox('all')
    hboxRegion.addWidget(self.allItemCosmic)
    self.R1ItemCosmic.setChecked(True)
    self.R2ItemCosmic.setChecked(True)
    self.R3ItemCosmic.setChecked(True)
    self.allItemCosmic.setChecked(False)
    self.groupboxRegionsCosmic.setMaximumHeight(68)
    vboxModeSpec.addWidget(self.groupboxRegionsCosmic)

    # active, dark, active-dark
    self.groupboxModeCosmic = QGroupBox('Select Mode')
    vboxMode = QVBoxLayout()
    self.groupboxModeCosmic.setLayout(vboxMode)
    self.activeItemCosmic = QRadioButton('Active')
    vboxMode.addWidget(self.activeItemCosmic)
    self.darkItemCosmic = QRadioButton('Dark')
    vboxMode.addWidget(self.darkItemCosmic)
    self.darkSubItemCosmic = QRadioButton('Active - Dark')
    vboxMode.addWidget(self.darkSubItemCosmic)
    self.groupboxModeCosmic.setMaximumHeight(100)
    vboxModeSpec.addWidget(self.groupboxModeCosmic)

    # Spectrum Display
    self.groupboxDisplayTypeCosmic = QGroupBox('Select Display Type')
    #groupbox.setCheckable(True)
    vboxMode = QGridLayout()
    self.groupboxDisplayTypeCosmic.setLayout(vboxMode)
    self.meanDisplayCosmic = QRadioButton('Mean')
    vboxMode.addWidget(self.meanDisplayCosmic, 0, 0, 1, 6)
    self.meanStdDisplayCosmic = QCheckBox('+/- 1 SD')
    self.meanStdDisplayCosmic.setChecked(False)
    vboxMode.addWidget(self.meanStdDisplayCosmic, 0, 7, 1, 2)
    self.medianDisplayCosmic = QRadioButton('Median')
    self.medianDisplayCosmic.setChecked(False)
    vboxMode.addWidget(self.medianDisplayCosmic, 1, 0, 1, 6)
    self.medianStdDisplayCosmic = QCheckBox('+/- 1 SD')
    self.medianStdDisplayCosmic.setChecked(False)
    vboxMode.addWidget(self.medianStdDisplayCosmic, 1, 7, 1, 2)
    self.maxDisplayCosmic = QRadioButton('Max')
    vboxMode.addWidget(self.maxDisplayCosmic, 2, 0, 1, 9)
    self.minDisplayCosmic = QRadioButton('Min')
    vboxMode.addWidget(self.minDisplayCosmic, 3, 0, 1, 9)
    self.indexDisplayCosmic = QRadioButton('Spectrum Index')
    vboxMode.addWidget(self.indexDisplayCosmic, 4, 0, 1, 6)
    self.indexSpecCosmic = QLineEdit()
    self.indexSpecCosmic.setPlaceholderText('0')
    self.indexSpecCosmic.setMaximumWidth(60)
    #self.indexSpecCosmic.setMaximumWidth(40)
    vboxMode.addWidget(self.indexSpecCosmic, 4, 7, 1, 2)
    self.selectionScrollbarCosmic = QScrollBar(Qt.Horizontal)
    self.selectionScrollbarCosmic.setMinimum(0)
    self.selectionScrollbarCosmic.setMaximum(1)
    self.selectionScrollbarCosmic.setValue(0)
    vboxMode.addWidget(self.selectionScrollbarCosmic, 5, 0, 1, 9)

    self.meanDisplayCosmic.setChecked(True)
    vboxModeSpec.addWidget(self.groupboxDisplayTypeCosmic)
    self.groupboxDisplayTypeCosmic.setMaximumHeight(1575)

    # Domain selection
    self.groupboxDomainTypeCosmic = QGroupBox('Select Domain Mode')
    vboxMode = QVBoxLayout()
    self.groupboxDomainTypeCosmic.setLayout(vboxMode)
    self.waveDomainCosmic = QRadioButton('Wavelength')
    vboxMode.addWidget(self.waveDomainCosmic)
    self.ccdDomainCosmic = QRadioButton('CCD Pixel')
    vboxMode.addWidget(self.ccdDomainCosmic)
    self.groupboxDomainTypeCosmic.setDisabled(True)
    self.waveDomainCosmic.setChecked(True)
    vboxModeSpec.addWidget(self.groupboxDomainTypeCosmic)
    self.groupboxDomainTypeCosmic.setMaximumHeight(80)

    self.groupboxROICosmic = QGroupBox('ROI Selection: ')
    self.vboxRoiCosmic = QVBoxLayout()
    self.groupboxROICosmic.setLayout(self.vboxRoiCosmic)
    for _roiName in self.workspace.roiNames:
        _roiDictKey = self.workspace.roiHumanToDictKey[_roiName]
        if self.roiDict[_roiDictKey].checkboxWidgetCosmic is None:
            _checkboxCosmic = QCheckBox(self.roiDict[_roiDictKey].humanReadableName)
            self.roiDict[_roiDictKey].checkboxWidgetCosmic = _checkboxCosmic
        self.vboxRoiCosmic.addWidget(self.roiDict[_roiDictKey].checkboxWidgetCosmic)
        if len(self.roiDict) < 2:
            _checkboxCosmic.setDisabled(True)
        else:
            _checkboxCosmic.setDisabled(False)
    vboxModeSpec.addWidget(self.groupboxROICosmic)
    # TODO: enable this eventually, if ROIs should be included on this tab
    self.groupboxROICosmic.setEnabled(False)
    self.groupboxSpectrumCosmic.setEnabled(False)

    cosmicLeftLayout.addWidget(self.groupboxSpectrumCosmic)



    # algorithm groupbox:
    self.groupboxCosmicAlgorithm = QGroupBox('Automated Cosmic Ray Removal')
    gridAlgorithmParms = QGridLayout()
    self.groupboxCosmicAlgorithm.setLayout(gridAlgorithmParms)
    _labelThreshold = QLabel()
    _labelThreshold.setText('Threshold Multiplier:')
    gridAlgorithmParms.addWidget(_labelThreshold, 0, 0, 1, 6)
    #hspacer = QSpacerItem(QSizePolicy.Expanding, QSizePolicy.Minimum)
    #gridAlgorithmParms.addItem(hspacer, 0, 6, 1, 2)
    self.cosmicRayThreshold = QLineEdit()
    self.cosmicRayThreshold.setText('10')
    self.cosmicRayThreshold.setMaximumWidth(60)
    gridAlgorithmParms.addWidget(self.cosmicRayThreshold, 0, 8, 1, 1)

    _labelSigma = QLabel()
    _labelSigma.setText('Sigma Clipping:')
    gridAlgorithmParms.addWidget(_labelSigma, 1, 0, 1, 6)
    self.cosmicRaySigma = QLineEdit()
    self.cosmicRaySigma.setText('4')
    self.cosmicRaySigma.setMaximumWidth(60)
    gridAlgorithmParms.addWidget(self.cosmicRaySigma, 1, 8, 1, 1)

    _labelMax = QLabel()
    _labelMax.setText('Max CRs in Spectrum:')
    gridAlgorithmParms.addWidget(_labelMax, 2, 0, 1, 6)
    self.cosmicRayMaxCRs = QLineEdit()
    self.cosmicRayMaxCRs.setText('20')
    self.cosmicRayMaxCRs.setMaximumWidth(60)
    gridAlgorithmParms.addWidget(self.cosmicRayMaxCRs, 2, 8, 1, 1)

    _labelWavelength = QLabel()
    _labelWavelength.setText('Wavelength Range:')
    gridAlgorithmParms.addWidget(_labelWavelength, 3, 0, 1, 6)
    self.cosmicRayWavelengthRange = QLineEdit()
    self.cosmicRayWavelengthRange.setPlaceholderText('250-360')
    self.cosmicRayWavelengthRange.setMaximumWidth(110)
    gridAlgorithmParms.addWidget(self.cosmicRayWavelengthRange, 3, 8, 1, 1)

    _labelReplace = QLabel()
    _labelReplace.setText('Replace:')
    gridAlgorithmParms.addWidget(_labelReplace, 4, 0, 1, 3)
    self.cosmicRayReplacementAvg = QRadioButton('Average')
    gridAlgorithmParms.addWidget(self.cosmicRayReplacementAvg, 4, 3, 1, 3)
    self.cosmicRayReplacementInterpol = QRadioButton('Interpolate')
    self.cosmicRayReplacementInterpol.setChecked(True)
    gridAlgorithmParms.addWidget(self.cosmicRayReplacementInterpol, 4, 6, 1, 3)

    _labelWidth = QLabel()
    _labelWidth.setText('CR Width (pixels):')
    gridAlgorithmParms.addWidget(_labelWidth, 5, 0, 1, 6)
    self.cosmicRayWidth = QLineEdit()
    self.cosmicRayWidth.setText('3')
    self.cosmicRayWidth.setMaximumWidth(60)
    gridAlgorithmParms.addWidget(self.cosmicRayWidth, 5, 8, 1, 1)

    self.executeCosmicRay = QPushButton()
    self.executeCosmicRay.setText('Automated Cosmic Ray Removal')
    self.executeCosmicRay.setEnabled(True)
    gridAlgorithmParms.addWidget(self.executeCosmicRay, 6, 0, 1, 9)
    self.cosmicProgressBar = QProgressBar(self)
    self.cosmicProgressBar.setValue(0)
    gridAlgorithmParms.addWidget(self.cosmicProgressBar, 7, 0, 1, 9)


    self.groupboxCosmicAlgorithm.setEnabled(False)
    cosmicLeftLayout.addWidget(self.groupboxCosmicAlgorithm)


    self.groupboxCosmicManual = QGroupBox('Manual Cosmic Ray Removal')
    gridManualParms = QGridLayout()
    self.groupboxCosmicManual.setLayout(gridManualParms)

    self.groupboxCosmicManualRegions = QGroupBox('Region Selection')
    gridManualParmsRegions = QHBoxLayout()
    self.groupboxCosmicManualRegions.setLayout(gridManualParmsRegions)
    self.R1ItemCosmicManual = QRadioButton('R1')
    gridManualParmsRegions.addWidget(self.R1ItemCosmicManual)
    self.R2ItemCosmicManual = QRadioButton('R2')
    gridManualParmsRegions.addWidget(self.R2ItemCosmicManual)
    self.R3ItemCosmicManual = QRadioButton('R3')
    gridManualParmsRegions.addWidget(self.R3ItemCosmicManual)
    self.R1ItemCosmicManual.setChecked(True)
    gridManualParms.addWidget(self.groupboxCosmicManualRegions, 0, 0, 1, 9)


    self.groupboxCosmicManualReplacement = QGroupBox('Replacement Method')
    gridManualParmsReplacement = QHBoxLayout()
    self.groupboxCosmicManualReplacement.setLayout(gridManualParmsReplacement)
    self.cosmicRayReplacementManualAvg = QRadioButton('Average')
    gridManualParmsReplacement.addWidget(self.cosmicRayReplacementManualAvg)
    self.cosmicRayReplacementManualInterpol = QRadioButton('Interpolate')
    self.cosmicRayReplacementManualInterpol.setChecked(True)
    gridManualParmsReplacement.addWidget(self.cosmicRayReplacementManualInterpol)
    gridManualParms.addWidget(self.groupboxCosmicManualReplacement, 1, 0, 1, 9)

    _labelWidthManual = QLabel()
    _labelWidthManual.setText('CR Width (pixels):')
    gridManualParms.addWidget(_labelWidthManual, 2, 0, 1, 6)
    self.cosmicRayManualWidth = QLineEdit()
    self.cosmicRayManualWidth.setText('3')
    self.cosmicRayManualWidth.setMaximumWidth(60)
    gridManualParms.addWidget(self.cosmicRayManualWidth, 2, 8, 1, 1)

    _labelSpecManual = QLabel()
    _labelSpecManual.setText('Spectrum Selected:')
    gridManualParms.addWidget(_labelSpecManual, 3, 0, 1, 6)
    self.cosmicRayManualSpec = QLineEdit()
    self.cosmicRayManualSpec.setText('0')
    self.cosmicRayManualSpec.setMaximumWidth(60)
    gridManualParms.addWidget(self.cosmicRayManualSpec, 3, 8, 1, 1)

    _labelWavelengthManual = QLabel()
    _labelWavelengthManual.setText('Wavelength Selected:')
    gridManualParms.addWidget(_labelWavelengthManual, 4, 0, 1, 6)
    self.cosmicRayManualWavelength = QLineEdit()
    self.cosmicRayManualWavelength.setText('')
    self.cosmicRayManualWavelength.setMaximumWidth(60)
    gridManualParms.addWidget(self.cosmicRayManualWavelength, 4, 8, 1, 1)

    _labelChannelManual = QLabel()
    _labelChannelManual .setText('Channel Selected:')
    gridManualParms.addWidget(_labelChannelManual , 5, 0, 1, 6)
    self.cosmicRayManualChannel = QLineEdit()
    self.cosmicRayManualChannel.setText('')
    self.cosmicRayManualChannel.setMaximumWidth(60)
    gridManualParms.addWidget(self.cosmicRayManualChannel, 5, 8, 1, 1)


    self.executeCosmicRaySelect = QPushButton()
    self.executeCosmicRaySelect.setText('Select CR')
    self.executeCosmicRaySelect.setEnabled(False)
    gridManualParms.addWidget(self.executeCosmicRaySelect, 6, 0, 1, 5)
    self.executeCosmicRayManual = QPushButton()
    self.executeCosmicRayManual.setText('Replace CR')
    self.executeCosmicRayManual.setEnabled(False)
    gridManualParms.addWidget(self.executeCosmicRayManual, 6, 5, 1, 4)

    self.groupboxCosmicManual.setEnabled(False)
    cosmicLeftLayout.addWidget(self.groupboxCosmicManual)

    self.saveCosmicRaySpec = QPushButton()
    self.saveCosmicRaySpec.setText('Save Cosmic Ray-Removed Spectra')
    self.saveCosmicRaySpec.setEnabled(False)
    cosmicLeftLayout.addWidget(self.saveCosmicRaySpec)

    self.resetCosmicRaySpec = QPushButton()
    self.resetCosmicRaySpec.setText('Reset Cosmic Ray Processing')
    self.resetCosmicRaySpec.setEnabled(False)
    cosmicLeftLayout.addWidget(self.resetCosmicRaySpec)

    cosmicLeftLayout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
    self.LoupeViewCosmicTabLayout.addWidget(cosmicLeftScrollContainer)


###################################################
###################################################
#  COSMIC RAY REMOVAL Plot Panel
###################################################
###################################################
def _addCosmicCenterPanel(self):
    #_container = QWidget()
    #_container.setStyleSheet("background-color:black;")
    cosmicPlotLayout = QVBoxLayout()
    _vertScaleIconPath = self._appctxt.get_resource('rescale_vertical_40px.png')


    # cosmic (mean, median, max) plot widget
    self.traceCanvasCosmicPlot1 = MPL_plots.MplCanvas(self, width=5, height=4, dpi=100)
    self.traceCanvasCosmicPlot1.axes.plot([0], [0])

    # list of axes in the plot
    self.axCosmicPlot1 = []

    # Create toolbar, passing canvas as first parameter, parent (self, the CosmicWindow) as second.
    self.toolbarCosmicPlot1 = NavigationToolbar2QT(self.traceCanvasCosmicPlot1, self)
    self.toolbarCosmicPlot1.setMaximumHeight(25)
    self.toolbarResizeCosmic1 = QAction(QIcon(_vertScaleIconPath), 'Autoscale vertical axis', self.toolbarCosmicPlot1)
    self.toolbarCosmicPlot1.insertAction(self.toolbarCosmicPlot1.actions()[5], self.toolbarResizeCosmic1)
    self.toolbarCosmicPlot1.removeAction(self.toolbarCosmicPlot1.actions()[7])
    self.toolbarCosmicPlot1.setStyleSheet("QToolBar { border: 0px }")

    cosmicPlotLayout.addWidget(self.toolbarCosmicPlot1)
    cosmicPlotLayout.addWidget(self.traceCanvasCosmicPlot1)


    self._hLineCosmic = QFrame()
    self._hLineCosmic.setFrameShape(QFrame.HLine)
    #_hLine.setFrameShadow(QFrame.Raised)
    self._hLineCosmic.setLineWidth(100)
    #_hLine.setMinimumHeight(5)
    self._hLineCosmic.setStyleSheet("color: #a6a6a6;")
    cosmicPlotLayout.addWidget(self._hLineCosmic)


    # selection (or all) plot widget
    self.traceCanvasCosmicPlot2 = MPL_plots.MplCanvas(self, width=5, height=4, dpi=100)
    self.traceCanvasCosmicPlot2.axes.plot([0], [0])

    # list of axes in the plot
    self.axCosmicPlot2 = []

    # Create toolbar, passing canvas as first parameter, parent (self, the CosmicWindow) as second.
    self.toolbarCosmicPlot2 = NavigationToolbar2QT(self.traceCanvasCosmicPlot2, self)
    self.toolbarCosmicPlot2.setMaximumHeight(25)
    self.toolbarResizeCosmic2 = QAction(QIcon(_vertScaleIconPath), 'Autoscale vertical axis', self.toolbarCosmicPlot2)
    self.toolbarCosmicPlot2.insertAction(self.toolbarCosmicPlot2.actions()[5], self.toolbarResizeCosmic2)
    self.toolbarCosmicPlot2.removeAction(self.toolbarCosmicPlot2.actions()[7])
    self.toolbarCosmicPlot2.setStyleSheet("QToolBar { border: 0px }")

    cosmicPlotLayout.addWidget(self.toolbarCosmicPlot2)
    cosmicPlotLayout.addWidget(self.traceCanvasCosmicPlot2)


    #cosmicPlotLayout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
    #cosmicPlotLayout.addStretch()
    # Add the display to the Cosmic tab layout
    # row, column, rowspan, colspan
    self.LoupeViewCosmicTabLayout.addLayout(cosmicPlotLayout, 0, 3, 1, 7)
