import os
import numpy as np
import functools
import math
import pandas as pd

import matplotlib as mpl
from matplotlib import cm as mpl_cm
from scipy.interpolate import interp1d
from scipy.stats import sigmaclip
from operator import itemgetter
from itertools import groupby

from PyQt5.QtWidgets import QApplication

from matplotlib import pyplot as plt

from src import log_parsing
from src import generate_images
from src import file_IO
from src import generate_plots
from src import helper_functions
from src import cosmic_ray_calculations
from src.loupe_view import _tab_cosmic_ray
from src.loupe_control import _control_cosmic
from src.loupe_control import _control_main



def _updateCosmicLeftPanel(self):
    log_parsing.log_info(self._view, 'Updating cosmic ray left panel')
    _populateWorkspaceName(self)
    _populateRoiCheckGroup(self)
    _setIndexScrollSize(self)
    # enable button and groupboxes


def _updateCosmicCentralPanel(self):
    log_parsing.log_info(self._view, 'Updating cosmic ray plot panel')
    _histCosmicUpdate(self)
    _roiSelectCosmicUpdate(self)



def _populateWorkspaceName(self):
    self._view.workspaceLabelCosmic.setText('Workspace: {0}'.format(self._view.workspace.humanReadableName))


def _clearCosmicPlotSpec(self):
    # remove top axis and wavenumber ticks, if they are present
    if self._view.axTopCosmic is not None and self._view.axTopCosmic.xaxis.label != '':
        self._view.axTopCosmic.set_xticks([])
        self._view.axTopCosmic.set_xticklabels([])
        self._view.axTopCosmic.xaxis.set_minor_locator(plt.FixedLocator([]))
        self._view.axTopCosmic.set_xlabel('', fontsize=10)

    for _ax in self._view.axCosmicPlot2:
        if isinstance(_ax, mpl.lines.Line2D):
            _ax.remove()
        else:
            for _line in _ax.lines:
                _line.remove()
            # remove std fill_betweens
            for i in range(len(_ax.collections)):
                _ax.collections[0].remove()
    self._view.axCosmicPlot2 = []
    self._view.traceCanvasCosmicPlot2.axes.clear()
    if self._view.traceCanvasCosmicPlot2.axes.get_legend() is not None:
        self._view.traceCanvasCosmicPlot2.axes.get_legend().remove()
    self._view.traceCanvasCosmicPlot2.draw_idle()

def _clearCosmic(self):
    log_parsing.log_info(self._view, 'Clearing cosmic ray removal tab contents')
    _resetGroupboxEnable(self)

    for _roi_name in self._view.workspace.roiNames:
        _roi_dict_name = self._view.workspace.roiHumanToDictKey[_roi_name]
        if _roi_name == 'Full Map':
            self._view.roiDict[_roi_dict_name].checkboxWidgetCosmic.setChecked(True)
        else:
            self._view.roiDict[_roi_dict_name].checkboxWidgetCosmic.setChecked(False)

    for i in reversed(range(self._view.vboxRoiCosmic.count())):
        self._view.vboxRoiCosmic.itemAt(i).widget().setParent(None)
    self._view.groupboxROICosmic.resize(self._view.groupboxROICosmic.sizeHint())

    # completely removing and re-adding the MPL canvas prevents plotting slow-downs from accumulating after many switches between workspaces
    self._view.LoupeViewCosmicTabLayout.removeWidget(self._view.toolbarCosmicPlot1)
    self._view.toolbarCosmicPlot1.deleteLater()
    self._view.toolbarCosmicPlot1 = None
    self._view.LoupeViewCosmicTabLayout.removeWidget(self._view.traceCanvasCosmicPlot1)
    self._view.traceCanvasCosmicPlot1.deleteLater()
    self._view.traceCanvasCosmicPlot1 = None
    self._view.LoupeViewCosmicTabLayout.removeWidget(self._view._hLineCosmic)
    self._view._hLineCosmic.deleteLater()
    self._view._hLineCosmic = None
    self._view.LoupeViewCosmicTabLayout.removeWidget(self._view.toolbarCosmicPlot2)
    self._view.toolbarCosmicPlot2.deleteLater()
    self._view.toolbarCosmicPlot2 = None
    self._view.LoupeViewCosmicTabLayout.removeWidget(self._view.traceCanvasCosmicPlot2)
    self._view.traceCanvasCosmicPlot2.deleteLater()
    self._view.traceCanvasCosmicPlot2 = None
    _tab_cosmic_ray._addCosmicCenterPanel(self._view)

    self._view.toolbarResizeCosmic1.triggered.disconnect()
    self._view.toolbarResizeCosmic2.triggered.disconnect()
    self._view.toolbarResizeCosmic1.triggered.connect(functools.partial(_control_cosmic._rescaleYCosmic1, self))
    self._view.toolbarResizeCosmic2.triggered.connect(functools.partial(_control_cosmic._rescaleYCosmic2, self))

    self._view._yRangeCosmic = None
    self._view._xRangeCosmic = None
    self._view._ax1BackgroundCosmic = None
    self._view._ax2BackgroundCosmic = None

    self._view.axCosmicPlot1 = []
    self._view.axCosmicPlot2 = []
    self._view.traceCanvasCosmicPlot1.axes.clear()
    self._view.traceCanvasCosmicPlot1.draw_idle()
    self._view.traceCanvasCosmicPlot2.draw_idle()
    self._view.axTopCosmic = None



def _resetGroupboxEnable(self):
    self._view.groupboxHistogramCosmic.setEnabled(True)
    self._view.R1ItemHistCosmic.setChecked(True)
    self._view.R2ItemHistCosmic.setChecked(False)
    self._view.R3ItemHistCosmic.setChecked(False)
    self._view.activeItemHistCosmic.setChecked(True)
    self._view.indexChannelCosmic.setText('50')
    self._view.selectionScrollbarChannelCosmic.setValue(50)

    self._view.groupboxSpectrumCosmic.setEnabled(True)
    self._view.R1ItemCosmic.setChecked(True)
    self._view.R2ItemCosmic.setChecked(True)
    self._view.R3ItemCosmic.setChecked(True)
    self._view.allItemCosmic.setChecked(False)
    self._view.activeItemCosmic.setChecked(False)
    self._view.darkItemCosmic.setChecked(False)
    self._view.darkSubItemCosmic.setChecked(True)
    self._view.meanDisplayCosmic.setEnabled(True)
    self._view.meanStdDisplayCosmic.setChecked(False)
    self._view.medianDisplayCosmic.setEnabled(True)
    self._view.medianStdDisplayCosmic.setChecked(False)
    self._view.maxDisplayCosmic.setEnabled(True)
    self._view.minDisplayCosmic.setEnabled(True)
    self._view.indexDisplayCosmic.setEnabled(True)
    self._view.indexSpecCosmic.setEnabled(True)
    self._view.groupboxDomainTypeCosmic.setEnabled(True)
    self._view.selectionScrollbarCosmic.setEnabled(True)
    self._view.selectionScrollbarChannelCosmic.setEnabled(True)

    self._view.groupboxCosmicAlgorithm.setEnabled(True)
    self._view.cosmicRayThreshold.setText('10')
    self._view.cosmicRaySigma.setText('4')
    self._view.cosmicRayMaxCRs.setText('20')
    self._view.cosmicRayWavelengthRange.setText('')
    self._view.cosmicRayWavelengthRange.setPlaceholderText('250-360')
    self._view.cosmicRayWidth.setText('3')
    self._view.groupboxCosmicAlgorithm.setEnabled(True)

    #self._view.groupboxCosmicManual.setEnabled(True)
    self._view.R1ItemCosmicManual.setChecked(True)
    self._view.cosmicRayManualWidth.setText('3')
    self._view.cosmicRayManualSpec.setText('')
    self._view.cosmicRayManualWavelength.setText('')
    self._view.executeCosmicRaySelect.setEnabled(True)
    self._view.executeCosmicRayManual.setEnabled(False)

    # enable this after at least one cosmic ray has been removed? (I guess a user could save this at any time)
    self._view.saveCosmicRaySpec.setEnabled(False)
    _manualGroupboxUpdate(self)


def _manualGroupboxUpdate(self):
    if self._view.indexDisplayCosmic.isChecked():
        self._view.groupboxCosmicManual.setEnabled(True)
    else:
        self._view.groupboxCosmicManual.setEnabled(False)

def _executeAutomatedCosmicRayRemoval(self):
    log_parsing.log_info(self._view, 'Applying automated cosmic ray removal algorithm. This may take up to 30 seconds.')
    self._view.executeCosmicRay.setText('Removing Cosmic Rays...')
    #QApplication.processEvents()
    self._view.executeCosmicRay.setEnabled(False)
    #QApplication.processEvents()
    # get spectrum index numbers
    if self._view.workspace.selectedROICosmic == []:
        _ROIindex = list(range(self._view.workspace.nSpectra))
    else:
        _ROIindex = []
        for _ROI in self._view.workspace.selectedROICosmic:
            for _i in self._view.roiDict[_ROI].specIndexList:
                _ROIindex.append(_i)
            _ROIindex = sorted(set(_ROIindex))

    _channelStr = self._view.cosmicRayWavelengthRange.text()
    if '-' not in _channelStr:
        _channels = range(0, self._view.workspace.nChannels)
    else:
        _nmStart = float(_channelStr.split('-')[0])
        _nmEnd = float(_channelStr.split('-')[-1])
        _channelStart = np.argmin([np.abs(_nmStart - _nm) for _nm in self._view.workspace.wavelength])
        _channelEnd = np.argmin([np.abs(_nmEnd - _nm) for _nm in self._view.workspace.wavelength])
        _channels = range(_channelStart, _channelEnd)

    CR_limit = self._view.cosmicRayMaxCRs.text()
    if CR_limit.isdigit():
        CR_limit = int(CR_limit)
    else:
        CR_limit = 20

    if self._view.cosmicRayReplacementAvg.isChecked():
        _method = 'A'
    else:
        _method = 'I'

    # [number of spectra, length of spectra] - assumes that all wavelength channels in a spectrum could be flagged
    CR_list = {'R1_active': np.full((len(_ROIindex), len(_channels)), -1),
               'R2_active': np.full((len(_ROIindex), len(_channels)), -1),
               'R3_active': np.full((len(_ROIindex), len(_channels)), -1),
               'R1_dark': np.full((len(_ROIindex), len(_channels)), -1),
               'R2_dark': np.full((len(_ROIindex), len(_channels)), -1),
               'R3_dark': np.full((len(_ROIindex), len(_channels)), -1)}


    # calculate histogram for each active frame for each region
    _rCounter = -1
    for _spec, _label in zip([self._view.workspace.activeSpectraR1, self._view.workspace.activeSpectraR2, self._view.workspace.activeSpectraR3], ['R1', 'R2', 'R3']):
        _rCounter += 1
        _cCounter = 0
        for _channelIndex in _channels:
            _cCounter += 1
            self._view.cosmicProgressBar.setValue(np.round((_rCounter*25/3)+((25/3)*_cCounter/self._view.workspace.nChannels)))
            QApplication.processEvents()
            # CR_confirm contains a list of index values associated with spectra that have had cosmic rays flagged at this wavelength channel
            CR_confirm = []
            _y = _spec[self._view.specProcessingSelected].iloc[_ROIindex, _channelIndex].values
            _hist, _edges = cosmic_ray_calculations.getHist(self, _y)
            # display histogram and threshold on top plot
            thresholdVal, thresholdBin = cosmic_ray_calculations.getThreshold(self, _y, _edges)
            # TODO: update plot? (blitting is not possible)
            #_histCosmicAutomatedUpdate(self)
            #_plotCosmicHistSingle(self, _hist, _edges, 'w', label=_label, threshold=thresholdVal)
            #self._view.traceCanvasCosmicPlot1.draw_idle()
            # determine cosmic ray candidates
            if thresholdVal is not None and len(_hist) > 3:
                CR_candidates = np.argwhere(_hist[thresholdBin:] > 0)
                while len(CR_candidates) > 0:
                    # CR_index - index of intensity array associated with 1st occurrence of int values > outlier int value
                    # self.bins[gaps[-1]] = index of bin that has at least one intensity value associated with it
                    # this identifies the first occurence of an intensity array value larger than the bin+threshold value
                    CR_index = np.abs(_y - _edges[CR_candidates[-1] + thresholdBin][0]).argmin()
                    CR_index = np.argwhere(CR_index == np.array(_ROIindex))[0][0]

                    if _hist[CR_candidates[-1] + thresholdBin] == 1:
                        CR_candidates = CR_candidates[0:-1]
                    else:
                        _hist[CR_candidates[-1] + thresholdBin] -= 1
                        _y[CR_index] = -1
                    if CR_index not in CR_confirm:
                        CR_list[_label+'_active'][CR_index, np.argwhere(CR_list[_label+'_active'][CR_index, :] < 0)[0][0]] = _channelIndex
                        CR_confirm.append(CR_index)


    # calculate histogram for each dark frame for each region
    for _spec, _label in zip([self._view.workspace.darkSpectraR1, self._view.workspace.darkSpectraR2, self._view.workspace.darkSpectraR3], ['R1', 'R2', 'R3']):
        _rCounter += 1
        _cCounter = 0
        for _channelIndex in _channels:
            _cCounter += 1
            self._view.cosmicProgressBar.setValue(np.round((_rCounter*25/3)+((25/3)*_cCounter/self._view.workspace.nChannels)))
            QApplication.processEvents()
            # CR_confirm contains a list of index values associated with spectra that have had cosmic rays flagged at this wavelength channel
            CR_confirm = []
            _y = _spec[self._view.specProcessingSelected].iloc[_ROIindex, _channelIndex].values
            _hist, _edges = cosmic_ray_calculations.getHist(self, _y)
            # display histogram and threshold on top plot
            thresholdVal, thresholdBin = cosmic_ray_calculations.getThreshold(self, _y, _edges)
            # TODO: update plot? (blitting is not possible)
            #_histCosmicAutomatedUpdate(self)
            #_plotCosmicHistSingle(self, _hist, _edges, 'w', label=_label, threshold=thresholdVal)
            #self._view.traceCanvasCosmicPlot1.draw_idle()
            # determine cosmic ray candidates
            if thresholdVal is not None and len(_hist) > 3:
                CR_candidates = np.argwhere(_hist[thresholdBin:] > 0)
                while len(CR_candidates) > 0:
                    # CR_index - index of intensity array associated with 1st occurrence of int values > outlier int value
                    # self.bins[gaps[-1]] = index of bin that has at least one intensity value associated with it
                    # this identifies the first occurence of an intensity array value larger than the bin+threshold value
                    CR_index = np.abs(_y - _edges[CR_candidates[-1] + thresholdBin][0]).argmin()
                    CR_index = np.argwhere(CR_index == np.array(_ROIindex))[0][0]

                    if _hist[CR_candidates[-1] + thresholdBin] == 1:
                        CR_candidates = CR_candidates[0:-1]
                    else:
                        _hist[CR_candidates[-1] + thresholdBin] -= 1
                        _y[CR_index] = -1
                    if CR_index not in CR_confirm:
                        CR_list[_label+'_dark'][CR_index, np.argwhere(CR_list[_label+'_dark'][CR_index, :] < 0)[0][0]] = _channelIndex
                        CR_confirm.append(CR_index)

    # sort cosmic ray candidates
    # filter cosmic ray candidates that contain too many cosmic rays
    #   count subsequent channels as a single cosmic ray event
    #   events that exceed CR width * 2 are rejected
    CR_list_all = {'R1': [],
                   'R2': [],
                   'R3': []}
    CRcounter = 0


    log_parsing.log_info(self._view, 'Calculating width of each event and removing cosmic rays')
    # loop over all spectra
    self._view.workspace.tempCosmicRayR1 = pd.DataFrame(np.zeros(self._view.workspace.activeSpectraR1['None'].shape), columns = self._view.workspace.activeSpectraR1['None'].columns)
    self._view.workspace.tempCosmicRayR2 = pd.DataFrame(np.zeros(self._view.workspace.activeSpectraR2['None'].shape), columns = self._view.workspace.activeSpectraR2['None'].columns)
    self._view.workspace.tempCosmicRayR3 = pd.DataFrame(np.zeros(self._view.workspace.activeSpectraR3['None'].shape), columns = self._view.workspace.activeSpectraR3['None'].columns)
    _rCounter = -1
    for _specA, _specD, _mode, _crSpec in zip([self._view.workspace.activeSpectraR1, self._view.workspace.activeSpectraR2, self._view.workspace.activeSpectraR3],
                                              [self._view.workspace.darkSpectraR1, self._view.workspace.darkSpectraR2, self._view.workspace.darkSpectraR3],
                                              ['R1', 'R2', 'R3'],
                                              [self._view.workspace.tempCosmicRayR1, self._view.workspace.tempCosmicRayR2, self._view.workspace.tempCosmicRayR3]):
        _rCounter += 1
        _sCounter = 0
        for _specIndex in _ROIindex:
            _sCounter += 1
            self._view.cosmicProgressBar.setValue(np.round(50+(_rCounter*50/3)+((50/3)*_sCounter/self._view.workspace.nSpectra)))
            QApplication.processEvents()

            _crSpec.loc[_specIndex] = _specA[self._view.specProcessingSelected].iloc[_specIndex, :].values - _specD[self._view.specProcessingSelected].iloc[_specIndex, :].values
            # get width of cosmic rays:
            ranges2 = []
            ranges3 = []
            if CR_list[_mode+'_active'][_specIndex, 0] > -1:
                ranges = []
                for k, g in groupby(enumerate(CR_list[_mode+'_active'][_specIndex, :]), lambda x: x[0] - x[1]):
                    group = list(map(itemgetter(1), g))
                    ranges.append((group[0], group[-1]))
                for j, CR in enumerate(ranges):
                    if CR[0] == -1:
                        # ranges2 contains the channel ranges of each cosmic ray in the spectrum
                        ranges2 = ranges[0:j]
                        break
            if CR_list[_mode+'_dark'][_specIndex, 0] > -1:
                ranges = []
                for k, g in groupby(enumerate(CR_list[_mode+'_dark'][_specIndex, :]), lambda x: x[0] - x[1]):
                    group = list(map(itemgetter(1), g))
                    ranges.append((group[0], group[-1]))
                for j, CR in enumerate(ranges):
                    if CR[0] == -1:
                        ranges3 = ranges[0:j]
                        break

            # get new ranges list that contain cosmic ray candidates from dark/active combined lists
            rangesAD = [list(range(r[0], r[1]+1)) for r in ranges2] + [list(range(r[0], r[1]+1)) for r in ranges3]
            rangesAD = list(set(sorted([item for sublist in rangesAD for item in sublist])))
            ranges = []
            for k, g in groupby(enumerate(rangesAD), lambda x: x[0] - x[1]):
                group = list(map(itemgetter(1), g))
                ranges.append((group[0], group[-1]))

            # ranges contains all cosmic rays
            if len(ranges) < 2 * CR_limit:
                for j in ranges:
                    if j[0] > 48 and j[-1] < 2100:
                        width = int(j[1] - j[0]) + 1
                        loc = j[0] + math.floor(width / 2)
                        # print('cosmic ray width: ' + str(width), 'at loc: ', str(self.raw_spectra['shift'][loc]))
                        if loc > -1 and width < 20:
                            _y = _crSpec.loc[_specIndex]
                            # if the width is too large, interpolation can fail (and this usually indicates the presence of a high baseline)
                            if _method == 'A' or width > 10:
                                # remove cosmic rays and replace with mean of surrounding points
                                _yRevised = cosmic_ray_calculations.CRreplace_avg(self, int(loc), _specIndex, width + 3, _y, _ROIindex)
                            else:
                                # remove cosmic rays and replace with interpolated curve of nearby points
                                _yRevised = cosmic_ray_calculations.CRreplace_interp(self, int(loc), _specIndex, width + 3, _y, _ROIindex)
                            log_parsing.log_info(self._view, 'Identified cosmic ray in region ' + str(_rCounter+1) + ', spectrum # ' + str(_ROIindex[_specIndex]) + ' at channel: ' + '{0}'.format(loc))
                            CRcounter+=1
                            _crSpec.loc[_specIndex] = _yRevised

    self._view.saveCosmicRaySpec.setEnabled(True)
    self._view.resetCosmicRaySpec.setEnabled(True)
    _plotCosmicUpdate(self)
    self._view.cosmicProgressBar.setValue(100)
    log_parsing.log_info(self._view, 'Completed automated cosmic ray removal. Identified {0} cosmic rays.'.format(CRcounter))
    self._view.executeCosmicRay.setText('Automated Cosmic Ray Removal')
    self._view.executeCosmicRay.setEnabled(True)

