import os
import csv
import pandas as pd
import numpy as np
import bitstruct
import cv2
import re
import xml.etree.ElementTree as ET
from PyQt5.QtWidgets import QCheckBox
from PIL import Image
from scipy import interpolate


from src import log_parsing
from src import helper_functions
#from src import parse_rawDPs
from src import roi_class
from src import ACI_WATSON_calc



#######################################
# SETUP
#######################################

def mkdir(dir):
    if not os.path.exists(dir):
        os.mkdir(dir)

def rmFiles(fileList):
    for file in fileList:
        if os.path.exists(file):
            os.remove(file)

def get_working_dir(main_file):
    # determine if file selected is a workspace (SOFF) file
    if '_Loupe_working' in main_file:
        workingDir = os.path.split(main_file)[0]
    else:
        workingSubDir = os.path.split(main_file)[-1].split('.')[0]+'_Loupe_working'
        workingDir = os.path.join(os.path.split(main_file)[0], workingSubDir)
        mkdir(workingDir)
    return workingDir




#######################################
# MAIN PARSING
#######################################

# parse file, generate Loupe working directory, generate SOFF, return SOFF filename
def parseMainFile(view, file, workspace):
    log_parsing.log_info(view, 'Parsing file: '+file)
    # TODO: determine if _soff.xml file exists in working directory, open that instead?
    # determine type of file
    # SOFF
    if file.endswith('_soff.xml'):
        log_parsing.log_info(view, 'SOFF manifest file identified')
        parse_loupe_csv(view, file)
        parse_roi_csv(view)
    # dat/emd
    elif file.endswith('.dat') or file.endswith('.emd'):
        log_parsing.log_info(view, 'rawDP file identified')
        parse_rawDPs.parse_dat_dir(view, workspace, os.path.split(file)[0], file, workspace.azScale, workspace.elScale, workspace.laserCenter, workspace.rotation)
        # write data to working directory, update workspace class with some additional data, and generate SOFF
        view.workspace.initNames(file)

    # CSV (EDR)
    elif (file.endswith('.CSV') or file.endswith('.csv') or file.endswith('.LBL') or file.endswith('.lbl')) and os.path.split(file)[-1][23]=='E':
        log_parsing.log_info(view, 'EDR file identified')
        log_parsing.log_warning(view, 'Not yet implemented')

    # CSV (RDR)
    elif (file.endswith('.CSV') or file.endswith('.csv') or file.endswith('.LBL') or file.endswith('.lbl')) and os.path.split(file)[-1][23]=='R':
        log_parsing.log_info(view, 'RDR file identified')
        log_parsing.log_warning(view, 'Not yet implemented')

    # other (MOBIUS, I&T, ATLO output)
    else:
        log_parsing.log_warning(view, 'Unidentified file type: '+os.path.split(file)[-1])


# read Loupe session file
def parse_loupe_session(view, lpe_file):
    view.loupeSession = pd.read_csv(lpe_file)
    # clean paths, in case session file was generated on different OS
    for i in range(view.loupeSession.shape[0]):
        view.loupeSession['soffPath'][i] = os.path.join(*re.split(r'\|/', view.loupeSession['soffPath'][i]))
    _soff_file0 = os.path.join(*re.split(r'\|/', os.path.split(lpe_file)[0]), view.loupeSession['soffPath'][0])
    return _soff_file0

# read Loupe file
# update selectedWorkspaceCombo, which triggers SOFF read function
# check if spec or position files are in workspace, if not, find csv files and read them (in control class)
def parse_loupe_csv(view, soff_file):
    # loupe.csv file is expected to exist in the same directory as the *_soff.xml file
    view.workspace.SOFFfile = soff_file
    view.workspace.workingDir = os.path.join(os.path.split(soff_file)[0])

    _loupe_file = os.path.join(os.path.split(soff_file)[0], 'loupe.csv')
    _loupe_contents = pd.read_csv(_loupe_file, header=None, index_col=0, squeeze=True)
    _loupe_contents = _loupe_contents.fillna('N/A')
    if 'rotation' not in _loupe_contents:
        _loupe_contents['rotation'] = 20.6793583

    view.workspace.selectedMainFilename = _loupe_contents['original_data_file']
    view.workspace.dictName = _loupe_contents['original_data_file']
    view.workspace.humanReadableName = _loupe_contents['human_readable_workspace']
    view.workspace.laserWavelength = float(_loupe_contents['laser_wavelength'])
    view.workspace.azScale = float(_loupe_contents['az_scale'])
    view.workspace.elScale = float(_loupe_contents['el_scale'])
    view.workspace.laserCenter = (float(_loupe_contents['laser_x']), float(_loupe_contents['laser_y']))
    view.workspace.rotation = float(_loupe_contents['rotation'])
    view.workspace.specProcessingApplied = _loupe_contents['specProcessingApplied']

    # COLLECT_SOH
    view.workspace.CNDH_PCB_TEMP_STAT_REG = [_loupe_contents['CNDH_PCB_TEMP_STAT_REG']]
    view.workspace.CNDH_1_2_V_STAT_REG = [_loupe_contents['CNDH_1_2_V_STAT_REG']]
    view.workspace.CNDH_5_V_DAC_STAT_REG = [_loupe_contents['CNDH_5_V_DAC_STAT_REG']]
    view.workspace.CNDH_3_3_V_STAT_REG = [_loupe_contents['CNDH_3_3_V_STAT_REG']]
    view.workspace.CNDH_5_V_ADC_STAT_REG = [_loupe_contents['CNDH_5_V_ADC_STAT_REG']]
    view.workspace.CNDH_NEG_15_V_STAT_REG = [_loupe_contents['CNDH_NEG_15_V_STAT_REG']]
    view.workspace.CNDH_15_V_STAT_REG = [_loupe_contents['CNDH_15_V_STAT_REG']]
    view.workspace.CNDH_1_5_V_STAT_REG = [_loupe_contents['CNDH_1_5_V_STAT_REG']]
    view.workspace.laser_shot_counter = [_loupe_contents['laser_shot_counter']]
    view.workspace.laser_misfire_counter = [_loupe_contents['laser_misfire_counter']]
    view.workspace.arc_event_counter = [_loupe_contents['arc_event_counter']]
    # SE_COLLECT_SOH
    view.workspace.SE_CCD_ID_STAT_REG = [_loupe_contents['SE_CCD_ID_STAT_REG']]
    view.workspace.SE_CCD_TEMP_STAT_REG = [_loupe_contents['SE_CCD_TEMP_STAT_REG']]
    view.workspace.SE_PCB_TEMP_STAT_REG = [_loupe_contents['SE_PCB_TEMP_STAT_REG']]
    view.workspace.SE_V_1_5_STAT_REG = [_loupe_contents['SE_V_1_5_STAT_REG']]
    view.workspace.SE_LASER_PRT2_STAT_REG = [_loupe_contents['SE_LASER_PRT2_STAT_REG']]
    view.workspace.SE_LASER_PRT1_STAT_REG = [_loupe_contents['SE_LASER_PRT1_STAT_REG']]
    view.workspace.SE_LPS_PRT1_STAT_REG = [_loupe_contents['SE_LPS_PRT1_STAT_REG']]
    view.workspace.SE_TPRB_HOUSING_PRT_STAT_REG = [_loupe_contents['SE_TPRB_HOUSING_PRT_STAT_REG']]
    view.workspace.SE_LPS_PRT2_STAT_REG = [_loupe_contents['SE_LPS_PRT2_STAT_REG']]
    view.workspace.SE_SPARE1_PRT_STAT_REG = [_loupe_contents['SE_SPARE1_PRT_STAT_REG']]
    # CONFIG_CCD_VERT_TIMING
    view.workspace.CCD_VERT_COL1_LOW = [_loupe_contents['CCD_VERT_COL1_LOW']]
    view.workspace.CCD_VERT_COL1_HIGH = [_loupe_contents['CCD_VERT_COL1_HIGH']]
    view.workspace.CCD_VERT_COL2_LOW = [_loupe_contents['CCD_VERT_COL2_LOW']]
    view.workspace.CCD_VERT_COL2_HIGH = [_loupe_contents['CCD_VERT_COL2_HIGH']]
    view.workspace.CCD_VERT_COL3_LOW = [_loupe_contents['CCD_VERT_COL3_LOW']]
    view.workspace.CCD_VERT_COL3_HIGH = [_loupe_contents['CCD_VERT_COL3_HIGH']]
    # CONFIG_CCD_HORZ_TIMING
    view.workspace.CCD_HORZ_CLOCK_LIM = [_loupe_contents['CCD_HORZ_CLOCK_LIM']]
    view.workspace.CCD_HORZ_R1_CLOCK_HIGH = [_loupe_contents['CCD_HORZ_R1_CLOCK_HIGH']]
    view.workspace.CCD_HORZ_R1_CLOCK_Low = [_loupe_contents['CCD_HORZ_R1_CLOCK_Low']]
    view.workspace.CCD_HORZ_R2_CLOCK_HIGH = [_loupe_contents['CCD_HORZ_R2_CLOCK_HIGH']]
    view.workspace.CCD_HORZ_R2_CLOCK_Low = [_loupe_contents['CCD_HORZ_R2_CLOCK_Low']]
    view.workspace.CCD_HORZ_R3_CLOCK_HIGH = [_loupe_contents['CCD_HORZ_R3_CLOCK_HIGH']]
    view.workspace.CCD_HORZ_R3_CLOCK_Low = [_loupe_contents['CCD_HORZ_R3_CLOCK_Low']]
    # CONFIG_CCD_REGIONS
    view.workspace.CCD_GAIN_2D = [_loupe_contents['CCD_GAIN_2D']]
    view.workspace.MODE_2D = [_loupe_contents['MODE_2D']]
    view.workspace.REGION_ENABLE = [_loupe_contents['REGION_ENABLE']]
    view.workspace.HORZ_ENABLE = [_loupe_contents['HORZ_ENABLE']]
    view.workspace.GAIN_ENABLE = [_loupe_contents['GAIN_ENABLE']]
    view.workspace.SKIP_1 = [_loupe_contents['SKIP_1']]
    view.workspace.SUM_1 = [_loupe_contents['SUM_1']]
    view.workspace.SKIP_2 = [_loupe_contents['SKIP_2']]
    view.workspace.SUM_2 = [_loupe_contents['SUM_2']]
    view.workspace.SKIP_3 = [_loupe_contents['SKIP_3']]
    view.workspace.SUM_3 = [_loupe_contents['SUM_3']]
    view.workspace.SKIP_4 = [_loupe_contents['SKIP_4']]
    view.workspace.SUM_4 = [_loupe_contents['SUM_4']]
    view.workspace.SKIP_5 = [_loupe_contents['SKIP_5']]
    view.workspace.SUM_5 = [_loupe_contents['SUM_5']]
    view.workspace.LAST_SKIP = [_loupe_contents['LAST_SKIP']]
    # CONFI_LASER_TIMING
    view.workspace.LASER_INT_TIME = [_loupe_contents['LASER_INT_TIME']]
    view.workspace.LASER_REP_RATE = [_loupe_contents['LASER_REP_RATE']]
    view.workspace.LASER_ON_TIME = [_loupe_contents['LASER_ON_TIME']]
    view.workspace.PULSE_WIDTH = [_loupe_contents['PULSE_WIDTH']]
    view.workspace.LASER_CURRENT = [_loupe_contents['LASER_CURRENT']]
    view.workspace.LASER_SHOTS = [_loupe_contents['LASER_SHOTS']]


    #workspace.addWorkspaceItemCombo(view)


