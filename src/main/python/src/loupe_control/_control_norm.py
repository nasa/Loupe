import os

from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QPainter
from PyQt5.QtGui import QTransform
from PyQt5.QtGui import QPen
from PyQt5.QtGui import QBrush
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QPoint
from PyQt5.QtCore import QRect
from PyQt5.QtWidgets import QApplication

from matplotlib import cm as mpl_cm

from src import log_parsing
from src import file_IO
from src import generate_images
from src import generate_plots
from src.loupe_control import _control_main



def _updateNormLeftPanel(self):
    log_parsing.log_info(self._view, 'Updating laser normalization left panel')
    _populateWorkspaceName(self)
    # enable button and groupboxes
    self._view.LaserNormButton.setEnabled(True)
    self._view.groupboxImageNorm.setEnabled(True)
    self._view.groupboxPlotNorm.setEnabled(True)

    # set ACI image combo box
    # performed in _setImgCombo


def _updateNormCentralPanel(self):
    if self._view.workspace.selectedACIFilename is not None:
        _displayNormACI(self)
    _displayPhotodiodePlot(self)


def _populateWorkspaceName(self):
    self._view.workspaceLabelNorm.setText('Workspace: {0}'.format(self._view.workspace.humanReadableName))

def clearNorm(self):
    print()

def _displayNormACI(self):
    # check if image format is IMG or PNG
    if self._view.workspace.selectedACIFilename.endswith('IMG') or self._view.workspace.selectedACIFilename.endswith('PNG') or self._view.workspace.selectedACIFilename.endswith('png'):
        _addACIImageNorm(self)
        # fitinview will not set the zoom correctly unless the image is already loaded
        self._view.imageACINorm.fitInView()#self._view.imageACINorm._scene.sceneRect())
        if not self._view.laserTabOpened:
            self._view.imageACINorm.setTransform(QTransform.fromScale(5.78, 5.78), True)
        QApplication.processEvents()

        # enable other buttons
        self._view.opacityLaserNorm.setEnabled(True)
        self._view.opacityACINorm.setEnabled(True)

    else:
        log_parsing.log_warning(self._view, 'Selected ACI file {0} does not have the expected PNG or IMG extension'.format(self._view.workspace.selectedACIFilename))


def _displayPhotodiodePlot(self):
    if self._view.axNormPlot1 != []:
        for _ax in self._view.axNormPlot1:
            for _line in _ax.lines:
                _line.remove()
        self._view.traceCanvasNormPlot1.axes.clear()
        self._view.traceCanvasNormPlot1.draw_idle()
    self._view.axNormPlot1 = []

    axes = self._view.traceCanvasNormPlot1.axes
    if self._view.avgPdSpecNorm.isChecked():
        _x = range(self._view.workspace.nSpectra)
        _y = self._view.workspace.photodiodeSummary.values
        _ax = generate_plots.plotTrace(axes, _x, _y, 'w', alpha=0.9)
        _ax.axes.set_ylim(0.8*min(_y), 1.1*max(_y))
        _ax.axes.set_xlabel('Spectrum #')
        _ax.axes.set_ylabel('Average Photodiode Intensity')
        self._view.axNormPlot1.append(_ax)
    elif self._view.avgPdShotNorm.isChecked():
        _x = range(self._view.workspace.nShots)
        _y = self._view.workspace.photodiodeAll.mean(axis=0)
        _ax = generate_plots.plotTrace(axes, _x, _y, 'w', alpha=0.9)
        _ax.axes.set_xlabel('Shot #')
        _ax.axes.set_ylabel('Average Photodiode Intensity')
        self._view.axNormPlot1.append(_ax)
    elif self._view.allPdShotNorm.isChecked():
        _x = range(self._view.workspace.nShots*self._view.workspace.nSpectra)
        _y = self._view.workspace.photodiodeAll.to_numpy().flatten()
        _ax = generate_plots.plotTrace(axes, _x, _y, 'w', alpha=0.9)
        _ax.axes.set_xlabel('Shot #')
        _ax.axes.set_ylabel('Photodiode Intensity')
        self._view.axNormPlot1.append(_ax)
    else:
        _x = range(self._view.workspace.nShots)
        _cmap = mpl_cm.get_cmap('viridis')
        _alpha = 0.6-0.0006*self._view.workspace.nSpectra
        if _alpha < 0:
            _alpha = 0.05
        for _i in range(self._view.workspace.nSpectra):
            _y = self._view.workspace.photodiodeAll.loc[_i]
            _c = _cmap(_i/self._view.workspace.nSpectra)
            _ax = generate_plots.plotTrace(axes, _x, _y, _c, alpha=_alpha)
            self._view.axNormPlot1.append(_ax)
        _ax.axes.set_xlabel('Shot #')
        _ax.axes.set_ylabel('Photodiode Intensity')

    self._view.traceCanvasNormPlot1.draw_idle()


