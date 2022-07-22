import os
from PyQt5.QtCore import Qt

import numpy as np

from src import file_IO
from src import log_parsing
from src import soff_class


class workspaceClass():
    def __init__(self):
        self.selectedSOFFFilename = None
        self.selectedMainFilename = None
        self.selectedWATSONFilename = None
        self.selectedACIFilename = None
        self.selectedROI = []
        self.selectedROIRGB = []
        self.selectedROICosmic = []
        self.workingDir = None
        self.humanReadableName = ''
        self.dictName = ''
        self.azScale = 0.628154699
        self.elScale = 0.422441487
        self.laserCenter = (809, 664)
        self.rotation = 20.6793583
        self.SOFFfile = None
        self.roiNames = []
        self.roiHumanToDictKey = {}
        self.aciNames = []
        self.SelectedAciIndex = []
        self.watsonNames = []

        self.colorR1 = '#0099FF'
        self.colorR2 = '#00FF00'
        self.colorR3 = '#FF0000'
        self.colorComposite = 'w'


        self.activeSpectraR1 = {'None': None,
                                'N': None,
                                'B': None,
                                'C': None,
                                'NB': None,
                                'NC': None,
                                'BN': None,
                                'BC': None,
                                'CN': None,
                                'CB': None,
                                'NBC': None,
                                'NCB': None,
                                'CNB': None,
                                'CBN': None,
                                'BNC': None,
                                'BCN': None}
        self.darkSpectraR1 = {'None': None,
                              'N': None,
                              'B': None,
                              'C': None,
                              'NB': None,
                              'NC': None,
                              'BN': None,
                              'BC': None,
                              'CN': None,
                              'CB': None,
                              'NBC': None,
                              'NCB': None,
                              'CNB': None,
                              'CBN': None,
                              'BNC': None,
                              'BCN': None}
        self.darkSubSpectraR1 = {'None': None,
                                 'N': None,
                                 'B': None,
                                 'C': None,
                                 'NB': None,
                                 'NC': None,
                                 'BN': None,
                                 'BC': None,
                                 'CN': None,
                                 'CB': None,
                                 'NBC': None,
                                 'NCB': None,
                                 'CNB': None,
                                 'CBN': None,
                                 'BNC': None,
                                 'BCN': None}

        self.activeSpectraR2 = {'None': None,
                                'N': None,
                                'B': None,
                                'C': None,
                                'NB': None,
                                'NC': None,
                                'BN': None,
                                'BC': None,
                                'CN': None,
                                'CB': None,
                                'NBC': None,
                                'NCB': None,
                                'CNB': None,
                                'CBN': None,
                                'BNC': None,
                                'BCN': None}
        self.darkSpectraR2 = {'None': None,
                              'N': None,
                              'B': None,
                              'C': None,
                              'NB': None,
                              'NC': None,
                              'BN': None,
                              'BC': None,
                              'CN': None,
                              'CB': None,
                              'NBC': None,
                              'NCB': None,
                              'CNB': None,
                              'CBN': None,
                              'BNC': None,
                              'BCN': None}
        self.darkSubSpectraR2 = {'None': None,
                                 'N': None,
                                 'B': None,
                                 'C': None,
                                 'NB': None,
                                 'NC': None,
                                 'BN': None,
                                 'BC': None,
                                 'CN': None,
                                 'CB': None,
                                 'NBC': None,
                                 'NCB': None,
                                 'CNB': None,
                                 'CBN': None,
                                 'BNC': None,
                                 'BCN': None}

        self.activeSpectraR3 = {'None': None,
                                'N': None,
                                'B': None,
                                'C': None,
                                'NB': None,
                                'NC': None,
                                'BN': None,
                                'BC': None,
                                'CN': None,
                                'CB': None,
                                'NBC': None,
                                'NCB': None,
                                'CNB': None,
                                'CBN': None,
                                'BNC': None,
                                'BCN': None}
        self.darkSpectraR3 = {'None': None,
                              'N': None,
                              'B': None,
                              'C': None,
                              'NB': None,
                              'NC': None,
                              'BN': None,
                              'BC': None,
                              'CN': None,
                              'CB': None,
                              'NBC': None,
                              'NCB': None,
                              'CNB': None,
                              'CBN': None,
                              'BNC': None,
                              'BCN': None}
        self.darkSubSpectraR3 = {'None': None,
                                 'N': None,
                                 'B': None,
                                 'C': None,
                                 'NB': None,
                                 'NC': None,
                                 'BN': None,
                                 'BC': None,
                                 'CN': None,
                                 'CB': None,
                                 'NBC': None,
                                 'NCB': None,
                                 'CNB': None,
                                 'CBN': None,
                                 'BNC': None,
                                 'BCN': None}

        self.specProcessingApplied = 'None'

        self.tempCosmicRayR1 = None
        self.tempCosmicRayR2 = None
        self.tempCosmicRayR3 = None

        self.activeSpectra2D = None
        self.darkSpectra2D = None

        self.processSpectraR1 = None
        self.processSpectraR2 = None
        self.processSpectraR3 = None

        self.processSpectraBin = None

        self.spectraRank = None

        self.nSpectra = 0
        self.nShots = 0
        self.nChannels = 0
        self.laserWavelength = 0
        self.wavelength = []
        self.wavenumber = []
        self.nBinSpectra = 0
        self.spectralBinChannels = None
        self.spectraRank = None
        self.algorithmsApplied = None
        self.classificationID = None
        self.zoneStart = [0]*6
        self.zoneStop = [0]*6
        self.photodiodeAll = None
        self.photodiodeSummary = None
        self.spatialBinningTable = None

        self.az = None
        self.el = None
        self.scannerTable = None
        self.azCommanded = None
        self.elCommanded = None
        self.scannerTableCommanded = None
        self.x = None
        self.y = None
        self.xPix = None
        self.yPix = None
        self.laserPix = None
        self.xyTable = None
        self.xCommanded = None
        self.yCommanded = None
        self.xyTableCommanded = None
        self.azErr = None
        self.elErr = None
        self.scannerTableErr = None
        self.sumCurrent = None
        self.diffCurrent = None
        self.scannerCurrent = None

        # COLLECT_SOH
        self.CNDH_PCB_TEMP_STAT_REG = ['N/A']
        self.CNDH_1_2_V_STAT_REG = ['N/A']
        self.CNDH_5_V_DAC_STAT_REG = ['N/A']
        self.CNDH_3_3_V_STAT_REG = ['N/A']
        self.CNDH_5_V_ADC_STAT_REG = ['N/A']
        self.CNDH_NEG_15_V_STAT_REG = ['N/A']
        self.CNDH_15_V_STAT_REG = ['N/A']
        self.CNDH_1_5_V_STAT_REG = ['N/A']
        self.laser_shot_counter = ['N/A']
        self.laser_misfire_counter = ['N/A']
        self.arc_event_counter = ['N/A']
        # SE_COLLECT_SOH
        self.SE_CCD_ID_STAT_REG = ['N/A']
        self.SE_CCD_TEMP_STAT_REG = ['N/A']
        self.SE_PCB_TEMP_STAT_REG = ['N/A']
        self.SE_V_1_5_STAT_REG = ['N/A']
        self.SE_LASER_PRT2_STAT_REG = ['N/A']
        self.SE_LASER_PRT1_STAT_REG = ['N/A']
        self.SE_LPS_PRT1_STAT_REG = ['N/A']
        self.SE_TPRB_HOUSING_PRT_STAT_REG = ['N/A']
        self.SE_LPS_PRT2_STAT_REG = ['N/A']
        self.SE_SPARE1_PRT_STAT_REG = ['N/A']
        # CONFIG_CCD_VERT_TIMING
        self.CCD_VERT_COL1_LOW = ['N/A']
        self.CCD_VERT_COL1_HIGH = ['N/A']
        self.CCD_VERT_COL2_LOW = ['N/A']
        self.CCD_VERT_COL2_HIGH = ['N/A']
        self.CCD_VERT_COL3_LOW = ['N/A']
        self.CCD_VERT_COL3_HIGH = ['N/A']
        # CONFIG_CCD_HORZ_TIMING
        self.CCD_HORZ_CLOCK_LIM = ['N/A']
        self.CCD_HORZ_R1_CLOCK_HIGH = ['N/A']
        self.CCD_HORZ_R1_CLOCK_Low = ['N/A']
        self.CCD_HORZ_R2_CLOCK_HIGH = ['N/A']
        self.CCD_HORZ_R2_CLOCK_Low = ['N/A']
        self.CCD_HORZ_R3_CLOCK_HIGH = ['N/A']
        self.CCD_HORZ_R3_CLOCK_Low = ['N/A']
        # CONFIG_CCD_REGIONS
        self.CCD_GAIN_2D = ['N/A']
        self.MODE_2D = ['N/A']
        self.REGION_ENABLE = ['N/A']
        self.HORZ_ENABLE = ['N/A']
        self.GAIN_ENABLE = ['N/A']
        self.SKIP_1 = ['N/A']
        self.SUM_1 = ['N/A']
        self.SKIP_2 = ['N/A']
        self.SUM_2 = ['N/A']
        self.SKIP_3 = ['N/A']
        self.SUM_3 = ['N/A']
        self.SKIP_4 = ['N/A']
        self.SUM_4 = ['N/A']
        self.SKIP_5 = ['N/A']
        self.SUM_5 = ['N/A']
        self.LAST_SKIP = ['N/A']
        # CONFI_LASER_TIMING
        self.LASER_INT_TIME = ['N/A']
        self.LASER_REP_RATE = ['N/A']
        self.LASER_ON_TIME = ['N/A']
        self.PULSE_WIDTH = ['N/A']
        self.LASER_CURRENT = ['N/A']
        self.LASER_SHOTS = ['N/A']

        self.WATSONAttributes = {'pixelScale': 'N/A',
                                 'range': 'N/A',
                                 'CDPID': 'N/A',
                                 'motor_pos': 'N/A',
                                 'exp_time': 'N/A',
                                 'product_ID': 'N/A',
                                 'led_flag': 'N/A'}

        self.ACIAttributes = {'pixelScale': 'N/A',
                              'range': 'N/A',
                              'CDPID': 'N/A',
                              'motor_pos': 'N/A',
                              'exp_time': 'N/A',
                              'product_ID': 'N/A',
                              'led_flag': 'N/A'}

        self.laserIntMap = None

    def initNames(self, selectedMainFilename):
        self.workingDir = file_IO.get_working_dir(selectedMainFilename)
        self.selectedMainFilename = os.path.split(selectedMainFilename)[-1].split('.')[0]
        self.dictName = os.path.split(selectedMainFilename)[-1].split('.')[0]
        self.humanReadableName = os.path.split(selectedMainFilename)[-1].split('.')[0]


    # updating this combobox is a signal for : read SOFF file to get dimension information
    def addWorkspaceItemCombo(self, view):
        #_selectedWorkspaceComboItems = [self.selectedWorkspaceCombo.itemText(i) for i in range(self.selectedWorkspaceCombo.count())]
        _selectedWorkspaceIndex = view.selectedWorkspaceCombo.findText(self.humanReadableName, Qt.MatchFixedString)
        if _selectedWorkspaceIndex > 0:
            view.selectedWorkspaceCombo.setCurrentIndex(_selectedWorkspaceIndex)
        else:
            view.selectedWorkspaceCombo.addItem(self.humanReadableName)
        # get index of this item
        _workspaceItems = [view.selectedWorkspaceCombo.itemText(i) for i in range(view.selectedWorkspaceCombo.count())]
        _workspaceIndex = np.argwhere(np.array(_workspaceItems) == self.humanReadableName)[0][0]
        # populate workspace combobox from loupeSession
        if view.loupeSession is not None:
            for _item in view.loupeSession['workspaceHumanReadableName']:
                if _item not in _workspaceItems:
                    view.selectedWorkspaceCombo.addItem(_item)

        view.selectedWorkspaceCombo.setCurrentIndex(_workspaceIndex)




    def writeDataCsv(self, view, SOFF_only = False):
        log_parsing.log_info(view, 'Writing data to {0} for easier access next time this workspace is accessed'.format(self.workingDir))
        # save spectral data
        # determine which kind of spectra were acquired
        # for raw spec:
        if self.activeSpectraR1['None'] is not None:
            log_parsing.log_info(view, 'Identified full spectrum')
            _active_spec_file = os.path.join(self.workingDir, 'activeSpectra.csv')
            if not SOFF_only:
                file_IO.writeSpectraRegions(_active_spec_file, view, self.activeSpectraR1['None'], self.activeSpectraR2['None'], self.activeSpectraR3['None'])
            _dark_spec_file = os.path.join(self.workingDir, 'darkSpectra.csv')
            if not SOFF_only:
                file_IO.writeSpectraRegions(_dark_spec_file, view, self.darkSpectraR1['None'], self.darkSpectraR2['None'], self.darkSpectraR3['None'])
            _dark_sub_spec_file = os.path.join(self.workingDir, 'darkSubSpectra.csv')
            if not SOFF_only:
                file_IO.writeSpectraRegions(_dark_sub_spec_file, view, self.darkSubSpectraR1['None'], self.darkSubSpectraR2['None'], self.darkSubSpectraR3['None'])
            _pd_file = os.path.join(self.workingDir, 'photodiodeRaw.csv')
            if not SOFF_only:
                file_IO.writePandasArr(_pd_file, view, self.photodiodeAll)
            _spatial_file = os.path.join(self.workingDir, 'spatial.csv')
            if not SOFF_only:
                file_IO.writeTable(_spatial_file, view, self.scannerTable, self.scannerTableCommanded, self.xyTable, self.xyTableCommanded, self.scannerTableErr, self.scannerCurrent)
            _loupe_file = os.path.join(self.workingDir, 'loupe.csv')
            if not SOFF_only:
                file_IO.writeLoupeCsv(_loupe_file, view)
            _roi_file = os.path.join(self.workingDir, 'roi.csv')
            if not SOFF_only:
                file_IO.writeRoiCsv(_roi_file, view)
            # TODO: write processed spectra (when reading EDRs/RDRs)

            self.defineSoffClassesRawDp(_active_spec_file, _dark_spec_file, _dark_sub_spec_file, _pd_file, _spatial_file)

        elif self.processSpectraR1 is not None and self.spatialBinningTable is None:
            log_parsing.log_info(view, 'Identified process data spectra. No spatial binning')

        elif self.processSpectraR1 is not None and self.spatialBinningTable is not None:
            log_parsing.log_info(view, 'Identified process data spectra with spatial binning')

        elif self.processSpectraBin is not None:
            log_parsing.log_info(view, 'Identified spectrally binned product')

        elif self.spectraRank is not None:
            log_parsing.log_info(view, 'Identified ranked spectra product')

        else:
            log_parsing.log_error(view, 'No spectral data. Process data photodiode dump product identified')


    def defineSoffClassesRawDp(self, _active_spec_file, _dark_spec_file, _dark_sub_spec_file, _pd_file, _spatial_file):
        # define SOFF class for each data table, dimension, and SOFF table
        self.tableR1Active = soff_class.SoffClassTable()
        self.tableR1Active.table_define(filename = os.path.split(_active_spec_file)[-1],
                                        lid = 'active_R1',
                                        byte_offset = file_IO.get_offset(_active_spec_file, self.activeSpectraR1['None']),
                                        records = self.nSpectra,
                                        fields_main = 0,
                                        groups = 1,
                                        groups_repetitions = 2148,
                                        groups_fields = 1,
                                        groups_groups = 0,
                                        field_names = ['Channels'],
                                        data_type = ['ASCII_Real'])

        self.tableR2Active = soff_class.SoffClassTable()
        self.tableR2Active.table_define(filename = os.path.split(_active_spec_file)[-1],
                                        lid = 'active_R2',
                                        byte_offset = file_IO.get_offset(_active_spec_file, self.activeSpectraR2['None']),
                                        records = self.nSpectra,
                                        fields_main = 0,
                                        groups = 1,
                                        groups_repetitions = 2148,
                                        groups_fields = 1,
                                        groups_groups = 0,
                                        field_names = ['Channels'],
                                        data_type = ['ASCII_Real'])

        self.tableR3Active = soff_class.SoffClassTable()
        self.tableR3Active.table_define(filename = os.path.split(_active_spec_file)[-1],
                                        lid = 'active_R3',
                                        byte_offset = file_IO.get_offset(_active_spec_file, self.activeSpectraR3['None']),
                                        records = self.nSpectra,
                                        fields_main = 0,
                                        groups = 1,
                                        groups_repetitions = 2148,
                                        groups_fields = 1,
                                        groups_groups = 0,
                                        field_names = ['Channels'],
                                        data_type = ['ASCII_Real'])


        self.tableR1Dark = soff_class.SoffClassTable()
        self.tableR1Dark.table_define(filename = os.path.split(_dark_spec_file)[-1],
                                      lid = 'dark_R1',
                                      byte_offset = file_IO.get_offset(_dark_spec_file, self.darkSpectraR1['None']),
                                      records = self.nSpectra,
                                      fields_main = 0,
                                      groups = 1,
                                      groups_repetitions = 2148,
                                      groups_fields = 1,
                                      groups_groups = 0,
                                      field_names = ['Channels'],
                                      data_type = ['ASCII_Real'])

        self.tableR2Dark = soff_class.SoffClassTable()
        self.tableR2Dark.table_define(filename = os.path.split(_dark_spec_file)[-1],
                                      lid = 'dark_R2',
                                      byte_offset = file_IO.get_offset(_dark_spec_file, self.darkSpectraR2['None']),
                                      records = self.nSpectra,
                                      fields_main = 0,
                                      groups = 1,
                                      groups_repetitions = 2148,
                                      groups_fields = 1,
                                      groups_groups = 0,
                                      field_names = ['Channels'],
                                      data_type = ['ASCII_Real'])

        self.tableR3Dark = soff_class.SoffClassTable()
        self.tableR3Dark.table_define(filename = os.path.split(_dark_spec_file)[-1],
                                      lid = 'dark_R3',
                                      byte_offset = file_IO.get_offset(_dark_spec_file, self.darkSpectraR3['None']),
                                      records = self.nSpectra,
                                      fields_main = 0,
                                      groups = 1,
                                      groups_repetitions = 2148,
                                      groups_fields = 1,
                                      groups_groups = 0,
                                      field_names = ['Channels'],
                                      data_type = ['ASCII_Real'])

        self.tableR1DarkSub = soff_class.SoffClassTable()
        self.tableR1DarkSub.table_define(filename = os.path.split(_dark_sub_spec_file)[-1],
                                         lid = 'darkSub_R1',
                                         byte_offset = file_IO.get_offset(_dark_sub_spec_file, self.darkSubSpectraR1['None']),
                                         records = self.nSpectra,
                                         fields_main = 0,
                                         groups = 1,
                                         groups_repetitions = 2148,
                                         groups_fields = 1,
                                         groups_groups = 0,
                                         field_names = ['Channels'],
                                         data_type = ['ASCII_Real'])

        self.tableR2DarkSub = soff_class.SoffClassTable()
        self.tableR2DarkSub.table_define(filename = os.path.split(_dark_sub_spec_file)[-1],
                                         lid = 'darkSub_R2',
                                         byte_offset = file_IO.get_offset(_dark_sub_spec_file, self.darkSubSpectraR2['None']),
                                         records = self.nSpectra,
                                         fields_main = 0,
                                         groups = 1,
                                         groups_repetitions = 2148,
                                         groups_fields = 1,
                                         groups_groups = 0,
                                         field_names = ['Channels'],
                                         data_type = ['ASCII_Real'])

        self.tableR3DarkSub = soff_class.SoffClassTable()
        self.tableR3DarkSub.table_define(filename = os.path.split(_dark_sub_spec_file)[-1],
                                         lid = 'darkSub_R3',
                                         byte_offset = file_IO.get_offset(_dark_sub_spec_file, self.darkSubSpectraR3['None']),
                                         records = self.nSpectra,
                                         fields_main = 0,
                                         groups = 1,
                                         groups_repetitions = 2148,
                                         groups_fields = 1,
                                         groups_groups = 0,
                                         field_names = ['Channels'],
                                         data_type = ['ASCII_Real'])


        self.dimensionPoints = soff_class.SoffClassDimension()
        self.dimensionPoints.dimension_define(soff_class = 'Points',
                                              comment = 'Single SHERLOC Map',
                                              elements = self.nSpectra,
                                              lid = 'Points')

        self.dimensionChannels = soff_class.SoffClassDimension()
        self.dimensionChannels.dimension_define(soff_class = 'Channels',
                                                comment = 'Channel for SHERLOC SCCD',
                                                elements = 2148,
                                                lid = 'Channels')

        self.dimensionShots = soff_class.SoffClassDimension()
        self.dimensionShots.dimension_define(soff_class='Shots',
                                             comment='Number of laser shots at each point',
                                             elements=self.nShots,
                                             lid='Shots')

        self.dimensionUnity = soff_class.SoffClassDimension()
        self.dimensionUnity.dimension_define(soff_class='Unity',
                                             comment='Unity dimension - size=1',
                                             elements=1,
                                             lid='Unity')



        self.soffActiveR1 = soff_class.SoffClassSoffTable()
        self.soffActiveR1.dataTable_define(name = 'R1 Active Table',
                                           dimensionLID = ['Points', 'Channels'],
                                           tableLID = 'active_R1',
                                           description = 'Region 1 active spectra')

        self.soffActiveR2 = soff_class.SoffClassSoffTable()
        self.soffActiveR2.dataTable_define(name = 'R2 Active Table',
                                           dimensionLID = ['Points', 'Channels'],
                                           tableLID = 'active_R2',
                                           description = 'Region 2 active spectra')

        self.soffActiveR3 = soff_class.SoffClassSoffTable()
        self.soffActiveR3.dataTable_define(name = 'R3 Active Table',
                                           dimensionLID = ['Points', 'Channels'],
                                           tableLID = 'active_R3',
                                           description = 'Region 3 active spectra')

        self.soffDarkR1 = soff_class.SoffClassSoffTable()
        self.soffDarkR1.dataTable_define(name = 'R1 Dark Table',
                                         dimensionLID = ['Points', 'Channels'],
                                         tableLID = 'dark_R1',
                                         description = 'Region 1 dark spectra')

        self.soffDarkR2 = soff_class.SoffClassSoffTable()
        self.soffDarkR2.dataTable_define(name = 'R2 Dark Table',
                                         dimensionLID = ['Points', 'Channels'],
                                         tableLID = 'dark_R2',
                                         description = 'Region 2 dark spectra')

        self.soffDarkR3 = soff_class.SoffClassSoffTable()
        self.soffDarkR3.dataTable_define(name = 'R3 Dark Table',
                                         dimensionLID = ['Points', 'Channels'],
                                         tableLID = 'dark_R3',
                                         description = 'Region 3 dark spectra')

        self.soffDarkSubR1 = soff_class.SoffClassSoffTable()
        self.soffDarkSubR1.dataTable_define(name = 'R1 Dark-Subtracted Table',
                                            dimensionLID = ['Points', 'Channels'],
                                            tableLID = 'darkSub_R1',
                                            description = 'Region 1 dark-subtracted spectra')

        self.soffDarkSubR2 = soff_class.SoffClassSoffTable()
        self.soffDarkSubR2.dataTable_define(name = 'R2 Dark-Subtracted Table',
                                            dimensionLID = ['Points', 'Channels'],
                                            tableLID = 'darkSub_R2',
                                            description = 'Region 2 dark-subtracted spectra')

        self.soffDarkSubR3 = soff_class.SoffClassSoffTable()
        self.soffDarkSubR3.dataTable_define(name = 'R3 Dark-Subtracted Table',
                                            dimensionLID = ['Points', 'Channels'],
                                            tableLID = 'darkSub_R3',
                                            description = 'Region 3 dark-subtracted spectra')

        self.soffTableList = [self.tableR1Active, self.tableR1Dark, self.tableR2Active, self.tableR2Dark, self.tableR3Active, self.tableR3Dark, self.tableR1DarkSub, self.tableR2DarkSub, self.tableR3DarkSub]
        self.soffSoffTableList = [self.soffActiveR1, self.soffDarkR1, self.soffActiveR2, self.soffDarkR2, self.soffActiveR3, self.soffDarkR3, self.soffDarkSubR1, self.soffDarkSubR2, self.soffDarkSubR3]




        if self.photodiodeAll is not None:
            self.tablePhotodiodeAll = soff_class.SoffClassTable()
            self.tablePhotodiodeAll.table_define(filename=os.path.split(_pd_file)[-1],
                                                 lid='photodiode_all',
                                                 byte_offset=file_IO.get_offset(_pd_file, self.photodiodeAll),
                                                 records=self.nSpectra,
                                                 fields_main=0,
                                                 groups=1,
                                                 groups_repetitions=self.nShots,
                                                 groups_fields=1,
                                                 groups_groups=0,
                                                 field_names=['Shots'],
                                                 data_type=['ASCII_Real'])
            self.soffPhotodiodeAll = soff_class.SoffClassSoffTable()
            self.soffPhotodiodeAll.dataTable_define(name='Photodiode All',
                                                    dimensionLID=['Points', 'Shots'],
                                                    tableLID='photodiode_all',
                                                    description='All photodiode data')
            self.soffTableList.append(self.tablePhotodiodeAll)
            self.soffSoffTableList.append(self.soffPhotodiodeAll)

        if self.scannerTable is not None:
            self.tableSpatial = soff_class.SoffClassTable()
            self.tableSpatial.table_define(filename=os.path.split(_spatial_file)[-1],
                                           lid='spatial_az_el',
                                           byte_offset=file_IO.get_offset(_spatial_file, self.scannerTable),
                                           records=self.nSpectra,
                                           fields_main=2,
                                           groups=0,
                                           groups_repetitions=0,
                                           groups_fields=0,
                                           groups_groups=0,
                                           field_names=['Azimuth', 'Elevation'],
                                           data_type=['ASCII_Real', 'ASCII_Real'])
            self.soffSpatial = soff_class.SoffClassSoffTable()
            self.soffSpatial.dataTable_define(name='Spatial Table',
                                                dimensionLID=['Points'],
                                                tableLID='spatial_az_el',
                                                description='Scanner Azimuth/Elevation')
            self.soffTableList.append(self.tableSpatial)
            self.soffSoffTableList.append(self.soffSpatial)

        if self.scannerTableCommanded is not None:
            self.tableSpatialCommanded = soff_class.SoffClassTable()
            self.tableSpatialCommanded.table_define(filename=os.path.split(_spatial_file)[-1],
                                           lid='spatial_az_el_commanded',
                                           byte_offset=file_IO.get_offset(_spatial_file, self.scannerTableCommanded),
                                           records=self.nSpectra,
                                           fields_main=2,
                                           groups=0,
                                           groups_repetitions=0,
                                           groups_fields=0,
                                           groups_groups=0,
                                           field_names=['Azimuth Commanded', 'Elevation Commanded'],
                                           data_type=['ASCII_Real', 'ASCII_Real'])
            self.soffSpatialCommanded = soff_class.SoffClassSoffTable()
            self.soffSpatialCommanded.dataTable_define(name='Spatial Table Commanded',
                                                dimensionLID=['Points'],
                                                tableLID='spatial_az_el_commanded',
                                                description='Commanded Scanner Azimuth/Elevation')
            self.soffTableList.append(self.tableSpatialCommanded)
            self.soffSoffTableList.append(self.soffSpatialCommanded)

        if self.xyTable is not None:
            self.tableXy= soff_class.SoffClassTable()
            self.tableXy.table_define(filename=os.path.split(_spatial_file)[-1],
                                           lid='spatial_x_y',
                                           byte_offset=file_IO.get_offset(_spatial_file, self.xyTable),
                                           records=self.nSpectra,
                                           fields_main=2,
                                           groups=0,
                                           groups_repetitions=0,
                                           groups_fields=0,
                                           groups_groups=0,
                                           field_names=['x', 'y'],
                                           data_type=['ASCII_Real', 'ASCII_Real'])
            self.soffXyTable = soff_class.SoffClassSoffTable()
            self.soffXyTable.dataTable_define(name='Spatial Table XY',
                                                dimensionLID=['Points'],
                                                tableLID='spatial_x_y',
                                                description='X/Y Table')
            self.soffTableList.append(self.tableXy)
            self.soffSoffTableList.append(self.soffXyTable)

        if self.xyTableCommanded is not None:
            self.tableXyCommanded = soff_class.SoffClassTable()
            self.tableXyCommanded.table_define(filename=os.path.split(_spatial_file)[-1],
                                           lid='spatial_x_y_commanded',
                                           byte_offset=file_IO.get_offset(_spatial_file, self.xyTableCommanded),
                                           records=self.nSpectra,
                                           fields_main=2,
                                           groups=0,
                                           groups_repetitions=0,
                                           groups_fields=0,
                                           groups_groups=0,
                                           field_names=['x Commanded', 'y Commanded'],
                                           data_type=['ASCII_Real', 'ASCII_Real'])
            self.soffXyTableCommanded = soff_class.SoffClassSoffTable()
            self.soffXyTableCommanded.dataTable_define(name='Commanded Spatial Table XY',
                                                dimensionLID=['Points'],
                                                tableLID='spatial_x_y_commanded',
                                                description='Commanded X/Y Table')
            self.soffTableList.append(self.tableXyCommanded)
            self.soffSoffTableList.append(self.soffXyTableCommanded)

        if self.scannerTableErr is not None:
            self.tableScannerErr = soff_class.SoffClassTable()
            self.tableScannerErr.table_define(filename=os.path.split(_spatial_file)[-1],
                                           lid='scanner_err',
                                           byte_offset=file_IO.get_offset(_spatial_file, self.scannerTableErr),
                                           records=self.nSpectra,
                                           fields_main=2,
                                           groups=0,
                                           groups_repetitions=0,
                                           groups_fields=0,
                                           groups_groups=0,
                                           field_names=['azimuth error', 'elevation error'],
                                           data_type=['ASCII_Real', 'ASCII_Real'])
            self.soffScannerErr = soff_class.SoffClassSoffTable()
            self.soffScannerErr.dataTable_define(name='Scanner Error',
                                                dimensionLID=['Points'],
                                                tableLID='scanner_err',
                                                description='Azimuth/Elevation error')
            self.soffTableList.append(self.tableScannerErr)
            self.soffSoffTableList.append(self.soffScannerErr)

        if self.scannerCurrent is not None:
            self.tableScannerCurrent = soff_class.SoffClassTable()
            self.tableScannerCurrent.table_define(filename=os.path.split(_spatial_file)[-1],
                                           lid='scanner_current',
                                           byte_offset=file_IO.get_offset(_spatial_file, self.scannerCurrent),
                                           records=self.nSpectra,
                                           fields_main=2,
                                           groups=0,
                                           groups_repetitions=0,
                                           groups_fields=0,
                                           groups_groups=0,
                                           field_names=['sum current', 'difference current'],
                                           data_type=['ASCII_Real', 'ASCII_Real'])
            self.soffScannerCurrent = soff_class.SoffClassSoffTable()
            self.soffScannerCurrent.dataTable_define(name='Scanner Current',
                                                dimensionLID=['Points'],
                                                tableLID='scanner_current',
                                                description='Sum/Diff scanner current')
            self.soffTableList.append(self.tableScannerCurrent)
            self.soffSoffTableList.append(self.soffScannerCurrent)


        self.soffFileList = [os.path.split(_active_spec_file)[-1], os.path.split(_dark_spec_file)[-1], os.path.split(_dark_sub_spec_file)[-1], os.path.split(_pd_file)[-1], os.path.split(_spatial_file)[-1]]
        self.soffDimensionList = [self.dimensionPoints, self.dimensionChannels, self.dimensionShots]


        # TODO: add all other spectral files, if they exist (this may not be necessary unless using the SOFF viewer - this is a low priority)


    def generateSOFF(self, view):
        log_parsing.log_info(view, 'Generating SOFF file')
        # define SOFF file name
        self.SOFFfile = os.path.join(self.workingDir, os.path.split(self.selectedMainFilename)[-1].split('.')[0]+'_soff.xml')
        # write SOFF file
        file_IO.writeSOFF(self, view._appctxt.get_resource('soff_xml_text.txt'))


    def calculateWavelengthWavenumber(self, view):
        # use default wavelength calibration values
        log_parsing.log_info(view, 'Calculating wavelength and Raman shift from default segmented polynomial parameters.')
        #popt_R = [-7.84787e-06, 6.61748e-02, 2.46616e+02]
        popt_R = [-7.85000e-06, 6.52400e-02, 2.46690e+02]
        popt_F = [-5.65724e-06, 6.33627e-02, 2.47474e+02]
        cutoff_channel = 500
        _pixels = list(range(self.nChannels))
        self.wavelength = list(np.polyval(popt_R, _pixels[0:cutoff_channel+1]))+list(np.polyval(popt_F, _pixels[cutoff_channel+1:]))
        self.wavenumber = [(10**7)*((1/248.5794) - (1/w)) for w in self.wavelength]



    # add new content to SOFF - re-read the file to update dimensions
    # update views accordingly
    def updateSOFF(self):
        print('updateSOFF')



    def openWorkspace(self):
        # read SOFF
        # determine the kind of data present and populate the proper class attributes
        print('openWorkspace')