# read ROI file
def parse_roi_csv(view):
    # roi.csv file is expected to exist in the same directory as the *_soff.xml file
    _roi_file = os.path.join(view.workspace.workingDir, 'roi.csv')
    # read each ROI section, add Full Map to main roi, add other rois to roiDict
    with open(_roi_file, 'r') as f:
        _contents = f.read()

    # first ROI is the Full Map
    _roi_name = _contents.split('\n')[0]
    _roi_lines = len(_contents.split('ENDROI\n')[0].split('ENDROI\n')[0].split('\n'))-1
    _roi_color = _contents.split('\n')[1].split('\n')[-1]
    _roi_spec_index = pd.read_csv(_roi_file, header=None, skiprows = 2, nrows = _roi_lines-2, index_col=None, squeeze=True)
    #view.roi.defineFull(_roi_name, view.workspace, list(_roi_spec_index.values))
    _roi = roi_class.roiClass()
    _roi.humanReadableName = _roi_name
    _roi.color = _roi_color
    _roi.dictName = view.workspace.dictName+'_'+_roi_name
    _roi.checkboxWidget = QCheckBox(_roi_name)
    _roi.checkboxWidgetRoi = QCheckBox(_roi_name)
    _roi.checkboxWidgetCosmic = QCheckBox(_roi_name)
    _roi.specIndexList = list(_roi_spec_index.values)
    view.workspace.roiNames = [_roi_name]
    view.roiDict[_roi.dictName] = _roi
    view.workspace.roiHumanToDictKey[_roi.humanReadableName] = _roi.dictName
    view.roi = _roi

    for _roi_index in range(_contents.count('ENDROI')-1):
        _roi_name = _contents.split('ENDROI\n')[_roi_index+1].split('\n')[0]
        if _roi_name != '':
            _roi_color = _contents.split('ENDROI\n')[_roi_index+1].split('\n')[1].split('\n')[-1]
            _roi_skip = len(''.join(_contents.split('ENDROI\n')[0:_roi_index+1]).split('\n'))+len(_contents.split('ENDROI\n')[0:_roi_index+1])+1
            _roi_lines = len(_contents.split('ENDROI\n')[_roi_index+1].split('ENDROI\n')[0].split('\n'))-2
            _roi_spec_index = pd.read_csv(_roi_file, header=None, skiprows = _roi_skip, nrows = _roi_lines-1, index_col=None, squeeze=True)
            _roi = roi_class.roiClass()
            _roi.humanReadableName = _roi_name
            _roi.color = _roi_color
            _roi.dictName = view.workspace.dictName+'_'+_roi_name
            _roi.checkboxWidget = QCheckBox(_roi_name)
            _roi.checkboxWidgetRoi = QCheckBox(_roi_name)
            _roi.checkboxWidgetCosmic = QCheckBox(_roi_name)
            _roi.specIndexList = list(_roi_spec_index.values)
            view.workspace.roiNames.append(_roi_name)
            view.roiDict[_roi.dictName] = _roi
            view.workspace.roiHumanToDictKey[_roi.humanReadableName] = _roi.dictName


# image parsing

