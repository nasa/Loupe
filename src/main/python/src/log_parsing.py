import os
import logging
import time

from PyQt5.QtWidgets import QStatusBar
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QApplication
from src import file_IO

##################################
# Logging functions

def logging_setup(log_dir, view, version):
    # need to remove all handlers associated with the root logger object in order to generate file
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    file_IO.mkdir(log_dir)
    log_file = os.path.join(log_dir, 'log_'+time.strftime('%Y%m%d_%H%M%S')+'.log')
    logging.basicConfig(filename = log_file, level=logging.DEBUG, format='%(levelname)s %(asctime)s.%(msecs)03d | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    log_info(view, 'Started Loupe Version '+ version + ': ' + time.strftime('%a, %d %b %Y %H:%M:%S')+' system time')
    log_info(view, 'Root directory: '+os.path.split(os.path.split(log_dir)[0])[0])


def log_info(view, event):
    print(event)
    logging.info(event)
    if type(event) == type(''):
        view.statusBar.setStyleSheet("background-color : #333333")
        view.statusBar.showMessage(event)

def log_info_mute(view, event):
    print(event)

def log_warning(view, event):
    print(event)
    logging.warning(event)
    if type(event) == type(''):
        view.statusBar.setStyleSheet("background-color : #595921")
        view.statusBar.showMessage(event)

def log_error(view, event):
    print(event)
    logging.error(event)
    if type(event) == type(''):
        view.statusBar.setStyleSheet("background-color : #b5102c")
        view.statusBar.showMessage(event)

