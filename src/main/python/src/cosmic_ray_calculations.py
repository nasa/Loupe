import os
import math
import numpy as np

from scipy.stats import sigmaclip
from scipy.interpolate import interp1d

from src import log_parsing


def getThreshold(self, intArr, hist_edges):
    # get threshold multiplier
    _threshold = self._view.cosmicRayThreshold.text()
    _sigmaVal = self._view.cosmicRaySigma.text()
    thresholdVal = None
    if _threshold.replace('.', '', 1).isdigit() and _sigmaVal.replace('.', '', 1).isdigit():
        _yOld = intArr
        delta_len = 2
        while delta_len > 1:
            _yNew = sigmaclip(_yOld, float(_sigmaVal), float(_sigmaVal))[0]
            delta_len = len(_yOld) - len(_yNew)
            _yOld = _yNew
        std = _yNew.std()
        meanHist = _yNew.mean()
        threshold_bin_list = np.argwhere(hist_edges < ((float(_threshold) * std) + meanHist))
        if len(threshold_bin_list) > 0:
            thresholdBin = threshold_bin_list[-1][0]
            thresholdVal = hist_edges[thresholdBin]
        else:
            thresholdBin = None
            thresholdVal = None

    return thresholdVal, thresholdBin

def getHist(self, intArr):
    _hist, _edges = np.histogram(intArr, bins='fd')
    _edges = np.insert(_edges, 0, max([0, _edges[0]-(_edges[-1]-_edges[-2])]))
    _edges = np.insert(_edges, len(_edges), _edges[-1]+(_edges[-1]-_edges[-2]))
    _hist = np.insert(_hist, 0, 0)
    _hist = np.insert(_hist, len(_hist), 0)
    return _hist, _edges


#remove cosmic rays by replacing adjacent cosmic ray hits with an average of surrounding values
def CRreplace_avg(self, loc, i, limit, raw_spectra, spectra_index, median=False):
    #limit=7
    avg = 0
    #if loc of cosmic ray is not near edge:
    #if loc < len(self.raw_spectra['shift']) - math.floor(limit / 2) - 1 and loc > math.ceil(limit / 2) - 1:
    if loc < len(raw_spectra) - math.floor(limit / 2) and loc > math.ceil(limit / 2):
        removal_list = list(range(math.ceil(-limit / 2), math.ceil(limit / 2)))
        if loc >= limit and loc <= len(raw_spectra)-limit-1:
            mean_list = list(range(-limit, math.ceil(-limit / 2))) + list(range(math.ceil(limit / 2), limit + 1))
        elif loc < limit:
            mean_list = list(range(-loc, math.ceil(-limit / 2))) + list(range(math.ceil(limit / 2), limit + 1))
        elif loc > len(raw_spectra)-limit-1:
            mean_list = list(range(-limit, math.ceil(-limit / 2))) + list(range(math.ceil(limit / 2), len(raw_spectra)-loc))
    #if loc is near beginning of spectrum:
    elif loc <= math.ceil(limit / 2):
        mean_list = list(range(math.ceil(limit/2), limit+1))
        removal_list = list(range(-loc, math.ceil(limit / 2)))
    #if loc is near end of spectrum:
    elif loc >= len(raw_spectra) - math.ceil(limit / 2):
        mean_list = list(range(-limit, math.ceil(-limit/2)))
        removal_list = list(range(math.ceil(-limit / 2), len(raw_spectra)-loc))
    #calculate mean of points around cosmic ray
    for f in mean_list:
        avg += raw_spectra[loc+f] / len(mean_list)
    if median:
            np.median(mean_list)
    #replace cosmic ray and surrounding points with mean
    for q in removal_list:
        g = int(loc+q)
        raw_spectra[g] = avg
    return raw_spectra

#replace cosmic ray hits by interpolating the remaining points
def CRreplace_interp(self, loc, i, limit, raw_spectra, spectra_index):
    #limit=7
    #if loc of cosmic ray is not near edge:
    if loc < len(raw_spectra) - math.floor(limit/2)-1 and loc > math.ceil(limit/2):
        shift_new = list(range(math.ceil(-limit / 2), math.ceil(limit / 2)))
        if loc >= limit and loc <= len(raw_spectra)-limit-1:
            interp_shift = list(range(-limit, math.ceil(-limit / 2))) + list(range(math.ceil(limit / 2), limit + 1))
        elif loc < limit:
            interp_shift = list(range(-loc, math.ceil(-limit / 2))) + list(range(math.ceil(limit / 2), limit + 1))
        elif loc > len(raw_spectra)-limit-1:
            interp_shift = list(range(-limit, math.ceil(-limit / 2))) + list(range(math.ceil(limit / 2), len(raw_spectra)-loc))
    #if loc is near beginning of spectrum:
    elif loc <= math.ceil(limit / 2):
        interp_shift = [-loc]+list(range(math.ceil(limit/2), limit+1))
        shift_new = list(range(-loc, math.ceil(limit / 2)))
    #if loc is near end of spectrum:
    elif loc >= len(raw_spectra) - math.ceil(limit / 2):
        interp_shift = list(range(-limit, math.ceil(-limit/2)))+[len(raw_spectra)-1-loc]
        shift_new = list(range(math.ceil(-limit / 2), len(raw_spectra)-loc))
    #calculate the new intensity values through the interpolation procedure
    #interp_shift = [item for item in interp_shift if item >= 0]
    loc = np.int64(loc)
    try:
        interp_int = interp1d(interp_shift+loc, raw_spectra[interp_shift+loc], kind='cubic')
        int_new = interp_int(shift_new + loc)
        raw_spectra[shift_new + loc] = int_new
        return raw_spectra
    except:
        log_parsing.log_warning(self.view, 'Failed to fit a cubic interpolation to data points. Falling back to linear interpolation.')
        try:
            interp_int = interp1d(interp_shift+loc, raw_spectra[interp_shift+loc], kind='linear')
            int_new = interp_int(shift_new + loc)
            raw_spectra[shift_new + loc] = int_new
            return raw_spectra
        except:
            log_parsing.log_warning(self.view, 'Failed to interpolate points adjacent to cosmic ray. Fitting mean to adjacent points.')
            raw_spectra = CRreplace_avg(loc, i, limit, raw_spectra, spectra_index)
            return raw_spectra