def parseImgFile(view, file, workspace):
    log_parsing.log_info(view, 'Parsing file: '+file)
    _pngFile = os.path.join(workspace.workingDir, 'img', os.path.split(file)[-1].split('.')[0]+'.PNG')
    _csvFile = os.path.join(workspace.workingDir, 'img', os.path.split(file)[-1].split('.')[0]+'.CSV')

    if file.endswith('IMG'):
        vic_file, odl_contents = vic_from_img(os.path.split(file)[0], file)
        im_arr = im_arr_from_vicar(vic_file)
        odl_contents = odl_contents.decode('utf-8')
    elif file.endswith('PNG') or file.endswith('png'):
        if os.path.split(file)[-1][0:2] == 'SC':
            im_arr = im_arr_from_ACI_png(file)
        else:
            im_arr = im_arr_from_WATSON_png(file)
        # TODO: need LBL files to test this with
        lbl_file = file.split('.')[0]+'.LBL'
        if os.path.exists(lbl_file):
            with open(lbl_file, 'r') as file_handle:
                odl_contents = file_handle.read()
        else:
            odl_contents = ''

    _PID = os.path.split(file)[-1][23:26]
    _LED = os.path.split(file)[-1][2]
    if odl_contents != '':
        if 'FOCUS_POSITION_COUNT=' in odl_contents:
            _motor = int(odl_contents.split('FOCUS_POSITION_COUNT=')[1].split(' ')[0])
            _CDPID = int(odl_contents.split('IMAGE_ID=')[1].split(' ')[0].strip('\''))
            _expTime = float(odl_contents.split('EXPOSURE_DURATION=')[1].split(' ')[0])
        else:
            _motor = int(odl_contents.split('FOCUS_POSITION_COUNT            = ')[1].split(' ')[0])
            _CDPID = int(odl_contents.split('IMAGE_ID                         = ')[1].split('\r\n')[0].strip('\'').strip('\"'))
            _expTime = float(odl_contents.split('EXPOSURE_DURATION               = ')[1].split(' ')[0])
        if os.path.split(file)[-1][0:2] == 'SC':
            _range = round(ACI_WATSON_calc.working_distance_ACI(_motor), 2)
            _pixelScale = 10.1
        else:
            _range = round(ACI_WATSON_calc.working_distance_WATSON(_motor), 2)
            _pixelScale = round(ACI_WATSON_calc.working_distance_WATSON(_motor, tb=False), 2)
    elif os.path.exists(_csvFile):
        _attributes = pd.read_csv(_csvFile, header=None, index_col=0)
        _motor = _attributes.loc['motor_pos'].values[0]
        _CDPID = _attributes.loc['CDPID'].values[0]
        _expTime = _attributes.loc['exp_time'].values[0]
        _pixelScale = _attributes.loc['pixel_scale'].values[0]
        _range = _attributes.loc['range'].values[0]
    else:
        _motor = 'N/A'
        _CDPID = 'N/A'
        _expTime = 'N/A'
        if os.path.split(file)[-1][0:2] == 'SC':
            _pixelScale = '10.1'
            _range = '~48'
        else:
            _pixelScale = 'N/A'
            _range = 'N/A'

    view.workspace.ACIAttributes = {'pixelScale': _pixelScale,
                                    'range': _range,
                                    'CDPID': _CDPID,
                                    'motor_pos': _motor,
                                    'exp_time': _expTime,
                                    'product_ID': _PID,
                                    'led_flag': _LED}

    if os.path.split(file)[-1] not in workspace.aciNames:
        workspace.aciNames.append(os.path.split(file)[-1])
        # convert to PNG for easier access next time
        if not os.path.exists(_pngFile):
            writeImgCsv(_csvFile, view)
            if os.path.split(file)[-1][0:2] == 'SC':
                color_mode = False
                addSOFFFAOCsv(workspace, _csvFile, 'ACIAttributes', file_name = os.path.join(os.path.split(os.path.split(_csvFile)[0])[-1], os.path.split(_csvFile)[-1]))
            else:
                color_mode = True
                addSOFFFAOCsv(workspace, _csvFile, 'WATSONAttributes', file_name = os.path.join(os.path.split(os.path.split(_csvFile)[0])[-1], os.path.split(_csvFile)[-1]))
            im_arr_to_png(im_arr, _pngFile, color_mode = color_mode, fod_removal=False)
            addSOFFFAOSupplementalImg(workspace, _pngFile)

    return im_arr, _pngFile


def vic_from_img(output_dir, input_img):
    # vicar2png(input_vicar, output_png)
    with open(input_img, 'rb') as file_handle:
        file_contents = file_handle.read()

    parts = file_contents.split('LBLSIZE'.encode('utf-8'))

    # save VICAR label
    vic_file_name = os.path.join(output_dir, os.path.split(input_img)[-1])
    if os.path.exists(vic_file_name):
        os.remove(vic_file_name)
    write_to_file(vic_file_name, 'LBLSIZE'.encode('utf-8')+parts[1], mode='wb')

    if parts[0] == b'':
        lbl_len = int(parts[1].split(b'=')[1].split(b' ')[0])
        odl_contents = parts[1][0:lbl_len]
    else:
        odl_contents = parts[0]

    # file name and ODL label
    return vic_file_name, odl_contents

# functions adapted from https://github.com/jesstess/vicar2png/blob/master/bin/vicar2png
def im_arr_from_vicar(input_vicar):
    # vicar2png(input_vicar, output_png)
    file_handle_in = open(input_vicar, 'rb')
    vicar_metadata = process_vicar_metadata(file_handle_in)
    im_arr = extract_vicar_image(vicar_metadata, file_handle_in)
    file_handle_in.close()
    return im_arr

class VICARMetadata(object):
    def __init__(self, metadata):
        for key, value in metadata.items():
            if value.isdigit():
                value = int(value)
            setattr(self, key.upper(), value)

def process_vicar_metadata(file_h):
    lblsize_key = file_h.read(len('LBLSIZE='))
    lblsize = ''
    while True:
        char = file_h.read(1).decode('ascii')
        if char == ' ':
            break
        else:
            lblsize += char

    file_h.seek(0)
    metadata = file_h.read(int(lblsize))

    metadata_dict = {}
    has_lquote = False
    has_lparen = False
    tag_buf = ""
    for char in metadata.decode('ascii'):
        if char == "'":
            if has_lquote and not has_lparen:
                # We have a full string tag, save it.
                tag, value = tag_buf.split("=",1)
                metadata_dict[tag] = value

                has_lquote = has_lparen = False
                tag_buf = ""
            else:
                has_lquote = True
        elif char == "(":
            has_lparen = True
            tag_buf += char
        elif char == ")":
            # We have a full parenthesized tag, save it.
            tag, value = tag_buf.split("=")
            metadata_dict[tag] = value

            has_lquote = has_lparen = False
            tag_buf = ""
        elif char == " " and tag_buf and not (has_lquote or has_lparen):
            # We have a full integer or real tag, save it.
            tag, value = tag_buf.split("=")
            metadata_dict[tag] = value

            has_lquote = has_lparen = False
            tag_buf = ""
        elif char == " ":
            continue
        else:
            tag_buf += char

    return VICARMetadata(metadata_dict)

def extract_vicar_image(metadata, file_h):
    file_h.seek(metadata.LBLSIZE + metadata.NLB * metadata.RECSIZE)
    #num_records = metadata.N2*metadata.N3
    num_records = metadata.N2#*metadata.N3
    num_bands = metadata.N3
    pixels = []
    if metadata.FORMAT == 'BYTE':
        format=1
    elif metadata.FORMAT == 'HALF':
        format = 2
    elif metadata.FORMAT == 'FULL':
        format = 4

    im_array = np.zeros([num_records, metadata.N1, num_bands])
    # Skip prefix.
    file_h.read(metadata.NBB)
    for j in range(num_bands):
        for i in range(num_records):
            pixel_data = file_h.read(metadata.N1 * format)
            if metadata.FORMAT == 'BYTE':
                im_array[i, :, j] = list(bitstruct.unpack('>u8'*metadata.N1, pixel_data))
            else:
                pixel_row = list(bitstruct.unpack('>u16'*metadata.N1, pixel_data))
                # For now we just handle BYTE and HALF.
                im_array[i, :, j] = pixel_row

    return im_array

def unsign(signed_data):
    return signed_data * 32768*2/4096.0


def write_to_file(file_name, contents, mode='w'):
    file_handle = open(file_name, mode)
    file_handle.write(contents)
    file_handle.close()


def im_arr_from_ACI_png(file):
    with Image.open(file) as image:
        image_array = np.fromstring(image.tobytes(), dtype=np.uint8)
        try:
            image_array = image_array.reshape((image.size[1], image.size[0]))
        except ValueError:
            image_array = image_array.reshape((image.size[1], image.size[0], 3))
            # ACI images should not be multi-band, but for some reason, they are
            image_array = image_array[:,:,0]
    return image_array