def _selectCosmicRay(self):
    def onpick(event):
        if event.dblclick:
            _xRangeWvl = event.canvas.axes.get_xbound()
            _yRangeInt = event.canvas.axes.get_ybound()
            #print(_xRangeWvl, _yRangeInt)
            #_x = (_xRangeWvl[1] - _xRangeWvl[0])*event.xdata+_xRangeWvl[0]
            #_y = event.ydata
            #print(_x, _y)
            _xRange = (event.inaxes.bbox.xmin, event.inaxes.bbox.xmax)
            _yRange = (event.inaxes.bbox.ymin, event.inaxes.bbox.ymax)
            _xData = (event.x - _xRange[0])/(_xRange[1] - _xRange[0])
            _yData = (event.y - _yRange[0])/(_yRange[1] - _yRange[0])
            _x = (_xRangeWvl[1] - _xRangeWvl[0])*_xData+_xRangeWvl[0]
            _y = (_yRangeInt[1] - _yRangeInt[0])*_yData+_yRangeInt[0]
            if self._view.ccdDomainCosmic.isChecked():
                self._view.cosmicRayManualChannel.setText('{0}'.format(int(_x)))
                _calcWavelengthManual(self)
            else:
                self._view.cosmicRayManualWavelength.setText('{0:.2f}'.format(_x))
                _calcChannelManual(self)
            self._view.traceCanvasCosmicPlot2.mpl_disconnect(_cid)


    #_cid = self._view.traceCanvasCosmicPlot2.mpl_connect('button_press_event', lambda event: onpick(event, self._view))
    _cid = self._view.traceCanvasCosmicPlot2.mpl_connect('button_press_event', onpick)


def _calcChannelManual(self):
    _wavelength = float(self._view.cosmicRayManualWavelength.text())
    _channel = helper_functions.channel_from_wavelength(_wavelength, self._view.workspace.wavelength)
    self._view.cosmicRayManualChannel.setText('{0}'.format(_channel))
    self._view.executeCosmicRayManual.setEnabled(True)
    _addCosmicAlpha(self)


def _calcWavelengthManual(self):
    _channel = int(self._view.cosmicRayManualChannel.text())
    _wavelength = self._view.workspace.wavelength[_channel]
    self._view.cosmicRayManualWavelength.setText('{0:.2f}'.format(_wavelength))
    self._view.executeCosmicRayManual.setEnabled(True)
    _addCosmicAlpha(self)

def _addCosmicAlpha(self):
    _removeCosmicAlpha(self)
    if self._view.cosmicRayManualWavelength.text() != '' and self._view.cosmicRayManualChannel.text() != '':
        if self._view.R1ItemCosmicManual.isChecked():
            _color = '#0099FF'
            _label = 'CR_fill_R1'
        elif self._view.R2ItemCosmicManual.isChecked():
            _color = '#00FF00'
            _label = 'CR_fill_R2'
        else:
            _color = '#FF0000'
            _label = 'CR_fill_R3'

        _range = float(self._view.cosmicRayManualWidth.text())
        if self._view.ccdDomainCosmic.isChecked():
            _x = int(self._view.cosmicRayManualChannel.text())
            _x1 = _x - _range/2.0
            _x2 = _x + _range/2.0
        else:
            _wavelength = float(self._view.cosmicRayManualWavelength.text())
            _ch = helper_functions.channel_from_wavelength(_wavelength, self._view.workspace.wavelength)
            _x1 = self._view.workspace.wavelength[int(_ch-_range/2.0)]
            _x2 = self._view.workspace.wavelength[int(_ch+_range/2.0)]

        _addCosmicFill(self, _x1, _x2, _color, _label, alpha = 0.3)

def _removeCosmicAlpha(self):
    if self._view.axCosmicPlot2 != []:
        for _ax in self._view.axCosmicPlot2:
            remove_ax = False
            if not isinstance(_ax, mpl.lines.Line2D):
                # remove CR axvspan
                for i in range(len(_ax.patches)):
                    #if 'CR_fill' in _ax.label:
                    _ax.patches = []
                    remove_ax = True
                if remove_ax:
                    self._view.axCosmicPlot2.remove(_ax)
        self._view.traceCanvasCosmicPlot2.draw_idle()


def _addCosmicFill(self, x1, x2, color, label, alpha=0.5):
    _ax = generate_plots.plotCosmicFill(self._view.traceCanvasCosmicPlot2.axes, x1, x2, color, alpha=alpha, label=label)
    self._view.traceCanvasCosmicPlot2.draw_idle()
    self._view.axCosmicPlot2.append(_ax)

def _executeManualCosmicRayRemoval(self):
    # replace cosmic ray
    if self._view.workspace.selectedROICosmic == []:
        _ROIindex = list(range(self._view.workspace.nSpectra))
    else:
        _ROIindex = []
        for _ROI in self._view.workspace.selectedROICosmic:
            for _i in self._view.roiDict[_ROI].specIndexList:
                _ROIindex.append(_i)
            _ROIindex = sorted(set(_ROIindex))

    if self._view.cosmicRayReplacementAvg.isChecked():
        _method = 'A'
    else:
        _method = 'I'

    _specIndex = int(self._view.cosmicRayManualSpec.text())
    _width = int(self._view.cosmicRayManualWidth.text())
    _channel = int(self._view.cosmicRayManualChannel.text())

    if self._view.workspace.tempCosmicRayR1 is None:
        self._view.workspace.tempCosmicRayR1 = self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].copy()
        self._view.workspace.tempCosmicRayR2 = self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].copy()
        self._view.workspace.tempCosmicRayR3 = self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].copy()

    if self._view.R1ItemCosmicManual.isChecked():
        _y = self._view.workspace.tempCosmicRayR1.iloc[_specIndex, :].values
        _region = '1'
    elif self._view.R2ItemCosmicManual.isChecked():
        _y = self._view.workspace.tempCosmicRayR2.iloc[_specIndex, :].values
        _region = '2'
    else:
        _y = self._view.workspace.tempCosmicRayR3.iloc[_specIndex, :].values
        _region = '3'


    # if the width is too large, interpolation can fail (and this usually indicates the presence of a high baseline)
    if _method == 'A' or _width > 10:
        # remove cosmic rays and replace with mean of surrounding points
        _yRevised = cosmic_ray_calculations.CRreplace_avg(self, int(_channel), _specIndex, _width + 3, _y, _ROIindex)
    else:
        # remove cosmic rays and replace with interpolated curve of nearby points
        _yRevised = cosmic_ray_calculations.CRreplace_interp(self, int(_channel), _specIndex, _width + 3, _y, _ROIindex)
    log_parsing.log_info(self._view, 'User identified cosmic ray in region ' + _region + ', spectrum # ' + str(_ROIindex[_specIndex]) + ' at channel: ' + '{0}'.format(_channel))

    if self._view.R1ItemCosmicManual.isChecked():
        self._view.workspace.tempCosmicRayR1.loc[_specIndex] = _yRevised
    elif self._view.R2ItemCosmicManual.isChecked():
        self._view.workspace.tempCosmicRayR2.loc[_specIndex] = _yRevised
    else:
        self._view.workspace.tempCosmicRayR3.loc[_specIndex] = _yRevised

    _removeCosmicAlpha(self)
    _addSelectionPlotCosmic(self, retain_zoom=True)

    self._view.cosmicRayManualWavelength.setText('')
    self._view.cosmicRayManualChannel.setText('')
    self._view.saveCosmicRaySpec.setEnabled(True)
    self._view.executeCosmicRayManual.setEnabled(False)
    # this forces the plot to update
    _removeCosmicAlpha(self)

def _resetCosmicRayRemoval(self):
    self._view.workspace.tempCosmicRayR1 = None
    self._view.workspace.tempCosmicRayR2 = None
    self._view.workspace.tempCosmicRayR3 = None
    log_parsing.log_warning(self._view, 'Resetting cosmic ray processing.')
    self._view.cosmicProgressBar.setValue(0)
    # reset plots (call plotting functions, which should check for tempCosmicRayR1 data)
    _plotCosmicUpdate(self)


def _saveCosmicRayRemoval(self):
    if self._view.specProcessingSelected != 'None' and 'C' in self._view.specProcessingSelected:
        log_parsing.log_warning(self._view, 'Cosmic Ray Removal already applied. Overwriting previously saved spectra')
    _specDictKey = self._view.workspace.specProcessingApplied
    _specDictKeySelect = self._view.specProcessingSelected
    # applying cosmic ray removal to active-dark
    if _specDictKey == 'None':
        self._view.workspace.specProcessingApplied = 'C'
    elif 'C' in _specDictKey:
        self._view.workspace.specProcessingApplied = _specDictKey
    else:
        self._view.workspace.specProcessingApplied += 'C'
    if _specDictKeySelect == 'None':
        _specFlag = 'C'
    elif 'C' in _specDictKeySelect:
        _specFlag = _specDictKeySelect
    else:
        _specFlag = _specDictKeySelect + 'C'

    if self._view.workspace.tempCosmicRayR1 is not None:
        self._view.workspace.darkSubSpectraR1[_specFlag] = self._view.workspace.tempCosmicRayR1.copy()
    else:
        self._view.workspace.darkSubSpectraR1[_specFlag] = self._view.workspace.darkSubSpectraR1[_specDictKey].copy()
    if self._view.workspace.tempCosmicRayR2 is not None:
        self._view.workspace.darkSubSpectraR2[_specFlag] = self._view.workspace.tempCosmicRayR2.copy()
    else:
        self._view.workspace.darkSubSpectraR2[_specFlag] = self._view.workspace.darkSubSpectraR2[_specDictKey].copy()
    if self._view.workspace.tempCosmicRayR3 is not None:
        self._view.workspace.darkSubSpectraR3[_specFlag] = self._view.workspace.tempCosmicRayR3.copy()
    else:
        self._view.workspace.darkSubSpectraR3[_specFlag] = self._view.workspace.darkSubSpectraR3[_specDictKey].copy()

    self._view.workspace.darkSpectraR1[_specFlag] = self._view.workspace.darkSpectraR1[_specDictKey].copy()
    self._view.workspace.darkSpectraR2[_specFlag] = self._view.workspace.darkSpectraR2[_specDictKey].copy()
    self._view.workspace.darkSpectraR3[_specFlag] = self._view.workspace.darkSpectraR3[_specDictKey].copy()
    self._view.workspace.activeSpectraR1[_specFlag] = self._view.workspace.activeSpectraR1[_specDictKey].copy()
    self._view.workspace.activeSpectraR2[_specFlag] = self._view.workspace.activeSpectraR2[_specDictKey].copy()
    self._view.workspace.activeSpectraR3[_specFlag] = self._view.workspace.activeSpectraR3[_specDictKey].copy()

    # add data to csv files
    _spec_file = os.path.join(self._view.workspace.workingDir, 'darkSubSpectra{0}.csv'.format(_specFlag))
    file_IO.writeSpectraRegions(_spec_file, self._view, self._view.workspace.darkSubSpectraR1[_specFlag], self._view.workspace.darkSubSpectraR2[_specFlag], self._view.workspace.darkSubSpectraR3[_specFlag])
    _spec_file = os.path.join(self._view.workspace.workingDir, 'darkSpectra{0}.csv'.format(_specFlag))
    file_IO.writeSpectraRegions(_spec_file, self._view, self._view.workspace.darkSpectraR1[_specFlag], self._view.workspace.darkSpectraR2[_specFlag], self._view.workspace.darkSpectraR3[_specFlag])
    _spec_file = os.path.join(self._view.workspace.workingDir, 'activeSpectra{0}.csv'.format(_specFlag))
    file_IO.writeSpectraRegions(_spec_file, self._view, self._view.workspace.activeSpectraR1[_specFlag], self._view.workspace.activeSpectraR2[_specFlag], self._view.workspace.activeSpectraR3[_specFlag])

    _control_main._updateSpecProcessing(self)
    _loupe_file = os.path.join(self._view.workspace.workingDir, 'loupe.csv')
    file_IO.writeLoupeCsv(_loupe_file, self._view)