def _addACIImageNorm(self):
    self._view.pixmapACINorm = QPixmap(self._view.workspace.selectedACIFilename)

    # add discrete points
    # add interpolated map
    if self._view.normInterpolated.isChecked():
        _addInterpolatedPointsNorm(self)
    else:
        _addDiscretePointsNorm(self)

    self._view.imageACINorm.setPhoto(pixmap = self._view.pixmapACINorm, zoomSelect = self._view.imageACINorm._zoom)


# add point selection capability? (isolate view of a single photodiode spectrum)
def _addDiscretePointsNorm(self):
    self._view.OverlayNorm = QPainter(self._view.pixmapACINorm)
    self._view.OverlayNorm.setPen(QPen(Qt.black, 1, Qt.SolidLine))
    self._view.OverlayNorm.setBrush(QBrush(Qt.black, Qt.SolidPattern))
    self._view.OverlayNorm.setOpacity(1 - float(self._view.opacityACINorm.value())/100.0)
    self._view.OverlayNorm.drawRect(0, 0, self._view.pixmapACINorm.width(), self._view.pixmapACINorm.height())
    self._view.OverlayNorm.end()

    # add laser shots
    self._view.laserPainterInstanceNorm = QPainter(self._view.pixmapACINorm)
    self._view.laserPainterInstanceNorm.setOpacity(float(self._view.opacityLaserNorm.value())/100.0)
    #_width = self._view.laserPainterInstanceNorm.window().size().width()
    #_height = self._view.laserPainterInstanceNorm.window().size().height()
    for i in range(len(self._view.workspace.xPix)):
        if self._view.workspace.photodiodeSummary.values.max()-self._view.workspace.photodiodeSummary.values.min() == 0:
            _c = 255
        else:
            _c = int(255*(self._view.workspace.photodiodeSummary.values[i]-self._view.workspace.photodiodeSummary.values.min())/(self._view.workspace.photodiodeSummary.values.max()-self._view.workspace.photodiodeSummary.values.min()))
        self._view.laserPainterInstanceNorm.setPen(QPen(QColor(_c, _c, _c), 1, Qt.SolidLine))
        self._view.laserPainterInstanceNorm.setBrush(QBrush(QColor(_c, _c, _c), Qt.SolidPattern))
        _x = self._view.workspace.xPix[i]
        _y = self._view.workspace.yPix[i]
        self._view.laserPainterInstanceNorm.drawEllipse(QPoint(_x, _y), self._view.workspace.laserPix/2.0, self._view.workspace.laserPix/2.0)

    self._view.laserPainterInstanceNorm.end()

def _addInterpolatedPointsNorm(self):
    self._view.OverlayNorm = QPainter(self._view.pixmapACINorm)
    self._view.OverlayNorm.setPen(QPen(Qt.black, 1, Qt.SolidLine))
    self._view.OverlayNorm.setBrush(QBrush(Qt.black, Qt.SolidPattern))
    self._view.OverlayNorm.setOpacity(1 - float(self._view.opacityACINorm.value())/100.0)
    self._view.OverlayNorm.drawRect(0, 0, self._view.pixmapACINorm.width(), self._view.pixmapACINorm.height())
    self._view.OverlayNorm.end()

    # generate interpolated laser intensity map
    _tmp_dir = os.path.join(self._view.workspace.workingDir, 'tmp')
    file_IO.mkdir(_tmp_dir)
    _laserIntMap = os.path.join(_tmp_dir, 'laser_intensity_map.png')
    if not os.path.exists(_laserIntMap):
        generate_images.grayscale_image_interpolate(self._view.workspace.xPix, self._view.workspace.yPix, self._view.workspace.photodiodeSummary.values, _laserIntMap, method='nearest', invert_color=False, clip_low=0.00, clip_high = 1.00)

    _pixmap = QPixmap(_laserIntMap)
    self._view.laserPainterInstanceNorm = QPainter(self._view.pixmapACINorm)
    self._view.laserPainterInstanceNorm.setOpacity(float(self._view.opacityLaserNorm.value())/100.0)
    _width = max(self._view.workspace.xPix) - min(self._view.workspace.xPix)
    _height = max(self._view.workspace.yPix) - min(self._view.workspace.yPix)
    self._view.laserPainterInstanceNorm.drawPixmap(QRect(min(self._view.workspace.xPix), min(self._view.workspace.yPix), _width, _height), _pixmap)
    self._view.laserPainterInstanceNorm.end()


