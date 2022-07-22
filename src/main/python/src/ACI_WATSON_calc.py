# based on model results from October 2021
def working_distance_WATSON(mech_0, tb=False):
    if tb:
        if mech_0 == 0:
            working_distance = 0
        elif mech_0 < 12270:
            working_distance = 500
        elif mech_0 > 15480:
            working_distance = 1.9
        else:
            working_distance = round(1/((17.0594/(mech_0))+(-9.42229)+(0.00233026*(mech_0))+(-0.000000197497*((mech_0)**2))+(0.00000000000571883*((mech_0)**3))),2)
    else:
        if mech_0 == 0:
            working_distance = 0
        elif mech_0 < 12204:
            working_distance = '> 220 cm'
        elif mech_0 > 15420:
            working_distance = 1.8
        else:
            working_distance = round(1/((1091060/(mech_0))+(-332.921)+(0.0382592*(mech_0))+(-0.00000196922*((mech_0)**2))+(0.0000000000384562*((mech_0)**3))),2)
    return working_distance

def working_distance_ACI(mech_0):
    return (0.005*mech_0)-20.34

# calculation not included in Oct 7 revision
def calc_DOF_far(mech_0, working_dist, tb=False):
    if tb:
        if mech_0 > 0:
            DOF_far_cm = round(abs((1/((0.43844/mech_0)-8.54596+(0.00212806*mech_0)-(0.000000181929*(mech_0**2))+(0.00000000000531799*(mech_0**3))))-mech_0), 2)
        else:
            DOF_far_cm = 0
    else:
        if mech_0 > 14850:
            DOF_far_cm = 0.1
        elif mech_0 > 0:
            DOF_far_cm = round(abs((1/((755933/mech_0)+(-234.525)+(0.0274318*mech_0)+(-0.00000143997*(mech_0**2))+(0.0000000000287582*(mech_0**3))))-working_dist), 2)
        else:
            DOF_far_cm = 0
    return DOF_far_cm

# calculation not included in Oct 7 revision
def calc_DOF_near(mech_0, working_dist, tb=False):
    if tb:
        if mech_0 > 0:
            DOF_near_cm = -1*(round(abs((1/((0.352038/mech_0)-9.06544+(0.00226609*mech_0)-(0.000000193895*(mech_0**2))+(0.00000000000566064*(mech_0**3))))-working_dist), 2))
        else:
            DOF_near_cm = 0
    else:
        if mech_0 > 15045:
            DOF_near_cm = -0.1
        elif mech_0 > 0:
            DOF_near_cm = -1.0*round(abs((1/((758336/mech_0)-235.879+(0.0276772*mech_0)+(-0.00000145801*(mech_0**2))+(0.0000000000292292*(mech_0**3))))-working_dist), 2)
        else:
            DOF_near_cm = 0
    return DOF_near_cm


def working_distance_err(mech_0, working_dist, tb=False):
    if type(working_dist) == type(''):
        working_dist_err = 'N/A'
    else:
        if tb:
            DOF_far_cm = calc_DOF_far(mech_0, working_dist, tb=tb)
            DOF_near_cm = calc_DOF_near(mech_0, working_dist, tb=tb)
            working_dist_err = (DOF_far_cm-DOF_near_cm)/2.0
            working_dist_err = round(working_dist_err, 2)
        else:
            if working_dist < 4.5:
                working_dist_err = 0.1
            else:
                working_dist_err = (((1/((1091060/(mech_0-15))+(-332.921)+(0.0382592*(mech_0-15))+(-0.00000196922*((mech_0-15)**2))+(0.0000000000384562*((mech_0-15)**3))))-working_dist)+(working_dist-(1/((1091060/(mech_0+15))+(-332.921)+(0.0382592*(mech_0+15))+(-0.00000196922*((mech_0+15)**2))+(0.0000000000384562*((mech_0+15)**3))))))/2
    return working_dist_err

def pix_scale_WATSON(working_dist, tb=False):
    if working_dist == 0:
        pix_scale = 0
    else:
        if tb:
            pix_scale = round(6.953+(3.606*working_dist), 2)
        else:
            pix_scale = round(6.528+(3.7261*working_dist)+(-0.0057102*(working_dist**2))+(0.000040576*(working_dist**3))+(-0.000000083282*(working_dist**4)), 2)
    return pix_scale

