import numpy as np

def shift_to_wavelength(shift, laser=248.5794):
    wavelength = [(1/((1/laser)-(s/(10**7)))) for s in shift]
    return wavelength

def wavelength_to_shift(wavelength, laser=248.5794):
    wavelength = [(10**7)*((1/laser)-(1/w)) for w in wavelength]
    return wavelength

def channel_from_wavelength(wavelength, wavelength_list):
    channel = np.argmin(np.abs(wavelength-np.array(wavelength_list)))
    return channel

def channels_from_wavelength(wavelength_list, orig_wavelength_list):
    channels = []
    for w in wavelength_list:
        # find channels of original wavelength
        _c_i_low = np.argmin(np.abs(w-np.array(orig_wavelength_list)))
        #_c_i_high = _c_i_low+1
        #if _c_i_high < len(orig_wavelength_list):
            #_wvl_diff = orig_wavelength_list[_c_i_high] - orig_wavelength_list[_c_i_low]
        #else:
            #_wvl_diff = orig_wavelength_list[_c_i_low] - orig_wavelength_list[_c_i_low-1]
        _wvl_diff = orig_wavelength_list[_c_i_low] - orig_wavelength_list[_c_i_low-1]
        channels.append(_c_i_low + (w-orig_wavelength_list[_c_i_low])/_wvl_diff)

    # this list comprehension isn't any faster
    #channels = [np.argmin(np.abs(w-np.array(orig_wavelength_list))) + (w-orig_wavelength_list[np.argmin(np.abs(w-np.array(orig_wavelength_list)))])/(orig_wavelength_list[np.argmin(np.abs(w-np.array(orig_wavelength_list)))] - orig_wavelength_list[np.argmin(np.abs(w-np.array(orig_wavelength_list)))-1]) for w in wavelength_list]
    return channels

def sum_regions(R1, R2, R3):

    # calculate intensity for each point
    # R1 out to channel 565
    # find index closest to channel 565
    _iR1_limit = np.argmin([abs(565-w) for w in _channels])
    _R1 = np.interp(_wavenumbers[0:_iR1_limit], view.workspace.wavenumber, view.workspace.darkSubSpectraR1[view.specProcessingSelected].loc[specIndexList].mean().values)

    # R1 + R2 from 565 to 690
    _iR12_limit = np.argmin([abs(690-w) for w in _channels])
    _R121 = np.interp(_wavenumbers[_iR1_limit:_iR12_limit], view.workspace.wavenumber, view.workspace.darkSubSpectraR1[view.specProcessingSelected].loc[specIndexList].mean().values)
    _R122 = np.interp(_wavenumbers[_iR1_limit:_iR12_limit], view.workspace.wavenumber, view.workspace.darkSubSpectraR2[view.specProcessingSelected].loc[specIndexList].mean().values)
    _R12 = _R121+_R122

    # R2 from 690 to 1663
    _iR2_limit_low = np.argmin([abs(690-w) for w in _channels])
    _iR2_limit_high = np.argmin([abs(1668-w) for w in _channels])
    _R2 = np.interp(_wavenumbers[_iR2_limit_low:_iR2_limit_high], view.workspace.wavenumber, view.workspace.darkSubSpectraR2[view.specProcessingSelected].loc[specIndexList].mean().values)

    # R2 + R3 from 1663 to 1696
    _iR23_limit = np.argmin([abs(1690-w) for w in _channels])
    _R232 = np.interp(_wavenumbers[_iR2_limit_high:_iR23_limit], view.workspace.wavenumber, view.workspace.darkSubSpectraR2[view.specProcessingSelected].loc[specIndexList].mean().values)
    _R233 = np.interp(_wavenumbers[_iR2_limit_high:_iR23_limit], view.workspace.wavenumber, view.workspace.darkSubSpectraR3[view.specProcessingSelected].loc[specIndexList].mean().values)
    _R23 = _R232+_R233

    # R3 from 1696
    _R3 = np.interp(_wavenumbers[_iR23_limit:], view.workspace.wavenumber, view.workspace.darkSubSpectraR3[view.specProcessingSelected].loc[specIndexList].mean().values)

    _asciiDf = pd.DataFrame({'wavelength (nm)': _wavelengths, 'Raman shift (cm-1)': _wavenumbers, 'Intensity': list(_R1)+list(_R12)+list(_R2)+list(_R23)+list(_R3)})
    _asciiDf.to_csv(ascii_filename, index=False)



    return _summed_regions