def _indexCosmicUpdate(self):
    self._view.indexChannelCosmic.setText(str(self._view.selectionScrollbarChannelCosmic.value()))
    _histCosmicUpdate(self)

def _histCosmicUpdate(self):
    if self._view.axCosmicPlot1 != []:
        #for _ax in self._view.axCosmicPlot1:
            #_ax.remove()
            #self._view.axCosmicPlot1.remove(_ax)
        self._view.traceCanvasCosmicPlot1.axes.clear()
        self._view.traceCanvasCosmicPlot1.draw_idle()
    self._view.axCosmicPlot1 = []
    self._view.selectionScrollbarChannelCosmic.disconnect()
    self._view.selectionScrollbarChannelCosmic.setValue(int(self._view.indexChannelCosmic.text()))
    self._view.selectionScrollbarChannelCosmic.valueChanged.connect(functools.partial(_control_cosmic._indexCosmicUpdate, self))
    _histCosmicAdd(self)

def _histCosmicAutomatedUpdate(self):
    if self._view.axCosmicPlot1 != []:
        #for _ax in self._view.axCosmicPlot1:
            #_ax.remove()
            #self._view.axCosmicPlot1.remove(_ax)
        self._view.traceCanvasCosmicPlot1.axes.clear()
        self._view.traceCanvasCosmicPlot1.draw_idle()
    self._view.axCosmicPlot1 = []


def _histCosmicAdd(self):
    if self._view.workspace.selectedROICosmic == []:
        _ROIindex = list(range(self._view.workspace.nSpectra))
    else:
        _ROIindex = []
        for _ROI in self._view.workspace.selectedROICosmic:
            for _i in self._view.roiDict[_ROI].specIndexList:
                _ROIindex.append(_i)
            _ROIindex = sorted(set(_ROIindex))

    # read textbox
    # if empty, use index 0
    if self._view.indexChannelCosmic.text() == '' or not self._view.indexChannelCosmic.text().isdigit():
        log_parsing.log_warning(self._view, 'No channel index entered. Using index 0')
        self._view.indexChannelCosmic.setText('0')
    _indexText = self._view.indexChannelCosmic.text()
    log_parsing.log_info(self._view, 'Adding histogram for channel: '+_indexText)
    _indexStrList = _indexText.split(',')
    self.indexListCosmicHist = []
    for i in _indexStrList:
        if ':' not in i:
            self.indexListCosmicHist.append(int(i))
        else:
            _iList = list(range(int(i.split(':')[0]), int(i.split(':')[1])+1))
            for j in _iList:
                self.indexListCosmicHist.append(int(j))

    if self._view.R1ItemHistCosmic.isChecked():
        if self._view.activeItemHistCosmic.isChecked():
            _y = self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex, self.indexListCosmicHist].values
        else:
            _y = self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex, self.indexListCosmicHist].values
        _label = 'R1'

    elif self._view.R2ItemHistCosmic.isChecked():
        if self._view.activeItemHistCosmic.isChecked():
            _y = self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex, self.indexListCosmicHist].values
        else:
            _y = self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex, self.indexListCosmicHist].values
        _label = 'R2'

    elif self._view.R3ItemHistCosmic.isChecked():
        if self._view.activeItemHistCosmic.isChecked():
            _y = self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex, self.indexListCosmicHist].values
        else:
            _y = self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex, self.indexListCosmicHist].values
        _label = 'R3'

    _hist = []
    if _y.shape[1] > 1:
        _cmap = mpl_cm.get_cmap('viridis')
        _color = []
        _bins = np.arange(_y.min(), _y.max() + (_y.max()-_y.min())/40, (_y.max()-_y.min())/40)
        for _i, _yi in enumerate(_y.T):
            _c = _cmap((1+_i)/len(_y.T))
            _h, _edges = np.histogram(_yi, bins=_bins)
            _h = np.insert(_h, 0, 0)
            _h = np.insert(_h, len(_h), 0)
            _hist.append(_h)
            _color.append(_c)
        _edges = np.insert(_edges, 0, max([0, _edges[0]-(_edges[-1]-_edges[-2])]))
        _edges = np.insert(_edges, len(_edges), _edges[-1]+(_edges[-1]-_edges[-2]))
    else:
        _hist, _edges = np.histogram(_y, bins='fd')
        _color='w'
        _edges = np.insert(_edges, 0, max([0, _edges[0]-(_edges[-1]-_edges[-2])]))
        _edges = np.insert(_edges, len(_edges), _edges[-1]+(_edges[-1]-_edges[-2]))
        _hist = np.insert(_hist, 0, 0)
        _hist = np.insert(_hist, len(_hist), 0)

    if _y.shape[1] == 1:
        thresholdVal, thresholdBin = cosmic_ray_calculations.getThreshold(self, _y, _edges)
        _plotCosmicHistSingle(self, _hist, _edges, _color, label=_label, threshold=thresholdVal)
    else:
        _plotCosmicHistMulti(self, _hist, _edges, _color, label=_label)

    self._view.axCosmicPlot1[-1].axes.relim()
    self._view.axCosmicPlot1[-1].axes.autoscale()
    self._view.traceCanvasCosmicPlot1.draw_idle()


def _plotCosmicHistSingle(self, hist, edges, color, alpha=0.9, label='', threshold=None):
    _ax = generate_plots.plotCosmicHist(self._view, hist, edges, color, alpha=alpha, label=label, threshold=threshold)
    _ax[0].axes.set_xlabel('Spectrum Intensity Bin')
    _ax[0].axes.set_ylabel('Bin Size')
    self._view.axCosmicPlot1.append(_ax[0])


def _plotCosmicHistMulti(self, hist, edges, color, label='', legend = False):
    _alpha = 0.6-0.0006*len(hist)
    # TODO: fix the calling sequences so that a list is always passed, rather than converting to the right type here
    if type(color) == type(''):
        color = [color]*len(hist)
    if type(label) == type(''):
        label = [label]*len(hist)
    edges = [edges]*len(hist)

    for _hist_i, _edges_i, c_i, _label in zip(hist, edges, color, label):
        _ax = generate_plots.plotCosmicHist(self._view, _hist_i, _edges_i, c_i, alpha=_alpha, label=_label)
        _ax[0].axes.set_xlabel('Spectrum Intensity Bin')
        _ax[0].axes.set_ylabel('Bin Size')
        self._view.axCosmicPlot1.append(_ax[0])


def _setIndexScrollSize(self):
    self._view.selectionScrollbarCosmic.setMaximum(self._view.workspace.nSpectra-1)
    self._view.selectionScrollbarChannelCosmic.setMaximum(self._view.workspace.nChannels-1)
    self._view.selectionScrollbarChannelCosmic.setValue(50)

# if this gets called anywhere else, remove the last conditional statement that sets the checkboxes and add them to a new function called when switching workspaces
def _populateRoiCheckGroup(self):
    # clear group box
    for _checkboxIndex in reversed(range(self._view.vboxRoiCosmic.count())):
        self._view.vboxRoiCosmic.itemAt(_checkboxIndex).widget().setParent(None)
    # add each roi checkbox widget to the groupbox
    for _roi_name in self._view.workspace.roiNames:
        _roi_dict_name = self._view.workspace.roiHumanToDictKey[_roi_name]
        # get ROI class
        #_roiDictName = self._view.workspace.roiHumanToDictKey[_roi_name]
        _checkboxRoi = self._view.roiDict[_roi_dict_name].checkboxWidgetCosmic
        _checkboxRoi.clicked.connect(functools.partial(_roiSelectCosmicUpdate, self))
        self._view.vboxRoiCosmic.addWidget(_checkboxRoi)
        if len(self._view.workspace.roiNames) < 2:
            _checkboxRoi.setDisabled(True)
        else:
            _checkboxRoi.setDisabled(False)
        if _roi_name == 'Full Map':
            self._view.roiDict[_roi_dict_name].checkboxWidgetCosmic.setChecked(True)
        else:
            self._view.roiDict[_roi_dict_name].checkboxWidgetCosmic.setChecked(False)


def _roiSelectCosmicUpdate(self):
    # determine which ROI checkboxes are selected
    _roiSelected = []
    self._view.workspace.selectedROICosmic = []
    for _roiName in self._view.workspace.roiNames:
        _roiKey = self._view.workspace.roiHumanToDictKey[_roiName]
        if self._view.roiDict[_roiKey].checkboxWidgetCosmic.isChecked():
            _roiSelected.append(_roiKey)
            self._view.workspace.selectedROICosmic.append(_roiKey)

    if len(_roiSelected) == 1 and _roiSelected[0].split('_')[-1] == 'Full Map':
        self._view.indexDisplayCosmic.setEnabled(True)
        self._view.indexSpecCosmic.setEnabled(True)
        self._view.cosmicRayManualSpec.setEnabled(True)
        _plotCosmicUpdate(self)
    elif len(_roiSelected) == 1:
        _plotCosmicUpdate(self)
    else:
        self._view.R1ItemCosmic.setChecked(False)
        self._view.R2ItemCosmic.setChecked(False)
        self._view.R3ItemCosmic.setChecked(False)
        self._view.allItemCosmic.setChecked(True)
        self._view.indexDisplayCosmic.setEnabled(False)
        self._view.indexSpecCosmic.setEnabled(False)
        self._view.cosmicRayManualSpec.setEnabled(False)
        if self._view.indexDisplayCosmic.isChecked():
            self._view.meanDisplayCosmic.setChecked(True)
        _plotCosmicUpdate(self)


def _plotCosmicUpdate(self):
    if self._view.axCosmicPlot2 != []:
        for _ax in self._view.axCosmicPlot2:
            if isinstance(_ax, mpl.lines.Line2D):
                _ax.remove()
            else:
                for _line in _ax.lines:
                    _line.remove()
                # remove std fill_betweens
                for i in range(len(_ax.collections)):
                    _ax.collections[0].remove()
                # remove CR axvspan
                for i in range(len(_ax.patches)):
                    _ax.patches = []

        self._view.traceCanvasCosmicPlot2.draw_idle()
    self._view.axCosmicPlot2 = []
    # if no ROIs are selected, or one ROI is selected, plot as normal and use ROI index for mean/median
    if len(self._view.workspace.selectedROICosmic) < 2:
        if self._view.darkSubItemCosmic.isChecked():
            _plotCosmicActiveDark(self)
        elif self._view.darkItemCosmic.isChecked():
            _plotCosmicDark(self)
        elif self._view.activeItemCosmic.isChecked():
            _plotCosmicActive(self)
    # if multiple ROIs are selected, plot only one region (or all/composite) and use colors and legends to distinguish between ROIs
    else:
        if self._view.darkSubItemCosmic.isChecked():
            _plotCosmicActiveDarkMultiRoi(self)
        elif self._view.darkItemCosmic.isChecked():
            _plotCosmicDarkMultiRoi(self)
        elif self._view.activeItemCosmic.isChecked():
            _plotCosmicActiveMultiRoi(self)

def _specCosmicUpdateIndex(self):
    if not any([isinstance(_ax, mpl.lines.Line2D) for _ax in self._view.axCosmicPlot2]):
        self._view.axCosmicPlot2 = []
        self._view.traceCanvasCosmicPlot2.axes.clear()
        self._view.traceCanvasCosmicPlot2.draw_idle()
    self._view.indexDisplayCosmic.setChecked(True)
    _index = str(self._view.selectionScrollbarCosmic.value())
    self._view.cosmicRayManualSpec.setText(_index)
    self._view.indexSpecCosmic.setText(_index)
    _addSelectionPlotCosmic(self)

def _plotCosmicUpdateUpperIndex(self):
    if self._view.indexSpecCosmic.text() == '':
        log_parsing.log_warning(self._view, 'No spectral index entered. Using index 0')
        self._view.indexSpecCosmic.setText('0')
        self._view.cosmicRayManualSpec.setText('0')
    else:
        _indexText = self._view.indexSpecCosmic.text()
        self._view.cosmicRayManualSpec.setText(_indexText)
    if ':' not in _indexText and ',' not in _indexText:
        self._view.selectionScrollbarCosmic.disconnect()
        self._view.selectionScrollbarCosmic.setValue(int(_indexText))
        self._view.selectionScrollbarCosmic.valueChanged.connect(functools.partial(_control_cosmic._specCosmicUpdateIndex, self))
    self._view.indexDisplayCosmic.setChecked(True)
    _plotCosmicUpdate(self)

def _plotCosmicUpdateLowerIndex(self):
    if self._view.cosmicRayManualSpec.text() == '':
        log_parsing.log_warning(self._view, 'No spectral index entered. Using index 0')
        self._view.indexSpecCosmic.setText('0')
        self._view.cosmicRayManualSpec.setText('0')
    else:
        _indexText = self._view.cosmicRayManualSpec.text()
        self._view.indexSpecCosmic.setText(_indexText)
    if ':' not in _indexText and ',' not in _indexText:
        self._view.selectionScrollbarCosmic.disconnect()
        self._view.selectionScrollbarCosmic.setValue(int(_indexText))
        self._view.selectionScrollbarCosmic.valueChanged.connect(functools.partial(_control_cosmic._specCosmicUpdateIndex, self))
    self._view.indexDisplayCosmic.setChecked(True)
    _plotCosmicUpdate(self)


