"""
Loupe is currently designed to read SHERLOC hyperspectral datasets, and allows a user to process and visualize the data
The program has been written to be eventually extensible to other instrument datasets of similar type (hyperspectral or mapping spectrometery)

Python 3.7 required (SPAR will not yet work with Python 3.8)

SHERLOC types supported will include:
o EDR/RDR format


Loupe stores data in SOFF-style files as a conversion layer between each type. See https://github.com/NASA-AMMOS/SPAR


Critical features of Loupe
o Store processing/visualization in workspaces for easy re-loading
o Compare workspaces - allow a user to name a workspace and select it from a dropdown list
o overlay shots on an image
    o allow a user to nudge these shots
o processing:
    o cosmic ray correction
    o baseline subtraction
    o laser normalization
    o wavelength correction
    o re-do a processing step
o visualization
    o compare with library standard
    o compare with other data
    o toggle on/off processing
    o PCA
    o RGB maps
    o spectral maps
    o instantaneous plot of spectrum when hovering over shot
    o az/el x/y maps
    o laser photodiode map
o display metadata in a table:
    o Sol
    o RTT
    o target name
    o time info
    o number of shots
    o temperatures
    o power states
    o status flags
    o motor positions
    o az/el

GUI elements:
o toolbar:
    o file > load dataset
    o file > save dataset
o pages with distinct views/purposes:
    o main
        o selections
            o select workspace
            o select lower plot (temperature vs shot, sinlge spectrum, region spectrum
            o define ROIs (based on lasso or point number)
            o toggle processing
            o toggle active, dark, active-dark
            o toggle regions (1-3)
        o main spectrum
            o mean or median spectrum
            o +/- 1 STD about mean
        o lower spectrum
        o image (ACI overlay on WATSON)
        o image tools
            o selection for images
            o nudge points
            o selection for az/el scale and laser center
            o image properties
    o comparison
        o
    o cosmic ray removal
        o all spectra/histogram
        o individual spectrum
        o selection
            o method
            o
    o laser normalization
        o all spectra
        o laser photodiode trend
        o laser photodiode map
        o selection
            o
    o wavelength calibration
        o all spectra
        o individual spectra
        o
    o baseline subtraction
        o
    o PCA
        o
    o peak fitting
        o
    o RGB maps
        o
o action area
    o allow workspace selection


Author: Kyle Uckert (kyle.uckert@jpl.nasa.gov)
"""

import sys
import os
import numpy as np


import matplotlib
matplotlib.use('Qt5Agg')

import PyQt5
# import QApplication and required widgets
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QSystemTrayIcon

# necessary to pass arguments to controller class methods
from functools import partial
from darktheme.widget_template import DarkPalette
from fbs_runtime.application_context.PyQt5 import ApplicationContext

from src import log_parsing
from src import loupe_control
from src import loupe_view
from src import loupe_model


__version__ = '5.1.5'
__releaseDate__ = 'November 24, 2021'
# set _test to True to use hardcoded dataset
# set _test to False to allow a user to load a dataset from a dialog window
_test = False


def main():
    appctxt = ApplicationContext()
    # Create an instance of QApplication
    LoupeView = QApplication(sys.argv)
    LoupeView.setStyle('Fusion')
    LoupeView.setPalette(DarkPalette())
    LoupeView.setStyleSheet("QToolTip { color: #ffffff; background-color: grey; border: 1px solid white; }"
                            "QCheckBox:disabled {color:#191919;}"
                            "QRadioButton:disabled {color:#191919;}"
                            "QWidget:disabled {color:#191919;}")

    #_iconPath = os.path.join(os.path.dirname(sys.modules[__name__].__file__), 'resources', 'Loupe_logo.icns')
    _iconPath = appctxt.get_resource('Loupe_logo.icns')
    _icon = QIcon(_iconPath)
    LoupeView.setWindowIcon(_icon)
    # Show the application's GUI
    print('Running Loupe Version: ' + __version__)
    view = loupe_view.LoupeViewUi(__version__, __releaseDate__, _test, appctxt)
    view.show()
    # Create instances of the model and the controller
    model = loupe_model.LoupeAccess
    # need to save the controller to an unused variable to prevent it from being garbage collected
    controller = loupe_control.LoupeCtrl(model=model, view=view)
    # Execute the application's main loop
    exit_code = appctxt.app.exec()
    sys.exit(exit_code)
    #sys.exit(LoupeView.exec_())


if __name__ == '__main__':
    main()
