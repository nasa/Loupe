# for PyCharm, need to disable "PyQt compatible" in Build, Execution, Deployment -> Python Debugger
import cv2
import numpy as np
from scipy import interpolate
from PIL import Image



# generate an 2D greyscale map of spectra, interpolating between points
def grayscale_image_interpolate(pix_x, pix_y, data, save_file, method='cubic', invert_color=False, clip_low=0, clip_high = 1):
    grid_x, grid_y = np.mgrid[int(min(pix_x)):int(max(pix_x)), int(min(pix_y)):int(max(pix_y))]
    if clip_low > 0:
        data_min = min(sorted(data.flatten())[int(clip_low*len(data.flatten())):int(clip_high*len(data.flatten()))])
        data_max = max(sorted(data.flatten())[int(clip_low*len(data.flatten())):int(clip_high*len(data.flatten()))])
        data = np.clip(data, data_min, data_max)

    coords = np.array([[pix_x[i], pix_y[i]] for i in range(len(pix_x))])
    data_interpolate = interpolate.griddata(coords, np.array(data), (grid_x, grid_y), method=method)
    data_interpolate[np.isnan(data_interpolate)] = 0
    data_interpolate = data_interpolate-data_interpolate.min()
    image_array = 255.0*(data_interpolate/data_interpolate.max())
    #invert colors
    if invert_color:
        image_array = (255.0-image_array)

    # this rotation is needed to accommodate different coordinates used for cv2 image  -  (0,0) starts at top left
    image_array = np.rot90(image_array, 3)
    ##########################
    # this is needed, but I don't know why. There must be a sign error in the calculation of x points (converting az/el to x/y), but I cannot determine why
    image_array = cv2.flip(image_array, 1)
    ##########################
    cv2.imwrite(save_file, image_array)

def color_image_interpolate(grid_x, grid_y, coords, data, method='cubic', clip_low=None, clip_high = None, resize=None):
    if clip_low is not None and clip_high is not None:
        #data_min = min(sorted(data.flatten())[int(clip_low*len(data.flatten())):int(clip_high*len(data.flatten()))])
        #data_max = max(sorted(data.flatten())[int(clip_low*len(data.flatten())):int(clip_high*len(data.flatten()))])
        data = np.clip(data, clip_low, clip_high)

    data_interpolate = interpolate.griddata(coords, np.array(data), (grid_x, grid_y), method=method)
    data_interpolate[np.isnan(data_interpolate)] = 0
    data_interpolate = data_interpolate-data_interpolate.min()
    if data_interpolate.max() != 0:
        image_array = 255.0*(data_interpolate/data_interpolate.max())
    else:
        image_array = data_interpolate

    # this could be a result of mgrid transposing xy values
    # this rotation is needed to accommodate different coordinates used for cv2 image  -  (0,0) starts at top left
    image_array = np.rot90(image_array, 3)
    ##########################
    # this is needed, but I don't know why. There must be a sign error in the calculation of x points (converting az/el to x/y), but I cannot determine why
    image_array = cv2.flip(image_array, 1)
    ##########################

    # this isn't much faster - may need to resize grid_x/grid_y first to speed things up
    if resize is not None:
        image_array = cv2.resize(image_array, dsize=(int(resize*image_array.shape[0]), int(resize*image_array.shape[1])), interpolation = cv2.INTER_CUBIC)

    return image_array.astype(np.int8)


def gif_from_pngs(save_file, image_list):
    img, *imgs = [Image.open(f) for f in image_list]
    img.save(fp=save_file, format='GIF', append_images=imgs, save_all=True, duration=100, loop=0)