def _plotCosmicUpdateRegion1(self):
    # return a different axes to support blitting
    blitting = False
    # if the checkbox is checked:
    if self._view.R1ItemCosmic.isChecked():
        # if there are more than 2 ROIs selected:
        if len(self._view.workspace.selectedROICosmic) > 1:
            if self._view.axCosmicPlot2 != []:
                for _ax in self._view.axCosmicPlot2:
                    if isinstance(_ax, mpl.lines.Line2D):
                        _ax.remove()
                    else:
                        for _line in _ax.lines:
                            _line.remove()
                        # remove std fill_betweens
                        for i in range(len(_ax.collections)):
                            _ax.collections[0].remove()
                self._view.traceCanvasCosmicPlot2.draw_idle()
            self._view.axCosmicPlot2 = []

            self._view.R2ItemCosmic.setChecked(False)
            self._view.R3ItemCosmic.setChecked(False)
            self._view.allItemCosmic.setChecked(False)
            if self._view.darkSubItemCosmic.isChecked():
                _plotCosmicActiveDarkMultiRoi(self)
            elif self._view.activeItemCosmic.isChecked():
                _plotCosmicActiveMultiRoi(self)
            else:
                _plotCosmicDarkMultiRoi(self)

        else:
            # loop through all axes, check if the line label name R1 exists, if not add it
            for _ax in self._view.axCosmicPlot2:
                if not isinstance(_ax, mpl.lines.Line2D):
                    for _line in _ax.lines:
                        if _line._label == 'R1':
                            log_parsing.log_info(self._view, 'R1 trace already present in plot')
                            _add_plot_flag = False
            if self._view.workspace.selectedROICosmic == []:
                _ROIindex = list(range(self._view.workspace.nSpectra))
            else:
                _ROIindex = self._view.roiDict[self._view.workspace.selectedROICosmic[0]].specIndexList

            _yR1_std = None
            if self._view.meanDisplayCosmic.isChecked():
                if self._view.darkSubItemCosmic.isChecked():
                    if self._view.workspace.tempCosmicRayR1 is not None:
                        _yR1 = self._view.workspace.tempCosmicRayR1.iloc[_ROIindex].mean()
                    else:
                        _yR1 = self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].mean()
                    if self._view.meanStdDisplayCosmic.isChecked():
                        if self._view.workspace.tempCosmicRayR1 is not None:
                            _yR1_std = self._view.workspace.tempCosmicRayR1.iloc[_ROIindex].std()
                        else:
                            _yR1_std = self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].std()
                elif self._view.activeItemCosmic.isChecked():
                    _yR1 = self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].mean()
                    if self._view.meanStdDisplayCosmic.isChecked():
                        _yR1_std = self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].std()
                else:
                    _yR1 = self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].mean()
                    if self._view.meanStdDisplayCosmic.isChecked():
                        _yR1_std = self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].std()
            elif self._view.medianDisplayCosmic.isChecked():
                if self._view.darkSubItemCosmic.isChecked():
                    if self._view.workspace.tempCosmicRayR1 is not None:
                        _yR1 = np.median(self._view.workspace.tempCosmicRayR1.iloc[_ROIindex], axis=0)
                    else:
                        _yR1 = np.median(self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
                    if self._view.medianStdDisplayCosmic.isChecked():
                        if self._view.workspace.tempCosmicRayR1 is not None:
                            _yR1_std = self._view.workspace.tempCosmicRayR1.iloc[_ROIindex].std()
                        else:
                            _yR1_std = self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].std()
                elif self._view.activeItemCosmic.isChecked():
                    _yR1 = np.median(self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
                    if self._view.medianStdDisplayCosmic.isChecked():
                        _yR1_std = self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].std()
                else:
                    _yR1 = np.median(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
                    if self._view.medianStdDisplayCosmic.isChecked():
                        _yR1_std = self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].std()
            elif self._view.maxDisplayCosmic.isChecked():
                if self._view.darkSubItemCosmic.isChecked():
                    if self._view.workspace.tempCosmicRayR1 is not None:
                        _yR1 = np.max(self._view.workspace.tempCosmicRayR1.iloc[_ROIindex], axis=0)
                    else:
                        _yR1 = np.max(self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
                elif self._view.activeItemCosmic.isChecked():
                    _yR1 = np.max(self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
                else:
                    _yR1 = np.max(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
            elif self._view.minDisplayCosmic.isChecked():
                if self._view.darkSubItemCosmic.isChecked():
                    if self._view.workspace.tempCosmicRayR1 is not None:
                        _yR1 = np.min(self._view.workspace.tempCosmicRayR1.iloc[_ROIindex], axis=0)
                    else:
                        _yR1 = np.min(self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
                elif self._view.activeItemCosmic.isChecked():
                    _yR1 = np.min(self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
                else:
                    _yR1 = np.min(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
            else:
                _indexText = self._view.indexSpecCosmic.text()
                if _indexText == '':
                    self._view.indexSpecCosmic.setText('0')
                    _indexText = '0'
                blitting = True
                log_parsing.log_info(self._view, 'Adding traces for spectral indices: '+_indexText)
                _indexStrList = _indexText.split(',')
                self.indexListCosmic = []
                for i in _indexStrList:
                    if ':' not in i:
                        self.indexListCosmic.append(int(i))
                    else:
                        _iList = list(range(int(i.split(':')[0]), int(i.split(':')[1])+1))
                        for j in _iList:
                            self.indexListCosmic.append(int(j))

                if self._view.darkSubItemCosmic.isChecked():
                    if self._view.workspace.tempCosmicRayR1 is not None:
                        _yR1 = self._view.workspace.tempCosmicRayR1.loc[self.indexListCosmic].values
                    else:
                        _yR1 = self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].loc[self.indexListCosmic].values
                elif self._view.activeItemCosmic.isChecked():
                    _yR1 = self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].loc[self.indexListCosmic].values
                else:
                    _yR1 = self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].loc[self.indexListCosmic].values

            if self._view.waveDomainCosmic.isChecked():
                _x = self._view.workspace.wavelength
            else:
                _x = list(range(self._view.workspace.nChannels))

            _color = self._view.workspace.colorR1
            if len(_yR1) == self._view.workspace.nChannels:
                _plotCosmicSingle(self, _x, _yR1, _color, label='R1', y_std = _yR1_std, blitting = blitting)
            else:
                _plotCosmicMulti(self, _x, _yR1, _color, label='R1', y_std = _yR1_std, blitting = blitting)
            log_parsing.log_info(self._view, 'added R1 trace')

    # if the checkbox is unchecked:
    else:
        # loop through all axes, check if the line label name R1 exists, if so, remove it
        for _ax in self._view.axCosmicPlot2:
            if not isinstance(_ax, mpl.lines.Line2D):
                for _line in _ax.lines:
                    if _line._label == 'R1':
                        log_parsing.log_info(self._view, 'removed trace R1')
                        _line.remove()
                # remove std fill_betweens
                for _coll in _ax.collections:
                    if _coll._label == 'R1' or _coll._label == '_R1':
                        _coll.remove()
            else:
                if _ax.get_color() == '#0099FF':
                    _ax.remove()
                    self._view.axCosmicPlot2.remove(_ax)

    self._view.traceCanvasCosmicPlot2.draw_idle()
    if blitting:
        _addSelectionPlotCosmic(self)


def _plotCosmicUpdateRegion2(self):
    blitting = False
    # if the checkbox is checked:
    if self._view.R2ItemCosmic.isChecked():
        # if there are more than 2 ROIs selected:
        if len(self._view.workspace.selectedROICosmic) > 1:
            if self._view.axCosmicPlot2 != []:
                for _ax in self._view.axCosmicPlot2:
                    if not isinstance(_ax, mpl.lines.Line2D):
                        for _line in _ax.lines:
                            _line.remove()
                        # remove std fill_betweens
                        for i in range(len(_ax.collections)):
                            _ax.collections[0].remove()
                    else:
                        _ax.remove()
                self._view.traceCanvasCosmicPlot2.draw_idle()
            self._view.axCosmicPlot2 = []

            self._view.R1ItemCosmic.setChecked(False)
            self._view.R3ItemCosmic.setChecked(False)
            self._view.allItemCosmic.setChecked(False)
            if self._view.darkSubItemCosmic.isChecked():
                _plotCosmicActiveDarkMultiRoi(self)
            elif self._view.activeItemCosmic.isChecked():
                _plotCosmicActiveMultiRoi(self)
            else:
                _plotCosmicDarkMultiRoi(self)

        else:
            # loop through all axes, check if the line label name R2 exists, if not add it
            for _ax in self._view.axCosmicPlot2:
                if not isinstance(_ax, mpl.lines.Line2D):
                    for _line in _ax.lines:
                        if _line._label == 'R2':
                            log_parsing.log_info(self._view, 'R2 trace already present in plot')
                            _add_plot_flag = False
            if self._view.workspace.selectedROICosmic == []:
                _ROIindex = list(range(self._view.workspace.nSpectra))
            else:
                _ROIindex = self._view.roiDict[self._view.workspace.selectedROICosmic[0]].specIndexList

            _yR2_std = None
            if self._view.meanDisplayCosmic.isChecked():
                if self._view.darkSubItemCosmic.isChecked():
                    if self._view.workspace.tempCosmicRayR2 is not None:
                        _yR2 = self._view.workspace.tempCosmicRayR2.iloc[_ROIindex].mean()
                    else:
                        _yR2 = self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].mean()
                    if self._view.meanStdDisplayCosmic.isChecked():
                        if self._view.workspace.tempCosmicRayR2 is not None:
                            _yR2_std = self._view.workspace.tempCosmicRayR2.iloc[_ROIindex].std()
                        else:
                            _yR2_std = self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].std()
                elif self._view.activeItemCosmic.isChecked():
                    _yR2 = self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].mean()
                    if self._view.meanStdDisplayCosmic.isChecked():
                        _yR2_std = self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].std()
                else:
                    _yR2 = self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].mean()
                    if self._view.meanStdDisplayCosmic.isChecked():
                        _yR2_std = self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].std()
            elif self._view.medianDisplayCosmic.isChecked():
                if self._view.darkSubItemCosmic.isChecked():
                    if self._view.workspace.tempCosmicRayR2 is not None:
                        _yR2 = np.median(self._view.workspace.tempCosmicRayR2.iloc[_ROIindex], axis=0)
                    else:
                        _yR2 = np.median(self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
                    if self._view.medianStdDisplayCosmic.isChecked():
                        if self._view.workspace.tempCosmicRayR2 is not None:
                            _yR2_std = self._view.workspace.tempCosmicRayR2.iloc[_ROIindex].std()
                        else:
                            _yR2_std = self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].std()
                elif self._view.activeItemCosmic.isChecked():
                    _yR2 = np.median(self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
                    if self._view.medianStdDisplayCosmic.isChecked():
                        _yR2_std = self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].std()
                else:
                    _yR2 = np.median(self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
                    if self._view.medianStdDisplayCosmic.isChecked():
                        _yR2_std = self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].std()
            elif self._view.maxDisplayCosmic.isChecked():
                if self._view.darkSubItemCosmic.isChecked():
                    if self._view.workspace.tempCosmicRayR2 is not None:
                        _yR2 = np.max(self._view.workspace.tempCosmicRayR2.iloc[_ROIindex], axis=0)
                    else:
                        _yR2 = np.max(self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
                elif self._view.activeItemCosmic.isChecked():
                    _yR2 = np.max(self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
                else:
                    _yR2 = np.max(self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
            elif self._view.minDisplayCosmic.isChecked():
                if self._view.darkSubItemCosmic.isChecked():
                    if self._view.workspace.tempCosmicRayR2 is not None:
                        _yR2 = np.min(self._view.workspace.darkSubItemCosmic.iloc[_ROIindex], axis=0)
                    else:
                        _yR2 = np.min(self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
                elif self._view.activeItemCosmic.isChecked():
                    _yR2 = np.min(self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
                else:
                    _yR2 = np.min(self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
            else:
                blitting = True
                _indexText = self._view.indexSpecCosmic.text()
                if _indexText == '':
                    self._view.indexSpecCosmic.setText('0')
                    _indexText = '0'
                log_parsing.log_info(self._view, 'Adding traces for spectral indices: '+_indexText)
                _indexStrList = _indexText.split(',')
                self.indexListCosmic = []
                for i in _indexStrList:
                    if ':' not in i:
                        self.indexListCosmic.append(int(i))
                    else:
                        _iList = list(range(int(i.split(':')[0]), int(i.split(':')[1])+1))
                        for j in _iList:
                            self.indexListCosmic.append(int(j))
                if self._view.darkSubItemCosmic.isChecked():
                    if self._view.workspace.tempCosmicRayR2 is not None:
                        _yR2 = self._view.workspace.tempCosmicRayR2.loc[self.indexListCosmic].values
                    else:
                        _yR2 = self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].loc[self.indexListCosmic].values
                elif self._view.activeItemCosmic.isChecked():
                    _yR2 = self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].loc[self.indexListCosmic].values
                else:
                    _yR2 = self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].loc[self.indexListCosmic].values

            if self._view.waveDomainCosmic.isChecked():
                _x = self._view.workspace.wavelength
            else:
                _x = list(range(self._view.workspace.nChannels))
            _color = self._view.workspace.colorR2
            if len(_yR2) == self._view.workspace.nChannels:
                _plotCosmicSingle(self, _x, _yR2, _color, label='R2', y_std = _yR2_std, blitting = blitting)
            else:
                _plotCosmicMulti(self, _x, _yR2, _color, label='R2', y_std = _yR2_std, blitting = blitting)
            log_parsing.log_info(self._view, 'added R2 trace')

    # if the checkbox is unchecked:
    else:
        # loop through all axes, check if the line label name R2 exists, if so, remove it
        for _ax in self._view.axCosmicPlot2:
            if not isinstance(_ax, mpl.lines.Line2D):
                for _line in _ax.lines:
                    if _line._label == 'R2':
                        log_parsing.log_info(self._view, 'removed trace R2')
                        _line.remove()
                # remove std fill_betweens
                for _coll in _ax.collections:
                    if _coll._label == 'R2' or _coll._label == '_R2':
                        _coll.remove()
            else:
                if _ax.get_color() == '#00FF00':
                    _ax.remove()
                    self._view.axCosmicPlot2.remove(_ax)

    self._view.traceCanvasCosmicPlot2.draw_idle()
    if blitting:
        _addSelectionPlotCosmic(self)

def _plotCosmicUpdateRegion3(self):
    blitting = False
    # if the checkbox is checked:
    if self._view.R3ItemCosmic.isChecked():
        # if there are more than 2 ROIs selected:
        if len(self._view.workspace.selectedROICosmic) > 1:
            if self._view.axCosmicPlot2 != []:
                for _ax in self._view.axCosmicPlot2:
                    if not isinstance(_ax, mpl.lines.Line2D):
                        for _line in _ax.lines:
                            _line.remove()
                        # remove std fill_betweens
                        for i in range(len(_ax.collections)):
                            _ax.collections[0].remove()
                    else:
                        _ax.remove()
                self._view.traceCanvasCosmicPlot2.draw_idle()
            self._view.axCosmicPlot2 = []

            self._view.R1ItemCosmic.setChecked(False)
            self._view.R2ItemCosmic.setChecked(False)
            self._view.allItemCosmic.setChecked(False)
            if self._view.darkSubItemCosmic.isChecked():
                _plotCosmicActiveDarkMultiRoi(self)
            elif self._view.activeItemCosmic.isChecked():
                _plotCosmicActiveMultiRoi(self)
            else:
                _plotCosmicDarkMultiRoi(self)

        else:
            # loop through all axes, check if the line label name R3 exists, if not add it
            for _ax in self._view.axCosmicPlot2:
                if not isinstance(_ax, mpl.lines.Line2D):
                    for _line in _ax.lines:
                        if _line._label == 'R3':
                            log_parsing.log_info(self._view, 'R3 trace already present in plot')
                            _add_plot_flag = False
            if self._view.workspace.selectedROICosmic == []:
                _ROIindex = list(range(self._view.workspace.nSpectra))
            else:
                _ROIindex = self._view.roiDict[self._view.workspace.selectedROICosmic[0]].specIndexList

            _yR3_std = None
            if self._view.meanDisplayCosmic.isChecked():
                if self._view.darkSubItemCosmic.isChecked():
                    if self._view.workspace.tempCosmicRayR3 is not None:
                        _yR3 = self._view.workspace.tempCosmicRayR3.iloc[_ROIindex].mean()
                    else:
                        _yR3 = self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].mean()
                    if self._view.meanStdDisplayCosmic.isChecked():
                        if self._view.workspace.tempCosmicRayR3 is not None:
                            _yR3_std = self._view.workspace.tempCosmicRayR3.iloc[_ROIindex].std()
                        else:
                            _yR3_std = self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].std()
                elif self._view.activeItemCosmic.isChecked():
                    _yR3 = self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].mean()
                    if self._view.meanStdDisplayCosmic.isChecked():
                        _yR3_std = self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].std()
                else:
                    _yR3 = self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].mean()
                    if self._view.meanStdDisplayCosmic.isChecked():
                        _yR3_std = self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].std()
            elif self._view.medianDisplayCosmic.isChecked():
                if self._view.darkSubItemCosmic.isChecked():
                    if self._view.workspace.tempCosmicRayR3 is not None:
                        _yR3 = np.median(self._view.workspace.tempCosmicRayR3.iloc[_ROIindex], axis=0)
                    else:
                        _yR3 = np.median(self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
                    if self._view.medianStdDisplayCosmic.isChecked():
                        if self._view.workspace.tempCosmicRayR3 is not None:
                            _yR3_std = self._view.workspace.tempCosmicRayR3.iloc[_ROIindex].std()
                        else:
                            _yR3_std = self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].std()
                elif self._view.activeItemCosmic.isChecked():
                    _yR3 = np.median(self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
                    if self._view.medianStdDisplayCosmic.isChecked():
                        _yR3_std = self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].std()
                else:
                    _yR3 = np.median(self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
                    if self._view.medianStdDisplayCosmic.isChecked():
                        _yR3_std = self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].std()
            elif self._view.maxDisplayCosmic.isChecked():
                if self._view.darkSubItemCosmic.isChecked():
                    if self._view.workspace.tempCosmicRayR3 is not None:
                        _yR3 = np.max(self._view.workspace.tempCosmicRayR3.iloc[_ROIindex], axis=0)
                    else:
                        _yR3 = np.max(self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
                elif self._view.activeItemCosmic.isChecked():
                    _yR3 = np.max(self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
                else:
                    _yR3 = np.max(self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
            elif self._view.minDisplayCosmic.isChecked():
                if self._view.darkSubItemCosmic.isChecked():
                    if self._view.workspace.tempCosmicRayR3 is not None:
                        _yR3 = np.min(self._view.workspace.tempCosmicRayR3.iloc[_ROIindex], axis=0)
                    else:
                        _yR3 = np.min(self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
                elif self._view.activeItemCosmic.isChecked():
                    _yR3 = np.min(self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
                else:
                    _yR3 = np.min(self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
            else:
                blitting = True
                _indexText = self._view.indexSpecCosmic.text()
                if _indexText == '':
                    self._view.indexSpecCosmic.setText('0')
                    _indexText = '0'
                log_parsing.log_info(self._view, 'Adding traces for spectral indices: '+_indexText)
                _indexStrList = _indexText.split(',')
                self.indexListCosmic = []
                for i in _indexStrList:
                    if ':' not in i:
                        self.indexListCosmic.append(int(i))
                    else:
                        _iList = list(range(int(i.split(':')[0]), int(i.split(':')[1])+1))
                        for j in _iList:
                            self.indexListCosmic.append(int(j))

                if self._view.darkSubItemCosmic.isChecked():
                    if self._view.workspace.tempCosmicRayR3 is not None:
                        _yR3 = self._view.workspace.tempCosmicRayR3.loc[self.indexListCosmic].values
                    else:
                        _yR3 = self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].loc[self.indexListCosmic].values
                elif self._view.activeItemCosmic.isChecked():
                    _yR3 = self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].loc[self.indexListCosmic].values
                else:
                    _yR3 = self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].loc[self.indexListCosmic].values

            if self._view.waveDomainCosmic.isChecked():
                _x = self._view.workspace.wavelength
            else:
                _x = list(range(self._view.workspace.nChannels))
            _color = self._view.workspace.colorR3
            if len(_yR3) == self._view.workspace.nChannels:
                _plotCosmicSingle(self, _x, _yR3, _color, label='R3', y_std = _yR3_std, blitting = blitting)
            else:
                _plotCosmicMulti(self, _x, _yR3, _color, label='R3', y_std = _yR3_std, blitting = blitting)
            log_parsing.log_info(self._view, 'added R3 trace')

    # if the checkbox is unchecked:
    else:
        # loop through all axes, check if the line label name R3 exists, if so, remove it
        for _ax in self._view.axCosmicPlot2:
            if not isinstance(_ax, mpl.lines.Line2D):
                for _line in _ax.lines:
                    if _line._label == 'R3':
                        log_parsing.log_info(self._view, 'removed trace R3')
                        _line.remove()
                # remove std fill_betweens
                for _coll in _ax.collections:
                    if _coll._label == 'R3' or _coll._label == '_R3':
                        _coll.remove()
            else:
                if _ax.get_color() == '#FF0000':
                    _ax.remove()
                    self._view.axCosmicPlot2.remove(_ax)

    self._view.traceCanvasCosmicPlot2.draw_idle()
    if blitting:
        _addSelectionPlotCosmic(self)


def _plotCosmicUpdateRegionAll(self):
    blitting = False
    # if the checkbox is checked:
    if self._view.allItemCosmic.isChecked():
        # if there are more than 2 ROIs selected:
        if len(self._view.workspace.selectedROICosmic) > 1:
            if self._view.axCosmicPlot2 != []:
                for _ax in self._view.axCosmicPlot2:
                    if not isinstance(_ax, mpl.lines.Line2D):
                        for _line in _ax.lines:
                            _line.remove()
                        # remove std fill_betweens
                        for i in range(len(_ax.collections)):
                            _ax.collections[0].remove()
                    else:
                        _ax.remove()
                self._view.traceCanvasCosmicPlot2.draw_idle()
            self._view.axCosmicPlot2 = []

            self._view.R1ItemCosmic.setChecked(False)
            self._view.R2ItemCosmic.setChecked(False)
            self._view.R3ItemCosmic.setChecked(False)
            if self._view.darkSubItemCosmic.isChecked():
                _plotCosmicActiveDarkMultiRoi(self)
            elif self._view.activeItemCosmic.isChecked():
                _plotCosmicActiveMultiRoi(self)
            else:
                _plotCosmicDarkMultiRoi(self)
        else:
            # loop through all axes, check if the line label name R1 exists, if not add it
            for _ax in self._view.axCosmicPlot2:
                if not isinstance(_ax, mpl.lines.Line2D):
                    for _line in _ax.lines:
                        if _line._label == 'composite':
                            log_parsing.log_info(self._view, 'composite trace already present in plot')
                            _add_plot_flag = False
            #if _add_plot_flag:
            _yAll_std = None
            if self._view.meanDisplayCosmic.isChecked():
                if self._view.darkSubItemCosmic.isChecked():
                    if self._view.workspace.tempCosmicRayR1 is not None:
                        _yAll = (self._view.workspace.tempCosmicRayR1.mean().values + \
                                 self._view.workspace.tempCosmicRayR2.mean().values + \
                                 self._view.workspace.tempCosmicRayR3.mean().values)
                    else:
                        _yAll = (self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].mean().values + \
                                 self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].mean().values + \
                                 self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].mean().values)
                    if self._view.meanStdDisplayCosmic.isChecked():
                        if self._view.workspace.tempCosmicRayR1 is not None:
                            _yAll_std = (self._view.workspace.tempCosmicRayR1.std().values +
                                         self._view.workspace.tempCosmicRayR2.std().values +
                                         self._view.workspace.tempCosmicRayR3.std().values)
                        else:
                            _yAll_std = (self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].std().values +
                                         self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].std().values +
                                         self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].std().values)
                elif self._view.activeItemCosmic.isChecked():
                    _yAll = (self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].mean().values +
                             self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].mean().values +
                             self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].mean().values)
                    if self._view.meanStdDisplayCosmic.isChecked():
                        _yAll_std = (self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].std().values +
                                     self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].std().values +
                                     self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].std().values)
                else:
                    _yAll = (self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].mean().values +
                             self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].mean().values +
                             self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].mean().values)
                    if self._view.meanStdDisplayCosmic.isChecked():
                        _yAll_std = (self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].std().values +
                                     self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].std().values +
                                     self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].std().values)
            elif self._view.medianDisplayCosmic.isChecked():
                if self._view.darkSubItemCosmic.isChecked():
                    if self._view.workspace.tempCosmicRayR1 is not None:
                        _yAll = (np.median(self._view.workspace.tempCosmicRayR1, axis=0) + \
                                 np.median(self._view.workspace.tempCosmicRayR2, axis=0) + \
                                 np.median(self._view.workspace.tempCosmicRayR3, axis=0))
                    else:
                        _yAll = (np.median(self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected], axis=0) + \
                                 np.median(self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected], axis=0) + \
                                 np.median(self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected], axis=0))
                    if self._view.medianStdDisplayCosmic.isChecked():
                        if self._view.workspace.tempCosmicRayR1 is not None:
                            _yAll_std = (self._view.workspace.tempCosmicRayR1.std().values +
                                         self._view.workspace.tempCosmicRayR2.std().values +
                                         self._view.workspace.tempCosmicRayR3.std().values)
                        else:
                            _yAll_std = (self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].std().values +
                                         self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].std().values +
                                         self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].std().values)
                elif self._view.activeItemCosmic.isChecked():
                    _yAll = (np.median(self._view.workspace.activeSpectraR1[self._view.specProcessingSelected], axis=0) +
                             np.median(self._view.workspace.activeSpectraR2[self._view.specProcessingSelected], axis=0) +
                             np.median(self._view.workspace.activeSpectraR3[self._view.specProcessingSelected], axis=0))
                    if self._view.medianStdDisplayCosmic.isChecked():
                        _yAll_std = (self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].std().values +
                                     self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].std().values +
                                     self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].std().values)
                else:
                    _yAll = (np.median(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected], axis=0) +
                             np.median(self._view.workspace.darkSpectraR2[self._view.specProcessingSelected], axis=0) +
                             np.median(self._view.workspace.darkSpectraR3[self._view.specProcessingSelected], axis=0))
                    if self._view.medianStdDisplayCosmic.isChecked():
                        _yAll_std = (self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].std().values +
                                     self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].std().values +
                                     self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].std().values)
            elif self._view.maxDisplayCosmic.isChecked():
                if self._view.darkSubItemCosmic.isChecked():
                    if self._view.workspace.tempCosmicRayR1 is not None:
                        _yAll = (np.max(self._view.workspace.tempCosmicRayR1, axis=0).values + \
                                 np.max(self._view.workspace.tempCosmicRayR2, axis=0).values + \
                                 np.max(self._view.workspace.tempCosmicRayR3, axis=0).values)
                    else:
                        _yAll = (np.max(self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected], axis=0).values + \
                                 np.max(self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected], axis=0).values + \
                                 np.max(self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected], axis=0).values)
                elif self._view.activeItemCosmic.isChecked():
                    _yAll = (np.max(self._view.workspace.activeSpectraR1[self._view.specProcessingSelected], axis=0).values +
                             np.max(self._view.workspace.activeSpectraR2[self._view.specProcessingSelected], axis=0).values +
                             np.max(self._view.workspace.activeSpectraR3[self._view.specProcessingSelected], axis=0).values)
                else:
                    _yAll = (np.max(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected], axis=0).values +
                             np.max(self._view.workspace.darkSpectraR2[self._view.specProcessingSelected], axis=0).values +
                             np.max(self._view.workspace.darkSpectraR3[self._view.specProcessingSelected], axis=0).values)
            elif self._view.minDisplayCosmic.isChecked():
                if self._view.darkSubItemCosmic.isChecked():
                    if self._view.workspace.tempCosmicRayR1 is not None:
                        _yAll = (np.min(self._view.workspace.tempCosmicRayR1, axis=0).values + \
                                 np.min(self._view.workspace.tempCosmicRayR2, axis=0).values + \
                                 np.min(self._view.workspace.tempCosmicRayR3, axis=0).values)
                    else:
                        _yAll = (np.min(self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected], axis=0).values + \
                                 np.min(self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected], axis=0).values + \
                                 np.min(self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected], axis=0).values)
                elif self._view.activeItemCosmic.isChecked():
                    _yAll = (np.min(self._view.workspace.activeSpectraR1[self._view.specProcessingSelected], axis=0).values +
                             np.min(self._view.workspace.activeSpectraR2[self._view.specProcessingSelected], axis=0).values +
                             np.min(self._view.workspace.activeSpectraR3[self._view.specProcessingSelected], axis=0).values)
                else:
                    _yAll = (np.min(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected], axis=0) +
                             np.min(self._view.workspace.darkSpectraR2[self._view.specProcessingSelected], axis=0) +
                             np.min(self._view.workspace.darkSpectraR3[self._view.specProcessingSelected], axis=0))
            else:
                blitting = True
                _indexText = self._view.indexSpecCosmic.text()
                log_parsing.log_info(self._view, 'Adding traces for spectral indices: '+_indexText)
                if _indexText == '':
                    self._view.indexSpecCosmic.setText('0')
                    _indexText = '0'
                _indexStrList = _indexText.split(',')
                self.indexListCosmic = []
                for i in _indexStrList:
                    if ':' not in i:
                        self.indexListCosmic.append(int(i))
                    else:
                        _iList = list(range(int(i.split(':')[0]), int(i.split(':')[1])+1))
                        for j in _iList:
                            self.indexListCosmic.append(int(j))

                if self._view.darkSubItemCosmic.isChecked():
                    if self._view.workspace.tempCosmicRayR1 is not None:
                        _yAll = (self._view.workspace.tempCosmicRayR1.loc[self.indexListCosmic].values + \
                                 self._view.workspace.tempCosmicRayR2.loc[self.indexListCosmic].values + \
                                 self._view.workspace.tempCosmicRayR3.loc[self.indexListCosmic].values)
                    else:
                        _yAll = (self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].loc[self.indexListCosmic].values + \
                                 self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].loc[self.indexListCosmic].values + \
                                 self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].loc[self.indexListCosmic].values)
                elif self._view.activeItemCosmic.isChecked():
                    _yAll = (self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].loc[self.indexListCosmic].values +
                             self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].loc[self.indexListCosmic].values +
                             self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].loc[self.indexListCosmic].values)
                else:
                    _yAll = (self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].loc[self.indexListCosmic].values +
                             self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].loc[self.indexListCosmic].values +
                             self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].loc[self.indexListCosmic].values)

            if self._view.waveDomainCosmic.isChecked():
                _x = self._view.workspace.wavelength
            else:
                _x = list(range(self._view.workspace.nChannels))
            _color = self._view.workspace.colorComposite
            if len(_yAll) == self._view.workspace.nChannels:
                _plotCosmicSingle(self, _x, _yAll, _color, label='composite', y_std = _yAll_std, blitting = blitting)
            else:
                _plotCosmicMulti(self, _x, _yAll, _color, label='composite', y_std = _yAll_std, blitting = blitting)
            log_parsing.log_info(self._view, 'added composite trace')

    # if the checkbox is unchecked:
    else:
        # loop through all axes, check if the line label name R1 exists, if so, remove it
        for _ax in self._view.axCosmicPlot2:
            if not isinstance(_ax, mpl.lines.Line2D):
                for _line in _ax.lines:
                    if _line._label == 'composite':
                        log_parsing.log_info(self._view, 'removed composite trace')
                        _line.remove()
                        # remove std fill_betweens
                for _coll in _ax.collections:
                    if _coll._label == 'composite' or _coll._label == '_composite':
                        _coll.remove()
            else:
                bltting = True
                if _ax.get_color() == 'w':
                    _ax.remove()
                    self._view.axCosmicPlot2.remove(_ax)

    self._view.traceCanvasCosmicPlot2.draw_idle()
    if blitting:
        _addSelectionPlotCosmic(self)



