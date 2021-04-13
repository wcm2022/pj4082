"""A PyQt5 GUI to simulate an Akai MPD218 MIDI controller.  The actual controller
has pressure-sensitive pads, so the simulation is approximate, this is only
intended for testing offline without the physical controller.
"""
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

# for documentation on the PyQt5 API, see http://pyqt.sourceforge.net/Docs/PyQt5/index.html
from PyQt5 import QtCore, QtGui, QtWidgets

# set up logger for module
log = logging.getLogger('QtMPD218')

# filter out most logging; the default is NOTSET which passes along everything
log.setLevel(logging.WARNING)

################################################################
class QtMPD218(QtWidgets.QWidget):
    """A composite window providing a simulated MPD218 drum pad interface.
    Generated MIDI events are emitted as normal Python callbacks to a user-provided MIDI processor object.
    """

    def __init__(self):
        super(QtMPD218,self).__init__()

        self.processor = None

        # create the GUI elements
        self.setupUi()

        # start the channel pressure timer
        self.timer = QtCore.QTimer()
        self.timer.start(100)  # units are milliseconds
        self.timer.timeout.connect(self.timer_tick)
        return

    def connect_midi_processor(self, processor):
        self.processor = processor

    # ------------------------------------------------------------------------------------------------
    def setupUi(self):
        self.mainLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.setContentsMargins(-1, -1, -1, 9)
        self.setLayout(self.mainLayout)

        # generate an array of dial widgets
        self.dialGrid = QtWidgets.QGridLayout()
        self.dials = list()
        for i in range(6):
            row = i // 2
            col = i % 2
            dial = QtWidgets.QDial()
            dial.setMinimumSize(QtCore.QSize(0, 30))
            dial.setMaximum(127)
            self.dialGrid.addWidget(dial, row, col, 1, 1)
            dial.valueChanged['int'].connect(functools.partial(self.dialMoved, i))
            self.dials.append(dial)

        # add the bank selects at the bottom of the dial grid
        self.controlBank = QtWidgets.QComboBox()
        self.padBank     = QtWidgets.QComboBox()
        for item in ["A", "B", "C"]:
            self.controlBank.addItem(item)
            self.padBank.addItem(item)

        self.controlLabel = QtWidgets.QLabel()
        self.controlLabel.setText("CTRL BANK")
        self.padLabel = QtWidgets.QLabel()
        self.padLabel.setText("PAD BANK")
        self.dialGrid.addWidget(self.controlBank, 3, 0, 1, 1)
        self.dialGrid.addWidget(self.padBank, 3, 1, 1, 1)
        self.dialGrid.addWidget(self.controlLabel, 4, 0, 1, 1)
        self.dialGrid.addWidget(self.padLabel, 4, 1, 1, 1)

        self.mainLayout.addLayout(self.dialGrid)

        # generate a grid of buttons to represent the pads
        self.buttonGrid = QtWidgets.QGridLayout()
        self.pushbuttons = list()
        columns = 4
        for button in range(16):
            row = 3 - (button // columns)
            col = button % columns
            title = str(button+1)
            pushButton = QtWidgets.QPushButton()
            pushButton.setMinimumSize(QtCore.QSize(80, 80))
            self.buttonGrid.addWidget(pushButton, row, col, 1, 1)
            pushButton.setText(title)
            pushButton.pressed.connect(functools.partial(self.buttonPressed, button))
            pushButton.released.connect(functools.partial(self.buttonReleased, button))
            self.pushbuttons.append(pushButton)
        self.mainLayout.addLayout(self.buttonGrid)

        # add a velocity slider on the right
        self.velocitySlider = QtWidgets.QSlider()
        self.velocitySlider.setToolTip('Pad Velocity')
        self.velocitySlider.setMinimum(1)
        self.velocitySlider.setMaximum(127)
        self.velocitySlider.setValue(64)
        self.mainLayout.addWidget(self.velocitySlider)

        return

    # --------------------------------------------------------------------------------------------------
    def buttonPressed(self, button):
        bankname = self.padBank.currentText()
        log.debug("Pad %d on bank %s pressed.", button+1, bankname)
        if self.processor is not None:
            bank = self.padBank.currentIndex()
            vel = self.velocitySlider.value()
            self.processor.note_on(10, 36 + button + 16*bank, vel)

    def buttonReleased(self, button):
        bankname = self.padBank.currentText()
        log.debug("Pad %d on bank %s released.", button+1, bankname)
        if self.processor is not None:
            bank = self.padBank.currentIndex()
            self.processor.note_off(10, 36 + button + 16*bank, 0)

    def dialMoved(self, dial, value):
        bankname = self.controlBank.currentText()
        log.debug("Dial %d on bank %s moved to %d", dial+1, bankname, value)

        # the MPD218 has a non-contiguous controller channel mapping
        bank = self.controlBank.currentIndex()
        if bank == 0:
            cc = (3, 9, 12, 13, 14, 15)[dial]
        else:
            cc = 16 + dial + 6 * (bank-1)

        if self.processor is not None:
            self.processor.control_change(1, cc, value)

    # The MPD218 delivers channel pressure events as long as any pad is pressed.
    def timer_tick(self):
        if self.processor is not None:
            if any((button.isDown() for button in self.pushbuttons)):
                vel = self.velocitySlider.value()
                self.processor.channel_pressure(10, vel)

################################################################