def im_arr_from_WATSON_png(file):
    with Image.open(file) as image:
        image_array = np.fromstring(image.tobytes(), dtype=np.uint8)
        image_array = image_array.reshape((image.size[1], image.size[0], 3))
    return image_array


def im_arr_to_png(im_arr, output_file, color_mode = False, fod_removal=False):
    if color_mode:
        if im_arr.shape[2]==1:
            color = cv2.cvtColor(im_arr.astype('u1'), cv2.COLOR_BAYER_BG2BGR)
        else:
            if im_arr.max() > 255:
                #color = cv2.cvtColor(im_arr.astype(np.uint16), cv2.COLOR_RGB2BGR)
                color = cv2.cvtColor((255*(im_arr/im_arr.max())).astype(np.uint8), cv2.COLOR_RGB2BGR)
            else:
                color = cv2.cvtColor(im_arr.astype('u1'), cv2.COLOR_RGB2BGR)
        if fod_removal and im_arr.shape[0] == 1200 and im_arr.shape[1] == 1648:
            print('Removing FOD using interpolation')
            # get removal mask
            fod_mask = im_arr_from_ACI_png(fod_removal)
            fod_mask = np.rot90(fod_mask)
            mask = np.ma.masked_greater(fod_mask, 254)
            for color_i in range(3):
                array = np.ma.array(color[:,:,color_i], mask=mask.mask)
                """
                for i in range(im_arr.shape[0]):
                    for j in range(im_arr.shape[1]):
                        if mask[i,j]:
                            array[i,j] = 0#np.nan
                """
                # interpolate points around mask=255 points
                x = np.arange(0, im_arr.shape[1])
                y = np.arange(0, im_arr.shape[0])
                xx, yy = np.meshgrid(x, y)
                x1 = xx[~mask.mask]
                y1 = yy[~mask.mask]
                #new_arr = im_arr[~mask.mask]
                new_arr = array[~array.mask]

                color_arr =  interpolate.griddata((x1, y1), new_arr.ravel(), (xx, yy), method='nearest')
                #color_arr = np.expand_dims(color_arr, axis=2)
                color[:,:,color_i] = color_arr

        cv2.imwrite(output_file, color)
    else:
        if len(im_arr.shape)>2 and im_arr.shape[2]>1:
            cv2.imwrite(output_file, im_arr[:,:,0])
        else:
            cv2.imwrite(output_file, im_arr)




#######################################
# WRITE FILES
#######################################

def writeSpectraRegions(save_file, view, R1, R2, R3):
    if os.path.exists(save_file):
        log_parsing.log_info(view, 'Overwriting existing {0} file'.format(save_file))
        os.remove(save_file)
    R1.to_csv(save_file, header=True, index=False, float_format='%.3f', line_terminator='\r\n')
    R2.to_csv(save_file, mode='a', header=True, index=False, float_format='%.3f', line_terminator='\r\n')
    R3.to_csv(save_file, mode='a', header=True, index=False, float_format='%.3f', line_terminator='\r\n')


def writePandasArr(save_file, view, arr):
    if os.path.exists(save_file):
        log_parsing.log_info(view, 'Overwriting existing {0} file'.format(save_file))
        os.remove(save_file)
    arr.to_csv(save_file, header=True, index=False, float_format='%.3f', line_terminator='\r\n')

def writeTable(save_file, view, scannerTable, scannerTableCommanded, xyTable, xyTableCommanded, scannerTableErr, scannerCurrent):
    if os.path.exists(save_file):
        log_parsing.log_info(view, 'Overwriting existing {0} file'.format(save_file))
        os.remove(save_file)
    scannerTable.to_csv(save_file, header=True, index=False, float_format='%.3f', line_terminator='\r\n')
    if scannerTableCommanded is not None:
        scannerTableCommanded.to_csv(save_file, mode='a', header=True, index=False, float_format='%.3f', line_terminator='\r\n')
    if xyTable is not None:
        xyTable.to_csv(save_file, mode='a', header=True, index=False, float_format='%.3f', line_terminator='\r\n')
    if xyTableCommanded is not None:
        xyTableCommanded.to_csv(save_file, mode='a', header=True, index=False, float_format='%.3f', line_terminator='\r\n')
    scannerTableErr.to_csv(save_file, mode='a', header=True, index=False, float_format='%.3f', line_terminator='\r\n')
    scannerCurrent.to_csv(save_file, mode='a', header=True, index=False, float_format='%.3f', line_terminator='\r\n')


def writeLoupeSession(save_file, view):
    if os.path.exists(save_file):
        log_parsing.log_info(view, 'Overwriting existing {0} file'.format(save_file))
        os.remove(save_file)
    _loupePath = os.path.split(save_file)[0]
    with open(save_file, 'w') as f:
        writer = csv.writer(f, delimiter=',', lineterminator='\n')
        writer.writerow(('workspaceDictName', 'workspaceHumanReadableName', 'soffPath'))
        for _humanName, _dictName in view.workspaceHumanToDictKey.items():
            _fullWorkspaceDir = view.workspaceDict[_dictName].SOFFfile
            _relWorkspaceDir = os.path.relpath(_fullWorkspaceDir, _loupePath)
            writer.writerow((_dictName, _humanName, _relWorkspaceDir))


