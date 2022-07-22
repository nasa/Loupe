import os
import pandas as pd
import copy
import time
import numpy as np
from PyQt5.QtWidgets import QTreeWidgetItem
from matplotlib import pyplot as plt

import functools

from src import log_parsing
from src import file_IO
from src import workspace_class
from src import roi_class

from src.loupe_control import _control_main
from src.loupe_control import _control_norm
from src.loupe_control import _control_cosmic
from src.loupe_control import _control_false_color

# controller class:
# access GUI's public interface, handle expressions and data modifications, connect signals with slots
class LoupeCtrl:
    # pass an instance of the view SPARViewUi
    def __init__(self, model, view):
        """Controller initializer."""
        self._model = model
        self._view = view
        # Connect signals and slots
        self._connectSignals()
        log_parsing.log_info(view, 'Initialized LoupeCtrl Class')
        log_parsing.log_info(view, 'Initialized Loupe')

    def _tabChange(self):
        if self._view.LoupeViewTabs.currentIndex() == 4:
            self._view.laserTabOpened = True
        elif self._view.LoupeViewTabs.currentIndex() == 11:
            self._view.mapTabOpened = True

    def _setCurrentWorkspace(self):
        # get the human readable workspace name from the combobox
        _workspaceDictKeyHumanReadable = str(self._view.selectedWorkspaceCombo.currentText())
        # convert human readable workspace name to soff name (workspace dict id)
        if _workspaceDictKeyHumanReadable in self._view.workspaceHumanToDictKey.keys():
            _workspaceDictKey = self._view.workspaceHumanToDictKey[_workspaceDictKeyHumanReadable]
            self._view.workspace = self._view.workspaceDict[_workspaceDictKey]
            for _roiName in self._view.workspace.selectedROI:
                if 'Full Map' not in _roiName:
                    if _roiName in self._view.workspace.selectedROI:
                        self._view.workspace.selectedROI.remove(_roiName)
                    if _roiName in self._view.workspace.selectedROIRGB:
                        self._view.workspace.selectedROIRGB.remove(_roiName)
                    if _roiName in self._view.workspace.selectedROICosmic:
                        self._view.workspace.selectedROICosmic.remove(_roiName)
        # check if soff file exists in loupe session dataframe
        elif self._view.loupeSession is not None and _workspaceDictKeyHumanReadable in self._view.loupeSession['workspaceHumanReadableName'].to_list():
            _dfIndex = self._view.loupeSession.index[self._view.loupeSession['workspaceHumanReadableName'] == _workspaceDictKeyHumanReadable][0]
            self._view.selectedMainFilename = os.path.join(os.path.split(self._view.loupeSessionFile)[0], self._view.loupeSession['soffPath'][_dfIndex])
            self._view.workspace = workspace_class.workspaceClass()
            self._view.roi = roi_class.roiClass()
            self._view.tempRoi = []
            self._view.tempRoiColor = '#00f2ff'
            #self._view.workspace.selectedROI = []
            #self._view.workspace.selectedROIRGB = []
            self._view.workspace.initNames(self._view.selectedMainFilename)
            log_parsing.log_info(self._view, 'Parsing file: {0}.'.format(self._view.selectedMainFilename))
            file_IO.parseMainFile(self._view, self._view.selectedMainFilename, self._view.workspace)
            self._view.workspaceDict[self._view.workspace.dictName] = self._view.workspace
            self._view.workspaceHumanToDictKey[self._view.workspace.humanReadableName] = self._view.workspace.dictName
            # check for the presence of ROIs
            # if there are none, add the Full Map
            if len(self._view.workspace.roiNames) == 0:
                # the default ROI is the full map
                _roi_name = 'Full Map'
                self._view.roi = roi_class.roiClass()
                self._view.roi.defineFull(_roi_name, self._view.workspace)
                self._view.workspace.roiNames = [_roi_name]
                self._view.roiDict[self._view.roi.dictName] = self._view.roi
                self._view.workspace.roiHumanToDictKey[self._view.roi.humanReadableName] = self._view.roi.dictName


    def _accessSparData(self):
        self._view.dimensionClassDict, self._view.dimensionDict, self._view.tableDict, self._view.fileNames, self._view.SPARProd = self._model(self._view.workspace.SOFFfile)


    def _readDataTables(self):
        log_parsing.log_info(self._view, 'Reading all data tables')
        # assume if spectral data does not exist in the workspace class, no tables have been loaded
        # TODO: update this with SPAR class, when Bob completes it, otherwise need to iterate over each dim in SPAR, which is slow (the below methods assume file names, no process data)
        _existingWorkspaceKeys = [k for k in self._view.workspaceHumanToDictKey.keys()]
        if self._view.workspace.humanReadableName in _existingWorkspaceKeys and self._view.workspaceDict[self._view.workspaceHumanToDictKey[self._view.workspace.humanReadableName]].activeSpectraR1['None'] is not None:
            self._view.workspace = self._view.workspaceDict[self._view.workspaceHumanToDictKey[self._view.workspace.humanReadableName]]
        else:
            self._view.workspace.nSpectra = self._view.dimensionDict['Points']['size']
            self._view.workspace.nChannels = self._view.dimensionDict['Channels']['size']
            if self._view.workspace.wavenumber == [] and self._view.workspace.wavelength == []:
                self._view.workspace.calculateWavelengthWavenumber(self._view)
            self._view.workspace.activeSpectraR1['None'] = pd.read_csv(os.path.join(self._view.workspace.workingDir, 'activeSpectra.csv'),
                                                                       skiprows=0, nrows=self._view.workspace.nSpectra)
            self._view.workspace.activeSpectraR2['None'] = pd.read_csv(os.path.join(self._view.workspace.workingDir, 'activeSpectra.csv'),
                                                                       skiprows=1+self._view.workspace.nSpectra, nrows=self._view.workspace.nSpectra)
            self._view.workspace.activeSpectraR3['None'] = pd.read_csv(os.path.join(self._view.workspace.workingDir, 'activeSpectra.csv'),
                                                                       skiprows=2*(1+self._view.workspace.nSpectra), nrows=self._view.workspace.nSpectra)
            self._view.workspace.darkSpectraR1['None'] = pd.read_csv(os.path.join(self._view.workspace.workingDir, 'darkSpectra.csv'),
                                                                     skiprows=0, nrows=self._view.workspace.nSpectra)
            self._view.workspace.darkSpectraR2['None'] = pd.read_csv(os.path.join(self._view.workspace.workingDir, 'darkSpectra.csv'),
                                                                     skiprows=1+self._view.workspace.nSpectra, nrows=self._view.workspace.nSpectra)
            self._view.workspace.darkSpectraR3['None'] = pd.read_csv(os.path.join(self._view.workspace.workingDir, 'darkSpectra.csv'),
                                                                     skiprows=2*(1+self._view.workspace.nSpectra), nrows=self._view.workspace.nSpectra)
            self._view.workspace.darkSubSpectraR1['None'] = pd.read_csv(os.path.join(self._view.workspace.workingDir, 'darkSubSpectra.csv'),
                                                                        skiprows=0, nrows=self._view.workspace.nSpectra)
            self._view.workspace.darkSubSpectraR2['None'] = pd.read_csv(os.path.join(self._view.workspace.workingDir, 'darkSubSpectra.csv'),
                                                                        skiprows=1+self._view.workspace.nSpectra, nrows=self._view.workspace.nSpectra)
            self._view.workspace.darkSubSpectraR3['None'] = pd.read_csv(os.path.join(self._view.workspace.workingDir, 'darkSubSpectra.csv'),
                                                                        skiprows=2*(1+self._view.workspace.nSpectra), nrows=self._view.workspace.nSpectra)
            if self._view.workspace.specProcessingApplied != 'None':
                for _i in range(len(self._view.workspace.specProcessingApplied)):
                    _processingFlag = self._view.workspace.specProcessingApplied[0:_i+1]
                    #if _processingFlag == 'N':
                    # TODO: update this when three processing flags become available
                    if os.path.exists(os.path.join(self._view.workspace.workingDir, 'activeSpectra{0}.csv'.format(_processingFlag))):
                        _activeFile = os.path.join(self._view.workspace.workingDir, 'activeSpectra{0}.csv'.format(_processingFlag))
                        self._view.workspace.activeSpectraR1[_processingFlag] = pd.read_csv(_activeFile, skiprows=0, nrows=self._view.workspace.nSpectra)
                        self._view.workspace.activeSpectraR2[_processingFlag] = pd.read_csv(_activeFile, skiprows=1+self._view.workspace.nSpectra, nrows=self._view.workspace.nSpectra)
                        self._view.workspace.activeSpectraR3[_processingFlag] = pd.read_csv(_activeFile, skiprows=2*(1+self._view.workspace.nSpectra), nrows=self._view.workspace.nSpectra)
                        _darkFile = os.path.join(self._view.workspace.workingDir, 'darkSpectra{0}.csv'.format(_processingFlag))
                        self._view.workspace.darkSpectraR1[_processingFlag] = pd.read_csv(_darkFile, skiprows=0, nrows=self._view.workspace.nSpectra)
                        self._view.workspace.darkSpectraR2[_processingFlag] = pd.read_csv(_darkFile, skiprows=1+self._view.workspace.nSpectra, nrows=self._view.workspace.nSpectra)
                        self._view.workspace.darkSpectraR3[_processingFlag] = pd.read_csv(_darkFile, skiprows=2*(1+self._view.workspace.nSpectra), nrows=self._view.workspace.nSpectra)
                        _darkSubFile = os.path.join(self._view.workspace.workingDir, 'darkSubSpectra{0}.csv'.format(_processingFlag))
                        self._view.workspace.darkSubSpectraR1[_processingFlag] = pd.read_csv(_darkSubFile, skiprows=0, nrows=self._view.workspace.nSpectra)
                        self._view.workspace.darkSubSpectraR2[_processingFlag] = pd.read_csv(_darkSubFile, skiprows=1+self._view.workspace.nSpectra, nrows=self._view.workspace.nSpectra)
                        self._view.workspace.darkSubSpectraR3[_processingFlag] = pd.read_csv(_darkSubFile, skiprows=2*(1+self._view.workspace.nSpectra), nrows=self._view.workspace.nSpectra)
                    else:
                        _processingFlag = self._view.workspace.specProcessingApplied[_i]
                        _activeFile = os.path.join(self._view.workspace.workingDir, 'activeSpectra{0}.csv'.format(_processingFlag))
                        self._view.workspace.activeSpectraR1[_processingFlag] = pd.read_csv(_activeFile, skiprows=0, nrows=self._view.workspace.nSpectra)
                        self._view.workspace.activeSpectraR2[_processingFlag] = pd.read_csv(_activeFile, skiprows=1+self._view.workspace.nSpectra, nrows=self._view.workspace.nSpectra)
                        self._view.workspace.activeSpectraR3[_processingFlag] = pd.read_csv(_activeFile, skiprows=2*(1+self._view.workspace.nSpectra), nrows=self._view.workspace.nSpectra)
                        _darkFile = os.path.join(self._view.workspace.workingDir, 'darkSpectra{0}.csv'.format(_processingFlag))
                        self._view.workspace.darkSpectraR1[_processingFlag] = pd.read_csv(_darkFile, skiprows=0, nrows=self._view.workspace.nSpectra)
                        self._view.workspace.darkSpectraR2[_processingFlag] = pd.read_csv(_darkFile, skiprows=1+self._view.workspace.nSpectra, nrows=self._view.workspace.nSpectra)
                        self._view.workspace.darkSpectraR3[_processingFlag] = pd.read_csv(_darkFile, skiprows=2*(1+self._view.workspace.nSpectra), nrows=self._view.workspace.nSpectra)
                        _darkSubFile = os.path.join(self._view.workspace.workingDir, 'darkSubSpectra{0}.csv'.format(_processingFlag))
                        self._view.workspace.darkSubSpectraR1[_processingFlag] = pd.read_csv(_darkSubFile, skiprows=0, nrows=self._view.workspace.nSpectra)
                        self._view.workspace.darkSubSpectraR2[_processingFlag] = pd.read_csv(_darkSubFile, skiprows=1+self._view.workspace.nSpectra, nrows=self._view.workspace.nSpectra)
                        self._view.workspace.darkSubSpectraR3[_processingFlag] = pd.read_csv(_darkSubFile, skiprows=2*(1+self._view.workspace.nSpectra), nrows=self._view.workspace.nSpectra)


            self._view.workspace.photodiodeAll = pd.read_csv(os.path.join(self._view.workspace.workingDir, 'photodiodeRaw.csv'))
            self._view.workspace.photodiodeSummary = pd.DataFrame(self._view.workspace.photodiodeAll.mean(axis=1), columns = ['summary_photodiode_value_0'])
            self._view.workspace.nShots = self._view.workspace.photodiodeAll.shape[1]

            # read contents of spatial.csv to determine which items are present
            with open(os.path.join(self._view.workspace.workingDir, 'spatial.csv'), 'r') as f:
                _contents = f.read()

            if 'az,el' in _contents:
                self._view.workspace.scannerTable = pd.read_csv(os.path.join(self._view.workspace.workingDir, 'spatial.csv'), nrows=self._view.workspace.nSpectra)
                self._view.workspace.az = self._view.workspace.scannerTable['az']
                self._view.workspace.el = self._view.workspace.scannerTable['el']

            _spatial_items = 1
            if 'az_commanded,el_commanded' in _contents:
                self._view.workspace.scannerTableCommanded = pd.read_csv(os.path.join(self._view.workspace.workingDir, 'spatial.csv'), skiprows=_spatial_items*(1+self._view.workspace.nSpectra), nrows=self._view.workspace.nSpectra)
                self._view.workspace.azCommanded = self._view.workspace.scannerTable['az_commanded']
                self._view.workspace.elCommanded = self._view.workspace.scannerTable['el_commanded']
                _spatial_items += 1


            if 'x,y' in _contents:
                self._view.workspace.xyTable = pd.read_csv(os.path.join(self._view.workspace.workingDir, 'spatial.csv'), skiprows=_spatial_items*(1+self._view.workspace.nSpectra), nrows=self._view.workspace.nSpectra)
                self._view.workspace.x = self._view.workspace.xyTable['x']
                self._view.workspace.y = self._view.workspace.xyTable['y']
                _spatial_items += 1

            if 'x_commanded,y_commanded' in _contents:
                self._view.workspace.xyTableCommanded = pd.read_csv(os.path.join(self._view.workspace.workingDir, 'spatial.csv'), skiprows=_spatial_items*(1+self._view.workspace.nSpectra), nrows=self._view.workspace.nSpectra)
                self._view.workspace.xCommanded = self._view.workspace.xyTableCommanded['x_commanded']
                self._view.workspace.yCommanded = self._view.workspace.xyTableCommanded['y_commanded']
                _spatial_items += 1

            if 'az_err,el_err' in _contents:
                self._view.workspace.scannerTableErr = pd.read_csv(os.path.join(self._view.workspace.workingDir, 'spatial.csv'), skiprows=_spatial_items*(1+self._view.workspace.nSpectra), nrows=self._view.workspace.nSpectra)
                self._view.workspace.azErr = self._view.workspace.scannerTableErr['az_err']
                self._view.workspace.elErr = self._view.workspace.scannerTableErr['el_err']
                _spatial_items += 1

            if 'sum_current,diff_current' in _contents:
                self._view.workspace.scannerCurrent = pd.read_csv(os.path.join(self._view.workspace.workingDir, 'spatial.csv'), skiprows=_spatial_items*(1+self._view.workspace.nSpectra), nrows=self._view.workspace.nSpectra)
                self._view.workspace.sumCurrent = self._view.workspace.scannerCurrent['sum_current']
                self._view.workspace.diffCurrent = self._view.workspace.scannerCurrent['diff_current']
                _spatial_items += 1


    def _setImgCombo(self):
        log_parsing.log_info(self._view, 'Reading image data')
        # list of aci filenames
        self._view.selectedACICombo.clear()
        self._view.selectedACIComboNorm.clear()
        self._view.selectedACIComboRGB.clear()
        _aciFiles = [file for file in self._view.fileNames if file[0:2] == 'SC' and file.endswith('PNG')]
        if len(_aciFiles) > 0:
            # populate ACI comboBox
            for f in _aciFiles:
                self._view.workspace.aciNames.append(os.path.split(f)[-1])
                self._view.selectedACICombo.addItem(f)
                self._view.selectedACIComboNorm.addItem(f)
                self._view.selectedACIComboRGB.addItem(f)
            self._view.selectedACICombo.setCurrentIndex(0)
            self._view.selectedACIComboNorm.setCurrentIndex(0)
            self._view.selectedACIComboRGB.setCurrentIndex(0)


    def _setACIPngName(self):
        self._view.workspace.selectedACIFilename = os.path.join(self._view.workspace.workingDir, 'img', str(self._view.selectedACICombo.currentText()))
        _control_main._parseACI(self)


    def _getAciPos(self, event):
        _pixPos = self._view.imageACI.mapToScene(event.pos())
        x = _pixPos.x()
        y = _pixPos.y()
        _control_main._updateACIPlot(self, x, y)

    def _getAciMapPos(self, event):
        _pixPos = self._view.imageACIMap.mapToScene(event.pos())
        x = _pixPos.x()
        y = _pixPos.y()
        _control_false_color._updateACIMapPlot(self, x, y)


    def _clickAddRoiPointMain(self, event):
        _pixPos = self._view.imageACI.mapToScene(event.pos())
        x = _pixPos.x()
        y = _pixPos.y()
        _control_main._roiSelectionAci(self, x, y)

    def _clickDelRoiPointMain(self, event):
        _pixPos = self._view.imageACI.mapToScene(event.pos())
        x = _pixPos.x()
        y = _pixPos.y()
        _control_main._roiSelectionAciRemove(self, x, y)

    def _updateEvent(self):
        log_parsing.log_info(self._view, 'Loaded workspace: {0}'.format(self._view.workspace.humanReadableName))

    def _connectSignals(self):
        """Connect signals and slots."""
        # SOFF file open
        # updates to these signals should be identical to reconnections in  _renameWorkspace
        self._view.selectedWorkspaceCombo.currentIndexChanged.connect(functools.partial(_control_main._clearMain, self))
        self._view.selectedWorkspaceCombo.currentIndexChanged.connect(self._setCurrentWorkspace)
        self._view.selectedWorkspaceCombo.currentIndexChanged.connect(self._accessSparData)
        self._view.selectedWorkspaceCombo.currentIndexChanged.connect(self._readDataTables)
        self._view.selectedWorkspaceCombo.currentIndexChanged.connect(self._setImgCombo)

        self._view.LoupeViewTabs.currentChanged.connect(self._tabChange)

        ####################
        # MAIN TAB: START
        ####################

        #################### Spectrum
        self._view.selectedWorkspaceCombo.currentIndexChanged.connect(functools.partial(_control_main._updateMainLeftPanel, self))
        self._view.selectedWorkspaceCombo.currentIndexChanged.connect(functools.partial(_control_main._updateMainPlotPanel, self))
        self._view.selectedWorkspaceCombo.currentIndexChanged.connect(functools.partial(_control_main._updateMainImgPanel, self))
        # populate the SOFF dimensions combo boxes
        self._view.selectedWorkspaceCombo.currentIndexChanged.connect(functools.partial(_control_main._initSparDim1Selection, self))
        # select dimension (x axis)
        self._view.selectedXDimCombo.activated.connect(functools.partial(_control_main._init1DSparDim1, self))
        # select dimension (y axis)
        self._view.selectedYDimCombo.activated.connect(functools.partial(_control_main._selectSparPlotDim2, self))
        # cursor selected
        self._view.cursorSpecMain.textChanged.connect(functools.partial(_control_main._selectSparPlotCursor, self))
        # add trace selection to plot
        self._view.addTraceButtonMain.clicked.connect(functools.partial(_control_main._addSparTrace, self))
        self._view.cursorSpecMain.returnPressed.connect(functools.partial(_control_main._addSparTrace, self))
        self._view.clearTraceButtonMain.clicked.connect(functools.partial(_control_main._clearSparPlotMain, self))

        self._view.humanReadableRename.returnPressed.connect(functools.partial(_control_main._renameWorkspace, self))

        # refresh plot if user switches between processing
        self._view.CosmicRayRemovalProcessingItemMain.clicked.connect(functools.partial(_control_main._plotMainUpdate, self))
        self._view.CosmicRayRemovalProcessingItemMain.clicked.connect(functools.partial(_control_main._plotLowerUpdate, self))
        self._view.CosmicRayRemovalProcessingItemMain.clicked.connect(functools.partial(_control_main._updateProcessingFlagsMain, self))
        self._view.BaselineSubtractionItemMain.clicked.connect(functools.partial(_control_main._plotMainUpdate, self))
        self._view.BaselineSubtractionItemMain.clicked.connect(functools.partial(_control_main._plotLowerUpdate, self))
        self._view.BaselineSubtractionItemMain.clicked.connect(functools.partial(_control_main._updateProcessingFlagsMain, self))
        self._view.LaserNormalizationItemMain.clicked.connect(functools.partial(_control_main._plotMainUpdate, self))
        self._view.LaserNormalizationItemMain.clicked.connect(functools.partial(_control_main._plotLowerUpdate, self))
        self._view.LaserNormalizationItemMain.clicked.connect(functools.partial(_control_main._updateProcessingFlagsMain, self))

        # refresh plot if the user switches between active, dark, active-dark
        self._view.activeItemMain.clicked.connect(functools.partial(_control_main._plotMainUpdate, self))
        self._view.activeItemMain.clicked.connect(functools.partial(_control_main._updateSelectionPlotMain, self))
        self._view.darkItemMain.clicked.connect(functools.partial(_control_main._plotMainUpdate, self))
        self._view.darkItemMain.clicked.connect(functools.partial(_control_main._updateSelectionPlotMain, self))
        self._view.darkSubMain.clicked.connect(functools.partial(_control_main._plotMainUpdate, self))
        self._view.darkSubMain.clicked.connect(functools.partial(_control_main._updateSelectionPlotMain, self))

        # refresh the plot if the user switches between mean and median display
        self._view.meanDisplayMain.clicked.connect(functools.partial(_control_main._plotMainUpdate, self))
        self._view.meanStdDisplay.clicked.connect(functools.partial(_control_main._plotMainUpdate, self))
        self._view.medianDisplayMain.clicked.connect(functools.partial(_control_main._plotMainUpdate, self))
        self._view.medianStdDisplay.clicked.connect(functools.partial(_control_main._plotMainUpdate, self))
        self._view.indexDisplayMain.clicked.connect(functools.partial(_control_main._plotMainUpdate, self))
        self._view.indexSpecMain.returnPressed.connect(functools.partial(_control_main._plotMainUpdate, self))

        self._view.waveDomainMain.clicked.connect(functools.partial(_control_main._plotMainUpdate, self))
        self._view.ccdDomainMain.clicked.connect(functools.partial(_control_main._plotMainUpdate, self))

        # refresh the plot if the user selects/de-selects regions
        self._view.R1ItemMain.clicked.connect(functools.partial(_control_main._plotMainUpdateRegion1, self))
        self._view.R2ItemMain.clicked.connect(functools.partial(_control_main._plotMainUpdateRegion2, self))
        self._view.R3ItemMain.clicked.connect(functools.partial(_control_main._plotMainUpdateRegion3, self))
        self._view.allItemMain.clicked.connect(functools.partial(_control_main._plotMainUpdateRegionAll, self))

        # vertical scale button
        self._view.toolbarResizeMain1.triggered.connect(functools.partial(_control_main._rescaleYMain1, self))
        self._view.toolbarResizeMain2.triggered.connect(functools.partial(_control_main._rescaleYMain2, self))


        #################### Imaging
        self._view.ACIFileSelectButton.clicked.connect(functools.partial(_control_main._openACI, self))
        self._view.selectedACICombo.currentTextChanged.connect(self._setACIPngName)
        self._view.opacityACIMain.valueChanged.connect(functools.partial(_control_main._addACIImage, self))
        self._view.opacityLaserMain.valueChanged.connect(functools.partial(_control_main._addACIImage, self))
        self._view.pointFillMain.clicked.connect(functools.partial(_control_main._addACIImage, self))
        self._view.imageACI.mouseDoubleClickEvent = self._getAciPos

        self._view.selectionScrollbarMain.valueChanged.connect(functools.partial(_control_main._updateLaserSelectionLineEdit, self))
        self._view.selectionScrollbarEdit.returnPressed.connect(functools.partial(_control_main._updateLaserSelectionScrollbar, self))

        self._view.resetLaserSpotMain.clicked.connect(functools.partial(_control_main._recalculateLaserSpots, self))

        #################### ROI
        self._view.ROIPolySelectButton.clicked.connect(functools.partial(_control_main._roiBoxSelection, self))
        self._view.ROIAddPointButton.clicked.connect(functools.partial(_control_main._roiAddSelection, self))
        self._view.ROIDelPointButton.clicked.connect(functools.partial(_control_main._roiDelSelection, self))
        self._view.ROISaveButton.clicked.connect(functools.partial(_control_main._roiSave, self))
        self._view.ROIColorButton.clicked.connect(functools.partial(_control_main._roiColorSelect, self))
        self._view.ROIClearPointButton.clicked.connect(functools.partial(_control_main._roiClear, self))
        self._view.ROIEditButton.clicked.connect(functools.partial(_control_main._roiEdit, self))
        self._view.ROIDeleteButton.clicked.connect(functools.partial(_control_main._roiDelete, self))
        self._view.ROIExportButton.clicked.connect(functools.partial(_control_main._roiExport, self))

        ####################
        # MAIN TAB: END
        ####################


        ####################
        # LASER NORMALIZATION TAB: START
        ####################

        self._view.selectedWorkspaceCombo.currentIndexChanged.connect(functools.partial(_control_norm._updateNormLeftPanel, self))
        self._view.selectedWorkspaceCombo.currentIndexChanged.connect(functools.partial(_control_norm._updateNormCentralPanel, self))

        self._view.opacityACINorm.valueChanged.connect(functools.partial(_control_norm._addACIImageNorm, self))
        self._view.opacityLaserNorm.valueChanged.connect(functools.partial(_control_norm._addACIImageNorm, self))

        self._view.normDiscrete.clicked.connect(functools.partial(_control_norm._addACIImageNorm, self))
        self._view.normInterpolated.clicked.connect(functools.partial(_control_norm._addACIImageNorm, self))

        self._view.avgPdSpecNorm.clicked.connect(functools.partial(_control_norm._displayPhotodiodePlot, self))
        self._view.avgPdShotNorm.clicked.connect(functools.partial(_control_norm._displayPhotodiodePlot, self))
        self._view.allPdShotNorm.clicked.connect(functools.partial(_control_norm._displayPhotodiodePlot, self))
        self._view.allPdSpecNorm.clicked.connect(functools.partial(_control_norm._displayPhotodiodePlot, self))

        self._view.LaserNormButton.clicked.connect(functools.partial(_control_norm._executeLaserNorm, self))

        # vertical scale button
        self._view.toolbarResizeNorm1.triggered.connect(functools.partial(_control_norm._rescaleYNorm1, self))

        ####################
        # LASER NORMALIZATION TAB: END
        ####################


        ####################
        # COSMIC RAY TAB: START
        ####################

        self._view.selectedWorkspaceCombo.currentIndexChanged.connect(functools.partial(_control_cosmic._clearCosmic, self))
        self._view.selectedWorkspaceCombo.currentIndexChanged.connect(functools.partial(_control_cosmic._updateCosmicLeftPanel, self))
        self._view.selectedWorkspaceCombo.currentIndexChanged.connect(functools.partial(_control_cosmic._updateCosmicCentralPanel, self))

        # refresh the upper plot if the user switches between active/dark
        self._view.activeItemHistCosmic.clicked.connect(functools.partial(_control_cosmic._histCosmicUpdate, self))
        self._view.darkItemHistCosmic.clicked.connect(functools.partial(_control_cosmic._histCosmicUpdate, self))
        # refresh the upper plot if the user switches regions
        self._view.R1ItemHistCosmic.clicked.connect(functools.partial(_control_cosmic._histCosmicUpdate, self))
        self._view.R2ItemHistCosmic.clicked.connect(functools.partial(_control_cosmic._histCosmicUpdate, self))
        self._view.R3ItemHistCosmic.clicked.connect(functools.partial(_control_cosmic._histCosmicUpdate, self))

        # refresh the upper plot if the user selects a new channel
        self._view.indexChannelCosmic.returnPressed.connect(functools.partial(_control_cosmic._histCosmicUpdate, self))
        # update the channel if the slider bar is modified
        self._view.selectionScrollbarChannelCosmic.valueChanged.connect(functools.partial(_control_cosmic._indexCosmicUpdate, self))
        # refresh the upper plot if the user redefines the threshold multiplier or sigma clipping value
        self._view.cosmicRayThreshold.returnPressed.connect(functools.partial(_control_cosmic._histCosmicUpdate, self))
        self._view.cosmicRaySigma.returnPressed.connect(functools.partial(_control_cosmic._histCosmicUpdate, self))


        # refresh plot if the user switches between active, dark, active-dark
        self._view.activeItemCosmic.clicked.connect(functools.partial(_control_cosmic._plotCosmicUpdate, self))
        self._view.darkItemCosmic.clicked.connect(functools.partial(_control_cosmic._plotCosmicUpdate, self))
        self._view.darkSubItemCosmic.clicked.connect(functools.partial(_control_cosmic._plotCosmicUpdate, self))

        # refresh the plot if the user switches between mean and median display
        self._view.meanDisplayCosmic.clicked.connect(functools.partial(_control_cosmic._plotCosmicUpdate, self))
        self._view.meanStdDisplayCosmic.clicked.connect(functools.partial(_control_cosmic._plotCosmicUpdate, self))
        self._view.medianDisplayCosmic.clicked.connect(functools.partial(_control_cosmic._plotCosmicUpdate, self))
        self._view.medianStdDisplayCosmic.clicked.connect(functools.partial(_control_cosmic._plotCosmicUpdate, self))
        self._view.maxDisplayCosmic.clicked.connect(functools.partial(_control_cosmic._plotCosmicUpdate, self))
        self._view.minDisplayCosmic.clicked.connect(functools.partial(_control_cosmic._plotCosmicUpdate, self))
        self._view.indexDisplayCosmic.clicked.connect(functools.partial(_control_cosmic._plotCosmicUpdate, self))
        self._view.indexDisplayCosmic.toggled.connect(functools.partial(_control_cosmic._manualGroupboxUpdate, self))
        # sync self._view.cosmicRayManualSpec and self._view.indexSpecCosmic, call a single function when only one changes
        self._view.indexSpecCosmic.returnPressed.connect(functools.partial(_control_cosmic._plotCosmicUpdateUpperIndex, self))
        self._view.cosmicRayManualSpec.returnPressed.connect(functools.partial(_control_cosmic._plotCosmicUpdateLowerIndex, self))
        # update the spectrum if the slider bar is modified
        self._view.selectionScrollbarCosmic.valueChanged.connect(functools.partial(_control_cosmic._specCosmicUpdateIndex, self))


        # refresh the plot if the user selects/de-selects regions
        self._view.R1ItemCosmic.clicked.connect(functools.partial(_control_cosmic._plotCosmicUpdateRegion1, self))
        self._view.R2ItemCosmic.clicked.connect(functools.partial(_control_cosmic._plotCosmicUpdateRegion2, self))
        self._view.R3ItemCosmic.clicked.connect(functools.partial(_control_cosmic._plotCosmicUpdateRegion3, self))
        self._view.allItemCosmic.clicked.connect(functools.partial(_control_cosmic._plotCosmicUpdateRegionAll, self))

        # refresh the plot if the user changes the domain type
        self._view.waveDomainCosmic.clicked.connect(functools.partial(_control_cosmic._plotCosmicUpdate, self))
        self._view.ccdDomainCosmic.clicked.connect(functools.partial(_control_cosmic._plotCosmicUpdate, self))


        # execute cosmic ray removal
        self._view.executeCosmicRay.clicked.connect(functools.partial(_control_cosmic._executeAutomatedCosmicRayRemoval, self))

        self._view.executeCosmicRaySelect.clicked.connect(functools.partial(_control_cosmic._selectCosmicRay, self))
        self._view.executeCosmicRayManual.clicked.connect(functools.partial(_control_cosmic._executeManualCosmicRayRemoval, self))

        self._view.saveCosmicRaySpec.clicked.connect(functools.partial(_control_cosmic._saveCosmicRayRemoval, self))
        self._view.resetCosmicRaySpec.clicked.connect(functools.partial(_control_cosmic._resetCosmicRayRemoval, self))

        self._view.CosmicRayRemovalProcessingItemMain.clicked.connect(functools.partial(_control_cosmic._plotCosmicUpdate, self))
        self._view.CosmicRayRemovalProcessingItemMain.clicked.connect(functools.partial(_control_cosmic._histCosmicUpdate, self))
        self._view.BaselineSubtractionItemMain.clicked.connect(functools.partial(_control_cosmic._plotCosmicUpdate, self))
        self._view.BaselineSubtractionItemMain.clicked.connect(functools.partial(_control_cosmic._histCosmicUpdate, self))
        self._view.LaserNormalizationItemMain.clicked.connect(functools.partial(_control_cosmic._plotCosmicUpdate, self))
        self._view.LaserNormalizationItemMain.clicked.connect(functools.partial(_control_cosmic._histCosmicUpdate, self))


        # manual cosmic ray selection
        # if the user inputs a wavelength, calculate the channel
        self._view.cosmicRayManualWavelength.returnPressed.connect(functools.partial(_control_cosmic._calcChannelManual, self))
        # if the user inputs a channel, calculate the wavelength
        self._view.cosmicRayManualChannel.returnPressed.connect(functools.partial(_control_cosmic._calcWavelengthManual, self))
        self._view.cosmicRayManualWidth.returnPressed.connect(functools.partial(_control_cosmic._addCosmicAlpha, self))
        self._view.R1ItemCosmicManual.clicked.connect(functools.partial(_control_cosmic._addCosmicAlpha, self))
        self._view.R2ItemCosmicManual.clicked.connect(functools.partial(_control_cosmic._addCosmicAlpha, self))
        self._view.R3ItemCosmicManual.clicked.connect(functools.partial(_control_cosmic._addCosmicAlpha, self))


        # vertical scale button
        self._view.toolbarResizeCosmic1.triggered.connect(functools.partial(_control_cosmic._rescaleYCosmic1, self))
        self._view.toolbarResizeCosmic2.triggered.connect(functools.partial(_control_cosmic._rescaleYCosmic2, self))

        ####################
        # COSMIC RAY TAB: END
        ####################


        ####################
        # FALSE COLOR MAP TAB: START
        ####################

        self._view.selectedWorkspaceCombo.currentIndexChanged.connect(functools.partial(_control_false_color._clearMap, self))
        self._view.selectedWorkspaceCombo.currentIndexChanged.connect(functools.partial(_control_false_color._updateRGBLeftPanel, self))
        self._view.selectedWorkspaceCombo.currentIndexChanged.connect(functools.partial(_control_false_color._updateRGBCentralPanel, self))


        # refresh the plot if the user switches between mean and median display
        self._view.meanDisplayRGB.clicked.connect(functools.partial(_control_false_color._plotMapUpdate, self))
        self._view.medianDisplayRGB.clicked.connect(functools.partial(_control_false_color._plotMapUpdate, self))
        self._view.indexDisplayRGB.clicked.connect(functools.partial(_control_false_color._plotMapUpdate, self))
        self._view.indexSpecRGB.returnPressed.connect(functools.partial(_control_false_color._plotMapUpdate, self))

        # refresh the plot if the user selects/de-selects regions
        self._view.R1ItemRGB.clicked.connect(functools.partial(_control_false_color._plotMapUpdateRegion1, self))
        self._view.R2ItemRGB.clicked.connect(functools.partial(_control_false_color._plotMapUpdateRegion2, self))
        self._view.R3ItemRGB.clicked.connect(functools.partial(_control_false_color._plotMapUpdateRegion3, self))
        self._view.allItemRGB.clicked.connect(functools.partial(_control_false_color._plotMapUpdateRegionAll, self))

        # R/G/B rectangular boxes
        self._view.redCheckRGB.clicked.connect(functools.partial(_control_false_color._plotMapUpdateBoxSelect, self))
        self._view.redPosRGB.returnPressed.connect(functools.partial(_control_false_color._plotMapUpdateBoxSelect, self))
        self._view.redWidthRGB.returnPressed.connect(functools.partial(_control_false_color._plotMapUpdateBoxSelect, self))
        self._view.redPosRGB.textChanged.connect(functools.partial(_control_false_color._updateRedValue, self))
        self._view.redWidthRGB.textChanged.connect(functools.partial(_control_false_color._updateRedValue, self))
        self._view.greenCheckRGB.clicked.connect(functools.partial(_control_false_color._plotMapUpdateBoxSelect, self))
        self._view.greenPosRGB.returnPressed.connect(functools.partial(_control_false_color._plotMapUpdateBoxSelect, self))
        self._view.greenWidthRGB.returnPressed.connect(functools.partial(_control_false_color._plotMapUpdateBoxSelect, self))
        self._view.greenPosRGB.textChanged.connect(functools.partial(_control_false_color._updateGreenValue, self))
        self._view.greenWidthRGB.textChanged.connect(functools.partial(_control_false_color._updateGreenValue, self))
        self._view.blueCheckRGB.clicked.connect(functools.partial(_control_false_color._plotMapUpdateBoxSelect, self))
        self._view.bluePosRGB.returnPressed.connect(functools.partial(_control_false_color._plotMapUpdateBoxSelect, self))
        self._view.blueWidthRGB.returnPressed.connect(functools.partial(_control_false_color._plotMapUpdateBoxSelect, self))
        self._view.bluePosRGB.textChanged.connect(functools.partial(_control_false_color._updateBlueValue, self))
        self._view.blueWidthRGB.textChanged.connect(functools.partial(_control_false_color._updateBlueValue, self))

        self._view.redHistLowRGB.textChanged.connect(functools.partial(_control_false_color._updateMapContrast, self, red=True))
        self._view.redHistHighRGB.textChanged.connect(functools.partial(_control_false_color._updateMapContrast, self, red=True))
        self._view.greenHistLowRGB.textChanged.connect(functools.partial(_control_false_color._updateMapContrast, self, green=True))
        self._view.greenHistHighRGB.textChanged.connect(functools.partial(_control_false_color._updateMapContrast, self, green=True))
        self._view.blueHistLowRGB.textChanged.connect(functools.partial(_control_false_color._updateMapContrast, self, blue=True))
        self._view.blueHistHighRGB.textChanged.connect(functools.partial(_control_false_color._updateMapContrast, self, blue=True))

        # interpolation display type
        self._view.RGBDiscrete.clicked.connect(functools.partial(_control_false_color._addACIImageRGB, self))
        self._view.RGBInterpolatedNearest.clicked.connect(functools.partial(_control_false_color._addACIImageRGB, self))
        self._view.RGBInterpolatedCubic.clicked.connect(functools.partial(_control_false_color._addACIImageRGB, self))

        # RGB calc type
        self._view.RGBMax.clicked.connect(functools.partial(_control_false_color._plotMapUpdateBoxSelect, self))
        self._view.RGBMedian.clicked.connect(functools.partial(_control_false_color._plotMapUpdateBoxSelect, self))
        self._view.RGBMean.clicked.connect(functools.partial(_control_false_color._plotMapUpdateBoxSelect, self))
        self._view.RGBIntegratedIntensity.clicked.connect(functools.partial(_control_false_color._plotMapUpdateBoxSelect, self))

        # opacity sliders
        self._view.opacityACIRGB.valueChanged.connect(functools.partial(_control_false_color._addACIImageRGB, self))
        self._view.opacityMapRGB.valueChanged.connect(functools.partial(_control_false_color._addACIImageRGB, self))

        self._view.imageACIMap.mouseDoubleClickEvent = self._getAciMapPos
        self._view.RGBExportButton.clicked.connect(functools.partial(_control_false_color._exportImageRGB, self))

        self._view.CosmicRayRemovalProcessingItemMain.clicked.connect(functools.partial(_control_false_color._plotMapUpdate, self))
        self._view.CosmicRayRemovalProcessingItemMain.clicked.connect(functools.partial(_control_false_color._updateMapContrast, self))
        self._view.BaselineSubtractionItemMain.clicked.connect(functools.partial(_control_false_color._plotMapUpdate, self))
        self._view.BaselineSubtractionItemMain.clicked.connect(functools.partial(_control_false_color._updateMapContrast, self))
        self._view.LaserNormalizationItemMain.clicked.connect(functools.partial(_control_false_color._plotMapUpdate, self))
        self._view.LaserNormalizationItemMain.clicked.connect(functools.partial(_control_false_color._updateMapContrast, self))

        # vertical scale button
        self._view.toolbarResizeMap1.triggered.connect(functools.partial(_control_false_color._rescaleYMap1, self))
        self._view.toolbarResizeMap2.triggered.connect(functools.partial(_control_false_color._rescaleYMap2, self))


        ####################
        # FALSE COLOR MAP TAB: END
        ####################


        self._view.selectedWorkspaceCombo.currentIndexChanged.connect(self._updateEvent)