def _executeLaserNorm(self):
    # perform laser normalization
    if self._view.workspace.specProcessingApplied != 'None' and 'N' in self._view.workspace.specProcessingApplied:
        log_parsing.log_warning(self._view, 'Laser normalization already applied. Loupe will not normalize spectra again')
    else:
        _specDictKey = self._view.workspace.specProcessingApplied
        # applying laser normalization to active and dark separately can only be conducted if no other processing has been done
        if _specDictKey == 'None':
            self._view.workspace.specProcessingApplied = 'N'
        else:
            self._view.workspace.specProcessingApplied += 'N'
        _specFlag = self._view.workspace.specProcessingApplied
        _specActiveR1 = self._view.workspace.activeSpectraR1[_specDictKey]
        _specActiveR2 = self._view.workspace.activeSpectraR2[_specDictKey]
        _specActiveR3 = self._view.workspace.activeSpectraR3[_specDictKey]
        _specDarkR1 = self._view.workspace.darkSpectraR1[_specDictKey]
        _specDarkR2 = self._view.workspace.darkSpectraR2[_specDictKey]
        _specDarkR3 = self._view.workspace.darkSpectraR3[_specDictKey]
        _specDarkSubR1 = self._view.workspace.darkSubSpectraR1[_specDictKey]
        _specDarkSubR2 = self._view.workspace.darkSubSpectraR2[_specDictKey]
        _specDarkSubR3 = self._view.workspace.darkSubSpectraR3[_specDictKey]

        # increase the intensity of other spectra
        _pd = self._view.workspace.photodiodeSummary.to_numpy().flatten()
        _norm = [max(_pd)/_pd_i for _pd_i in _pd]

        self._view.workspace.darkSubSpectraR1[_specFlag] = _specDarkSubR1.multiply(_norm, axis='rows')
        self._view.workspace.darkSubSpectraR2[_specFlag] = _specDarkSubR2.multiply(_norm, axis='rows')
        self._view.workspace.darkSubSpectraR3[_specFlag] = _specDarkSubR3.multiply(_norm, axis='rows')
        # add data to csv files
        _spec_file = os.path.join(self._view.workspace.workingDir, 'darkSubSpectra{0}.csv'.format(_specFlag))
        file_IO.writeSpectraRegions(_spec_file, self._view, self._view.workspace.darkSubSpectraR1[_specFlag], self._view.workspace.darkSubSpectraR2[_specFlag], self._view.workspace.darkSubSpectraR3[_specFlag])

        #if _specDictKey == 'None':
        self._view.workspace.activeSpectraR1[_specFlag] = _specActiveR1.multiply(_norm, axis='rows')
        self._view.workspace.activeSpectraR2[_specFlag] = _specActiveR2.multiply(_norm, axis='rows')
        self._view.workspace.activeSpectraR3[_specFlag] = _specActiveR3.multiply(_norm, axis='rows')
        self._view.workspace.darkSpectraR1[_specFlag] = _specDarkR1.multiply(_norm, axis='rows')
        self._view.workspace.darkSpectraR2[_specFlag] = _specDarkR2.multiply(_norm, axis='rows')
        self._view.workspace.darkSpectraR3[_specFlag] = _specDarkR3.multiply(_norm, axis='rows')

        # add data to csv files
        _spec_file = os.path.join(self._view.workspace.workingDir, 'activeSpectra{0}.csv'.format(_specFlag))
        file_IO.writeSpectraRegions(_spec_file, self._view, self._view.workspace.activeSpectraR1[_specFlag], self._view.workspace.activeSpectraR2[_specFlag], self._view.workspace.activeSpectraR3[_specFlag])
        _spec_file = os.path.join(self._view.workspace.workingDir, 'darkSpectra{0}.csv'.format(_specFlag))
        file_IO.writeSpectraRegions(_spec_file, self._view, self._view.workspace.darkSpectraR1[_specFlag], self._view.workspace.darkSpectraR2[_specFlag], self._view.workspace.darkSpectraR3[_specFlag])

        # add csv files to SOFF file

        _control_main._updateSpecProcessing(self)
        _loupe_file = os.path.join(self._view.workspace.workingDir, 'loupe.csv')
        file_IO.writeLoupeCsv(_loupe_file, self._view)


def _rescaleYNorm1(self):
    generate_plots.autoscale_y(self._view.traceCanvasNormPlot1.axes, margin=0.1)
    self._view.traceCanvasNormPlot1.draw_idle()