def _plotCosmicActiveDark(self):
    blitting = False
    if self._view.workspace.selectedROICosmic == []:
        _ROIindex = list(range(self._view.workspace.nSpectra))
    else:
        _ROIindex = self._view.roiDict[self._view.workspace.selectedROICosmic[0]].specIndexList
    _yR1_std = None
    _yR2_std = None
    _yR3_std = None
    _yAll_std = None
    if self._view.meanDisplayCosmic.isChecked():
        if self._view.workspace.tempCosmicRayR1 is not None:
            _yR1 = self._view.workspace.tempCosmicRayR1.iloc[_ROIindex].mean()
            _yR2 = self._view.workspace.tempCosmicRayR2.iloc[_ROIindex].mean()
            _yR3 = self._view.workspace.tempCosmicRayR3.iloc[_ROIindex].mean()
            _yAll = self._view.workspace.tempCosmicRayR1.iloc[_ROIindex].mean().values + \
                    self._view.workspace.tempCosmicRayR2.iloc[_ROIindex].mean().values + \
                    self._view.workspace.tempCosmicRayR3.iloc[_ROIindex].mean().values
            if self._view.meanStdDisplayCosmic.isChecked():
                _yR1_std = self._view.workspace.tempCosmicRayR1.iloc[_ROIindex].std()
                _yR2_std = self._view.workspace.tempCosmicRayR2.iloc[_ROIindex].std()
                _yR3_std = self._view.workspace.tempCosmicRayR3.iloc[_ROIindex].std()
                _yAll_std = self._view.workspace.tempCosmicRayR1.iloc[_ROIindex].std().values + \
                            self._view.workspace.tempCosmicRayR2.iloc[_ROIindex].std().values + \
                            self._view.workspace.tempCosmicRayR3.iloc[_ROIindex].std().values
        else:
            _yR1 = self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].mean()
            _yR2 = self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].mean()
            _yR3 = self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].mean()
            _yAll = self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].mean().values + \
                    self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].mean().values + \
                    self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].mean().values
            if self._view.meanStdDisplayCosmic.isChecked():
                _yR1_std = self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].std()
                _yR2_std = self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].std()
                _yR3_std = self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].std()
                _yAll_std = self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].std().values + \
                            self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].std().values + \
                            self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].std().values
    elif self._view.medianDisplayCosmic.isChecked():
        if self._view.workspace.tempCosmicRayR1 is not None:
            # using numpy is slightly faster than using pandas.median
            _yR1 = np.median(self._view.workspace.tempCosmicRayR1.iloc[_ROIindex], axis=0)
            _yR2 = np.median(self._view.workspace.tempCosmicRayR2.iloc[_ROIindex], axis=0)
            _yR3 = np.median(self._view.workspace.tempCosmicRayR3.iloc[_ROIindex], axis=0)
            _yAll = (np.median(self._view.workspace.tempCosmicRayR1.iloc[_ROIindex], axis=0) +
                     np.median(self._view.workspace.tempCosmicRayR2.iloc[_ROIindex], axis=0) +
                     np.median(self._view.workspace.tempCosmicRayR3.iloc[_ROIindex], axis=0))
            if self._view.medianStdDisplayCosmic.isChecked():
                _yR1_std = self._view.workspace.tempCosmicRayR1.iloc[_ROIindex].std()
                _yR2_std = self._view.workspace.tempCosmicRayR2.iloc[_ROIindex].std()
                _yR3_std = self._view.workspace.tempCosmicRayR3.iloc[_ROIindex].std()
                _yAll_std = self._view.workspace.tempCosmicRayR1.iloc[_ROIindex].std().values + \
                            self._view.workspace.tempCosmicRayR2.iloc[_ROIindex].std().values + \
                            self._view.workspace.tempCosmicRayR3.iloc[_ROIindex].std().values
        else:
            # using numpy is slightly faster than using pandas.median
            _yR1 = np.median(self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
            _yR2 = np.median(self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
            _yR3 = np.median(self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
            _yAll = (np.median(self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0) +
                     np.median(self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0) +
                     np.median(self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0))
            if self._view.medianStdDisplayCosmic.isChecked():
                _yR1_std = self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].std()
                _yR2_std = self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].std()
                _yR3_std = self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].std()
                _yAll_std = self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].std().values + \
                            self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].std().values + \
                            self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].std().values

    elif self._view.maxDisplayCosmic.isChecked():
        if self._view.workspace.tempCosmicRayR1 is not None:
            # using numpy is slightly faster than using pandas.median
            _yR1 = np.max(self._view.workspace.tempCosmicRayR1.iloc[_ROIindex], axis=0)
            _yR2 = np.max(self._view.workspace.tempCosmicRayR2.iloc[_ROIindex], axis=0)
            _yR3 = np.max(self._view.workspace.tempCosmicRayR3.iloc[_ROIindex], axis=0)
            _yAll = (np.max(self._view.workspace.tempCosmicRayR1.iloc[_ROIindex], axis=0).values +
                     np.max(self._view.workspace.tempCosmicRayR2.iloc[_ROIindex], axis=0).values +
                     np.max(self._view.workspace.tempCosmicRayR3.iloc[_ROIindex], axis=0).values)
        else:
            # using numpy is slightly faster than using pandas.median
            _yR1 = np.max(self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
            _yR2 = np.max(self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
            _yR3 = np.max(self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
            _yAll = (np.max(self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0).values +
                     np.max(self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0).values +
                     np.max(self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0).values)

    elif self._view.minDisplayCosmic.isChecked():
        if self._view.workspace.tempCosmicRayR1 is not None:
            # using numpy is slightly faster than using pandas.median
            _yR1 = np.min(self._view.workspace.tempCosmicRayR1.iloc[_ROIindex], axis=0)
            _yR2 = np.min(self._view.workspace.tempCosmicRayR2.iloc[_ROIindex], axis=0)
            _yR3 = np.min(self._view.workspace.tempCosmicRayR3.iloc[_ROIindex], axis=0)
            _yAll = (np.min(self._view.workspace.tempCosmicRayR1.iloc[_ROIindex], axis=0).values +
                     np.min(self._view.workspace.tempCosmicRayR2.iloc[_ROIindex], axis=0).values +
                     np.min(self._view.workspace.tempCosmicRayR3.iloc[_ROIindex], axis=0).values)
        else:
            # using numpy is slightly faster than using pandas.median
            _yR1 = np.min(self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
            _yR2 = np.min(self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
            _yR3 = np.min(self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
            _yAll = (np.min(self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0).values +
                     np.min(self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0).values +
                     np.min(self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0).values)
    else:
        blitting = True
        # read textbox
        # if empty, use index 0
        if self._view.indexSpecCosmic.text() == '' and self._view.cosmicRayManualSpec.text() == '':
            log_parsing.log_warning(self._view, 'No spectral index entered. Using index 0')
            self._view.indexSpecCosmic.setText('0')
            self._view.cosmicRayManualSpec.setText('0')
        _indexText = self._view.indexSpecCosmic.text()
        log_parsing.log_info(self._view, 'Adding traces for spectral indices: '+_indexText)
        _indexStrList = _indexText.split(',')
        self.indexListCosmic = []
        for i in _indexStrList:
            if ':' not in i:
                self.indexListCosmic.append(int(i))
            else:
                _iList = list(range(int(i.split(':')[0]), int(i.split(':')[1])+1))
                for j in _iList:
                    self.indexListCosmic.append(int(j))
        if self._view.workspace.tempCosmicRayR1 is not None:
            _yR1 = self._view.workspace.tempCosmicRayR1.loc[self.indexListCosmic].values
            _yR2 = self._view.workspace.tempCosmicRayR2.loc[self.indexListCosmic].values
            _yR3 = self._view.workspace.tempCosmicRayR3.loc[self.indexListCosmic].values
            _yAll = (self._view.workspace.tempCosmicRayR1.loc[self.indexListCosmic].values +
                     self._view.workspace.tempCosmicRayR2.loc[self.indexListCosmic].values +
                     self._view.workspace.tempCosmicRayR3.loc[self.indexListCosmic].values)
        else:
            _yR1 = self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].loc[self.indexListCosmic].values
            _yR2 = self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].loc[self.indexListCosmic].values
            _yR3 = self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].loc[self.indexListCosmic].values
            _yAll = (self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].loc[self.indexListCosmic].values +
                     self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].loc[self.indexListCosmic].values +
                     self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].loc[self.indexListCosmic].values)


    if self._view.waveDomainCosmic.isChecked():
        _x = self._view.workspace.wavelength
    else:
        _x = list(range(self._view.workspace.nChannels))

    if self._view.R1ItemCosmic.isChecked():
        _color = self._view.workspace.colorR1
        if len(_yR1) == self._view.workspace.nChannels:
            _plotCosmicSingle(self, _x, _yR1, _color, label='R1', y_std =_yR1_std, blitting = blitting)
        else:
            _plotCosmicMulti(self, _x, _yR1, _color, label='R1', y_std =_yR1_std, blitting = blitting)
    if self._view.R2ItemCosmic.isChecked():
        _color = self._view.workspace.colorR2
        if len(_yR2) == self._view.workspace.nChannels:
            _plotCosmicSingle(self, _x, _yR2, _color, label='R2', y_std = _yR2_std, blitting = blitting)
        else:
            _plotCosmicMulti(self, _x, _yR2, _color, label='R2', y_std = _yR2_std, blitting = blitting)
    if self._view.R3ItemCosmic.isChecked():
        _color = self._view.workspace.colorR3
        if len(_yR3) == self._view.workspace.nChannels:
            _plotCosmicSingle(self, _x, _yR3, _color, label='R3', y_std =_yR3_std, blitting = blitting)
        else:
            _plotCosmicMulti(self, _x, _yR3, _color, label='R3', y_std = _yR3_std, blitting = blitting)
    if self._view.allItemCosmic.isChecked():
        _color = self._view.workspace.colorComposite
        if len(_yAll) == self._view.workspace.nChannels:
            _plotCosmicSingle(self, _x, _yAll, _color, label='composite', y_std = _yAll_std, blitting = blitting)
        else:
            _plotCosmicMulti(self, _x, _yAll, _color, label='composite', y_std = _yAll_std, blitting = blitting)

    if self._view.traceCanvasCosmicPlot2.axes.xaxis.label._text == '' or True:
        _plotCosmicFormat(self)
    self._view.traceCanvasCosmicPlot2.draw_idle()