def writeLoupeCsv(save_file, view):
    if os.path.exists(save_file):
        log_parsing.log_info(view, 'Overwriting existing {0} file'.format(save_file))
        os.remove(save_file)
    with open(save_file, 'w') as f:
        writer = csv.writer(f, delimiter=',', lineterminator='\n')
        writer.writerow(('original_data_file', view.workspace.selectedMainFilename))
        writer.writerow(('human_readable_workspace', view.workspace.humanReadableName))
        writer.writerow(('n_spectra', view.workspace.nSpectra))
        writer.writerow(('n_channels', view.workspace.nChannels))
        writer.writerow(('laser_wavelength', view.workspace.laserWavelength))
        writer.writerow(('shots_per_spec', view.workspace.nShots))
        writer.writerow(('az_scale', view.workspace.azScale))
        writer.writerow(('el_scale', view.workspace.elScale))
        writer.writerow(('laser_x', view.workspace.laserCenter[0]))
        writer.writerow(('laser_y', view.workspace.laserCenter[1]))
        writer.writerow(('rotation', view.workspace.rotation))
        writer.writerow(('specProcessingApplied', view.workspace.specProcessingApplied))
        # COLLECT_SOH
        writer.writerow(('CNDH_PCB_TEMP_STAT_REG', view.workspace.CNDH_PCB_TEMP_STAT_REG[-1]))
        writer.writerow(('CNDH_1_2_V_STAT_REG', view.workspace.CNDH_1_2_V_STAT_REG[-1]))
        writer.writerow(('CNDH_5_V_DAC_STAT_REG', view.workspace.CNDH_5_V_DAC_STAT_REG[-1]))
        writer.writerow(('CNDH_3_3_V_STAT_REG', view.workspace.CNDH_3_3_V_STAT_REG[-1]))
        writer.writerow(('CNDH_5_V_ADC_STAT_REG', view.workspace.CNDH_5_V_ADC_STAT_REG[-1]))
        writer.writerow(('CNDH_NEG_15_V_STAT_REG', view.workspace.CNDH_NEG_15_V_STAT_REG[-1]))
        writer.writerow(('CNDH_15_V_STAT_REG', view.workspace.CNDH_15_V_STAT_REG[-1]))
        writer.writerow(('CNDH_1_5_V_STAT_REG', view.workspace.CNDH_1_5_V_STAT_REG[-1]))
        writer.writerow(('laser_shot_counter', view.workspace.laser_shot_counter[-1]))
        writer.writerow(('laser_misfire_counter', view.workspace.laser_misfire_counter[-1]))
        writer.writerow(('arc_event_counter', view.workspace.arc_event_counter[-1]))
        # SE_COLLECT_SOH
        writer.writerow(('SE_CCD_ID_STAT_REG', view.workspace.SE_CCD_ID_STAT_REG[-1]))
        writer.writerow(('SE_CCD_TEMP_STAT_REG', view.workspace.SE_CCD_TEMP_STAT_REG[-1]))
        writer.writerow(('SE_PCB_TEMP_STAT_REG', view.workspace.SE_PCB_TEMP_STAT_REG[-1]))
        writer.writerow(('SE_V_1_5_STAT_REG', view.workspace.SE_V_1_5_STAT_REG[-1]))
        writer.writerow(('SE_LASER_PRT2_STAT_REG', view.workspace.SE_LASER_PRT2_STAT_REG[-1]))
        writer.writerow(('SE_LASER_PRT1_STAT_REG', view.workspace.SE_LASER_PRT1_STAT_REG[-1]))
        writer.writerow(('SE_LPS_PRT1_STAT_REG', view.workspace.SE_LPS_PRT1_STAT_REG[-1]))
        writer.writerow(('SE_TPRB_HOUSING_PRT_STAT_REG', view.workspace.SE_TPRB_HOUSING_PRT_STAT_REG[-1]))
        writer.writerow(('SE_LPS_PRT2_STAT_REG', view.workspace.SE_LPS_PRT2_STAT_REG[-1]))
        writer.writerow(('SE_SPARE1_PRT_STAT_REG', view.workspace.SE_SPARE1_PRT_STAT_REG[-1]))
        # CONFIG_CCD_VERT_TIMING
        writer.writerow(('CCD_VERT_COL1_LOW', view.workspace.CCD_VERT_COL1_LOW[-1]))
        writer.writerow(('CCD_VERT_COL1_HIGH', view.workspace.CCD_VERT_COL1_HIGH[-1]))
        writer.writerow(('CCD_VERT_COL2_LOW', view.workspace.CCD_VERT_COL2_LOW[-1]))
        writer.writerow(('CCD_VERT_COL2_HIGH', view.workspace.CCD_VERT_COL2_HIGH[-1]))
        writer.writerow(('CCD_VERT_COL3_LOW', view.workspace.CCD_VERT_COL3_LOW[-1]))
        writer.writerow(('CCD_VERT_COL3_HIGH', view.workspace.CCD_VERT_COL3_HIGH[-1]))
        # CONFIG_CCD_HORZ_TIMING
        writer.writerow(('CCD_HORZ_CLOCK_LIM', view.workspace.CCD_HORZ_CLOCK_LIM[-1]))
        writer.writerow(('CCD_HORZ_R1_CLOCK_HIGH', view.workspace.CCD_HORZ_R1_CLOCK_HIGH[-1]))
        writer.writerow(('CCD_HORZ_R1_CLOCK_Low', view.workspace.CCD_HORZ_R1_CLOCK_Low[-1]))
        writer.writerow(('CCD_HORZ_R2_CLOCK_HIGH', view.workspace.CCD_HORZ_R2_CLOCK_HIGH[-1]))
        writer.writerow(('CCD_HORZ_R2_CLOCK_Low', view.workspace.CCD_HORZ_R2_CLOCK_Low[-1]))
        writer.writerow(('CCD_HORZ_R3_CLOCK_HIGH', view.workspace.CCD_HORZ_R3_CLOCK_HIGH[-1]))
        writer.writerow(('CCD_HORZ_R3_CLOCK_Low', view.workspace.CCD_HORZ_R3_CLOCK_Low[-1]))
        # CONFIG_CCD_REGIONS
        writer.writerow(('CCD_GAIN_2D', view.workspace.CCD_GAIN_2D[-1]))
        writer.writerow(('MODE_2D', view.workspace.MODE_2D[-1]))
        writer.writerow(('REGION_ENABLE', view.workspace.REGION_ENABLE[-1]))
        writer.writerow(('HORZ_ENABLE', view.workspace.HORZ_ENABLE[-1]))
        writer.writerow(('GAIN_ENABLE', view.workspace.GAIN_ENABLE[-1]))
        writer.writerow(('SKIP_1', view.workspace.SKIP_1[-1]))
        writer.writerow(('SUM_1', view.workspace.SUM_1[-1]))
        writer.writerow(('SKIP_2', view.workspace.SKIP_2[-1]))
        writer.writerow(('SUM_2', view.workspace.SUM_2[-1]))
        writer.writerow(('SKIP_3', view.workspace.SKIP_3[-1]))
        writer.writerow(('SUM_3', view.workspace.SUM_3[-1]))
        writer.writerow(('SKIP_4', view.workspace.SKIP_4[-1]))
        writer.writerow(('SUM_4', view.workspace.SUM_4[-1]))
        writer.writerow(('SKIP_5', view.workspace.SKIP_5[-1]))
        writer.writerow(('SUM_5', view.workspace.SUM_5[-1]))
        writer.writerow(('LAST_SKIP', view.workspace.LAST_SKIP[-1]))
        # CONFIG_LASER_TIMING
        try:
            writer.writerow(('LASER_INT_TIME', view.workspace.LASER_INT_TIME[-1]))
        except:
            writer.writerow(('LASER_INT_TIME', view.workspace.LASER_INT_TIME[-1].split(' ')[0]))
        writer.writerow(('LASER_REP_RATE', view.workspace.LASER_REP_RATE[-1]))
        writer.writerow(('LASER_ON_TIME', view.workspace.LASER_ON_TIME[-1]))
        try:
            writer.writerow(('PULSE_WIDTH', view.workspace.PULSE_WIDTH[-1]))
        except:
            writer.writerow(('PULSE_WIDTH', view.workspace.PULSE_WIDTH[-1].split(' ')[0]))
        writer.writerow(('LASER_CURRENT', view.workspace.LASER_CURRENT[-1]))
        writer.writerow(('LASER_SHOTS', view.workspace.LASER_SHOTS[-1]))


def writeRoiCsv(save_file, view):
    if os.path.exists(save_file):
        log_parsing.log_info(view, 'Overwriting existing {0} file'.format(save_file))
        os.remove(save_file)
    if len(view.workspace.roiNames) == 0:
        with open(save_file, 'w') as f:
            writer = csv.writer(f, delimiter=',', lineterminator='\n')
            writer.writerow((['Full Map']))
            writer.writerow((['#ffffff']))
            for i in range(view.workspace.nSpectra):
                writer.writerow(([str(i)]))
            writer.writerow((['ENDROI']))
    else:
        with open(save_file, 'w') as f:
            writer = csv.writer(f, delimiter=',', lineterminator='\n')
            for _roiName in view.workspace.roiNames:
                _roiKey = view.workspace.roiHumanToDictKey[_roiName]
                writer.writerow(([_roiName]))
                writer.writerow(([view.roiDict[_roiKey].color]))
                for i in view.roiDict[_roiKey].specIndexList:
                    writer.writerow(([str(i)]))
                writer.writerow((['ENDROI']))


