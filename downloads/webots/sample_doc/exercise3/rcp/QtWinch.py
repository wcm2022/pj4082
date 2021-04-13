"""PyQt5 widgets to render cartoons of winch and line systems.
"""

################################################################
# Written in 2018-2019 by Garth Zeglin <garthz@cmu.edu>

# To the extent possible under law, the author has dedicated all copyright
# and related and neighboring rights to this software to the public domain
# worldwide. This software is distributed without any warranty.

# You should have received a copy of the CC0 Public Domain Dedication along with this software.
# If not, see <http://creativecommons.org/publicdomain/zero/1.0/>.

################################################################

# for documentation on the PyQt5 API, see http://pyqt.sourceforge.net/Docs/PyQt5/index.html
from PyQt5 import QtCore, QtGui, QtWidgets

################################################################
class QtWinchCartoon(QtWidgets.QWidget):
    """Custom widget representing a single winch as a 2D cartoon view."""

    def __init__(self):
        super().__init__()
        self.setMinimumSize(QtCore.QSize(100, 100))
        self.setAutoFillBackground(True)

        # graphical state variables
        self.position = 0.0  # units are microsteps
        self.steps_per_rev = 3200  # KF used 800

        # Create a path representing the basic glyph.  The default coordinates
        # have +X to the right, +Y down.
        self.winch_symbol = QtGui.QPainterPath()
        self.winch_symbol.addEllipse(QtCore.QPointF(0.0, 0.0), 0.9, 0.9)  # center, rx, ry
        self.winch_symbol.moveTo( 0.25, -0.8)
        self.winch_symbol.lineTo( 0.00, -0.5)
        self.winch_symbol.lineTo(-0.25, -0.8)

        # finish initialization
        self.show()
        return

    def update_position(self, position):
        self.position = position
        self.repaint()

    def paintEvent(self, e):
        geometry = self.geometry()
        width = geometry.width()
        height = geometry.height()

        qp = QtGui.QPainter()
        qp.begin(self)
        # qp.fillRect(QtCore.QRectF(0, 0, width, height), QtCore.Qt.white)
        # qp.setRenderHint(QtGui.QPainter.Antialiasing)

        # set up a unit coordinate system centered in the visible area
        qp.save()
        scaling = width/2 if width < height else height/2
        qp.translate(QtCore.QPointF(width/2, height/2))
        qp.scale(scaling, scaling)

        # The default coordinate system rotation uses +Z pointing into the
        # screen; this changes sign so positive displacements are
        # counter-clockwise, i.e.  right-hand-rule on the vector pointing *out*
        # of the screen.  This rescales from microsteps to degrees.
        qp.rotate(-self.position*(360/self.steps_per_rev))

        if False:
            # draw the winch symbol
            pen = QtGui.QPen(QtCore.Qt.black)
            pen.setWidthF(0.1)
            qp.setPen(pen)
            qp.setBrush(QtCore.Qt.NoBrush)
            qp.drawPath(self.winch_symbol)
        else:
            # use simplified line graphics for better drawing speed
            pen = QtGui.QPen(QtCore.Qt.black)
            pen.setWidthF(0.05)
            qp.setPen(pen)
            qp.drawLine(QtCore.QPointF(0,0), QtCore.QPointF(0,-0.8))
            qp.drawRect(QtCore.QRectF(-0.2, -0.2, 0.4, 0.4))

        qp.restore()

        # draw the text annotation
        qp.drawText(10, height-4, "%d" % int(self.position))
        qp.end()

################################################################
class QtWinchSet(QtWidgets.QWidget):
    """Composite widget representing a set of winches as a 2D cartoon view."""

    def __init__(self, count=4):
        super().__init__()
        self._layout = QtWidgets.QHBoxLayout()
        self._winches = list()
        for winch in range(count):
            winch = QtWinchCartoon()
            self._layout.addWidget(winch)
            self._winches.append(winch)
        self.setLayout(self._layout)
        return

    def winches(self):
        """Return a list of QtWinch objects contained in the set."""
        return self._winches

