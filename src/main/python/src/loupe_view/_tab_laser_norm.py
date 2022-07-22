import os
import sys

import PyQt5
# import QApplication and required widgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QSlider
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QRadioButton
from PyQt5.QtWidgets import QHBoxLayout # horizontal layout
from PyQt5.QtWidgets import QVBoxLayout # vertical layout
from PyQt5.QtWidgets import QGridLayout # grid layout
# from PyQt5.QtWidgets import QFormLayout # form layout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QScrollArea
from PyQt5.QtWidgets import QSpacerItem
from PyQt5.QtWidgets import QSizePolicy

from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT


from src import MPL_plots
from src import image_viewer



###################################################
###################################################
#  LASER NORM Left Panel
###################################################
###################################################
def _addLaserNormLeftPanel(self):
    # define grid layout for labels and lists
    normLeftScrollContainer = QScrollArea()
    normLeftScrollContainer.setFixedWidth(350)
    normLeftScrollContainer.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
    normLeftScrollContainer.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    normLeftScrollContainer.setWidgetResizable(True)

    normLeftWidgetContainer = QWidget()
    normLeftScrollContainer.setWidget(normLeftWidgetContainer)
    normLeftLayout = QGridLayout(normLeftWidgetContainer)

    # workspace
    _workspaceLabelWidget = QWidget()
    gridMode = QGridLayout()
    _workspaceLabelWidget.setLayout(gridMode)
    self.workspaceLabelNorm = QLabel()
    self.workspaceLabelNorm.setText('Workspace: {0}'.format(self.workspace.humanReadableName))
    gridMode.addWidget(self.workspaceLabelNorm)
    normLeftLayout.addWidget(_workspaceLabelWidget)

    # Execute laser normalization
    # ROI dropdown with previous selections
    _laserExeWidget = QWidget()
    gridMode = QGridLayout()
    _laserExeWidget.setLayout(gridMode)
    _laserNormExeLabel = QLabel()
    _laserNormExeLabel.setText('Execute Laser Normalization:')
    gridMode.addWidget(_laserNormExeLabel, 0, 0, 1, 1)
    self.LaserNormButton = QPushButton()
    self.LaserNormButton.setText('Laser Norm.')
    self.LaserNormButton.setEnabled(False)
    gridMode.addWidget(self.LaserNormButton , 0, 1, 1, 1)
    normLeftLayout.addWidget(_laserExeWidget)


    # image groupbox
    self.groupboxImageNorm = QGroupBox('Image Configuration')
    gboxMode = QGridLayout()
    self.groupboxImageNorm.setLayout(gboxMode)
    _laserNormImgLabel = QLabel()
    _laserNormImgLabel.setText('Select ACI Image')
    gboxMode.addWidget(_laserNormImgLabel, 0, 0, 1, 3)
    # ACI file select dropdown
    if self.workspace.selectedACIFilename is None:
        self.selectedACIComboNorm = QComboBox()
    else:
        self.selectedACIComboNorm = QComboBox(self.workspace.selectedACIFilename)
    self.selectedACIComboNorm.setFixedHeight(30)
    self.selectedACIComboNorm.setMinimumWidth(50)
    gboxMode.addWidget(self.selectedACIComboNorm, 0, 3, 1, 7)
    self.selectedACIComboNorm.setMaximumHeight(100)

    # image opacity
    _OpacityLabel = QLabel()
    _OpacityLabel.setText('Image Opacity')
    gboxMode.addWidget(_OpacityLabel, 1, 0, 1, 2)
    self.opacityACINorm = QSlider(Qt.Horizontal)
    self.opacityACINorm.setMinimum(0)
    self.opacityACINorm.setMaximum(100)
    self.opacityACINorm.setValue(100)
    gboxMode.addWidget(self.opacityACINorm, 1, 2, 1, 8)

    # laser opacity
    _OpacityLabel = QLabel()
    _OpacityLabel.setText('Laser Opacity')
    gboxMode.addWidget(_OpacityLabel, 2, 0, 1, 2)
    self.opacityLaserNorm = QSlider(Qt.Horizontal)
    self.opacityLaserNorm.setMinimum(0)
    self.opacityLaserNorm.setMaximum(100)
    self.opacityLaserNorm.setValue(100)
    gboxMode.addWidget(self.opacityLaserNorm, 2, 2, 1, 8)

    # toggle between spots and integrated map
    self.groupboxImageModeNorm = QGroupBox('Laser Intensity Display Mode')
    hboxMode = QHBoxLayout()
    self.groupboxImageModeNorm.setLayout(hboxMode)
    self.normDiscrete = QRadioButton('Discrete')
    hboxMode.addWidget(self.normDiscrete)
    self.normInterpolated = QRadioButton('Interpolated')
    hboxMode.addWidget(self.normInterpolated)
    self.normDiscrete.setChecked(True)
    self.opacityLaserNorm.setEnabled(False)
    self.opacityACINorm.setEnabled(False)
    gboxMode.addWidget(self.groupboxImageModeNorm, 3, 0, 1, 10)

    normLeftLayout.addWidget(self.groupboxImageNorm)
    self.groupboxImageNorm.setEnabled(False)


    # plot groupbox
    self.groupboxPlotNorm = QGroupBox('Photodiode Plot Display')
    vboxMode = QVBoxLayout()
    self.groupboxPlotNorm.setLayout(vboxMode)
    # display avg photodiode (vs spec number)
    self.avgPdSpecNorm = QRadioButton('Avg. Photodiode vs Spectrum')
    vboxMode.addWidget(self.avgPdSpecNorm)
    # display avg photodiode (vs shot number)
    self.avgPdShotNorm = QRadioButton('Avg. Photodiode vs Shot')
    vboxMode.addWidget(self.avgPdShotNorm)
    # display all shots (in series)
    self.allPdShotNorm = QRadioButton('All Photodiode - all shots in series')
    vboxMode.addWidget(self.allPdShotNorm)
    # display all shots (spectra stacked)
    self.allPdSpecNorm = QRadioButton('All Photodiode - all spectra stacked')
    vboxMode.addWidget(self.allPdSpecNorm)
    self.groupboxPlotNorm.setEnabled(False)
    self.avgPdSpecNorm.setChecked(True)
    normLeftLayout.addWidget(self.groupboxPlotNorm)

    normLeftLayout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
    self.LoupeViewNormTabLayout.addWidget(normLeftScrollContainer)