def exportRoiBundle(roiName, specIndexList, view):
    # define export directory
    _roiDirRoot = os.path.join(view.workspace.workingDir, 'ROI')
    if not os.path.exists(_roiDirRoot):
        os.mkdir(_roiDirRoot)
    _roiDir = os.path.join(_roiDirRoot, roiName)
    if not os.path.exists(_roiDir):
        os.mkdir(_roiDir)
    # save current image with annotations
    view.pixmapACI.save(os.path.join(_roiDir, roiName+'_ACI_overlay.png'))

    # save CSV for each region (using currently selected processing - include processing in file name)
    proc_str = 'ZZZ'
    if view.specProcessingSelected != 'None':
        if 'N' in view.specProcessingSelected:
            proc_str = proc_str[0] + 'N' + proc_str[2]
        if 'C' in view.specProcessingSelected:
            proc_str = 'C' + proc_str[1] + proc_str[2]
        if 'B' in view.specProcessingSelected:
            proc_str = proc_str[0] + proc_str[1] + 'B'

    csv_file_root = os.path.join(_roiDir, roiName+'_spectra_'+proc_str+'_R')
    for region, darksub_spec in enumerate([view.workspace.darkSubSpectraR1[view.specProcessingSelected], view.workspace.darkSubSpectraR2[view.specProcessingSelected], view.workspace.darkSubSpectraR3[view.specProcessingSelected]]):
        # pixel channel
        dfR = pd.DataFrame([np.array(range(view.workspace.nChannels))])
        # wavelength channel
        dfR = dfR.append(pd.DataFrame([view.workspace.wavelength]).round(decimals=2))
        dfR = dfR.append(pd.DataFrame([view.workspace.wavenumber]).round(decimals=2))
        dfR = dfR.append(pd.DataFrame(darksub_spec.loc[specIndexList].values))
        # transpose data
        dfR = dfR.T
        dfR.columns = ['CCD pixel', 'wavelength (nm)', 'Raman shift (cm-1)']+['Point '+str(i) for i in specIndexList]
        dfR.to_csv(csv_file_root+str(region+1)+'.csv', index=False)

    if view.asciiExportRoi.isChecked():
        log_parsing.log_info(view, 'Exporting Raman data in ASCII-format')
        ascii_filename = csv_file_root[:-2]+'.txt'
        _wavenumber_spacing = view.asciiExportSpacing.text()
        if not _wavenumber_spacing.replace('.', '').isdigit():
            _wavenumber_spacing = 0.1
        else:
            _wavenumber_spacing = float(_wavenumber_spacing)
        _wavenumbers = list(np.arange(0, int(view.workspace.wavenumber[-1]), _wavenumber_spacing))
        _wavelengths = helper_functions.shift_to_wavelength(_wavenumbers)
        _channels = np.interp(_wavelengths, view.workspace.wavelength, list(range(len(view.workspace.wavelength))))
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


        """
        # R1 out to 4000 cm-1
        # find index closest to 4000 cm-1
        _iR1_limit = np.argmin([abs(4000-w) for w in _wavenumbers])
        _R1 = np.interp(_wavenumbers[0:_iR1_limit], view.workspace.wavenumber, view.workspace.darkSubSpectraR1[view.specProcessingSelected].loc[specIndexList].mean().values)
        # R2 + R3 from 4000 cm-1
        _R23 = np.interp(_wavenumbers[_iR1_limit:], view.workspace.wavenumber, view.workspace.darkSubSpectraR2[view.specProcessingSelected].loc[specIndexList].mean().values+view.workspace.darkSubSpectraR3[view.specProcessingSelected].loc[specIndexList].mean().values)
        _asciiDf = pd.DataFrame({'wavelength (nm)': _wavelengths, 'Raman shift (cm-1)': _wavenumbers, 'Intensity': list(_R1)+list(_R23)})
        _asciiDf.to_csv(ascii_filename, index=False)
        """

def writeImgCsv(save_file, view):
    if os.path.exists(save_file):
        log_parsing.log_info(view, 'Overwriting existing {0} file'.format(save_file))
        os.remove(save_file)
    with open(save_file, 'w') as f:
        writer = csv.writer(f, delimiter=',', lineterminator='\n')
        writer.writerow(('pixel_scale', view.workspace.ACIAttributes['pixelScale']))
        writer.writerow(('range', view.workspace.ACIAttributes['range']))
        writer.writerow(('CDPID', view.workspace.ACIAttributes['CDPID']))
        writer.writerow(('motor_pos', view.workspace.ACIAttributes['motor_pos']))
        writer.writerow(('exp_time', view.workspace.ACIAttributes['exp_time']))
        writer.writerow(('product_ID', view.workspace.ACIAttributes['product_ID']))
        writer.writerow(('led_flag', view.workspace.ACIAttributes['led_flag']))




#######################################
# SUPPORT FUNCTIONS
#######################################

# this function will retrieve the correct offset if the contents of spreadsheet_dfs is the same as the table structure in the RDR file
def get_offset(output_file, df):
    # get byte offset
    with open (output_file, 'rb') as f:
        data=f.readlines()
    data_string = b''.join(data)
    target = bytes(df.columns[-1], 'utf-8')+b'\r\n'
    byte_offset = data_string.find(target)
    offset = byte_offset+len(target)
    return offset



#######################################
# XML Parsing
#######################################

def XMLindent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            XMLindent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

