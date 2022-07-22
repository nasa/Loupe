import os
import time
import copy
import sys

import PyQt5
# import QApplication and required widgets
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QFont
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication
# from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QFileDialog
# from PyQt5.QtWidgets import QDialogButtonBox
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QRadioButton
from PyQt5.QtWidgets import QListWidget
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtWidgets import QHBoxLayout # horizontal layout
from PyQt5.QtWidgets import QVBoxLayout # vertical layout
from PyQt5.QtWidgets import QGridLayout # grid layout
# from PyQt5.QtWidgets import QFormLayout # form layout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QStatusBar
from PyQt5.QtWidgets import QToolBar
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QScrollArea
from PyQt5.QtWidgets import QSpacerItem
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QFrame

from PyQt5.QtGui import QPalette
from PyQt5.QtGui import QColor

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT

from functools import partial
from darktheme.widget_template import DarkPalette

from src import log_parsing
from src import MPL_plots
from src import file_IO
from src import popup_window
from src import workspace_class
from src import roi_class

from src.loupe_view import _tab_main
from src.loupe_view import _tab_laser_norm
from src.loupe_view import _tab_cosmic_ray
from src.loupe_view import _tab_false_color


# Create a subclass of QMainWindow to setup the application GUI
class LoupeViewUi(QMainWindow):
    """Loupe's View (GUI)."""
    def __init__(self, __version__, __releaseDate__, _test, _appctxt):
        self._test = _test
        self._appctxt = _appctxt
        self.__version__ = __version__
        self.__releaseDate__ = __releaseDate__
        """View initializer."""
        super().__init__()
        self.setAttribute(Qt.WA_DeleteOnClose)
        #_palette = self.palette()
        #_palette.setColor(QPalette.Window, QColor(255, 18, 14))
        #self.setPalette(_palette)

        # set the borders to see the extent of the widgets
        #self.setStyleSheet("background-color: rgb(230,230,230); margin:5px; border:1px solid rgb(220, 0, 0); ")
        # Set some main window's properties
        self.setWindowTitle('Loupe Version '+str(self.__version__))
        # x, y coordinates of window, width, height
        # this size fits will on a 13" monitor. Performance on smaller screens may be poor
        self.setGeometry(10, 0, 1650, 950)

        # session file, which stores all open workspaces
        self.loupeSessionFile = None
        self.loupeSession = None

        # workspace dictionary - store all workspaces
        self.workspaceDict = {}
        self.workspaceHumanToDictKey = {}
        # initialize workspace
        self.workspace = workspace_class.workspaceClass()
        # ROI dictionary - store all ROIs associated with the current workspace
        self.roiDict = {}
        # initialize ROI
        self.roi = roi_class.roiClass()
        # holds ROI points that have been selected by a user, but not yet committed to a new ROI
        self.tempRoi = []
        self.tempRoiColor = '#00f2ff'
        # top axis, which need to be cleared when re-drawing
        self.axTopSparMain = None
        self.axTopMain = None
        self.axTopMap = None
        self.axTopTopMap = None
        self.specProcessingSelected = 'None'


        # set the layout
        self.generalLayout = QGridLayout()
        # Set the central widget
        # this object is a parent for the rest of the GUI component
        # this is essentially a placeholder widget
        self._centralWidget = QWidget(self)
        self.setCentralWidget(self._centralWidget)
        self._centralWidget.setLayout(self.generalLayout)
        # Create the display and the buttons
        self._createMainWidgets()
        #self._createMenu()
        self._createToolBar()
        self._createStatusBar()

    def _createMenu(self):
        # without this extra line here, the menubar will not be displayed
        self.menuBar().setNativeMenuBar(False)
        self.menu = self.menuBar().addMenu("&Menu")
        self.menu.addAction('&About', self.about)
        self.menu.addAction('&Exit', self.close)

    def about(self):
        msg = QMessageBox()
        #msg.setIcon(QMessageBox.Information)
        msg.setText('Loupe: M2020 SHERLOC Visualization Tool\t\t')
        _copyright_text = 'Copyright 2022, by the California Institute of Technology. ALL RIGHTS RESERVED. United States Government Sponsorship acknowledged. Any commercial use must be negotiated with the Office of Technology Transfer at the California Institute of Technology.\n\nThis software may be subject to U.S. export control laws. By accepting this software, the user agrees to comply with all applicable U.S. export laws and regulations. User has the responsibility to obtain export licenses, or other export authority as may be required before exporting such information to foreign countries or providing access to foreign persons.\n\n'
        msg.setInformativeText(_copyright_text+'Developed by:  Kyle Uckert\n\tkyle.uckert@jpl.nasa.gov')
        # will not be displayed on Mac OS X systems
        msg.setWindowTitle('Loupe ' + self.__version__)
        msg.setDetailedText('Release Date: ' + self.__releaseDate__ + '\nVersion: '+ self.__version__ + '\n\nData: https://pds-geosciences.wustl.edu/missions/mars2020/sherloc.htm\n\nhttps://github.com/nasa/Loupe')
        msg.setStandardButtons(QMessageBox.Ok)
        #msg.setStyleSheet("QLabel{min-height: 100px;}")
        #msg.setWindowIcon(QIcon(self._appctxt.get_resource('Loupe_logo.icns')))
        msg.exec_()


    def _createToolBar(self):
        self.asciiExportRoi = QCheckBox('ASCII Export')
        self.asciiExportSpacing = QLineEdit()
        self.asciiExportSpacing.setPlaceholderText('0.1')
        self.asciiExportSpacing.setMaximumWidth(50)
        tools = QToolBar()
        self.addToolBar(tools)
        tools.addAction('Open', self.openFileMain)
        tools.addAction('Save Session', self.saveSession)
        tools.addAction('Export Options', self.exportData).setDisabled(False)
        tools.addAction('About', self.about).setDisabled(False)
        tools.addAction('Exit', self.close)

    def _createStatusBar(self, status_text='N/A'):
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage('Status: '+status_text)


    def openFileMain(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        # save a deepcopy of the current workspace to the workspaceDict, if one is active
        if self.workspace.dictName is not '':
            self.workspaceDict[self.workspace.dictName] = copy.deepcopy(self.workspace)

        # for testing (to prevent the need to navigate through the dialog repeatedly)
        if self._test:
            self.selectedMainFilename = os.path.join(os.sep, 'Users', '[user_name]', 'Documents', 'Loupe', 'test_data', 'sol_0059', 'Sol_0186_Bellegarde.lpe')
        else:
            self.selectedMainFilename, _ = QFileDialog.getOpenFileName(self,"Select SHERLOC data file", "","All Files (*);;RawDps (*.dat);;EDR/RDRs (*.csv)", options = options)

        if self.selectedMainFilename:
            # initialize workspace
            self.workspace = workspace_class.workspaceClass()
            # initialize ROI
            self.roi = roi_class.roiClass()
            # holds ROI points that have been selected by a user, but not yet committed to a new ROI
            self.tempRoi = []
            self.tempRoiColor = '#00f2ff'


            # return focus to main tab
            self.LoupeViewTabs.setCurrentIndex(0)

            # if the selected file is a .lpe file, open the first workspace
            if self.selectedMainFilename.endswith('.lpe'):
                self.loupeSessionFile = self.selectedMainFilename
                # read loupe session file
                self.selectedMainFilename = file_IO.parse_loupe_session(self, self.loupeSessionFile)


            self.workspace.initNames(self.selectedMainFilename)
            self.logDir = os.path.join(self.workspace.workingDir, 'logs')
            file_IO.mkdir(self.logDir)
            log_parsing.logging_setup(self.logDir, self, self.__version__)
            log_parsing.log_info(self, 'Parsing file: {0}.'.format(self.selectedMainFilename))
            if self.selectedMainFilename.endswith('.dat'):
                log_parsing.log_warning(self, 'Parsing raw binary data products. This process may take up to 30 seconds.')
            #QApplication.processEvents()
            file_IO.parseMainFile(self, self.selectedMainFilename, self.workspace)

            if not self.selectedMainFilename.endswith('_soff.xml'):
                self.workspace.writeDataCsv(self)
                self.workspace.generateSOFF(self)
                _loupe_file = os.path.join(self.workspace.workingDir, 'loupe.csv')
                file_IO.addSOFFFAOCsv(self.workspace, _loupe_file, 'LoupeTable')

            self.workspaceDict[self.workspace.dictName] = self.workspace
            self.workspaceHumanToDictKey[self.workspace.humanReadableName] = self.workspace.dictName

            # check for the presence of ROIs
            # if there are none, add the Full Map
            if len(self.workspace.roiNames) == 0:
                # the default ROI is the full map
                _roi_name = 'Full Map'
                self.roi = roi_class.roiClass()
                self.roi.defineFull(_roi_name, self.workspace)
                self.workspace.roiNames = [_roi_name]
                self.roiDict[self.roi.dictName] = self.roi
                self.workspace.roiHumanToDictKey[self.roi.humanReadableName] = self.roi.dictName
            self.tempRoi = []
            self.tempRoiColor = '#00f2ff'

            # add to combo box selection
            self.workspace.addWorkspaceItemCombo(self)

            # TODO generate a Loupe Session file to hold locations of workspace/SOFF files
            # could this be transferable? the SOFF files would need be referenced by relative path
            # opening a .lpe file would update the workspace combo box will all workspaces and would access all SOFF files to generate the workspace dictionary

            self.humanReadableRename.setDisabled(False)
            self.groupboxACI.setDisabled(False)


    # generate .LPE session file containing info on all soff files in session
    def saveSession(self):
        if len(self.workspaceDict) > 0:
            # dialog to save session file
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            self.loupeSessionFile, _ = QFileDialog.getSaveFileName(self,"Define SHERLOC Loupe Session filename (.lpe extension)", "","All Files (*);;Loupe Session (*.lpe)", options = options)
            self.loupeSessionFile = self.loupeSessionFile.split('.')[0]+'.lpe'
            log_parsing.log_info(self, 'Saving workspaces to Loupe session file {0}'.format(self.loupeSessionFile))
            file_IO.writeLoupeSession(self.loupeSessionFile, self)
            log_parsing.log_info(self, 'Saved workspaces to Loupe session file {0}'.format(self.loupeSessionFile))

        else:
            log_parsing.log_warning(self, 'Warning: No workspaces exist. Loupe session file not saved.')

    def exportData(self):
        exPopup = popup_window.ROI_export_selection_popup(self.asciiExportRoi, self.asciiExportSpacing, self)
        exPopup.setGeometry(300, 150, 200, 100)
        exPopup.show()

    def _createMainWidgets(self):
        self._addTabPane()


    def _addTabPane(self):
        self.LoupeViewTabs = QTabWidget()
        self.LoupeViewMainTab = QWidget()
        self.LoupeViewCompareTab = QWidget()
        self.LoupeViewStandardTab = QWidget()
        self.LoupeViewCosmicTab = QWidget()
        self.LoupeViewNormTab = QWidget()
        self.LoupeViewDarkTab = QWidget()
        self.LoupeViewWaveCorrTab = QWidget()
        self.LoupeViewBaselineTab = QWidget()
        self.LoupeViewPeakFitTab = QWidget()
        self.LoupeViewSparExploreTab = QWidget()
        self.LoupeViewPCATab = QWidget()
        self.LoupeViewRGBTab = QWidget()

        # add tabs
        self.LoupeViewTabs.addTab(self.LoupeViewMainTab,"Main")
        self.LoupeViewTabs.addTab(self.LoupeViewCompareTab,"Compare Spectra")
        self.LoupeViewTabs.addTab(self.LoupeViewStandardTab,"Standards")
        self.LoupeViewTabs.addTab(self.LoupeViewCosmicTab,"Cosmic Ray Removal")
        self.LoupeViewTabs.addTab(self.LoupeViewNormTab,"Laser Normalization")
        self.LoupeViewTabs.addTab(self.LoupeViewDarkTab,"Dark Frame")
        self.LoupeViewTabs.addTab(self.LoupeViewWaveCorrTab,"Wavelength Correction")
        self.LoupeViewTabs.addTab(self.LoupeViewBaselineTab,"Baseline Removal")
        self.LoupeViewTabs.addTab(self.LoupeViewPeakFitTab,"Peak Fitting")
        self.LoupeViewTabs.addTab(self.LoupeViewSparExploreTab,"Data Explore")
        self.LoupeViewTabs.addTab(self.LoupeViewPCATab,"PCA")
        self.LoupeViewTabs.addTab(self.LoupeViewRGBTab,"False Color Map")
        self.LoupeViewTabs.setTabEnabled(0, True)
        self.LoupeViewTabs.setTabEnabled(1, False)
        self.LoupeViewTabs.setTabEnabled(2, False)
        self.LoupeViewTabs.setTabEnabled(3, True)
        self.LoupeViewTabs.setTabEnabled(4, True)
        self.LoupeViewTabs.setTabEnabled(5, False)
        self.LoupeViewTabs.setTabEnabled(6, False)
        self.LoupeViewTabs.setTabEnabled(7, False)
        self.LoupeViewTabs.setTabEnabled(8, False)
        self.LoupeViewTabs.setTabEnabled(9, False)
        self.LoupeViewTabs.setTabEnabled(10, False)
        self.LoupeViewTabs.setTabEnabled(11, True)

        # keep track of tabs that have been opened (no need to scale images)
        self.laserTabOpened = False
        self.mapTabOpened = False

        # create main tab
        self._addMainTab()
        # create laser normalization tab
        self._addLaserNormTab()
        # create cosmic ray removal tab
        self._addCosmicRayRemovalTab()
        # create false color map tab
        self._addFalseColorMapTab()

        # Add the display to the general layout
        # row, column, rowspan, colspan
        self.generalLayout.addWidget(self.LoupeViewTabs, 0, 0, 1, 1)



    ###################################################
    #  MAIN TAB START
    ###################################################
    def _addMainTab(self):
        # Add left pane with SOFF/table file information
        self.LoupeViewMainTabLayout = QGridLayout()
        _tab_main._addMainLeftPanel(self)
        _tab_main._addMainPlotPanel(self)
        _tab_main._addMainImgPanel(self)
        # Add the display to the general layout
        self.LoupeViewMainTab.setLayout(self.LoupeViewMainTabLayout)


    ###################################################
    #  MAIN TAB END
    ###################################################


    ###################################################
    #  COSMIC RAY TAB START
    ###################################################
    def _addCosmicRayTab(self):
        # Add left pane with SOFF/table file information
        self.LoupeViewCosmicRayTabLayout = QGridLayout()
        _tab_cosmic_ray._addCosmicRayLeftPanel(self)
        _tab_cosmic_ray._addCosmicRayPlotPanel(self)
        _tab_cosmic_ray._addCosmicRayImgPanel(self)
        # Add the display to the general layout
        self.LoupeViewCosmicRayTab.setLayout(self.LoupeViewCosmicRayTabLayout)


    ###################################################
    #  COSMIC RAY TAB END
    ###################################################


    ###################################################
    #  LASER NORMALIZATION TAB START
    ###################################################
    def _addLaserNormTab(self):
        # Add left pane with SOFF/table file information
        self.LoupeViewNormTabLayout = QGridLayout()
        _tab_laser_norm._addLaserNormLeftPanel(self)
        _tab_laser_norm._addLaserNormCenterPanel(self)
        # Add the display to the general layout
        self.LoupeViewNormTab.setLayout(self.LoupeViewNormTabLayout)


    ###################################################
    #  LASER NORMALIZATION TAB END
    ###################################################


    ###################################################
    #  COSMIC RAY REMOVAL TAB START
    ###################################################
    def _addCosmicRayRemovalTab(self):
        # Add left pane with SOFF/table file information
        self.LoupeViewCosmicTabLayout = QGridLayout()
        _tab_cosmic_ray._addCosmicLeftPanel(self)
        _tab_cosmic_ray._addCosmicCenterPanel(self)
        # Add the display to the general layout
        self.LoupeViewCosmicTab.setLayout(self.LoupeViewCosmicTabLayout)


    ###################################################
    #  COSMIC RAY REMOVAL TAB END
    ###################################################


    ###################################################
    #  FALSE COLOR MAP TAB START
    ###################################################
    def _addFalseColorMapTab(self):
        # Add left pane with SOFF/table file information
        self.LoupeViewRGBTabLayout = QGridLayout()
        _tab_false_color._addFalseColorLeftPanel(self)
        _tab_false_color._addFalseColorCenterPanel(self)
        # Add the display to the general layout
        self.LoupeViewRGBTab.setLayout(self.LoupeViewRGBTabLayout)


    ###################################################
    #  FALSE COLOR MAP TAB END
    ###################################################
