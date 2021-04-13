"""PyQt5 GUI objects for DMX lighting control and display."""
################################################################
# Written in 2018-2019 by Garth Zeglin <garthz@cmu.edu>

# To the extent possible under law, the author has dedicated all copyright
# and related and neighboring rights to this software to the public domain
# worldwide. This software is distributed without any warranty.

# You should have received a copy of the CC0 Public Domain Dedication along with this software.
# If not, see <http://creativecommons.org/publicdomain/zero/1.0/>.

################################################################
# standard Python libraries
from __future__ import print_function
import logging, functools
import numpy as np

# for documentation on the PyQt5 API, see http://pyqt.sourceforge.net/Docs/PyQt5/index.html
from PyQt5 import QtCore, QtGui, QtWidgets

# set up logger for module
log = logging.getLogger('QtDMX')

# filter out most logging; the default is NOTSET which passes along everything
# log.setLevel(logging.WARNING)

################################################################
class QtDMXControls(QtWidgets.QWidget):
    """A composite window providing a set of DMX channel sliders.

    :param channels: optional count of channels to control, defaults to 12
    :param callback: optional callable which receives (channel, value) arguments
    """

    def __init__(self, channels=12, callback=None):
        super(QtDMXControls,self).__init__()
        self.channels = channels  # number of visible channels
        self.callback = callback

        # create the GUI elements
        self._setupUi()
        self.show()
        return

    def connect_callback(self, callback):
        """Connect a callback to receive slider updates as (channel, value) arguments."""
        self.callback = callback

    def set_channel_count(self, channels):
        """Adjust the UI for a different number of DMX channels."""
        if self.channels > channels:   # if fewer need to be visible
            log.debug("Hiding extra DMX channel strips.")
            total = len(self.strips)
            for i in range(channels, total):
                self.strips[i].hide()
            self.channels = channels

        elif self.channels < channels:  # if more need to be visible
            total = len(self.strips)
            if total > self.channels:
                log.debug("Unhiding DMX channel strips.")
                for i in range(self.channels, total):
                    self.strips[i].show()
            if channels > total:
                log.debug("Adding more DMX channel strips.")
                for i in range(total, channels):
                    self.sliderLayout.addWidget(self._make_channel_strip(i))
            self.channels = channels
            self.show()
        return

    def get_channel_count(self):
        return self.channels

    # ------------------------------------------------------------------------------------------------
    def _make_channel_strip(self, i):
        channel_strip = QtWidgets.QWidget()
        box = QtWidgets.QVBoxLayout()
        channel_strip.setLayout(box)
        slider = QtWidgets.QSlider()
        slider.setMinimumSize(QtCore.QSize(20, 60))
        slider.setMaximum(255)
        slider.setOrientation(QtCore.Qt.Vertical)
        slider.valueChanged['int'].connect(functools.partial(self._sliderMoved, i))
        self.sliders.append(slider)
        label = QtWidgets.QLabel()
        label.setText("%d" % (i+1))
        box.addWidget(slider)
        box.addWidget(label)
        self.strips.append(channel_strip)
        return channel_strip

    def _setupUi(self):
        # create the overall vertical layout
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.setContentsMargins(-1, -1, -1, 9)
        self.setLayout(self.mainLayout)

        # create a scrollable area to hold the channel strips, since a large setup can easily exceed the screen width
        self.scrollArea = QtWidgets.QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.sliderWidget = QtWidgets.QWidget()
        self.sliderLayout = QtWidgets.QHBoxLayout()
        self.sliderLayout.setContentsMargins(-1, -1, -1, 9)
        self.sliderWidget.setLayout(self.sliderLayout)
        self.scrollArea.setWidget(self.sliderWidget)
        self.mainLayout.addWidget(self.scrollArea)

        # generate an array of vertical 'channel strips'
        self.sliders = list()
        self.strips = list()
        for i in range(self.channels):
            channel_strip = self._make_channel_strip(i)
            self.sliderLayout.addWidget(channel_strip)

        # add some global change buttons
        self.buttonLayout = QtWidgets.QHBoxLayout()

        button = QtWidgets.QPushButton()
        button.setText("All Off")
        button.pressed.connect(functools.partial(self._buttonPressed, "black"))
        self.buttonLayout.addWidget(button)

        button = QtWidgets.QPushButton()
        button.setText("All Half")
        button.pressed.connect(functools.partial(self._buttonPressed, "gray"))
        self.buttonLayout.addWidget(button)

        button = QtWidgets.QPushButton()
        button.setText("All Full")
        button.pressed.connect(functools.partial(self._buttonPressed, "white"))
        self.buttonLayout.addWidget(button)

        self.mainLayout.addLayout(self.buttonLayout)

        return

    # --------------------------------------------------------------------------------------------------
    def _sliderMoved(self, slider, value):
        # log.debug("DMX slider %s moved to %d", slider+1, value)
        if self.callback is not None:
            self.callback(slider, value)
        return

    def _buttonPressed(self, name):
        value = {'black' : 0, 'gray' : 127, 'white' : 255}.get(name)
        if value is not None:
            for slider in self.sliders:
                slider.setValue(value)
        return
    # --------------------------------------------------------------------------------------------------
    def set_channel(self, channel, value):
        """Change the position and value of a channel slider without issuing callbacks.
        This allows the set of sliders to be used as an output status display
        without creating infinite call loops.
        """
        if channel < len(self.sliders):
            slider = self.sliders[channel]
            blocked = slider.blockSignals(True)
            slider.setValue(value)
            slider.blockSignals(blocked)

    def set_channels(self, start, values):
        """Change the position and value of a set of channel sliders without issuing
        callbacks.  This allows the set of sliders to be used as an output
        status display without creating infinite call loops.
        """
        for i, value in enumerate(values):
            self.set_channel(start + i, value)

################################################################
class QtDMXColors(QtWidgets.QWidget):
    """A graphical widget to display a set of RGB color fields.  Note that the
    relationship between DMX channels and fixture colors depends on the specific
    fixtures and assigned addresses, so this mapping must be handled in user
    code.

    :param fixtures: optional number of simulated fixtures, defaults to 3
    """

    def __init__(self, fixtures=3):
        super().__init__()
        self.set_fixture_count(fixtures)
        return

    def set_fixture_count(self, fixtures):
        self._colors = np.zeros((fixtures, 3), dtype=np.uint8)
        self.setMinimumSize(QtCore.QSize(40*fixtures, 40))

    def get_fixture_count(self):
        return len(self._colors)

    def set_channel(self, fixture, channel, value):
        """Change a single color channel within a single fixture."""
        self._colors[fixture][channel] = value
        self.repaint()
        return

    def set_color(self, fixture, color):
        """Change the color of a single fixture."""
        self._colors[fixture] = color
        self.repaint()
        return

    def set_colors(self, colors):
        numcolors = min(len(colors), len(self._colors))
        for fixture in range(numcolors):
            self._colors[fixture] = colors[fixture]
        self.repaint()
        return

    def paintEvent(self, e):
        geometry = self.geometry()
        width = geometry.width()
        height = geometry.height()
        qp = QtGui.QPainter()
        qp.begin(self)
        area_width = int(width / len(self._colors))
        for i, color in enumerate(self._colors):
            x = i*area_width
            qp.fillRect(QtCore.QRect(x+2, 0, area_width-4, height), QtGui.QColor(color[0], color[1], color[2], 255))
        qp.end()
        return