# write initial SOFF file
def writeSOFF(workspace, soff_xml_text):
    ET.register_namespace('', "http://pds.nasa.gov/pds4/pds/v1")
    # read header information
    # TODO: eventually, replace this with programatically generated text
    with open(soff_xml_text, 'r') as f:
        _soffHeader = f.read()
    _soffFooter = '</Product_Observational>'

    #####################
    # Product Observational
    #####################

    _product_obs = ET.Element('Product_Observational')
    _product_obs.set('xmlns', 'http://pds.nasa.gov/pds4/pds/v1')

    _id_area = ET.SubElement(_product_obs, 'Identification_Area')
    _id_area_lid = ET.SubElement(_id_area, 'logical_identifier')
    _id_area_lid.text = 'test_id'
    _id_area_versionID = ET.SubElement(_id_area, 'version_id')
    _id_area_versionID.text = '1.0'
    _id_area_title = ET.SubElement(_id_area, 'title')
    _id_area_title.text = 'this is a test'
    _id_area_IM_version = ET.SubElement(_id_area, 'information_model_version')
    _id_area_IM_version.text = '1.11.1.0'
    _id_area_product_class = ET.SubElement(_id_area, 'product_class')
    _id_area_product_class.text = 'Product_Observational'

    _soffStringIdArea = ET.tostring(_product_obs).decode('utf-8')
    _soffString = _soffStringIdArea.split(_soffFooter)[0]

    #####################
    # File Area Observational
    #####################

    for _soffFile in workspace.soffFileList:
        _fao = ET.Element('File_Area_Observational')
        _file = ET.SubElement(_fao, 'File')
        _file_name = ET.SubElement(_file, 'file_name')
        _file_name.text = _soffFile
        for _soffTable in workspace.soffTableList:
            if _soffTable.filename == _soffFile:
                _table_delimited = ET.SubElement(_fao, 'Table_Delimited')
                _table_delimited_lid = ET.SubElement(_table_delimited, 'local_identifier')
                _table_delimited_lid.text = _soffTable.lid
                _table_delimited_parsing_std = ET.SubElement(_table_delimited, 'parsing_standard_id')
                _table_delimited_parsing_std.text = 'PDS DSV 1'
                _table_delimited_offset = ET.SubElement(_table_delimited, 'offset')
                _table_delimited_offset.set('unit', 'byte')
                _table_delimited_offset.text = str(_soffTable.byteOffset)
                _table_delimited_records = ET.SubElement(_table_delimited, 'records')
                _table_delimited_records.text = str(_soffTable.records)
                _table_delimited_record_del = ET.SubElement(_table_delimited, 'record_delimiter')
                _table_delimited_record_del.text = 'Carriage-Return Line-Feed'
                _table_delimited_field_del = ET.SubElement(_table_delimited, 'field_delimiter')
                _table_delimited_field_del.text = 'Comma'
                _record_del = ET.SubElement(_table_delimited, 'Record_Delimited')
                _record_del_fields = ET.SubElement(_record_del, 'fields')
                _record_del_fields.text = str(_soffTable.fieldsMain)
                _record_del_groups = ET.SubElement(_record_del, 'groups')
                _record_del_groups.text = str(_soffTable.groups)
                if _soffTable.fieldsMain == 0:
                    _group_del = ET.SubElement(_record_del, 'Group_Field_Delimited')
                    _group_rep = ET.SubElement(_group_del, 'repetitions')
                    _group_rep.text = str(_soffTable.groupsRepititions)
                    _group_fields = ET.SubElement(_group_del, 'fields')
                    _group_fields.text = str(_soffTable.groupsFields)
                    # TODO: this will need to be updated for 3D tables (nested repetitive groups)
                    _group_groups = ET.SubElement(_group_del, 'groups')
                    _group_groups.text = str(_soffTable.groupsGroups)
                    _group_field_del = ET.SubElement(_group_del, 'Field_Delimited')
                    # need to check this when I have multiple group names
                    for i in range(len(_soffTable.fieldNames)):
                        _group_field_name = ET.SubElement(_group_field_del, 'name')
                        _group_field_name.text = _soffTable.fieldNames[i]
                        _group_field_type = ET.SubElement(_group_field_del, 'data_type')
                        _group_field_type.text = _soffTable.dataType[i]
                else:
                    for i in range(len(_soffTable.fieldNames)):
                        _field_del = ET.SubElement(_record_del, 'Field_Delimited')
                        _field_name = ET.SubElement(_field_del, 'name')
                        _field_name.text = _soffTable.fieldNames[i]
                        _field_type = ET.SubElement(_field_del, 'data_type')
                        _field_type.text = _soffTable.dataType[i]
        _soffStringTable = ET.tostring(_fao).decode('utf-8')
        _soffString += _soffStringTable


    #####################
    # Observation Area
    #####################
    # TODO: update this from label - access from workspace
    _obsArea = ET.Element('Observation_Area')
    _time_coord = ET.SubElement(_obsArea, 'Time_Coordinates')
    _time_coord_start = ET.SubElement(_time_coord, 'start_date_time')
    _time_coord_start.text = '2000-00-00T00:00:00.000Z'
    _time_coord_stop = ET.SubElement(_time_coord, 'stop_date_time')
    _time_coord_stop.text = '2050-00-00T00:00:00.000Z'
    _inv_area = ET.SubElement(_obsArea, 'Investigation_Area')
    _inv_area_name = ET.SubElement(_inv_area, 'name')
    _inv_area_name.text = 'M2020'
    _inv_area_type = ET.SubElement(_inv_area, 'type')
    _inv_area_type.text = 'Mission'
    _inv_area_int_ref = ET.SubElement(_inv_area, 'Internal_Reference')
    _inv_area_int_ref_lid = ET.SubElement(_inv_area_int_ref, 'lid_reference')
    _inv_area_int_ref_lid.text = 'urn:nasa:pds:context:investigation:mission.m2020'
    _inv_area_int_ref_type = ET.SubElement(_inv_area_int_ref, 'reference_type')
    _inv_area_int_ref_type.text = 'data_to_investigation'
    _inv_area_int_comment = ET.SubElement(_inv_area_int_ref, 'comment')
    _inv_area_int_comment.text = 'This is the PDS4 logical identifier for the M2020 mission.'
    _obs_sys = ET.SubElement(_obsArea, 'Observing_System')
    _obs_sys_comp = ET.SubElement(_obs_sys, 'Observing_System_Component')
    _obs_sys_comp_name = ET.SubElement(_obs_sys_comp, 'name')
    _obs_sys_comp_name.text = 'M2020 Rover'
    _obs_sys_comp_type = ET.SubElement(_obs_sys_comp, 'type')
    _obs_sys_comp_type.text = 'Spacecraft'
    _obs_sys_comp_int_ref = ET.SubElement(_obs_sys_comp, 'Internal_Reference')
    _obs_sys_comp_int_ref_lid = ET.SubElement(_obs_sys_comp_int_ref, 'lid_reference')
    _obs_sys_comp_int_ref_lid.text = 'urn:nasa:pds:context:instrument_host:spacecraft.m2020'
    _obs_sys_comp_int_ref_ref = ET.SubElement(_obs_sys_comp_int_ref, 'reference_type')
    _obs_sys_comp_int_ref_ref.text = 'is_instrument_host'
    _obs_sys_comp_int_ref_comment = ET.SubElement(_obs_sys_comp_int_ref, 'comment')
    _obs_sys_comp_int_ref_comment.text = 'This is the PDS4 logical identifier for the M2020 Rover spacecraft.'
    _obs_sys_comp = ET.SubElement(_obs_sys, 'Observing_System_Component')
    _obs_sys_comp_name = ET.SubElement(_obs_sys_comp, 'name')
    _obs_sys_comp_name.text = 'SHERLOC'
    _obs_sys_comp_type = ET.SubElement(_obs_sys_comp, 'type')
    _obs_sys_comp_type.text = 'Instrument'
    _obs_sys_comp_int_ref = ET.SubElement(_obs_sys_comp, 'Internal_Reference')
    _obs_sys_comp_int_ref_lid = ET.SubElement(_obs_sys_comp_int_ref, 'lid_reference')
    _obs_sys_comp_int_ref_lid.text = 'urn:nasa:pds:context:instrument:ida.m2020'
    _obs_sys_comp_int_ref_ref = ET.SubElement(_obs_sys_comp_int_ref, 'reference_type')
    _obs_sys_comp_int_ref_ref.text = 'is_instrument'
    _target_id = ET.SubElement(_obsArea, 'Target_Identification')
    _target_id_name = ET.SubElement(_target_id, 'name')
    _target_id_name.text = 'Mars'
    _target_id_type = ET.SubElement(_target_id, 'type')
    _target_id_type.text = 'Planet'
    _target_id_int_ref = ET.SubElement(_target_id, 'Internal_Reference')
    _target_id_int_ref_lid = ET.SubElement(_target_id_int_ref, 'lid_reference')
    _target_id_int_ref_lid.text = 'urn:nasa:pds:context:target:planet.mars'
    _target_id_int_ref_ref = ET.SubElement(_target_id_int_ref, 'reference_type')
    _target_id_int_ref_ref.text = 'data_to_target'


    #####################
    # Discipline Area: Dimensions
    #####################

    _disArea = ET.SubElement(_obsArea, 'Discipline_Area')
    _disAreaSoff = ET.SubElement(_disArea, 'soff_Spectral_Open_File_Format')
    _disAreaSoffDims = ET.SubElement(_disAreaSoff, 'soff_Dimensions')
    for dim in workspace.soffDimensionList:
        _disAreaSoffDim = ET.SubElement(_disAreaSoffDims, 'soff_Dimension')
        _disAreaSoffDimClass = ET.SubElement(_disAreaSoffDim, 'soff_class')
        _disAreaSoffDimClass.text = dim.soffClass
        _disAreaSoffDimName = ET.SubElement(_disAreaSoffDim, 'name')
        _disAreaSoffDimName.text = dim.lid
        _disAreaSoffDimComment = ET.SubElement(_disAreaSoffDim, 'comment')
        _disAreaSoffDimComment.text = dim.comment
        _disAreaSoffDimElements = ET.SubElement(_disAreaSoffDim, 'elements')
        _disAreaSoffDimElements.text = str(dim.elements)
        _disAreaSoffDimLid = ET.SubElement(_disAreaSoffDim, 'local_identifier')
        _disAreaSoffDimLid.text = dim.lid


    #####################
    # Discipline Area: Data Tables
    #####################
    _disAreaSoffTabs = ET.SubElement(_disAreaSoff, 'soff_Data_Tables')
    for tab in workspace.soffSoffTableList:
        _disAreaSoffTab = ET.SubElement(_disAreaSoffTabs, 'soff_Data_Table')
        _disAreaSoffTabDimName = ET.SubElement(_disAreaSoffTab, 'name')
        _disAreaSoffTabDimName.text = tab.name
        _disAreaSoffTabDimDesc = ET.SubElement(_disAreaSoffTab, 'description')
        _disAreaSoffTabDimDesc.text = tab.description
        _disAreaSoffTabComp = ET.SubElement(_disAreaSoffTab, 'Composite_Structure')
        _disAreaSoffTabCompLidDim = ET.SubElement(_disAreaSoffTabComp, 'Local_ID_Reference')
        for dim in tab.dimensionLID:
            _disAreaSoffTabCompLidDimId = ET.SubElement(_disAreaSoffTabCompLidDim, 'id_reference_to')
            _disAreaSoffTabCompLidDimId.text = dim
        _disAreaSoffTabCompLidDimType = ET.SubElement(_disAreaSoffTabCompLidDim, 'id_reference_type')
        _disAreaSoffTabCompLidDimType.text = 'soff_table_to_dimension'
        _disAreaSoffTabCompLidTab = ET.SubElement(_disAreaSoffTabComp, 'Local_ID_Reference')
        _disAreaSoffTabCompLidTabId = ET.SubElement(_disAreaSoffTabCompLidTab, 'id_reference_to')
        _disAreaSoffTabCompLidTabId.text = tab.tableLID
        _disAreaSoffTabCompLidTabType = ET.SubElement(_disAreaSoffTabCompLidTab, 'id_reference_type')
        _disAreaSoffTabCompLidTabType.text = 'soff_to_local_table'

    _soffStringObs = ET.tostring(_obsArea).decode('utf-8')
    _soffString += _soffStringObs

    _soffString += _soffFooter

    _soffStringRoot = ET.fromstring(_soffString)
    _soffStringTree = ET.ElementTree(_soffStringRoot)
    XMLindent(_soffStringRoot, level=0)

    _soffFileXML = workspace.SOFFfile

    _soffStringTree.write(_soffFileXML, encoding='utf-8')

    with open(_soffFileXML, 'r') as f:
        _soffXMLtext = f.read()

    # ignore initial product_observational element
    _soffXMLtext = '\n'.join(_soffXMLtext.split('\n')[1:-1])

    os.remove(_soffFileXML)
    with open(_soffFileXML, 'w') as f:
        f.write(_soffHeader)
        f.write('\n  ')
        # remove last two spaces in last element to get footer at the right indent level
        f.write(_soffXMLtext[2:])
        #f.write(_soffFooter)

