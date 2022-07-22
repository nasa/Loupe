import os
import sys

import PyQt5
# import QApplication and required widgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QSlider
from PyQt5.QtWidgets import QScrollBar
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QRadioButton
from PyQt5.QtWidgets import QTableWidget
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtWidgets import QListWidget
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QHeaderView
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
from PyQt5.QtWidgets import QFrame

from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT


from src import MPL_plots
from src import image_viewer
from src import QScrollAreaImage



###################################################
###################################################
#  MAIN Left Panel
###################################################
###################################################
def _addMainLeftPanel(self):
    # define grid layout for labels and lists
    mainLeftScrollContainer = QScrollArea()
    mainLeftScrollContainer.setFixedWidth(250)
    mainLeftScrollContainer.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
    mainLeftScrollContainer.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    mainLeftScrollContainer.setWidgetResizable(True)

    mainLeftWidgetContainer = QWidget()
    mainLeftScrollContainer.setWidget(mainLeftWidgetContainer)
    #mainLeftLayout = QGridLayout(mainLeftWidgetContainer)
    mainLeftLayout = QVBoxLayout(mainLeftWidgetContainer)


    # Workspace/SOFF file name:
    groupboxWorkspaceMain = QGroupBox('Workspace: ')
    #groupbox.setCheckable(True)
    vboxProcessing = QVBoxLayout()
    groupboxWorkspaceMain.setLayout(vboxProcessing)
    self.selectedWorkspaceCombo = QComboBox()
    vboxProcessing.addWidget(self.selectedWorkspaceCombo)
    self.humanReadableRename = QLineEdit()
    self.humanReadableRename.setPlaceholderText('Rename Workspace')
    self.humanReadableRename.setDisabled(True)
    vboxProcessing.addWidget(self.humanReadableRename)
    mainLeftLayout.addWidget(groupboxWorkspaceMain)
    groupboxWorkspaceMain.setMaximumHeight(100)


    # Enable/Disable processing
    self.groupboxProcessingMain = QGroupBox('Enable/Disable Processing')
    #groupbox.setCheckable(True)
    vboxProcessing = QVBoxLayout()
    self.groupboxProcessingMain.setLayout(vboxProcessing)
    self.CosmicRayRemovalProcessingItemMain = QCheckBox('Cosmic Ray Removal')
    self.CosmicRayRemovalProcessingItemMain.setDisabled(True)
    vboxProcessing.addWidget(self.CosmicRayRemovalProcessingItemMain)
    self.LaserNormalizationItemMain = QCheckBox('Laser Normalization')
    self.LaserNormalizationItemMain.setDisabled(True)
    vboxProcessing.addWidget(self.LaserNormalizationItemMain)
    self.BaselineSubtractionItemMain = QCheckBox('Baseline Subtraction')
    self.BaselineSubtractionItemMain.setDisabled(True)
    vboxProcessing.addWidget(self.BaselineSubtractionItemMain)
    mainLeftLayout.addWidget(self.groupboxProcessingMain)
    self.groupboxProcessingMain.setMaximumHeight(100)


    # Region Selection
    self.groupboxRegionsMain = QGroupBox('SCCD Region Selection')
    #groupbox.setCheckable(True)
    hboxRegion = QHBoxLayout()
    self.groupboxRegionsMain.setLayout(hboxRegion)
    self.R1ItemMain = QCheckBox('R1')
    hboxRegion.addWidget(self.R1ItemMain)
    self.R2ItemMain = QCheckBox('R2')
    hboxRegion.addWidget(self.R2ItemMain)
    self.R3ItemMain = QCheckBox('R3')
    hboxRegion.addWidget(self.R3ItemMain)
    self.allItemMain = QCheckBox('all')
    hboxRegion.addWidget(self.allItemMain)
    self.groupboxRegionsMain.setDisabled(True)
    self.R1ItemMain.setChecked(True)
    self.R2ItemMain.setChecked(True)
    self.R3ItemMain.setChecked(True)
    self.allItemMain.setChecked(True)
    mainLeftLayout.addWidget(self.groupboxRegionsMain)
    self.groupboxRegionsMain.setMaximumHeight(68)


    # Spectrum Mode
    self.groupboxModeMain = QGroupBox('Select Mode')
    #groupbox.setCheckable(True)
    vboxMode = QVBoxLayout()
    self.groupboxModeMain.setLayout(vboxMode)
    self.activeItemMain = QRadioButton('Active')
    vboxMode.addWidget(self.activeItemMain)
    self.darkItemMain = QRadioButton('Dark')
    vboxMode.addWidget(self.darkItemMain)
    self.darkSubMain = QRadioButton('Active - Dark')
    vboxMode.addWidget(self.darkSubMain)
    self.groupboxModeMain.setDisabled(True)
    mainLeftLayout.addWidget(self.groupboxModeMain)
    self.groupboxModeMain.setMaximumHeight(100)

    # Spectrum Display
    self.groupboxDisplayTypeMain = QGroupBox('Select Display Type')
    #groupbox.setCheckable(True)
    vboxMode = QGridLayout()
    self.groupboxDisplayTypeMain.setLayout(vboxMode)
    self.meanDisplayMain = QRadioButton('Mean')
    vboxMode.addWidget(self.meanDisplayMain, 0, 0, 1, 3)
    self.meanStdDisplay = QCheckBox('+/- 1 SD')
    self.meanStdDisplay.setChecked(False)
    vboxMode.addWidget(self.meanStdDisplay, 0, 3, 1, 2)
    self.medianDisplayMain = QRadioButton('Median')
    self.medianDisplayMain.setChecked(False)
    vboxMode.addWidget(self.medianDisplayMain, 1, 0, 1, 3)
    self.medianStdDisplay = QCheckBox('+/- 1 SD')
    vboxMode.addWidget(self.medianStdDisplay, 1, 3, 1, 2)
    self.indexDisplayMain = QRadioButton('Spectrum Index')
    vboxMode.addWidget(self.indexDisplayMain, 2, 0, 1, 5)
    self.indexSpecMain = QLineEdit()
    self.indexSpecMain.setPlaceholderText('Index: 1, 4:10, 15')
    vboxMode.addWidget(self.indexSpecMain, 3, 0, 1, 5)
    self.groupboxDisplayTypeMain.setDisabled(True)
    self.meanDisplayMain.setChecked(True)
    mainLeftLayout.addWidget(self.groupboxDisplayTypeMain)
    self.groupboxDisplayTypeMain.setMaximumHeight(135)


    # Domain selection
    self.groupboxDomainTypeMain = QGroupBox('Select Domain Mode')
    #groupbox.setCheckable(True)
    vboxMode = QVBoxLayout()
    self.groupboxDomainTypeMain.setLayout(vboxMode)
    self.waveDomainMain = QRadioButton('Wavelength')
    vboxMode.addWidget(self.waveDomainMain)
    self.ccdDomainMain = QRadioButton('CCD Pixel')
    vboxMode.addWidget(self.ccdDomainMain)
    self.groupboxDomainTypeMain.setDisabled(True)
    self.waveDomainMain.setChecked(True)
    mainLeftLayout.addWidget(self.groupboxDomainTypeMain)
    self.groupboxDomainTypeMain.setMaximumHeight(80)


    # actions

    self.groupboxROIMain = QGroupBox('ROI Selection: ')
    self.vboxRoi = QVBoxLayout()
    self.groupboxROIMain.setLayout(self.vboxRoi)
    for _roiName in self.workspace.roiNames:
        _roiDictKey = self.workspace.roiHumanToDictKey[_roiName]
        if self.roiDict[_roiDictKey].checkboxWidget is None:
            _checkboxRoi = QCheckBox(self.roiDict[_roiDictKey].humanReadableName)
            self.roiDict[_roiDictKey].checkboxWidget = _checkboxRoi
        self.vboxRoi.addWidget(self.roiDict[_roiDictKey].checkboxWidget)
        if len(self.roiDict) < 2:
            _checkboxRoi.setDisabled(True)
        else:
            _checkboxRoi.setDisabled(False)

    mainLeftLayout.addWidget(self.groupboxROIMain)
    #self.groupboxROIMain.setMaximumHeight(100)


    # dataset metadata
    """
    _nSpectraWidget = QWidget()
    _nSpectraLayout = QHBoxLayout(_nSpectraWidget)
    _nSpectraLabel = QLabel('<h6>Number of Spectra: </h6>')
    _nSpectraLabel.setFixedHeight(35)
    _nSpectraLayout.addWidget(_nSpectraLabel)
    _nSpectraEntry = QLineEdit('')
    _nSpectraEntry.setReadOnly(True)
    #_nSpectraEntry.setMaximumWidth(30)
    _nSpectraLayout.addWidget(_nSpectraEntry)
    mainLeftLayout.addWidget(_nSpectraWidget)

    _avgPDWidget = QWidget()
    _avgPDLayout = QHBoxLayout(_avgPDWidget)
    _avgPDLabel = QLabel('<h6>Avg. Photodiode: </h6>')
    _avgPDLabel.setFixedHeight(35)
    _avgPDLayout.addWidget(_avgPDLabel)
    _avgPDEntry = QLineEdit('')
    _avgPDEntry.setReadOnly(True)
    _avgPDLayout.addWidget(_avgPDEntry)
    mainLeftLayout.addWidget(_avgPDWidget)
    """
    _metadataLabel = QLabel('<h6>Spectrometer Metadata: </h6>')
    _metadataLabel.setFixedHeight(35)
    mainLeftLayout.addWidget(_metadataLabel)

    self.metadataList = QTreeWidget()
    self.metadataList.setIndentation(10)
    self.metadataList.setFont(QFont('Helvetica', 11))
    self.metadataList.setMinimumWidth(50)
    self.metadataList.setMinimumHeight(150)
    self.metadataList.setColumnCount(2)
    self.metadataList.setHeaderLabels(['Parameter', 'Value'])
    mainLeftLayout.addWidget(self.metadataList)


    # list of files
    _dataFileLabel = QLabel('<h6>Source Data Files: </h6>')
    _dataFileLabel.setFixedHeight(35)
    mainLeftLayout.addWidget(_dataFileLabel)
    self.dataFileListTable = QListWidget()
    # to add items to the list:
    # QListWidgetItem("File 1", self.data_file_list)
    self.dataFileListTable.setFont(QFont('Helvetica', 12))
    self.dataFileListTable.setMinimumWidth(50)
    self.dataFileListTable.setMinimumHeight(80)
    mainLeftLayout.addWidget(self.dataFileListTable)


    # list of dimensions
    _dimensionListLabel = QLabel('<h6>Dimensions: </h6>')
    _dimensionListLabel.setFixedHeight(35)
    mainLeftLayout.addWidget(_dimensionListLabel)

    self.dimensionListTable = QTreeWidget()
    self.dimensionListTable.setIndentation(10)
    self.dimensionListTable.setFont(QFont('Helvetica', 11))
    self.dimensionListTable.setMinimumWidth(50)
    self.dimensionListTable.setMinimumHeight(100)
    self.dimensionListTable.setColumnCount(2)
    self.dimensionListTable.setHeaderLabels(['Dimension', 'Size'])
    mainLeftLayout.addWidget(self.dimensionListTable)


    # list of tables
    _tableListLabel = QLabel('<h6>Tables: </h6>')
    _tableListLabel.setFixedHeight(35)
    mainLeftLayout.addWidget(_tableListLabel)

    self.tableListTable = QTreeWidget()
    self.tableListTable.setIndentation(10)
    self.tableListTable.setFont(QFont('Helvetica', 11))
    self.tableListTable.setMinimumWidth(50)
    self.tableListTable.setMinimumHeight(100)
    self.tableListTable.setColumnCount(2)
    self.tableListTable.setHeaderLabels(['Dimension', 'Size'])
    mainLeftLayout.addWidget(self.tableListTable)



    # SOFF display widgets
    # Individual Plot: dimension selection
    self.groupboxIndividualPlotMain = QGroupBox('Individual Plot Selection')
    #groupbox.setCheckable(True)
    vboxIndPlot = QVBoxLayout()
    self.groupboxIndividualPlotMain.setLayout(vboxIndPlot)
    # x axis selection
    _dimensionXLabel = QLabel('<h6>X Dimension Selection</h6>')
    _dimensionXLabel.setFixedHeight(35)
    vboxIndPlot.addWidget(_dimensionXLabel)
    self.selectedXDimCombo = QComboBox()
    vboxIndPlot.addWidget(self.selectedXDimCombo)
    self.selectedXDimCombo.setEnabled(False)

    # y axis selection
    _dimensionYLabel = QLabel('<h6>Y Dimension Selection</h6>')
    _dimensionYLabel.setFixedHeight(35)
    vboxIndPlot.addWidget(_dimensionYLabel)
    self.selectedYDimCombo = QComboBox()
    vboxIndPlot.addWidget(self.selectedYDimCombo)
    self.selectedYDimCombo.setEnabled(False)

    # cursor/index selection
    #_cursorLabel = QLabel('<h6>Index/Cursor Selection</h6>')
    _cursorLabel = QLabel('<h6>Index Selection</h6>')
    _cursorLabel.setFixedHeight(35)
    vboxIndPlot.addWidget(_cursorLabel)
    self.cursorSpecMain = QLineEdit()
    self.cursorSpecMain.setPlaceholderText('Index: 1, 4:10, 15')
    vboxIndPlot.addWidget(self.cursorSpecMain)
    self.cursorSpecMain.setEnabled(False)

    # add trace button
    self.addTraceButtonMain = QPushButton()
    self.addTraceButtonMain.setText('Add Trace to Lower Plot')
    vboxIndPlot.addWidget(self.addTraceButtonMain)
    self.addTraceButtonMain.setEnabled(False)

    # clear trace button
    self.clearTraceButtonMain = QPushButton()
    self.clearTraceButtonMain.setText('Clear Lower Plot')
    vboxIndPlot.addWidget(self.clearTraceButtonMain)
    self.clearTraceButtonMain.setEnabled(True)


    self.groupboxIndividualPlotMain.setDisabled(True)
    mainLeftLayout.addWidget(self.groupboxIndividualPlotMain)
    self.groupboxIndividualPlotMain.setMaximumHeight(250)



    #mainLeftLayout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
    # row, column, rowspan, colspan
    self.LoupeViewMainTabLayout.addWidget(mainLeftScrollContainer, 0, 0, 1, 1)