def _plotCosmicDark(self):
    blitting = False
    if self._view.workspace.selectedROICosmic == []:
        _ROIindex = list(range(self._view.workspace.nSpectra))
    else:
        _ROIindex = self._view.roiDict[self._view.workspace.selectedROICosmic[0]].specIndexList
    _yR1_std  = None
    _yR2_std  = None
    _yR3_std  = None
    _yAll_std = None
    if self._view.meanDisplayCosmic.isChecked():
        _yR1 = self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].mean()
        _yR2 = self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].mean()
        _yR3 = self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].mean()
        _yAll = (self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].mean().values +
                 self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].mean().values +
                 self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].mean().values)
        if self._view.meanStdDisplayCosmic.isChecked():
            _yR1_std = self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].std()
            _yR2_std = self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].std()
            _yR3_std = self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].std()
            _yAll_std = (self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].std().values +
                         self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].std().values +
                         self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].std().values)

    elif self._view.medianDisplayCosmic.isChecked():
        # using numpy is slightly faster than using pandas.median
        _yR1 = np.median(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
        _yR2 = np.median(self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
        _yR3 = np.median(self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
        _yAll = (np.median(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0) +
                 np.median(self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0) +
                 np.median(self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0))
        if self._view.medianStdDisplayCosmic.isChecked():
            _yR1_std = self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].std()
            _yR2_std = self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].std()
            _yR3_std = self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].std()
            _yAll_std = (self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].std().values +
                         self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].std().values +
                         self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].std().values)
    elif self._view.maxDisplayCosmic.isChecked():
        # using numpy is slightly faster than using pandas.median
        _yR1 = np.max(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
        _yR2 = np.max(self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
        _yR3 = np.max(self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
        _yAll = (np.max(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0).values +
                 np.max(self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0).values +
                 np.max(self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0).values)
    elif self._view.minDisplayCosmic.isChecked():
        # using numpy is slightly faster than using pandas.median
        _yR1 = np.min(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
        _yR2 = np.min(self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
        _yR3 = np.min(self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
        _yAll = (np.min(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0).values +
                 np.min(self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0).values +
                 np.min(self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0).values)
    else:
        blitting = True
        # read textbox
        # if empty, use index 0
        if self._view.indexSpecCosmic.text() == '' and self._view.cosmicRayManualSpec.text() == '':
            log_parsing.log_warning(self._view, 'No spectral index entered. Using index 0')
            self._view.indexSpecCosmic.setText('0')
            self._view.cosmicRayManualSpec.setText('0')
        _indexText = self._view.indexSpecCosmic.text()
        log_parsing.log_info(self._view, 'Adding traces for spectral indices: '+_indexText)
        _indexStrList = _indexText.split(',')
        self.indexListCosmic = []
        for i in _indexStrList:
            if ':' not in i:
                self.indexListCosmic.append(int(i))
            else:
                _iList = list(range(int(i.split(':')[0]), int(i.split(':')[1])+1))
                for j in _iList:
                    self.indexListCosmic.append(int(j))
        _yR1 = self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].loc[self.indexListCosmic].values
        _yR2 = self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].loc[self.indexListCosmic].values
        _yR3 = self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].loc[self.indexListCosmic].values
        _yAll = self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].loc[self.indexListCosmic].values + \
                self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].loc[self.indexListCosmic].values + \
                self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].loc[self.indexListCosmic].values


    if self._view.waveDomainCosmic.isChecked():
        _x = self._view.workspace.wavelength
    else:
        _x = list(range(self._view.workspace.nChannels))

    if self._view.R1ItemCosmic.isChecked():
        _color = self._view.workspace.colorR1
        if len(_yR1) == self._view.workspace.nChannels:
            _plotCosmicSingle(self, _x, _yR1, _color, label='R1', y_std = _yR1_std, blitting = blitting)
        else:
            _plotCosmicMulti(self, _x, _yR1, _color, label='R1', y_std = _yR1_std, blitting = blitting)
    if self._view.R2ItemCosmic.isChecked():
        _color = self._view.workspace.colorR2
        if len(_yR2) == self._view.workspace.nChannels:
            _plotCosmicSingle(self, _x, _yR2, _color, label='R2', y_std = _yR2_std, blitting = blitting)
        else:
            _plotCosmicMulti(self, _x, _yR2, _color, label='R2', y_std = _yR2_std, blitting = blitting)
    if self._view.R3ItemCosmic.isChecked():
        _color = self._view.workspace.colorR3
        if len(_yR3) == self._view.workspace.nChannels:
            _plotCosmicSingle(self, _x, _yR3, _color, label='R3', y_std = _yR3_std, blitting = blitting)
        else:
            _plotCosmicMulti(self, _x, _yR3, _color, label='R3', y_std = _yR3_std, blitting = blitting)
    if self._view.allItemCosmic.isChecked():
        _color = self._view.workspace.colorComposite
        if len(_yAll) == self._view.workspace.nChannels:
            _plotCosmicSingle(self, _x, _yAll, _color, label='composite', y_std = _yAll_std, blitting = blitting)
        else:
            _plotCosmicMulti(self, _x, _yAll, _color, label='composite', y_std = _yAll_std, blitting = blitting)

    if self._view.traceCanvasCosmicPlot2.axes.xaxis.label._text == '' or True:
        _plotCosmicFormat(self)
    self._view.traceCanvasCosmicPlot2.draw_idle()