# TODO: change to supplemental (once SPAR is updated)
def addSOFFFAOSupplementalImg(workspace, file):
    _soffFileXML = workspace.SOFFfile
    with open(_soffFileXML, 'r') as f:
        _soffXMLtext = f.read()

    # check if file is already in text
    # add file to FAO supplemental
    if file not in _soffXMLtext:
        #_faoSupp = ET.Element('File_Area_Observational_Supplemental')
        _faoSupp = ET.Element('File_Area_Observational')
        _file = ET.SubElement(_faoSupp, 'File')
        _file_name = ET.SubElement(_file, 'file_name')
        _file_name.text = os.path.join(os.path.split(os.path.split(file)[0])[-1], os.path.split(file)[-1])
        _encodedImage = ET.SubElement(_faoSupp, 'Encoded_Image')
        _encodedImage_offset = ET.SubElement(_encodedImage, 'offset')
        _encodedImage_offset.set('unit', 'byte')
        _encodedImage_offset.text = str(0)

    _soffStringTable = ET.tostring(_faoSupp).decode('utf-8')
    _soffStringRoot = ET.fromstring(_soffStringTable)
    _soffStringTree = ET.ElementTree(_soffStringRoot)
    XMLindent(_soffStringRoot, level=1)

    _tmpFile = os.path.join(os.path.split(_soffFileXML)[0], 'temp.xml')
    _soffStringTree.write(_tmpFile, encoding='utf-8')
    with open(_tmpFile, 'r') as f:
        _suppXMLtext = f.read()
    _suppXMLtext = '  ' + _suppXMLtext[:-3]

    _soffTextBefore = ''.join(re.split('(</File_Area_Observational>)', _soffXMLtext)[0:-1])
    _soffTextAfter = ''.join(re.split('(</File_Area_Observational>)', _soffXMLtext)[-1])
    _soffText = _soffTextBefore+'\n'+_suppXMLtext+_soffTextAfter

    os.remove(_soffFileXML)
    with open(_soffFileXML, 'w') as f:
        f.write(_soffText)

    os.remove(_tmpFile)

# TODO: check what happens if multiple images are opened. I think I need to enable multiple loads automatically on open of SOFF file
def addSOFFFAOCsv(workspace, file, table_name, file_name=False):
    _soffFileXML = workspace.SOFFfile
    with open(_soffFileXML, 'r') as f:
        _soffXMLtext = f.read()

    tab = pd.read_csv(file, header=None)
    # check if file is already in text
    # add file to FAO supplemental
    if file not in _soffXMLtext:
        _fao = ET.Element('File_Area_Observational')
        _file = ET.SubElement(_fao, 'File')
        _file_name = ET.SubElement(_file, 'file_name')
        if file_name:
            _file_name.text = file_name
        else:
            _file_name.text = os.path.join(os.path.split(file)[-1])
        _table_delimited = ET.SubElement(_fao, 'Table_Delimited')
        _table_delimited_lid = ET.SubElement(_table_delimited, 'local_identifier')
        _table_delimited_lid.text = table_name
        _table_delimited_parsing_std = ET.SubElement(_table_delimited, 'parsing_standard_id')
        _table_delimited_parsing_std.text = 'PDS DSV 1'
        _table_delimited_offset = ET.SubElement(_table_delimited, 'offset')
        _table_delimited_offset.set('unit', 'byte')
        _table_delimited_offset.text = str(0)
        _table_delimited_records = ET.SubElement(_table_delimited, 'records')
        _table_delimited_records.text = str(tab.shape[0])
        _table_delimited_record_del = ET.SubElement(_table_delimited, 'record_delimiter')
        _table_delimited_record_del.text = 'Carriage-Return Line-Feed'
        _table_delimited_field_del = ET.SubElement(_table_delimited, 'field_delimiter')
        _table_delimited_field_del.text = 'Comma'
        _record_del = ET.SubElement(_table_delimited, 'Record_Delimited')
        _record_del_fields = ET.SubElement(_record_del, 'fields')
        _record_del_fields.text = str(2)
        _record_del_groups = ET.SubElement(_record_del, 'groups')
        _record_del_groups.text = str(0)
        _field_del = ET.SubElement(_record_del, 'Field_Delimited')
        _field_name = ET.SubElement(_field_del, 'name')
        _field_name.text = 'Parameter'
        _field_type = ET.SubElement(_field_del, 'data_type')
        _field_type.text = 'CHARACTER'
        _field_del = ET.SubElement(_record_del, 'Field_Delimited')
        _field_name = ET.SubElement(_field_del, 'name')
        _field_name.text = 'Value'
        _field_type = ET.SubElement(_field_del, 'data_type')
        _field_type.text = 'CHARACTER'


    _soffStringTable = ET.tostring(_fao).decode('utf-8')
    _soffStringRoot = ET.fromstring(_soffStringTable)
    _soffStringTree = ET.ElementTree(_soffStringRoot)
    XMLindent(_soffStringRoot, level=1)

    _tmpFile = os.path.join(os.path.split(_soffFileXML)[0], 'temp.xml')
    _soffStringTree.write(_tmpFile, encoding='utf-8')
    with open(_tmpFile, 'r') as f:
        _suppXMLtext = f.read()
    _suppXMLtext = '  ' + _suppXMLtext[:-3]

    _soffTextBefore = ''.join(re.split('(</File_Area_Observational>)', _soffXMLtext)[0:-1])
    _soffTextAfter = ''.join(re.split('(</File_Area_Observational>)', _soffXMLtext)[-1])
    _soffText = _soffTextBefore+'\n'+_suppXMLtext+_soffTextAfter

    os.remove(_soffFileXML)
    with open(_soffFileXML, 'w') as f:
        f.write(_soffText)

    os.remove(_tmpFile)