###################################################
###################################################
#  MAIN Plot Panel
###################################################
###################################################
def _addMainPlotPanel(self):
    #_container = QWidget()
    #_container.setStyleSheet("background-color:black;")
    mainPlotLayout = QVBoxLayout()
    _vertScaleIconPath = self._appctxt.get_resource('rescale_vertical_40px.png')


    # main (mean or median) plot widget
    self.traceCanvasMainPlot1 = MPL_plots.MplCanvas(self, width=5, height=4, dpi=100)
    self.traceCanvasMainPlot1.axes.plot([0], [0])

    # list of axes in the plot
    self.axMainPlot1 = []

    # Create toolbar, passing canvas as first parameter, parent (self, the MainWindow) as second.
    self.toolbarMainPlot1 = NavigationToolbar2QT(self.traceCanvasMainPlot1, self)
    self.toolbarMainPlot1.setMaximumHeight(25)
    self.toolbarResizeMain1 = QAction(QIcon(_vertScaleIconPath), 'Autoscale vertical axis', self.toolbarMainPlot1)
    self.toolbarMainPlot1.insertAction(self.toolbarMainPlot1.actions()[5], self.toolbarResizeMain1)
    self.toolbarMainPlot1.removeAction(self.toolbarMainPlot1.actions()[7])
    self.toolbarMainPlot1.setStyleSheet("QToolBar { border: 0px }")

    mainPlotLayout.addWidget(self.toolbarMainPlot1)
    mainPlotLayout.addWidget(self.traceCanvasMainPlot1)


    self._hLineMain = QFrame()
    self._hLineMain.setFrameShape(QFrame.HLine)
    #_hLine.setFrameShadow(QFrame.Raised)
    self._hLineMain.setLineWidth(100)
    #_hLine.setMinimumHeight(5)
    self._hLineMain.setStyleSheet("color: #a6a6a6;")
    mainPlotLayout.addWidget(self._hLineMain)


    # selection (or all) plot widget
    self.traceCanvasMainPlot2 = MPL_plots.MplCanvas(self, width=5, height=4, dpi=100)
    self.traceCanvasMainPlot2.axes.plot([0], [0])

    # list of axes in the plot
    self.axMainPlot2 = []

    # Create toolbar, passing canvas as first parameter, parent (self, the MainWindow) as second.
    self.toolbarMainPlot2 = NavigationToolbar2QT(self.traceCanvasMainPlot2, self)
    self.toolbarMainPlot2.setMaximumHeight(25)
    self.toolbarResizeMain2 = QAction(QIcon(_vertScaleIconPath), 'Autoscale vertical axis', self.toolbarMainPlot2)
    self.toolbarMainPlot2.insertAction(self.toolbarMainPlot2.actions()[5], self.toolbarResizeMain2)
    self.toolbarMainPlot2.removeAction(self.toolbarMainPlot2.actions()[7])
    self.toolbarMainPlot2.setStyleSheet("QToolBar { border: 0px }")

    mainPlotLayout.addWidget(self.toolbarMainPlot2)
    mainPlotLayout.addWidget(self.traceCanvasMainPlot2)


    #mainPlotLayout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
    #mainPlotLayout.addStretch()
    # Add the display to the Main tab layout
    # row, column, rowspan, colspan
    self.LoupeViewMainTabLayout.addLayout(mainPlotLayout, 0, 3, 1, 7)