def _plotCosmicActive(self):
    blitting = False
    if self._view.workspace.selectedROICosmic == []:
        _ROIindex = list(range(self._view.workspace.nSpectra))
    else:
        _ROIindex = self._view.roiDict[self._view.workspace.selectedROICosmic[0]].specIndexList
    _yR1_std = None
    _yR2_std = None
    _yR3_std = None
    _yAll_std = None
    if self._view.meanDisplayCosmic.isChecked():
        _yR1 = self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].mean()
        _yR2 = self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].mean()
        _yR3 = self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].mean()
        _yAll = self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].mean().values + \
                self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].mean().values + \
                self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].mean().values
        if self._view.meanStdDisplayCosmic.isChecked():
            _yR1_std = self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].mean()
            _yR2_std = self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].mean()
            _yR3_std = self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].mean()
            _yAll_std = self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].mean().values + \
                        self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].mean().values + \
                        self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].mean().values
    elif self._view.medianDisplayCosmic.isChecked():
        # using numpy is slightly faster than using pandas.median
        _yR1 = np.median(self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
        _yR2 = np.median(self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
        _yR3 = np.median(self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
        _yAll = np.median(self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0) + \
                np.median(self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0) + \
                np.median(self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
        if self._view.medianStdDisplayCosmic.isChecked():
            _yR1_std = self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].mean()
            _yR2_std = self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].mean()
            _yR3_std = self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].mean()
            _yAll_std = self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex].mean().values + \
                        self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex].mean().values + \
                        self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex].mean().values
    elif self._view.maxDisplayCosmic.isChecked():
        # using numpy is slightly faster than using pandas.median
        _yR1 = np.max(self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
        _yR2 = np.max(self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
        _yR3 = np.max(self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
        _yAll = np.max(self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0).values + \
                np.max(self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0).values + \
                np.max(self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0).values
    elif self._view.minDisplayCosmic.isChecked():
        # using numpy is slightly faster than using pandas.median
        _yR1 = np.min(self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
        _yR2 = np.min(self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
        _yR3 = np.min(self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0)
        _yAll = np.min(self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_ROIindex], axis=0).values + \
                np.min(self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_ROIindex], axis=0).values + \
                np.min(self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_ROIindex], axis=0).values
    else:
        blitting = True
        # read textbox
        # if empty, use index 0
        if self._view.indexSpecCosmic.text() == '' and self._view.cosmicRayManualSpec.text() == '':
            log_parsing.log_warning(self._view, 'No spectral index entered. Using index 0')
            self._view.indexSpecCosmic.setText('0')
            self._view.cosmicRayManualSpec.setText('0')
        _indexText = self._view.indexSpecCosmic.text()
        log_parsing.log_info(self._view, 'Adding traces for spectral indices: '+_indexText)
        _indexStrList = _indexText.split(',')
        self.indexListCosmic = []
        for i in _indexStrList:
            if ':' not in i:
                self.indexListCosmic.append(int(i))
            else:
                _iList = list(range(int(i.split(':')[0]), int(i.split(':')[1])+1))
                for j in _iList:
                    self.indexListCosmic.append(int(j))
        _yR1 = self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].loc[self.indexListCosmic].values
        _yR2 = self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].loc[self.indexListCosmic].values
        _yR3 = self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].loc[self.indexListCosmic].values
        _yAll = self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].loc[self.indexListCosmic].values + \
                self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].loc[self.indexListCosmic].values + \
                self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].loc[self.indexListCosmic].values


    if self._view.waveDomainCosmic.isChecked():
        _x = self._view.workspace.wavelength
    else:
        _x = list(range(self._view.workspace.nChannels))

    if self._view.R1ItemCosmic.isChecked():
        _color = self._view.workspace.colorR1
        if len(_yR1) == self._view.workspace.nChannels:
            _plotCosmicSingle(self, _x, _yR1, _color, label='R1', y_std = _yR1_std, blitting = blitting)
        else:
            _plotCosmicMulti(self, _x, _yR1, _color, label='R1', y_std = _yR1_std, blitting = blitting)
    if self._view.R2ItemCosmic.isChecked():
        _color = self._view.workspace.colorR2
        if len(_yR2) == self._view.workspace.nChannels:
            _plotCosmicSingle(self, _x, _yR2, _color, label='R2', y_std = _yR2_std, blitting = blitting)
        else:
            _plotCosmicMulti(self, _x, _yR2, _color, label='R2', y_std = _yR2_std, blitting = blitting)
    if self._view.R3ItemCosmic.isChecked():
        _color = self._view.workspace.colorR3
        if len(_yR3) == self._view.workspace.nChannels:
            _plotCosmicSingle(self, _x, _yR3, _color, label='R3', y_std = _yR3_std, blitting = blitting)
        else:
            _plotCosmicMulti(self, _x, _yR3, _color, label='R3', y_std = _yR3_std, blitting = blitting)
    if self._view.allItemCosmic.isChecked():
        _color = self._view.workspace.colorComposite
        if len(_yAll) == self._view.workspace.nChannels:
            _plotCosmicSingle(self, _x, _yAll, _color, label='composite', y_std = _yAll_std, blitting = blitting)
        else:
            _plotCosmicMulti(self, _x, _yAll, _color, label='composite', y_std = _yAll_std, blitting = blitting)

    if self._view.traceCanvasCosmicPlot2.axes.xaxis.label._text == '' or True:
        _plotCosmicFormat(self)
    self._view.traceCanvasCosmicPlot2.draw_idle()


