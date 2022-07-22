from PyQt5.QtGui import QPen
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.lines import Line2D
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import cycler
import numpy as np


plt.rcParams.update({
    "lines.color": "white",
    "patch.edgecolor": "white",
    "text.color": (1, 1, 1, 0.9),
    "axes.facecolor": (0.15, 0.15, 0.15, 1.0),
    "axes.edgecolor": "lightgray",
    "axes.labelcolor": (1, 1, 1, 0.9),
    "xtick.color": (1, 1, 1, 0.9),
    "ytick.color": (1, 1, 1, 0.9),
    "grid.color": (0.3, 0.3, 0.3, 0.5),
    "figure.facecolor": (0.2, 0.2, 0.2, 1.0),
    "figure.edgecolor": "black",
    "savefig.facecolor": (0.2, 0.2, 0.2, 1.0),
    "savefig.edgecolor": "black",
    "axes.prop_cycle": cycler.cycler("color", plt.cm.hsv(np.linspace(0, 1, 10)))})


class DraggablePoint:

    # https://stackoverflow.com/questions/28001655/draggable-line-with-draggable-points

    lock = None #  only one can be animated at a time

    def __init__(self, parent, view, x=0.1, y=0.1, width=0.1, height=0.1, color='w', label='_', multi=None, alpha=0.2):

        self.viewRGB = view
        self.parent = parent
        self.point = patches.Rectangle((x, y), width, height, fc=color, alpha=alpha, edgecolor=color, label=label)
        #print('x: {0}, y: {1}, width: {2}, height: {3}'.format(x, y, width, height))
        self.x = x
        self.y = y
        if multi is not None:
            parent.fig.axes[multi].add_patch(self.point)
            self.press = None
            self.background = None
            self.connect_subplot()
        else:
            parent.fig.axes[-1].add_patch(self.point)
            self.press = None
            self.background = None
            self.connect()

    def connect(self):

        # connect to all the events we need

        self.cidpress = self.point.figure.canvas.mpl_connect('button_press_event', self.on_press)
        self.cidrelease = self.point.figure.canvas.mpl_connect('button_release_event', self.on_release)
        self.cidmotion = self.point.figure.canvas.mpl_connect('motion_notify_event', self.on_motion)

    def connect_subplot(self):

        # connect to all the events we need

        self.cidpress = self.point.figure.canvas.mpl_connect('button_press_event', self.on_press_subplot)
        self.cidrelease = self.point.figure.canvas.mpl_connect('button_release_event', self.on_release)
        self.cidmotion = self.point.figure.canvas.mpl_connect('motion_notify_event', self.on_motion_subplot)


    def on_press(self, event):

        if event.inaxes != self.point.axes: return
        #if event.artist.get_label() != '_redBox' or event.artist.get_label() != '_greenBox' or event.artist.get_label() != '_blueBox': return
        if DraggablePoint.lock is not None: return
        contains, attrd = self.point.contains(event)
        if not contains: return
        #self.press = (self.point.center), event.xdata, event.ydata
        self.press = (self.point.xy), event.xdata, event.ydata
        DraggablePoint.lock = self

        # draw everything but the selected rectangle and store the pixel buffer
        canvas = self.point.figure.canvas
        axes = self.point.axes
        self.point.set_animated(True)
        canvas.draw()
        self.background = canvas.copy_from_bbox(self.point.axes.bbox)

        # now redraw just the rectangle
        axes.draw_artist(self.point)

        # and blit just the redrawn area
        canvas.blit(axes.bbox)

    def on_press_subplot(self, event):

        if event.inaxes is not None:
            ax = event.inaxes
            if DraggablePoint.lock is not None: return
            contains_all = []
            for _ax in ax.figure.axes:
                contains, attrd = _ax.contains(event)
                contains_all.append(contains)
            if not any(contains_all): return
            _ax_i = [i for i, x in enumerate(contains_all) if x][0]
            _ax = ax.figure.axes[_ax_i]
            contains_all = []
            for _patch in _ax.patches:
                contains, attrd = _patch.contains(event)
                contains_all.append(contains)
            if not any(contains_all): return
            _patch_i = [i for i, x in enumerate(contains_all) if x][0]
            self.point = _ax.patches[_patch_i]
            self.press = (self.point.xy), event.xdata, event.ydata
            DraggablePoint.lock = self

            # draw everything but the selected rectangle and store the pixel buffer
            canvas = self.point.figure.canvas
            axes = self.point.axes
            self.point.set_animated(True)
            canvas.draw()
            self.background = canvas.copy_from_bbox(self.point.axes.bbox)

            # now redraw just the rectangle
            axes.draw_artist(self.point)

            # and blit just the redrawn area
            canvas.blit(axes.bbox)


    def on_motion(self, event):

        if DraggablePoint.lock is not self:
            return
        if event.inaxes != self.point.axes: return
        self.point.xy, xpress, ypress = self.press
        dx = event.xdata - xpress
        dy = 0#event.ydata - ypress
        self.point.xy = (self.point.xy[0]+dx, self.point.xy[1]+dy)

        canvas = self.point.figure.canvas
        axes = self.point.axes
        # restore the background region
        canvas.restore_region(self.background)

        # redraw just the current rectangle
        axes.draw_artist(self.point)

        self.x = self.point.xy[0]
        self.y = self.point.xy[1]

        # blit just the redrawn area
        canvas.blit(axes.bbox)
        if self.point.get_label() == '_redBox':
            self.viewRGB.redPosRGB.setText('{0:.2f}'.format(self.x+self.point._width/2.0))
        if self.point.get_label() == '_greenBox':
            self.viewRGB.greenPosRGB.setText('{0:.2f}'.format(self.x+self.point._width/2.0))
        if self.point.get_label() == '_blueBox':
            self.viewRGB.bluePosRGB.setText('{0:.2f}'.format(self.x+self.point._width/2.0))

    def on_motion_subplot(self, event):

        if DraggablePoint.lock is not self:
            return
        if event.inaxes is not None:
            ax = event.inaxes
            contains_all = []
            for _ax in ax.figure.axes:
                contains, attrd = _ax.contains(event)
                contains_all.append(contains)
            if not any(contains_all): return

            self.point.xy, xpress, ypress = self.press
            dx = event.xdata - xpress
            dy = 0#event.ydata - ypress
            self.point.xy = (self.point.xy[0]+dx, self.point.xy[1]+dy)

            canvas = self.point.figure.canvas
            axes = self.point.axes
            # restore the background region
            canvas.restore_region(self.background)

            # redraw just the current rectangle
            axes.draw_artist(self.point)

            self.x = self.point.xy[0]
            self.y = self.point.xy[1]

            # blit just the redrawn area
            canvas.blit(axes.bbox)
            if self.point.get_label() == '_redHistHigh':
                self.viewRGB.redHistHighRGB.setText('{0:.2f}'.format(self.x+self.point._width/2.0))
            if self.point.get_label() == '_redHistLow':
                self.viewRGB.redHistLowRGB.setText('{0:.2f}'.format(self.x+self.point._width/2.0))
            if self.point.get_label() == '_greenHistHigh':
                self.viewRGB.greenHistHighRGB.setText('{0:.2f}'.format(self.x+self.point._width/2.0))
            if self.point.get_label() == '_greenHistLow':
                self.viewRGB.greenHistLowRGB.setText('{0:.2f}'.format(self.x+self.point._width/2.0))
            if self.point.get_label() == '_blueHistHigh':
                self.viewRGB.blueHistHighRGB.setText('{0:.2f}'.format(self.x+self.point._width/2.0))
            if self.point.get_label() == '_blueHistLow':
                self.viewRGB.blueHistLowRGB.setText('{0:.2f}'.format(self.x+self.point._width/2.0))


    def on_release(self, event):

        #on release we reset the press data
        if DraggablePoint.lock is not self:
            return

        self.press = None
        DraggablePoint.lock = None

        # turn off the rect animation property and reset the background
        self.point.set_animated(False)

        self.background = None

        # redraw the full figure
        self.point.figure.canvas.draw()

        self.x = self.point.xy[0]
        self.y = self.point.xy[1]

    def disconnect(self):

        #disconnect all the stored connection ids

        self.point.figure.canvas.mpl_disconnect(self.cidpress)
        self.point.figure.canvas.mpl_disconnect(self.cidrelease)
        self.point.figure.canvas.mpl_disconnect(self.cidmotion)