###################################################
###################################################
#  MAIN Image Panel
###################################################
###################################################
def _addMainImgPanel(self):
    self.imageACI = None
    # scrollArea: self.mainImgScrollContainer
    # scrollArea Widget: mainImgWidgetContainer
    # scrollArea Layout: mainImgLayout (QGridLayout)
    self.mainImgScrollContainer = QScrollAreaImage.QScrollAreaImage(self)
    #self.mainImgScrollContainer = QScrollArea()
    self.mainImgScrollContainer.setFixedWidth(450)
    #self.mainImgScrollContainer.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
    self.mainImgScrollContainer.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    self.mainImgScrollContainer.setWidgetResizable(True)

    mainImgWidgetContainer = QWidget()
    self.mainImgScrollContainer.setWidget(mainImgWidgetContainer)
    mainImgLayout = QGridLayout(mainImgWidgetContainer)

    # main container
    mainImgLayoutVBox = QVBoxLayout()
    mainImgLayoutVBox.addWidget(self.mainImgScrollContainer)



    # WATSON file name selection:
    self.groupboxWATSON = QGroupBox('WATSON Select')
    gboxMode = QGridLayout()
    self.groupboxWATSON.setLayout(gboxMode)
    self.WATSONFileSelectButton = QPushButton()
    self.WATSONFileSelectButton.setText('Open WATSON .IMG/.PNG')
    gboxMode.addWidget(self.WATSONFileSelectButton, 0, 0, 1, 5)
    # WATSON file select dropdown
    if self.workspace.selectedWATSONFilename is None:
        self.selectedWATSONCombo = QComboBox()
    else:
        self.selectedWATSONCombo = QComboBox(self.workspace.selectedWATSONFilename)
    self.selectedWATSONCombo.setFixedHeight(30)
    self.selectedWATSONCombo.setMinimumWidth(50)
    gboxMode.addWidget(self.selectedWATSONCombo, 0, 5, 1, 5)
    self.selectedWATSONCombo.setMaximumHeight(100)
    _OpacityLabel = QLabel()
    _OpacityLabel.setText('Opacity')
    gboxMode.addWidget(_OpacityLabel, 1, 0, 1, 2)
    self.opacityWATSONMain = QSlider(Qt.Horizontal)
    self.opacityWATSONMain.setMinimum(0)
    self.opacityWATSONMain.setMaximum(100)
    self.opacityWATSONMain.setValue(80)
    gboxMode.addWidget(self.opacityWATSONMain, 1, 2, 1, 8)
    # TODO: add groupboxWatson when functionality is available
    #mainImgLayout.addWidget(self.groupboxWATSON)
    #self.WATSONFileSelectButton.setEnabled(False)
    #self.selectedWATSONCombo.setEnabled(False)
    self.groupboxWATSON.setEnabled(False)

    # ACI file name selection:
    self.groupboxACI = QGroupBox('ACI Select')
    gboxMode = QGridLayout()
    self.groupboxACI.setLayout(gboxMode)
    self.ACIFileSelectButton = QPushButton()
    self.ACIFileSelectButton.setText('Open ACI .IMG/.PNG')
    gboxMode.addWidget(self.ACIFileSelectButton, 0, 0, 1, 5)
    # ACI file select dropdown
    if self.workspace.selectedACIFilename is None:
        self.selectedACICombo = QComboBox()
    else:
        self.selectedACICombo = QComboBox(self.workspace.selectedACIFilename)
    self.selectedACICombo.setFixedHeight(30)
    self.selectedACICombo.setMinimumWidth(50)
    gboxMode.addWidget(self.selectedACICombo, 0, 5, 1, 5)
    self.selectedACICombo.setMaximumHeight(100)
    _OpacityLabel = QLabel()
    _OpacityLabel.setText('Opacity')
    gboxMode.addWidget(_OpacityLabel, 1, 0, 1, 2)
    self.opacityACIMain = QSlider(Qt.Horizontal)
    self.opacityACIMain.setMinimum(0)
    self.opacityACIMain.setMaximum(100)
    self.opacityACIMain.setValue(100)
    gboxMode.addWidget(self.opacityACIMain, 1, 2, 1, 8)
    self.groupboxACI.setEnabled(False)

    mainImgLayout.addWidget(self.groupboxACI)


    # WATSON/ACI image display
    # WATSON Image Display
    """
    imageWidget = QWidget()
    imageLayout = QHBoxLayout(imageWidget)
    imageLayout.setContentsMargins(0, 0, 0, 0)

    img1_dir = os.path.join(os.path.dirname(sys.modules[__name__].__file__), os.pardir, os.pardir, 'resources', 'WATSON_placeholder.png')
    pixmap1 = QPixmap(img1_dir)
    pixmap1 = pixmap1.scaledToWidth(0.92*self.mainImgScrollContainer.width())
    self.imageWATSON = QLabel()
    self.imageWATSON.setPixmap(pixmap1)

    imageLayout.addWidget(self.imageWATSON)

    self.imageACI = QLabel(imageWidget)
    img2_dir = os.path.join(os.path.dirname(sys.modules[__name__].__file__), os.pardir, os.pardir, 'resources', 'ACI_placeholder.png')
    pixmap2 = QPixmap(img2_dir)
    #pixmap2 = pixmap2.scaled(0.95*self.imageWATSON.width(), 0.95*self.imageWATSON.height(), Qt.KeepAspectRatio)
    pixmap2 = pixmap2.scaledToWidth(0.85*self.imageWATSON.height())
    self.imageACI.setPixmap(pixmap2)
    self.imageACI.setFixedSize(pixmap2.width(), pixmap2.height())
    print(self.imageWATSON.width(), self.imageWATSON.height())
    print(pixmap2.width(), pixmap2.height())

    #p = self.imageWATSON.geometry().bottomRight() - self.imageACI.geometry().bottomRight() - QPoint(-10, 0)
    #self.imageACI.move(p)
    self.imageACI.move(QPoint(3, 160))

    mainImgLayout.addWidget(imageWidget)
    """
    # ACI Image Display
    imageWidget = QWidget()
    imageLayout = QHBoxLayout(imageWidget)
    imageLayout.setContentsMargins(0, 0, 0, 0)

    #img1_dir = os.path.join(os.path.dirname(sys.modules[__name__].__file__), os.pardir, os.pardir, 'resources', 'ACI_placeholder.png')
    img1_dir = self._appctxt.get_resource('ACI_placeholder.png')
    self.pixmapACI = QPixmap(img1_dir)
    self.pixmapACI = self.pixmapACI.scaledToWidth(0.92*self.mainImgScrollContainer.width())
    #self.imageACI = QLabel()
    #self.imageACI.setPixmap(pixmap1)

    """
    self.imageACIScene = QGraphicsScene()
    self.imageACI = QGraphicsView(self.imageACIScene)
    self.imageACI.setFixedHeight(360)
    #self.imageACI.setSceneRect(0, 0, pixmap1.width(), pixmap1.height())
    self.imageACIScene.addPixmap(pixmap1)
    self.imageACI.fitInView(self.imageACIScene.sceneRect(), Qt.KeepAspectRatio)
    #self.imageACI.fitInView(QRectF(0, 0, 1648, 1200), Qt.KeepAspectRatio)

    """
    self.imageACI = image_viewer.imageViewer(self)
    self.imageACI.setFixedHeight(360)
    self.imageACI.setPhoto(pixmap = self.pixmapACI, zoomSelect=1)

    imageLayout.addWidget(self.imageACI)
    mainImgLayout.addWidget(imageWidget)


    # ROI selection
    self.groupboxROI = QGroupBox('ROI Selection')
    gridMode = QGridLayout()
    self.groupboxROI.setLayout(gridMode)
    self.ROIPolySelectButton = QPushButton()
    self.ROIPolySelectButton.setText('Polynomial Selection')
    self.ROIPolySelectButton.setCheckable(True)
    gridMode.addWidget(self.ROIPolySelectButton, 0, 0, 1, 3)
    self.ROIAddPointButton = QPushButton()
    self.ROIAddPointButton.setText('Add Point(s)')
    self.ROIAddPointButton.setCheckable(True)
    gridMode.addWidget(self.ROIAddPointButton, 0, 3, 1, 3)
    self.ROIDelPointButton = QPushButton()
    self.ROIDelPointButton.setText('Delete Point(s)')
    self.ROIDelPointButton.setCheckable(True)
    self.ROIDelPointButton.setEnabled(False)
    gridMode.addWidget(self.ROIDelPointButton, 1, 0, 1, 3)
    self.ROIClearPointButton = QPushButton()
    self.ROIClearPointButton.setText('Clear All Points')
    self.ROIClearPointButton.setCheckable(False)
    self.ROIClearPointButton.setEnabled(False)
    gridMode.addWidget(self.ROIClearPointButton, 1, 3, 1, 3)
    self.ROISaveButton = QPushButton()
    self.ROISaveButton.setText('Save Selected Points to ROI')
    gridMode.addWidget(self.ROISaveButton, 2, 0, 1, 3)
    self.humanReadableRoi = QLineEdit()
    self.humanReadableRoi.setPlaceholderText('ROI Name')
    gridMode.addWidget(self.humanReadableRoi, 2, 3, 1, 3)
    self.ROISaveButton.setEnabled(False)

    _roiColorLabel = QLabel()
    _roiColorLabel.setText('ROI Color Selection')
    gridMode.addWidget(_roiColorLabel, 3, 0, 1, 2)
    self.ROIColorButton = QPushButton()
    self.ROIColorButton.setText('Color Selection')
    gridMode.addWidget(self.ROIColorButton, 3, 3, 1, 2)
    self.ROIColorBox = QCheckBox('')
    self.ROIColorBox.setStyleSheet("QCheckBox::indicator{background-color : #00f2ff;}")
    self.ROIColorButton.setEnabled(False)
    self.ROIColorBox.setEnabled(False)
    gridMode.addWidget(self.ROIColorBox, 3, 5, 1, 1)


    # ROI dropdown with previous selections
    _roiSelectLabel = QLabel()
    _roiSelectLabel.setText('Edit Saved ROI')
    gridMode.addWidget(_roiSelectLabel, 4, 0, 1, 2)
    if len(self.workspace.selectedROI) == 0:
        self.selectedROICombo = QComboBox()
    else:
        self.selectedROICombo = QComboBox(self.workspace.selectedROI[0])
    self.selectedROICombo.setFixedHeight(30)
    self.selectedROICombo.setMinimumWidth(50)
    gridMode.addWidget(self.selectedROICombo, 4, 2, 1, 2)
    self.selectedROICombo.setMaximumHeight(100)
    self.ROIEditButton = QPushButton()
    self.ROIEditButton.setText('Edit ROI')
    self.ROIEditButton.setEnabled(False)
    gridMode.addWidget(self.ROIEditButton, 4, 4, 1, 2)


    _roiDeleteLabel = QLabel()
    _roiDeleteLabel.setText('Delete Saved ROI')
    gridMode.addWidget(_roiDeleteLabel, 5, 0, 1, 2)
    if len(self.workspace.selectedROI) == 0:
        self.deleteROICombo = QComboBox()
    else:
        self.deleteROICombo = QComboBox(self.workspace.selectedROI[0])
    self.deleteROICombo.setFixedHeight(30)
    self.deleteROICombo.setMinimumWidth(50)
    gridMode.addWidget(self.deleteROICombo, 5, 2, 1, 2)
    self.deleteROICombo.setMaximumHeight(100)
    self.ROIDeleteButton = QPushButton()
    self.ROIDeleteButton.setText('Delete ROI')
    self.ROIDeleteButton.setEnabled(False)
    gridMode.addWidget(self.ROIDeleteButton, 5, 4, 1, 2)

    _roiExportLabel = QLabel()
    _roiExportLabel.setText('Export Saved ROI')
    gridMode.addWidget(_roiExportLabel, 6, 0, 1, 2)
    if len(self.workspace.selectedROI) == 0:
        self.exportROICombo = QComboBox()
    else:
        self.exportROICombo = QComboBox(self.workspace.selectedROI[0])
    self.exportROICombo.setFixedHeight(30)
    self.exportROICombo.setMinimumWidth(50)
    gridMode.addWidget(self.exportROICombo, 6, 2, 1, 2)
    self.exportROICombo.setMaximumHeight(100)
    self.ROIExportButton = QPushButton()
    self.ROIExportButton.setText('Export ROI')
    self.ROIExportButton.setEnabled(False)
    gridMode.addWidget(self.ROIExportButton, 6, 4, 1, 2)


    self.groupboxROI.setEnabled(False)
    mainImgLayout.addWidget(self.groupboxROI)


    self.groupboxLaserMain = QGroupBox('Point Selection')
    gridMode = QGridLayout()
    self.groupboxLaserMain.setLayout(gridMode)

    _LaserSliderLabel = QLabel()
    _LaserSliderLabel.setText('Point #')
    gridMode.addWidget(_LaserSliderLabel, 0, 0, 1, 1)
    self.selectionScrollbarEdit = QLineEdit()
    self.selectionScrollbarEdit.setPlaceholderText('0')
    self.selectionScrollbarEdit.setMaximumWidth(50)
    gridMode.addWidget(self.selectionScrollbarEdit, 0, 1, 1, 2)
    self.selectionScrollbarMain = QScrollBar(Qt.Horizontal)
    self.selectionScrollbarMain.setMinimum(0)
    self.selectionScrollbarMain.setMaximum(1)
    self.selectionScrollbarMain.setValue(0)
    gridMode.addWidget(self.selectionScrollbarMain, 0, 3, 1, 17)

    _OpacityLabel = QLabel()
    _OpacityLabel.setText('Point Opacity')
    gridMode.addWidget(_OpacityLabel, 1, 0, 1, 3)
    self.opacityLaserMain = QSlider(Qt.Horizontal)
    self.opacityLaserMain.setMinimum(0)
    self.opacityLaserMain.setMaximum(100)
    self.opacityLaserMain.setValue(80)
    gridMode.addWidget(self.opacityLaserMain, 1, 3, 1, 17)

    _PointFillLabel = QLabel()
    _PointFillLabel.setText('Point Fill')
    gridMode.addWidget(_PointFillLabel, 2, 0, 1, 1)
    self.pointFillMain = QCheckBox('')
    self.pointFillMain.setChecked(True)
    gridMode.addWidget(self.pointFillMain, 2, 1, 1, 2)

    _OffsetLabel = QLabel()
    _OffsetLabel.setText('Scanner Offset:')
    gridMode.addWidget(_OffsetLabel, 3, 0, 1, 2)
    _OffsetAzLabel = QLabel()
    _OffsetAzLabel.setText('Az:')
    gridMode.addWidget(_OffsetAzLabel, 3, 2, 1, 2)
    self.selectionOffsetAzEdit = QLineEdit()
    self.selectionOffsetAzEdit.setPlaceholderText(' ')
    self.selectionOffsetAzEdit.setReadOnly(True)
    self.selectionOffsetAzEdit.setMaximumWidth(100)
    gridMode.addWidget(self.selectionOffsetAzEdit, 3, 4, 1, 2)
    _OffsetElLabel = QLabel()
    _OffsetElLabel.setText('El:')
    gridMode.addWidget(_OffsetElLabel, 3, 6, 1, 2)
    self.selectionOffsetElEdit = QLineEdit()
    self.selectionOffsetElEdit.setPlaceholderText(' ')
    self.selectionOffsetElEdit.setReadOnly(True)
    self.selectionOffsetElEdit.setMaximumWidth(100)
    gridMode.addWidget(self.selectionOffsetElEdit, 3, 8, 1, 2)


    self.groupboxLaserMain.setEnabled(False)
    mainImgLayout.addWidget(self.groupboxLaserMain)




    groupboxRelPosWidget = QGroupBox('Relative Image Position')
    groupboxRelPosLayout = QHBoxLayout(groupboxRelPosWidget)
    groupboxRelPosLayout.setContentsMargins(0, 0, 0, 0)

    # nudge ACI relative to WATSON (x/y, rotation, scale)
    groupboxRelPosACIWidget = QGroupBox('ACI (relative to WATSON)')
    groupboxRelPosACILayout = QGridLayout(groupboxRelPosACIWidget)
    _xPos = QLabel()
    _xPos.setText('X Position')
    groupboxRelPosACILayout.addWidget(_xPos, 0, 0, 1, 1)
    self.xPosACI = QLineEdit()
    self.xPosACI.setPlaceholderText('0.0')
    groupboxRelPosACILayout.addWidget(self.xPosACI, 0, 1, 1, 1)
    _yPos = QLabel()
    _yPos.setText('Y Position')
    groupboxRelPosACILayout.addWidget(_yPos, 1, 0, 1, 1)
    self.yPosACI = QLineEdit()
    self.yPosACI.setPlaceholderText('0.0')
    groupboxRelPosACILayout.addWidget(self.yPosACI, 1, 1, 1, 1)
    _rotPos = QLabel()
    _rotPos.setText('Rotation (deg)')
    groupboxRelPosACILayout.addWidget(_rotPos, 2, 0, 1, 1)
    self.rotACI = QLineEdit()
    self.rotACI.setPlaceholderText('0.0')
    groupboxRelPosACILayout.addWidget(self.rotACI, 2, 1, 1, 1)
    _scalePos = QLabel()
    _scalePos.setText('Scale Factor')
    groupboxRelPosACILayout.addWidget(_scalePos, 3, 0, 1, 1)
    self.scaleACI = QLineEdit()
    self.scaleACI.setPlaceholderText('0.0')
    groupboxRelPosACILayout.addWidget(self.scaleACI, 3, 1, 1, 1)

    self.resetACIAlignMain = QPushButton()
    self.resetACIAlignMain.setText('Recalculate ACI Position')
    groupboxRelPosACILayout.addWidget(self.resetACIAlignMain, 4, 0, 1, 2)
    self.resetACIAlignMain.setEnabled(False)

    groupboxRelPosACIWidget.setDisabled(True)


    # nudge points relative to ACI (x/y, rotation, scale)
    # TODO: should there be additional buttons to adjust the laser rotation and scale factor?
    groupboxRelPosLaserWidget = QGroupBox('Laser (relative to ACI)')
    groupboxRelPosLaserLayout = QGridLayout(groupboxRelPosLaserWidget)
    _xPos = QLabel()
    _xPos.setText('X Center')
    groupboxRelPosLaserLayout.addWidget(_xPos, 0, 0, 1, 1)
    self.xPosLaser = QLineEdit()
    self.xPosLaser.setPlaceholderText('809')
    groupboxRelPosLaserLayout.addWidget(self.xPosLaser, 0, 1, 1, 1)
    _yPos = QLabel()
    _yPos.setText('Y Center')
    groupboxRelPosLaserLayout.addWidget(_yPos, 1, 0, 1, 1)
    self.yPosLaser = QLineEdit()
    self.yPosLaser.setPlaceholderText('664')
    groupboxRelPosLaserLayout.addWidget(self.yPosLaser, 1, 1, 1, 1)
    _azScale = QLabel()
    _azScale.setText('Azimuth Scale')
    groupboxRelPosLaserLayout.addWidget(_azScale, 2, 0, 1, 1)
    self.azScaleLaser = QLineEdit()
    self.azScaleLaser.setPlaceholderText('{0:.5f}'.format(0.628154699))
    groupboxRelPosLaserLayout.addWidget(self.azScaleLaser, 2, 1, 1, 1)
    _elScale = QLabel()
    _elScale.setText('Elevation Scale')
    groupboxRelPosLaserLayout.addWidget(_elScale, 3, 0, 1, 1)
    self.elScaleLaser = QLineEdit()
    self.elScaleLaser.setPlaceholderText('{0:.5f}'.format(0.422441487))
    groupboxRelPosLaserLayout.addWidget(self.elScaleLaser, 3, 1, 1, 1)
    _rotLaser = QLabel()
    _rotLaser.setText('Rotation')
    groupboxRelPosLaserLayout.addWidget(_rotLaser, 4, 0, 1, 1)
    self.rotLaser = QLineEdit()
    self.rotLaser.setPlaceholderText('{0:.5f}'.format(20.6793583))
    groupboxRelPosLaserLayout.addWidget(self.rotLaser, 4, 1, 1, 1)

    self.resetLaserSpotMain = QPushButton()
    self.resetLaserSpotMain.setText('Recalculate Laser Positions')
    groupboxRelPosLaserLayout.addWidget(self.resetLaserSpotMain, 5, 0, 1, 2)
    self.resetLaserSpotMain.setEnabled(False)

    #groupboxRelPosLaserWidget.setDisabled(True)

    groupboxRelPosLayout.addWidget(groupboxRelPosACIWidget)
    groupboxRelPosLayout.addWidget(groupboxRelPosLaserWidget)
    mainImgLayout.addWidget(groupboxRelPosWidget)

    # image properties table
    # motor position
    # temperatures
    # states/status flags
    # pixel scale
    # CDPID
    # exp time
    # product ID
    _imageMetadataLabel = QLabel('<h6>Imaging Metadata: </h6>')
    _imageMetadataLabel.setFixedHeight(35)
    mainImgLayout.addWidget(_imageMetadataLabel)

    self.imageMetadataList = QTableWidget()
    self.imageMetadataList.setEditTriggers(QTableWidget.NoEditTriggers)
    self.imageMetadataList.setFont(QFont('Helvetica', 11))
    self.imageMetadataList.setColumnCount(3)
    self.imageMetadataList.setHorizontalHeaderItem(0, QTableWidgetItem('Parameter'))
    self.imageMetadataList.setHorizontalHeaderItem(1, QTableWidgetItem('WATSON'))
    self.imageMetadataList.setHorizontalHeaderItem(2, QTableWidgetItem('ACI'))
    header = self.imageMetadataList.horizontalHeader()
    header.setSectionResizeMode(0, QHeaderView.Stretch)
    header.setSectionResizeMode(1, QHeaderView.Stretch)
    header.setSectionResizeMode(2, QHeaderView.Stretch)
    self.imageMetadataList.setMinimumWidth(50)
    self.imageMetadataList.setMinimumHeight(138)
    mainImgLayout.addWidget(self.imageMetadataList)

    self.imageMetadataList.insertRow(0)
    self.imageMetadataList.setItem(0, 0, QTableWidgetItem('Pixel Scale (um/pix)'))
    self.imageMetadataList.setItem(0, 1, QTableWidgetItem(str(self.workspace.WATSONAttributes['pixelScale'])))
    self.imageMetadataList.setItem(0, 2, QTableWidgetItem(str(self.workspace.ACIAttributes['pixelScale'])))

    self.imageMetadataList.insertRow(1)
    self.imageMetadataList.setItem(1, 0, QTableWidgetItem('Range (mm)'))
    self.imageMetadataList.setItem(1, 1, QTableWidgetItem(str(self.workspace.WATSONAttributes['range'])))
    self.imageMetadataList.setItem(1, 2, QTableWidgetItem(str(self.workspace.ACIAttributes['range'])))

    self.imageMetadataList.insertRow(2)
    self.imageMetadataList.setItem(2, 0, QTableWidgetItem('CDPID'))
    self.imageMetadataList.setItem(2, 1, QTableWidgetItem(str(self.workspace.WATSONAttributes['CDPID'])))
    self.imageMetadataList.setItem(2, 2, QTableWidgetItem(str(self.workspace.ACIAttributes['CDPID'])))

    self.imageMetadataList.insertRow(3)
    self.imageMetadataList.setItem(3, 0, QTableWidgetItem('Motor Position'))
    self.imageMetadataList.setItem(3, 1, QTableWidgetItem(str(self.workspace.WATSONAttributes['motor_pos'])))
    self.imageMetadataList.setItem(3, 2, QTableWidgetItem(str(self.workspace.ACIAttributes['motor_pos'])))

    self.imageMetadataList.insertRow(4)
    self.imageMetadataList.setItem(4, 0, QTableWidgetItem('Exposure Time (ms)'))
    self.imageMetadataList.setItem(4, 1, QTableWidgetItem(str(self.workspace.WATSONAttributes['exp_time'])))
    self.imageMetadataList.setItem(4, 2, QTableWidgetItem(str(self.workspace.ACIAttributes['exp_time'])))

    self.imageMetadataList.insertRow(5)
    self.imageMetadataList.setItem(5, 0, QTableWidgetItem('Product ID'))
    self.imageMetadataList.setItem(5, 1, QTableWidgetItem(str(self.workspace.WATSONAttributes['product_ID'])))
    self.imageMetadataList.setItem(5, 2, QTableWidgetItem(str(self.workspace.ACIAttributes['product_ID'])))

    self.imageMetadataList.insertRow(6)
    self.imageMetadataList.setItem(6, 0, QTableWidgetItem('LED Flag'))
    self.imageMetadataList.setItem(6, 1, QTableWidgetItem(str(self.workspace.WATSONAttributes['led_flag'])))
    self.imageMetadataList.setItem(6, 2, QTableWidgetItem(str(self.workspace.ACIAttributes['led_flag'])))

    self.imageMetadataList.resizeRowsToContents()
    self.imageMetadataList.verticalHeader().setVisible(False)

    self.imageMetadataList.setEnabled(False)

    #mainImgLayout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
    # row, column, rowspan, colspan
    self.LoupeViewMainTabLayout.addLayout(mainImgLayoutVBox, 0, 10, 1, 1)
