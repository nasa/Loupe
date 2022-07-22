from PyQt5 import QtCore, QtGui, QtWidgets

# based on https://stackoverflow.com/questions/60156142/how-to-use-qgraphicsviewrubberbanddrag
class GripItem(QtWidgets.QGraphicsPathItem):
    circle = QtGui.QPainterPath()
    circle.addEllipse(QtCore.QRectF(-10, -10, 15, 15))
    #square = QtGui.QPainterPath()
    #square.addRect(QtCore.QRectF(-15, -15, 30, 30))
    circle_select = QtGui.QPainterPath()
    circle_select.addEllipse(QtCore.QRectF(-10, -10, 15, 15))

    def __init__(self, annotation_item, index, _color):
        super(GripItem, self).__init__()
        self.m_annotation_item = annotation_item
        self.m_index = index
        self.color = _color

        self.setPath(GripItem.circle)
        # color of circles before reorienting them
        self.setBrush(QtGui.QColor(self.color[0], self.color[1], self.color[2], 150)) # magenta
        self.setPen(QtGui.QPen(QtGui.QColor(self.color[0], self.color[1], self.color[2], 150), 2))
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(11)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

    def hoverEnterEvent(self, event):
        self.setPath(GripItem.circle_select)
        # color of point when hovered over
        self.setBrush(QtGui.QColor(self.color[0], self.color[1], self.color[2], 150))
        super(GripItem, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setPath(GripItem.circle)
        self.setBrush(QtGui.QColor(self.color[0], self.color[1], self.color[2], 150))
        super(GripItem, self).hoverLeaveEvent(event)

    def mouseReleaseEvent(self, event):
        self.setSelected(False)
        super(GripItem, self).mouseReleaseEvent(event)

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.ItemPositionChange and self.isEnabled():
            self.m_annotation_item.movePoint(self.m_index, value)
        return super(GripItem, self).itemChange(change, value)


class PolygonAnnotation(QtWidgets.QGraphicsPolygonItem):
    def __init__(self, _color, parent=None):
        super(PolygonAnnotation, self).__init__(parent)
        self.m_points = []
        self.color = _color
        self.setZValue(10)
        self.setPen(QtGui.QPen(QtGui.QColor(_color[0], _color[1], _color[2], 150), 2))
        self.setAcceptHoverEvents(True)

        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges, True)

        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

        self.m_items = []

    def addPoint(self, p):
        self.m_points.append(p)
        self.setPolygon(QtGui.QPolygonF(self.m_points))
        item = GripItem(self, len(self.m_points) - 1, self.color)
        self.scene().addItem(item)
        self.m_items.append(item)
        item.setPos(p)
        return item

    def movePoint(self, i, p):
        if 0 <= i < len(self.m_points):
            self.m_points[i] = self.mapFromScene(p)
            self.setPolygon(QtGui.QPolygonF(self.m_points))

    def move_item(self, index, pos):
        if 0 <= index < len(self.m_items):
            item = self.m_items[index]
            item.setEnabled(False)
            item.setPos(pos)
            item.setEnabled(True)
            #self.m_points[index] = self.mapFromScene(pos)
            #self.setPolygon(QtGui.QPolygonF(self.m_points))

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.ItemPositionHasChanged:
            for i, point in enumerate(self.m_points):
                self.move_item(i, self.mapToScene(point))
        return super(PolygonAnnotation, self).itemChange(change, value)

    def hoverEnterEvent(self, event):
        self.setBrush(QtGui.QColor(self.color[0], self.color[1], self.color[2], 100))
        super(PolygonAnnotation, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setBrush(QtGui.QBrush(QtCore.Qt.NoBrush))
        super(PolygonAnnotation, self).hoverLeaveEvent(event)

