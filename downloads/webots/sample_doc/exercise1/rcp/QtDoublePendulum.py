"""PyQt5 widgets to render a double-pendulum cartoon.
"""

################################################################
# Written in 2019 by Garth Zeglin <garthz@cmu.edu>

# To the extent possible under law, the author has dedicated all copyright
# and related and neighboring rights to this software to the public domain
# worldwide. This software is distributed without any warranty.

# You should have received a copy of the CC0 Public Domain Dedication along with this software.
# If not, see <http://creativecommons.org/publicdomain/zero/1.0/>.

################################################################
import math, logging

import numpy

# for documentation on the PyQt5 API, see http://pyqt.sourceforge.net/Docs/PyQt5/index.html
from PyQt5 import QtCore, QtGui, QtWidgets

# set up logger for module
log = logging.getLogger('QtDoublePendulum')

# filter out most logging; the default is NOTSET which passes along everything
# log.setLevel(logging.WARNING)

################################################################
class QtDoublePendulum(QtWidgets.QWidget):
    """Custom widget representing a double pendulum."""

    def __init__(self):
        super().__init__()
        self.setMinimumSize(QtCore.QSize(100, 100))
        self.setAutoFillBackground(True)

        # configure a white fill around the image
        pal = QtGui.QPalette()
        pal.setColor(QtGui.QPalette.Background, QtCore.Qt.white)
        self.setPalette(pal)

        # graphical state variables
        self.positions = [0.0, 0.0]  # units are radians (pi radians = 180 degrees)

        # finish initialization
        self.show()
        return

    def update_positions(self, positions):
        """Update the joint angles for the double pendulum cartoon.  Angles are in radians, with zero defined pointing straight down, and CCW positive rotations.

        :param positions: an array or ndarray with at least two elements [q0 q1]
        """
        self.positions[0:2] = positions[0:2]
        return

    # === Qt API methods ============================================================
    # Subclass implementation of parent QWidget class callback to repaint the graphics.
    def paintEvent(self, e):
        geometry = self.geometry()
        view_width = geometry.width()
        view_height = geometry.height()

        # clear the background
        qp = QtGui.QPainter()
        qp.begin(self)
        qp.fillRect(QtCore.QRectF(0, 0, view_width, view_height), QtCore.Qt.white)
        qp.setRenderHint(QtGui.QPainter.Antialiasing)

        # Define minimum visible area in model-coordinate millimeters.
        scene_width   = 1400
        scene_height  = scene_width

        # Set up a coordinate system scaled to real-world millimeters, centered
        # in the visible area, keeping the minimum visible area in view.
        scene_aspect  = scene_width / scene_height
        view_aspect = view_width / view_height
        if scene_aspect > view_aspect:
            scaling = view_width / scene_width
        else:
            scaling = view_height/scene_height
        qp.save()
        qp.translate(QtCore.QPointF(view_width/2, view_height/2))
        qp.scale(scaling, scaling)

        # set up red fill with black outlines
        pen = QtGui.QPen(QtCore.Qt.black)
        pen.setWidthF(3.0)
        qp.setPen(pen)
        brush = QtGui.QBrush(QtCore.Qt.red)
        qp.setBrush(brush)

        # draw the two pendulum links
        qp.save()
        qp.rotate(-self.positions[0] * 180/math.pi)                                            # hub rotation
        qp.drawRoundedRect(QtCore.QRectF(-25, 0, 50, 300), 6.0, 6.0, QtCore.Qt.AbsoluteSize)  # first link
        qp.drawEllipse(QtCore.QPointF(0, 0), 40, 40)                                          # center hub
        qp.translate(0, 300)                                                                  # translate to elbow
        qp.rotate(-self.positions[1] * 180/math.pi)                                            # elbow rotation
        qp.drawRoundedRect(QtCore.QRectF(-25, 0, 50, 300), 6.0, 6.0, QtCore.Qt.AbsoluteSize)  # second link
        qp.drawEllipse(QtCore.QPointF(0, 0), 20, 20)                                          # elbow hub
        qp.restore()

        # restore the initial unscaled coordinates
        qp.restore()
        qp.end()

################################################################
class _DblPendulumLink(QtWidgets.QGraphicsItem):

    def __init__(self, parent = None, length=300):
        super().__init__(parent)
        self.length = length
        self.bounds = QtCore.QRectF(-50, -50, 100, length + 50)
        # Enable a rendering cache pixel buffer for the element, using the
        # bounding rectangle to set the pixel size (e.g. 1 mm == 1 pixel).  This
        # may or may not improve performance.
        # self.setCacheMode(QtWidgets.QGraphicsItem.ItemCoordinateCache)
        return

    def boundingRect(self):
        return self.bounds

    def paint(self, painter, options, widget):
        qp = painter

        # set up red fill with black outlines
        pen = QtGui.QPen(QtCore.Qt.black)
        pen.setWidthF(3.0)
        qp.setPen(pen)
        brush = QtGui.QBrush(QtCore.Qt.red)
        qp.setBrush(brush)

        # draw the link
        qp.drawRoundedRect(QtCore.QRectF(-25, 0, 50, self.length), 6.0, 6.0, QtCore.Qt.AbsoluteSize)

        # draw the joint hub
        qp.drawEllipse(QtCore.QPointF(0, 0), 40, 40)
        return

################################################################
class QtDoublePendulumItem(QtWidgets.QGraphicsItem):
    """Custom QGraphicsItem representing a double-pendulum in a QGraphicsScene."""

    def __init__(self, parent=None, l1=300, l2=300):
        super().__init__(parent)
        self.setFlag(QtWidgets.QGraphicsItem.ItemHasNoContents)

        self.upper_link = _DblPendulumLink(self, length=l1)
        self.lower_link = _DblPendulumLink(self, length=l2)
        self.upper_link.setPos(0, 0)
        self.lower_link.setPos(0, -l1)
        self.l1 = l1
        self.l2 = l2
        return

    def boundingRect(self):
        return QtCore.QRectF()

    def paint(self, painter, options, widget):
        pass

    def update_positions(self, positions):
        """Update the joint angles for the double pendulum cartoon.  Angles are in radians, with zero defined pointing straight down, and CCW positive rotations.

        :param positions: an array or ndarray with at least two elements [q0 q1]
        """

        q0 = -positions[0]
        q1 = -positions[1]

        self.upper_link.setRotation(q0 * 180/math.pi)
        self.lower_link.setRotation((q0+q1) * 180/math.pi)
        self.lower_link.setPos(-self.l1 * math.sin(q0), self.l1*math.cos(q0))
        return

################################################################
class QtMarkerItem(QtWidgets.QGraphicsItem):

    def __init__(self, parent = None):
        super().__init__(parent)
        self.bounds = QtCore.QRectF(-25, -25, 50, 50)
        return

    def boundingRect(self):
        return self.bounds

    def paint(self, painter, options, widget):
        qp = painter

        # set up green fill with black outlines
        pen = QtGui.QPen(QtCore.Qt.black)
        pen.setWidthF(3.0)
        qp.setPen(pen)
        brush = QtGui.QBrush(QtCore.Qt.green)
        qp.setBrush(brush)

        # draw the marker as a circle
        qp.drawEllipse(QtCore.QPointF(0, 0), 20, 20)
        return

################################################################    