def _plotCosmicActiveDarkMultiRoi(self):
    blitting = False
    _ROIindex = [self._view.roiDict[_roiList].specIndexList for _roiList in self._view.workspace.selectedROICosmic]
    _yR1_std = None
    _yR2_std = None
    _yR3_std = None
    _yAll_std = None
    if self._view.workspace.tempCosmicRayR1 is not None:
        _R1AD = self._view.workspace.tempCosmicRayR1
        _R2AD = self._view.workspace.tempCosmicRayR2
        _R3AD = self._view.workspace.tempCosmicRayR3
    else:
        _R1AD = self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected]
        _R2AD = self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected]
        _R3AD = self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected]
    if self._view.meanDisplayCosmic.isChecked():
        _yR1 = [_R1AD.iloc[_indexList].mean() for _indexList in _ROIindex]
        _yR2 = [_R2AD.iloc[_indexList].mean() for _indexList in _ROIindex]
        _yR3 = [_R3AD.iloc[_indexList].mean() for _indexList in _ROIindex]
        _yAll = [(_R1AD.iloc[_indexList].mean().values +
                  _R2AD.iloc[_indexList].mean().values +
                  _R3AD.iloc[_indexList].mean().values) for _indexList in _ROIindex]
        if self._view.meanStdDisplayCosmic.isChecked():
            _yR1_std = [_R1AD.iloc[_indexList].std() for _indexList in _ROIindex]
            _yR2_std = [_R2AD.iloc[_indexList].std() for _indexList in _ROIindex]
            _yR3_std = [_R3AD.iloc[_indexList].std() for _indexList in _ROIindex]
            _yAll_std = [(_R1AD.iloc[_indexList].std().values +
                          _R2AD.iloc[_indexList].std().values +
                          _R3AD.iloc[_indexList].std().values) for _indexList in _ROIindex]
    elif self._view.medianDisplayCosmic.isChecked():
        # using numpy is slightly faster than using pandas.median
        _yR1 = [np.median(_R1AD.iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yR2 = [np.median(_R2AD.iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yR3 = [np.median(_R3AD.iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yAll = [(np.median(_R1AD.iloc[_indexList], axis=0) +
                  np.median(_R2AD.iloc[_indexList], axis=0) +
                  np.median(_R3AD.iloc[_indexList], axis=0)) for _indexList in _ROIindex]
        if self._view.medianStdDisplayCosmic.isChecked():
            _yR1_std = [_R1AD.iloc[_indexList].std() for _indexList in _ROIindex]
            _yR2_std = [_R2AD.iloc[_indexList].std() for _indexList in _ROIindex]
            _yR3_std = [_R3AD.iloc[_indexList].std() for _indexList in _ROIindex]
            _yAll_std = [(_R1AD.iloc[_indexList].std().values +
                          _R2AD.iloc[_indexList].std().values +
                          _R3AD.iloc[_indexList].std().values) for _indexList in _ROIindex]
    elif self._view.maxDisplayCosmic.isChecked():
        # using numpy is slightly faster than using pandas.median
        _yR1 = [np.max(_R1AD.iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yR2 = [np.max(_R2AD.iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yR3 = [np.max(_R3AD.iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yAll = [(np.max(_R1AD.iloc[_indexList], axis=0).values +
                  np.max(_R2AD.iloc[_indexList], axis=0).values +
                  np.max(_R3AD.iloc[_indexList], axis=0).values) for _indexList in _ROIindex]
    elif self._view.minDisplayCosmic.isChecked():
        # using numpy is slightly faster than using pandas.median
        _yR1 = [np.min(_R1AD.iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yR2 = [np.min(_R2AD.iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yR3 = [np.min(_R3AD.iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yAll = [(np.min(_R1AD.iloc[_indexList], axis=0).values +
                  np.min(_R2AD.iloc[_indexList], axis=0).values +
                  np.min(_R3AD.iloc[_indexList], axis=0).values) for _indexList in _ROIindex]
    else:
        log_parsing.log_error(self._view, 'Cannot display subset of selected indices with multiple ROIs selected')

    if self._view.waveDomainCosmic.isChecked():
        _x = self._view.workspace.wavelength
    else:
        _x = list(range(self._view.workspace.nChannels))

    _color = [self._view.roiDict[_roiDictName].color for _roiDictName in self._view.workspace.selectedROICosmic]
    _legend = [self._view.roiDict[_roiDictName].humanReadableName for _roiDictName in self._view.workspace.selectedROICosmic]
    if self._view.R1ItemCosmic.isChecked():
        _plotCosmicMulti(self, _x, _yR1, _color, label=_legend, legend = True, y_std = _yR1_std, blitting = blitting)
    elif self._view.R2ItemCosmic.isChecked():
        _plotCosmicMulti(self, _x, _yR2, _color, label=_legend, legend = True, y_std = _yR2_std, blitting = blitting)
    elif self._view.R3ItemCosmic.isChecked():
        _plotCosmicMulti(self, _x, _yR3, _color, label=_legend, legend = True, y_std = _yR3_std, blitting = blitting)
    elif self._view.allItemCosmic.isChecked():
        _plotCosmicMulti(self, _x, _yAll, _color, label=_legend, legend = True, y_std = _yAll_std, blitting = blitting)

    # add the upper axis for wavenumbers
    if self._view.traceCanvasCosmicPlot2.axes.xaxis.label._text == '' or True:
        _plotCosmicFormat(self)
    self._view.traceCanvasCosmicPlot2.draw_idle()

def _plotCosmicDarkMultiRoi(self):
    blitting = False
    _ROIindex = [self._view.roiDict[_roiList].specIndexList for _roiList in self._view.workspace.selectedROICosmic]
    _yR1_std  = None
    _yR2_std  = None
    _yR3_std  = None
    _yAll_std = None
    if self._view.meanDisplayCosmic.isChecked():
        _yR1 = [self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_indexList].mean() for _indexList in _ROIindex]
        _yR2 = [self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_indexList].mean() for _indexList in _ROIindex]
        _yR3 = [self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_indexList].mean() for _indexList in _ROIindex]
        _yAll = [(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_indexList].mean().values +
                  self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_indexList].mean().values +
                  self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_indexList].mean().values) for _indexList in _ROIindex]
        if self._view.meanStdDisplayCosmic.isChecked():
            _yR1_std = [self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_indexList].std() for _indexList in _ROIindex]
            _yR2_std = [self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_indexList].std() for _indexList in _ROIindex]
            _yR3_std = [self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_indexList].std() for _indexList in _ROIindex]
            _yAll_std = [(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_indexList].std().values +
                          self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_indexList].std().values +
                          self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_indexList].std().values) for _indexList in _ROIindex]
    elif self._view.medianDisplayCosmic.isChecked():
        # using numpy is slightly faster than using pandas.median
        _yR1 = [np.median(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yR2 = [np.median(self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yR3 = [np.median(self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yAll = [(np.median(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_indexList], axis=0) +
                  np.median(self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_indexList], axis=0) +
                  np.median(self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_indexList], axis=0)) for _indexList in _ROIindex]
        if self._view.medianStdDisplayCosmic.isChecked():
            _yR1_std = [self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_indexList].std() for _indexList in _ROIindex]
            _yR2_std = [self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_indexList].std() for _indexList in _ROIindex]
            _yR3_std = [self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_indexList].std() for _indexList in _ROIindex]
            _yAll_std = [(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_indexList].std().values +
                          self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_indexList].std().values +
                          self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_indexList].std().values) for _indexList in _ROIindex]
    elif self._view.maxDisplayCosmic.isChecked():
        # using numpy is slightly faster than using pandas.median
        _yR1 = [np.max(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yR2 = [np.max(self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yR3 = [np.max(self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yAll = [(np.max(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_indexList], axis=0).values +
                  np.max(self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_indexList], axis=0).values +
                  np.max(self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_indexList], axis=0).values) for _indexList in _ROIindex]
    elif self._view.minDisplayCosmic.isChecked():
        # using numpy is slightly faster than using pandas.median
        _yR1 = [np.min(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yR2 = [np.min(self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yR3 = [np.min(self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yAll = [(np.min(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].iloc[_indexList], axis=0).values +
                  np.min(self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].iloc[_indexList], axis=0).values +
                  np.min(self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].iloc[_indexList], axis=0).values) for _indexList in _ROIindex]
    else:
        log_parsing.log_error(self._view, 'Cannot display subset of selected indices with multiple ROIs selected')

    if self._view.waveDomainCosmic.isChecked():
        _x = self._view.workspace.wavelength
    else:
        _x = list(range(self._view.workspace.nChannels))

    _color = [self._view.roiDict[_roiDictName].color for _roiDictName in self._view.workspace.selectedROICosmic]
    _legend = [self._view.roiDict[_roiDictName].humanReadableName for _roiDictName in self._view.workspace.selectedROICosmic]
    if self._view.R1ItemCosmic.isChecked():
        _plotCosmicMulti(self, _x, _yR1, _color, label=_legend, legend = True, y_std = _yR1_std, blitting = blitting)
    elif self._view.R2ItemCosmic.isChecked():
        _plotCosmicMulti(self, _x, _yR2, _color, label=_legend, legend = True, y_std = _yR2_std, blitting = blitting)
    elif self._view.R3ItemCosmic.isChecked():
        _plotCosmicMulti(self, _x, _yR3, _color, label=_legend, legend = True, y_std = _yR3_std, blitting = blitting)
    elif self._view.allItemCosmic.isChecked():
        _plotCosmicMulti(self, _x, _yAll, _color, label=_legend, legend = True, y_std = _yAll_std, blitting = blitting)

    if self._view.traceCanvasCosmicPlot2.axes.xaxis.label._text == '' or True:
        _plotCosmicFormat(self)
    self._view.traceCanvasCosmicPlot2.draw_idle()


def _plotCosmicActiveMultiRoi(self):
    blitting = False
    _ROIindex = [self._view.roiDict[_roiList].specIndexList for _roiList in self._view.workspace.selectedROICosmic]
    _yR1_std  = None
    _yR2_std  = None
    _yR3_std  = None
    _yAll_std = None
    if self._view.meanDisplayCosmic.isChecked():
        _yR1 = [self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_indexList].mean() for _indexList in _ROIindex]
        _yR2 = [self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_indexList].mean() for _indexList in _ROIindex]
        _yR3 = [self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_indexList].mean() for _indexList in _ROIindex]
        _yAll = [self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_indexList].mean().values + \
                 self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_indexList].mean().values + \
                 self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_indexList].mean().values for _indexList in _ROIindex]
        if self._view.meanStdDisplayCosmic.isChecked():
            _yR1_std = [self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_indexList].std() for _indexList in _ROIindex]
            _yR2_std = [self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_indexList].std() for _indexList in _ROIindex]
            _yR3_std = [self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_indexList].std() for _indexList in _ROIindex]
            _yAll_std = [self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_indexList].std().values + \
                         self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_indexList].std().values + \
                         self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_indexList].std().values for _indexList in _ROIindex]
    elif self._view.medianDisplayCosmic.isChecked():
        # using numpy is slightly faster than using pandas.median
        _yR1 = [np.median(self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yR2 = [np.median(self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yR3 = [np.median(self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yAll = [np.median(self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_indexList], axis=0) + \
                 np.median(self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_indexList], axis=0) + \
                 np.median(self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_indexList], axis=0) for _indexList in _ROIindex]
        if self._view.medianStdDisplayCosmic.isChecked():
            _yR1_std = [self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_indexList].std() for _indexList in _ROIindex]
            _yR2_std = [self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_indexList].std() for _indexList in _ROIindex]
            _yR3_std = [self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_indexList].std() for _indexList in _ROIindex]
            _yAll_std = [self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_indexList].std().values + \
                         self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_indexList].std().values + \
                         self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_indexList].std().values for _indexList in _ROIindex]
    elif self._view.maxDisplayCosmic.isChecked():
        # using numpy is slightly faster than using pandas.median
        _yR1 = [np.max(self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yR2 = [np.max(self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yR3 = [np.max(self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yAll = [np.max(self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_indexList], axis=0).values + \
                 np.max(self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_indexList], axis=0).values + \
                 np.max(self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_indexList], axis=0).values for _indexList in _ROIindex]
    elif self._view.minDisplayCosmic.isChecked():
        # using numpy is slightly faster than using pandas.median
        _yR1 = [np.min(self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yR2 = [np.min(self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yR3 = [np.min(self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_indexList], axis=0) for _indexList in _ROIindex]
        _yAll = [np.min(self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].iloc[_indexList], axis=0).values + \
                 np.min(self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].iloc[_indexList], axis=0).values + \
                 np.min(self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].iloc[_indexList], axis=0).values for _indexList in _ROIindex]
    else:
        log_parsing.log_error(self._view, 'Cannot display subset of selected indices with multiple ROIs selected')

    if self._view.waveDomainCosmic.isChecked():
        _x = self._view.workspace.wavelength
    else:
        _x = list(range(self._view.workspace.nChannels))

    _color = [self._view.roiDict[_roiDictName].color for _roiDictName in self._view.workspace.selectedROICosmic]
    _legend = [self._view.roiDict[_roiDictName].humanReadableName for _roiDictName in self._view.workspace.selectedROICosmic]
    if self._view.R1ItemCosmic.isChecked():
        _plotCosmicMulti(self, _x, _yR1, _color, label=_legend, legend = True, y_std = _yR1_std, blitting = blitting)
    elif self._view.R2ItemCosmic.isChecked():
        _plotCosmicMulti(self, _x, _yR2, _color, label=_legend, legend = True, y_std = _yR2_std, blitting = blitting)
    elif self._view.R3ItemCosmic.isChecked():
        _plotCosmicMulti(self, _x, _yR3, _color, label=_legend, legend = True, y_std = _yR3_std, blitting = blitting)
    elif self._view.allItemCosmic.isChecked():
        _plotCosmicMulti(self, _x, _yAll, _color, label=_legend, legend = True, y_std = _yAll_std, blitting = blitting)

    if self._view.traceCanvasCosmicPlot2.axes.xaxis.label._text == '' or True:
        _plotCosmicFormat(self)
    self._view.traceCanvasCosmicPlot2.draw_idle()


def _plotCosmicSingle(self, x, y, color, alpha=0.9, label='', y_std = None, blitting = False):
    if blitting:
        _ax = generate_plots.plotCosmicSingleTrace(self._view, x, y, color, alpha=alpha, label=label, x_range = self._view._xRangeCosmic, y_range = self._view._yRangeCosmic)
    else:
        _ax = generate_plots.plotCosmicTrace(self._view, x, y, color, alpha=alpha, label=label, std = y_std)
        _legend = _ax.get_legend()
        if _legend is not None:
            _legend.remove()
    self._view.axCosmicPlot2.append(_ax)


def _plotCosmicMulti(self, x, y, color, label='', legend = False, y_std = None, blitting = False):
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
        if blitting:
            _ax = generate_plots.plotCosmicSingleTrace(self._view, x, _y_i, c_i, alpha=_alpha, label=_label, x_range = self._view._xRangeCosmic, y_range = self._view._yRangeCosmic)
        else:
            _ax = generate_plots.plotCosmicTrace(self._view, x, _y_i, c_i, alpha=_alpha, label=_label, std = _ystd_i)
            if legend:
                _ax.legend()
            else:
                _legend = _ax.get_legend()
                if _legend is not None:
                    _legend.remove()
        self._view.axCosmicPlot2.append(_ax)
        i+=1



def _addSelectionPlotCosmic(self, retain_zoom=False):
    _i = self._view.selectionScrollbarCosmic.value()
    if self._view.waveDomainCosmic.isChecked():
        _x = self._view.workspace.wavelength
    else:
        _x = list(range(self._view.workspace.nChannels))
    _y = []
    _color = []
    if self._view.R1ItemCosmic.isChecked():
        if self._view.activeItemCosmic.isChecked():
            _y.append(self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].loc[_i].values)
        elif self._view.darkItemCosmic.isChecked():
            _y.append(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].loc[_i].values)
        else:
            if self._view.workspace.tempCosmicRayR1 is not None:
                _y.append(self._view.workspace.tempCosmicRayR1.loc[_i].values)
            else:
                _y.append(self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].loc[_i].values)
        _color.append(self._view.workspace.colorR1)
    if self._view.R2ItemCosmic.isChecked():
        if self._view.activeItemCosmic.isChecked():
            _y.append(self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].loc[_i].values)
        elif self._view.darkItemCosmic.isChecked():
            _y.append(self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].loc[_i].values)
        else:
            if self._view.workspace.tempCosmicRayR2 is not None:
                _y.append(self._view.workspace.tempCosmicRayR2.loc[_i].values)
            else:
                _y.append(self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].loc[_i].values)
        _color.append(self._view.workspace.colorR2)
    if self._view.R3ItemCosmic.isChecked():
        if self._view.activeItemCosmic.isChecked():
            _y.append(self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].loc[_i].values)
        elif self._view.darkItemCosmic.isChecked():
            _y.append(self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].loc[_i].values)
        else:
            if self._view.workspace.tempCosmicRayR3 is not None:
                _y.append(self._view.workspace.tempCosmicRayR3.loc[_i].values)
            else:
                _y.append(self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].loc[_i].values)
        _color.append(self._view.workspace.colorR3)
    if self._view.allItemCosmic.isChecked():
        if self._view.activeItemCosmic.isChecked():
            _y.append(self._view.workspace.activeSpectraR1[self._view.specProcessingSelected].loc[_i].values + self._view.workspace.activeSpectraR2[self._view.specProcessingSelected].loc[_i].values + self._view.workspace.activeSpectraR3[self._view.specProcessingSelected].loc[_i].values)
        elif self._view.darkItemCosmic.isChecked():
            _y.append(self._view.workspace.darkSpectraR1[self._view.specProcessingSelected].loc[_i].values + self._view.workspace.darkSpectraR2[self._view.specProcessingSelected].loc[_i].values + self._view.workspace.darkSpectraR3[self._view.specProcessingSelected].loc[_i].values)
        else:
            if self._view.workspace.tempCosmicRayR1 is not None:
                _y.append(self._view.workspace.tempCosmicRayR1.loc[_i].values + self._view.workspace.tempCosmicRayR2.loc[_i].values + self._view.workspace.tempCosmicRayR3.loc[_i].values)
            else:
                _y.append(self._view.workspace.darkSubSpectraR1[self._view.specProcessingSelected].loc[_i].values + self._view.workspace.darkSubSpectraR2[self._view.specProcessingSelected].loc[_i].values + self._view.workspace.darkSubSpectraR3[self._view.specProcessingSelected].loc[_i].values)
        _color.append(self._view.workspace.colorComposite)

    # determine if the user zoomed in on the plot
    if len(self._view.axCosmicPlot2) > 0 and ((self._view._xRangeCosmic is not None and self._view.axCosmicPlot2[0].axes.get_xbound() != self._view._xRangeCosmic) or (self._view._yRangeCosmic is not None and self._view.axCosmicPlot2[0].axes.get_ybound() != self._view._yRangeCosmic)):
        print('updating axis background')
        self._view._xRangeCosmic = self._view.axCosmicPlot2[0].axes.get_xbound()
        self._view._yRangeCosmic = self._view.axCosmicPlot2[0].axes.get_ybound()
        _clearCosmicPlotSpec(self)
        for _yi, _ci in zip(_y, _color):
            _ax = generate_plots.plotCosmicSingleTrace(self._view, _x, _yi, _ci, alpha=0.0, label=str(_i), x_range = self._view._xRangeCosmic, y_range = self._view._yRangeCosmic)
            self._view.axCosmicPlot2.append(_ax)
        if self._view.axTopCosmic is None or self._view.axTopCosmic.xaxis.label._text == '':
            _plotCosmicFormat(self, x_range = self._view._xRangeCosmic, y_range = self._view._yRangeCosmic)
        self._view.traceCanvasCosmicPlot2.draw()
        self._view._ax2BackgroundCosmic = self._view.traceCanvasCosmicPlot2.fig.canvas.copy_from_bbox(_ax.axes.bbox)

    elif len(self._view.axCosmicPlot2) == 0 or self._view._ax2BackgroundCosmic is None or len(_color) != len(self._view.axCosmicPlot2):
        print('updating axis background')
        _clearCosmicPlotSpec(self)
        for _yi, _ci in zip(_y, _color):
            _ax = generate_plots.plotCosmicSingleTrace(self._view, _x, _yi, _ci, alpha=0.0, label=str(_i))
            self._view.axCosmicPlot2.append(_ax)
        if self._view.axTopCosmic is None or self._view.axTopCosmic.xaxis.label._text == '':
            _plotCosmicFormat(self)
        self._view.traceCanvasCosmicPlot2.axes.relim()
        _rescaleYCosmic2(self)
        self._view.traceCanvasCosmicPlot2.draw()
        self._view._ax2BackgroundCosmic = self._view.traceCanvasCosmicPlot2.fig.canvas.copy_from_bbox(_ax.axes.bbox)
        self._view._xRangeCosmic = self._view.axCosmicPlot2[-1].axes.get_xbound()
        self._view._yRangeCosmic = self._view.axCosmicPlot2[-1].axes.get_ybound()
        #_ax.set_alpha(0.9)
        #_updateLaserSelectionLineEdit(self)
    # this is not needed?
    elif False and self._view.axCosmicPlot2[-1].axes.get_ybound() != self._view._yRangeCosmic and self._view.axCosmicPlot2[-1].axes.get_xbound() != self._view._xRangeCosmic:
        print('updating axis background (after zoom)')
        self._view._yRangeCosmic = self._view.axCosmicPlot2[-1].axes.get_ybound()
        self._view._xRangeCosmic = self._view.axCosmicPlot2[-1].axes.get_xbound()
        _xx = self._view.axCosmicPlot2[-1]._x
        _yy = self._view.axCosmicPlot2[-1]._y
        for _ax in self._view.axCosmicPlot2:
            _ax.remove()
            try:
                self._view.traceCanvasCosmicPlot2.axes._remove_legend(self._view.traceCanvasCosmicPlot2.axes.get_legend())
            except:
                pass
        self._view.axCosmicPlot2 = []
        _ax = generate_plots.plotCosmicSingleTrace(self._view, _xx, _yy, 'w', alpha=0.0, x_range=self._view._xRangeCosmic, y_range=self._view._yRangeCosmic)
        self._view.traceCanvasCosmicPlot2.draw_idle()
        self._view.axCosmicPlot2.append(_ax)
        self._view._ax2BackgroundCosmic = self._view.traceCanvasCosmicPlot2.fig.canvas.copy_from_bbox(_ax.axes.bbox)

    # restore background
    self._view.traceCanvasCosmicPlot2.fig.canvas.restore_region(self._view._ax2BackgroundCosmic)
    # define the new data
    for _yi, _ci in zip(_y, _color):
        _ax_list = [self._view.axCosmicPlot2[i] for i in range(len(self._view.axCosmicPlot2)) if self._view.axCosmicPlot2[i].get_color() == _ci]
        if len(_ax_list) > 0:
            _ax = _ax_list[0]
            _ax.set_alpha(0.9)
            _ax.set_color(_ci)
            _ax.set_data(_x, _yi)
            # redraw just the points
            _ax.axes.draw_artist(_ax)
            # fill in the axis
            self._view.traceCanvasCosmicPlot2.fig.canvas.blit(_ax.axes.bbox)
        else:
            print()
    self._view.traceCanvasCosmicPlot2.flush_events()




def _plotCosmicFormat(self, x_range_channel = [50, 2098], x_range = False, y_range = False):
    if self._view.axTopCosmic is None or (self._view.waveDomainCosmic.isChecked() and self._view.axTopCosmic.xaxis.label._text == ''):
        if self._view.axTopCosmic is not None:
            plotCosmicFormatReset(self)
        _x1 = self._view.workspace.wavelength
        _laser = self._view.workspace.laserWavelength
        _ax, self._view.axTopCosmic = generate_plots.formatWavelengthWavenumberCosmic(self._view, _x1, x_range = x_range, y_range = y_range, laser=_laser)
    elif (self._view.ccdDomainCosmic.isChecked() and self._view.axTopCosmic.xaxis.label._text != ''):
        plotCosmicFormatReset(self)
        _x1 = list(range(self._view.workspace.nChannels))
        _ax, self._view.axTopCosmic = generate_plots.formatCCDPixelCosmic(self._view, _x1, x_range = x_range_channel)


def plotCosmicFormatReset(self):
    self._view.axTopCosmic.set_xticks([])
    self._view.axTopCosmic.set_xticklabels([])
    self._view.axTopCosmic.xaxis.set_minor_locator(plt.FixedLocator([]))
    self._view.axTopCosmic.set_xlabel('', fontsize=10)
    try:
        self._view.axTopCosmic.remove()
    except:
        pass


def _rescaleYCosmic1(self):
    generate_plots.autoscale_y(self._view.traceCanvasCosmicPlot1.axes, margin=0.1)
    self._view.traceCanvasCosmicPlot1.draw_idle()

def _rescaleYCosmic2(self):
    generate_plots.autoscale_y(self._view.traceCanvasCosmicPlot2.axes, margin=0.1)
    self._view.traceCanvasCosmicPlot2.draw_idle()