def pix_scale_err_WATSON(mech_0, pix_scale, working_dist, tb=False):
    if working_dist == 0 or type(working_dist) == type(''):
        pix_scale_err = 0
    else:
        if tb:
            DOF_far_cm = calc_DOF_far(mech_0, working_dist, tb=False)
            DOF_near_cm = calc_DOF_near(mech_0, working_dist, tb=False)
            pix_scale_err = round((((pix_scale-(6.953+(3.606*(working_dist+DOF_near_cm))))+(6.953+(3.606*(working_dist+DOF_far_cm))-pix_scale))/2),2)
        else:
            if working_dist < 2.7:
                pix_scale_err = 0.1
            else:
                pix_scale_err = round(((abs(pix_scale-((7.1244+(3.474*working_dist)+(-0.0063308*(working_dist**2))+(0.000044869*(working_dist**3))+(-0.00000009283*(working_dist**4))))))+(abs(pix_scale-(5.897+(3.9814*working_dist)+(-0.0051608*(working_dist**2))+(0.000036832*(working_dist**3))+(-0.000000075067*(working_dist**4))))))/2, 2)
    return pix_scale_err


def motor_pos_from_img_label(label_file):
    focus_pos = 0
    # get INSTRUMENT_FOCUS_POSITION from label file
    with open(label_file, 'r') as f:
        label_contents = f.read()
    if 'FOCUS_POSITION_COUNT' in label_contents:
        focus_pos= int(label_contents.split('FOCUS_POSITION_COUNT ')[1].split('\n')[0].replace('=', '').strip(' '))
    if focus_pos == 0 and 'INSTRUMENT_FOCUS_POSITION' in label_contents:
        focus_pos= int(label_contents.split('INSTRUMENT_FOCUS_POSITION ')[1].split('\n')[0].replace('=', '').strip(' '))
    if focus_pos == 0 and 'FILTER_POSITION_COUNT' in label_contents:
        focus_pos= int(label_contents.split('FILTER_POSITION_COUNT ')[1].split('\n')[0].replace('=', '').strip(' '))
    return focus_pos

def exp_time_from_img_label(label_file):
    exp_time = 'N/A'
    # get INSTRUMENT_FOCUS_POSITION from label file
    with open(label_file, 'r') as f:
        label_contents = f.read()
    if 'EXPOSURE_DURATION' in label_contents:
        exp_time= label_contents.split('EXPOSURE_DURATION ')[1].split('\n')[0].replace('=', '').strip(' ').split(' ')[0] + ' ms'
    return exp_time


def image_ID_from_img_label(label_file):
    image_ID = 'N/A'
    # get IMAGE_ID from label file
    with open(label_file, 'r') as f:
        label_contents = f.read()
    if 'IMAGE_ID' in label_contents:
        # there may be two places that contain IMAGE_ID - the IMAGE_ID in the VICAR header is what is wanted
        # to confirm that the IMAGE_ID is in the correct place, the group should be part of the IDENTIFICATION DATA ELEMENTS
        if 'IDENTIFICATION DATA ELEMENTS' in label_contents.split('IMAGE_ID')[0].split('/*')[-1][0:200]:
            image_ID = label_contents.split('IMAGE_ID ')[1].split('\n')[0].replace('=', '').strip(' ').strip('\"')
        # if the IMAGE_ID is a thumbnail, or the IMAGE_ID is not in the EDM or ECZ product
        elif len(label_contents.split('IMAGE_ID ')) > 2 or 'IDENTIFICATION DATA ELEMENTS' not in label_contents.split('IMAGE_ID')[0].split('/*')[-1][0:200]:
            # find index number in split label_contents
            if len([s for s in label_contents.split('IMAGE_ID') if 'MINI_HEADER' in s]) > 0:
                index_before = [i for i in range(len(label_contents.split('IMAGE_ID'))) if 'MINI_HEADER' in label_contents.split('IMAGE_ID')[i]][0]
                image_id_int = int(label_contents.split('IMAGE_ID')[index_before+1].split('\n')[0].replace('=', '').strip(' ').strip('\"'))
                # convert this to a binary, unset high bit
                image_id_binary = '{0:b}'.format(image_id_int)
                image_id_binary_corrected = '0'+image_id_binary[1:]
                image_ID = int(image_id_binary_corrected, 2)
    return image_ID

def calc_pix_scale_WATSON(label_file, tb=False):
    focus_pos = motor_pos_from_img_label(label_file)
    # working distance in cm
    working_dist = working_distance_WATSON(focus_pos, tb=tb)
    if type(working_dist) == type(''):
        pixel_scale_um_pix = 0
    else:
        pixel_scale_um_pix = pix_scale_WATSON(working_dist, tb=tb)

    return pixel_scale_um_pix