################################################################
class QtWinchItem(QtWidgets.QGraphicsItem):
    """Custom QGraphicsItem representing a winch in a QGraphicsScene.  The color and radius can be configured so this can be used as a concentric ring with another, e.g. for showing actual and simulated positions in the same display."""

    def __init__(self, parent=None, location=(0,0), radius=40, color=QtCore.Qt.black, steps_per_rev=3200):
        super().__init__(parent)
        margin = radius + 10
        self.bounds = QtCore.QRectF(-margin, -margin, 2*margin, 2*margin)
        self.steps_per_rev = steps_per_rev

        # Enable a rendering cache pixel buffer for the element, using the
        # bounding rectangle to set the pixel size (e.g. 1 mm == 1 pixel).  This
        # may or may not improve performance.
        # self.setCacheMode(QtWidgets.QGraphicsItem.ItemCoordinateCache)

        self.setPos(*location)
        self.color = color
        self.radius = radius

        return

    def boundingRect(self):
        return self.bounds

    def paint(self, painter, options, widget):
        qp = painter

        # set up line drawing with no fill
        pen = QtGui.QPen(self.color)
        pen.setWidthF(6.0)
        qp.setPen(pen)
        qp.setBrush(QtCore.Qt.NoBrush)

        # draw the circle representing the capstan
        qp.drawEllipse(QtCore.QPointF(0, 0), self.radius, self.radius)

        # draw a line indicating the zero angle so rotation is visible
        qp.drawLine(QtCore.QPointF(0, 0), QtCore.QPointF(0, -self.radius))
        return

    def update_position(self, position):
        """Update the rotation angle for the winch.  Units are microsteps, which can be configured using the steps_per_rev attribute."""
        self.setRotation(-position*(360/self.steps_per_rev))
        return

################################################################
class QtWinchSetItem(QtWidgets.QGraphicsItem):
    """Custom QGraphicsItem representing a set of winches in a QGraphicsScene."""

    def __init__(self, parent=None, location=(0,0)):
        super().__init__(parent)
        self.setFlag(QtWidgets.QGraphicsItem.ItemHasNoContents)
        self.setPos(*location)

        self.targets = []
        self.winches = []
        self.target_displays = []
        self.winch_displays  = []
        for i in range(4):
            loc = (200 * i, 0)
            target = QtWinchItem(parent=self, location=loc, radius=60, color=QtCore.Qt.green)
            winch  = QtWinchItem(parent=self, location=loc, radius=40, color=QtCore.Qt.black)
            self.targets.append(target)
            self.winches.append(winch)

            target_display = QtWidgets.QGraphicsSimpleTextItem("0", self)
            target_display.setBrush(QtGui.QBrush(QtCore.Qt.green))
            target_display.setPos(200*i - 50, 70)
            target_display.setFont(QtGui.QFont("Sans Serif", 20))
            self.target_displays.append(target_display)

            winch_display = QtWidgets.QGraphicsSimpleTextItem("0", self)
            winch_display.setPos(200*i + 25, 70)
            winch_display.setFont(QtGui.QFont("Sans Serif", 20))
            self.winch_displays.append(winch_display)
            
        return
    
    def boundingRect(self):
        return QtCore.QRectF()

    def paint(self, painter, options, widget):
        pass

    def update_targets(self, positions):
        """Update the target rotation angles for the winch set.  Units are microsteps, which can be configured using the steps_per_rev attribute."""
        for pos, target, target_display in zip(positions, self.targets, self.target_displays):
            target.update_position(pos)
            target_display.setText("%d" % pos)
        return

    def update_winches(self, positions):
        """Update the winch rotation angles for the winch set.  Units are microsteps, which can be configured using the steps_per_rev attribute."""
        for pos, winch, winch_display in zip(positions, self.winches, self.winch_displays):
            winch.update_position(pos)
            winch_display.setText("%d" % pos)
        return

################################################################