###################################################
###################################################
#  LASER NORM Central Panel
###################################################
###################################################

def _addLaserNormCenterPanel(self):
    # ACI laser map overlay
    _vertScaleIconPath = self._appctxt.get_resource('rescale_vertical_40px.png')
    normPlotLayout = QVBoxLayout()

    imageWidget = QWidget()
    imageLayout = QHBoxLayout(imageWidget)
    imageLayout.setContentsMargins(0, 0, 0, 0)

    img1_dir = self._appctxt.get_resource('ACI_placeholder.png')
    self.pixmapACINorm = QPixmap(img1_dir)
    self.pixmapACINorm = self.pixmapACINorm.scaledToWidth(0.92*imageWidget.width())

    self.imageACINorm = image_viewer.imageViewer(self)
    self.imageACINorm.setMinimumHeight(420)
    self.imageACINorm.setPhoto(pixmap = self.pixmapACINorm, zoomSelect=1)

    imageLayout.addWidget(self.imageACINorm)
    normPlotLayout.addWidget(imageWidget)


    # photodiode plot
    self.traceCanvasNormPlot1 = MPL_plots.MplCanvas(self, width=5, height=4, dpi=100)
    self.traceCanvasNormPlot1.axes.plot([0], [0])

    # list of axes in the plot
    self.axNormPlot1 = []

    # Create toolbar, passing canvas as first parameter, parent (self, the MainWindow) as second.
    self.toolbarNormPlot1 = NavigationToolbar2QT(self.traceCanvasNormPlot1, self)
    self.toolbarNormPlot1.setMaximumHeight(25)
    self.toolbarResizeNorm1 = QAction(QIcon(_vertScaleIconPath), 'Autoscale vertical axis', self.toolbarNormPlot1)
    self.toolbarNormPlot1.insertAction(self.toolbarNormPlot1.actions()[5], self.toolbarResizeNorm1)
    self.toolbarNormPlot1.removeAction(self.toolbarNormPlot1.actions()[7])
    self.toolbarNormPlot1.setStyleSheet("QToolBar { border: 0px }")

    normPlotLayout.addWidget(self.toolbarNormPlot1)
    normPlotLayout.addWidget(self.traceCanvasNormPlot1)

    #normPlotLayout.addStretch()
    self.LoupeViewNormTabLayout.addLayout(normPlotLayout, 0, 3, 4, 7)

