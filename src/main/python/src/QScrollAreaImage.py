from PyQt5 import QtCore, QtWidgets

class QScrollAreaImage(QtWidgets.QScrollArea):
    def __init__(self, view):
        super().__init__()
        self.scrollArea = QtWidgets.QScrollArea()
        #self.installEventFilter(self)
        self._view = view

    def eventFilter(self, QObject, QEvent):
        if self._view.imageACI is not None:
            if self.underMouse() and not self._view.imageACI.underMouse() and QEvent.type() == QtCore.QEvent.Wheel:
                return False
            else:
                return True
        else:
            return False