class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100, projection = None, subplots = 1):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.fig.set_tight_layout(True)
        if subplots == 1:
            self.axes = self.fig.add_subplot(111, projection=projection)
        elif subplots == 3:
            _ax1 = self.fig.add_subplot(311, projection=projection)
            _ax1.get_yaxis().set_visible(False)
            _ax1.tick_params(axis='x', colors='#FF3B3B')
            _ax2 = self.fig.add_subplot(312, projection=projection)
            _ax2.get_yaxis().set_visible(False)
            _ax2.tick_params(axis='x', colors='#01FF24')
            _ax3 = self.fig.add_subplot(313, projection=projection)
            _ax3.get_yaxis().set_visible(False)
            _ax3.tick_params(axis='x', colors='#3CD0FF')
            self.axes = [_ax1, _ax2, _ax3]
        super(MplCanvas, self).__init__(self.fig)

        self.setParent(parent)
        # To store the 3 draggable points
        self.list_points = []


    # TODO: there is apparently a better way to do this in matplotlib >3.3.1. When Python cna be updated, this can be changed
    # https://matplotlib.org/3.3.1/users/whats_new.html#gtk-qt-zoom-rectangle-now-black-and-white
    # change the zoom tool to use a white grid
    # from https://stackoverflow.com/questions/28599068/changing-the-edge-color-of-zoom-rect-in-matplotlib
    # copied source function from /Users/[user_name]/.pyenv/versions/3.7.6/lib/python3.7/site-packages/matplotlib/backends/backend_qt5.py
    def drawRectangle(self, rect):
        # Draw the zoom rectangle to the QPainter.  _draw_rect_callback needs
        # to be called at the end of paintEvent.
        if rect is not None:
            def _draw_rect_callback(painter):
                pen = QPen(QtCore.Qt.white, 1 / self._dpi_ratio,
                           QtCore.Qt.DotLine)
                painter.setPen(pen)
                painter.drawRect(*(pt / self._dpi_ratio for pt in rect))
        else:
            def _draw_rect_callback(painter):
                return
        self._draw_rect_callback = _draw_rect_callback
        self.update()

    def plotDraggablePoints(self, view, red, green, blue):

        """Plot and define the 3 draggable rectangles"""

        del(self.list_points[:])
        # assumes patches are in upper (upper) axis
        # a second upper axis is defined with the same range as the lower axis
        # this is required because event picking only applies to the upper axis, but the upper axis is not linear
        # non-linear upper axis may not handle movement events properly.
        for i in range(len(self.fig.axes[-1].patches)):
            self.fig.axes[-1].patches[0].remove()
        self.updateFigure()
        #QApplication.processEvents()
        if red is not None:
            self.list_points.append(DraggablePoint(self, view, red[0], red[1], red[2], red[3], 'r', label='_redBox'))
        if green is not None:
            self.list_points.append(DraggablePoint(self, view, green[0], green[1], green[2], green[3], 'g', label='_greenBox'))
        if blue is not None:
            self.list_points.append(DraggablePoint(self, view, blue[0], blue[1], blue[2], blue[3], 'b', label='_blueBox'))
        self.updateFigure()


    def plotDraggablePointsHist(self, view, red, green, blue, alpha=0.8):

        """Plot and define the 3 draggable rectangles"""

        del(self.list_points[:])
        # assumes patches are in upper (upper) axis
        # a second upper axis is defined with the same range as the lower axis
        # this is required because event picking only applies to the upper axis, but the upper axis is not linear
        # non-linear upper axis may not handle movement events properly.
        #QApplication.processEvents()
        if red is not None:
            for i in range(len(self.fig.axes[0].patches)):
                self.fig.axes[0].patches[0].remove()
            self.updateFigure()
            self.list_points.append(DraggablePoint(self, view, red[0][0], red[0][1], red[0][2], red[0][3], 'r', label='_redHistLow', multi=0, alpha=alpha))
            self.list_points.append(DraggablePoint(self, view, red[1][0], red[1][1], red[1][2], red[1][3], 'r', label='_redHistHigh', multi=0, alpha=alpha))
        if green is not None:
            for i in range(len(self.fig.axes[1].patches)):
                self.fig.axes[1].patches[0].remove()
            self.updateFigure()
            self.list_points.append(DraggablePoint(self, view, green[0][0], green[0][1], green[0][2], green[0][3], 'g', label='_greenHistLow', multi=1, alpha=alpha))
            self.list_points.append(DraggablePoint(self, view, green[1][0], green[1][1], green[1][2], green[1][3], 'g', label='_greenHistHigh', multi=1, alpha=alpha))
        if blue is not None:
            for i in range(len(self.fig.axes[2].patches)):
                self.fig.axes[2].patches[0].remove()
            self.updateFigure()
            self.list_points.append(DraggablePoint(self, view, blue[0][0], blue[0][1], blue[0][2], blue[0][3], 'b', label='_blueHistLow', multi=2, alpha=alpha))
            self.list_points.append(DraggablePoint(self, view, blue[1][0], blue[1][1], blue[1][2], blue[1][3], 'b', label='_blueHistHigh', multi=2, alpha=alpha))
        self.updateFigure()


    def clearFigure(self):

        """Clear the graph"""

        self.axes.clear()
        self.axes.grid(True)
        del(self.list_points[:])
        self.updateFigure()


    def updateFigure(self):

        """Update the graph. Necessary, to call after each plot"""

        self.draw()
