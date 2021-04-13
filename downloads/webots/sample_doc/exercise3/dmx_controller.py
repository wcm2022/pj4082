#!/usr/bin/env python3
"""A PyQt5 GUI providing sliders to control DMX outputs via an Enttec DMX USB
Pro.  This is intended for testing DMX devices and as an example for generating
DMX output.
"""
################################################################
# Written in 2018 by Garth Zeglin <garthz@cmu.edu>

# To the extent possible under law, the author has dedicated all copyright
# and related and neighboring rights to this software to the public domain
# worldwide. This software is distributed without any warranty.

# You should have received a copy of the CC0 Public Domain Dedication along with this software.
# If not, see <http://creativecommons.org/publicdomain/zero/1.0/>.

################################################################
# standard Python libraries
from __future__ import print_function
import os, sys, struct, time, logging, functools, platform, argparse
import numpy as np

# for documentation on the PyQt5 API, see http://pyqt.sourceforge.net/Docs/PyQt5/index.html
from PyQt5 import QtCore, QtGui, QtWidgets, QtSerialPort

# set up logger for module
log = logging.getLogger('dmx_controller')

################################################################
class ButtonBox(QtWidgets.QMainWindow):
    """A custom main window which provides all GUI controls."""

    def __init__( self, *args, **kwargs):
        super(ButtonBox,self).__init__()

        # create the GUI elements
        self.setupUi()
        
        # finish initialization
        self.show()

        return

    # ------------------------------------------------------------------------------------------------
    def setupUi(self):
        self.setWindowTitle("DMX Controller")
        self.resize(500, 200)

        self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralwidget)
        self.mainLayout = QtWidgets.QVBoxLayout(self.centralwidget)

        # generate fields for configuring the DMX output
        self.outputSelectorLayout = QtWidgets.QHBoxLayout()
        self.outputSelectorLabel = QtWidgets.QLabel()
        self.outputSelectorLabel.setText("DMX output port:")
        self.outputSelector = QtWidgets.QComboBox()
        self.outputSelector.addItem("<no port selected>")
        for port in QtSerialPort.QSerialPortInfo.availablePorts():
            self.outputSelector.insertItem(0, port.portName())            
        self.outputSelectorLayout.addWidget(self.outputSelectorLabel)
        self.outputSelectorLayout.addWidget(self.outputSelector)
        self.outputSelector.activated['QString'].connect(self.chooseOutput)
        self.mainLayout.addLayout(self.outputSelectorLayout)

        # generate an array of vertical sliders        
        self.sliderLayout = QtWidgets.QHBoxLayout()
        self.sliderLayout.setContentsMargins(-1, -1, -1, 9)
        self.mainLayout.addLayout(self.sliderLayout)
        self.sliders = list()
        for i in range(24):
            box = QtWidgets.QVBoxLayout()
            slider = QtWidgets.QSlider()
            slider.setMinimumSize(QtCore.QSize(20, 60))
            slider.setMaximum(255)
            slider.setOrientation(QtCore.Qt.Vertical)
            # self.verticalLayout.addWidget(slider)
            slider.valueChanged['int'].connect(functools.partial(self.sliderMoved, i))
            self.sliders.append(slider)
            label = QtWidgets.QLabel()
            label.setText("%d" % (i+1))
            box.addWidget(slider)
            box.addWidget(label)
            self.sliderLayout.addLayout(box)

        # add some global change buttons
        self.buttonLayout = QtWidgets.QHBoxLayout()
        
        button = QtWidgets.QPushButton()
        button.setText("All Off")
        button.pressed.connect(functools.partial(self.buttonPressed, "black"))
        self.buttonLayout.addWidget(button)

        button = QtWidgets.QPushButton()
        button.setText("All Half")
        button.pressed.connect(functools.partial(self.buttonPressed, "gray"))
        self.buttonLayout.addWidget(button)

        button = QtWidgets.QPushButton()
        button.setText("All Full")
        button.pressed.connect(functools.partial(self.buttonPressed, "white"))
        self.buttonLayout.addWidget(button)

        self.mainLayout.addLayout(self.buttonLayout)
        
        # the status bar shows text at the bottom of the window
        self.statusbar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.statusbar)

        # set up the main menu
        if False:
            self.actionQuit = QtWidgets.QAction(self)
            self.actionQuit.setText("Quit")
            self.actionQuit.setShortcut("Ctrl+Q")
            self.actionQuit.triggered.connect(self.quitSelected)
            self.menubar = QtWidgets.QMenuBar(self)
            self.menubar.setGeometry(QtCore.QRect(0, 0, 500, 22))
            self.menubar.setNativeMenuBar(False)
            self.menubar.setObjectName("menubar")
            self.menuTitle = QtWidgets.QMenu(self.menubar)
            self.setMenuBar(self.menubar)
            self.menuTitle.addAction(self.actionQuit)
            self.menubar.addAction(self.menuTitle.menuAction())
            self.menuTitle.setTitle("File")

        return

    # --- window and qt event processing -------------------------------------------------------------
    def show_status(self, string):
        self.statusbar.showMessage(string)

    def write(self, string):
        """Write output to the status bar."""
        self.statusbar.showMessage(string)
        return

    def quitSelected(self):
        self.write("User selected quit.")
        self.close()

    def closeEvent(self, event):
        self.write("Received window close event.")
        super(ButtonBox,self).closeEvent(event)

    # --------------------------------------------------------------------------------------------------
    def chooseOutput(self, name):
        """Called when the user selects a DMX output port."""
        self.show_status("Opening %s." % name)
        self.main.open_dmx_output(name)
        return
    
    def sliderMoved(self, slider, value):
        self.write("Slider %s moved to %d" % (slider+1, value))
        self.main.set_dmx_channel(slider, value)
        return

    def buttonPressed(self, name):
        value = {'black' : 0, 'gray' : 127, 'white' : 255}.get(name)
        if value is not None:
            for slider in self.sliders:
                slider.setValue(value)
        
################################################################
class MainApp(object):
    """Main application object holding any non-GUI related state."""

    def __init__(self):
        # create the interface window
        self.window = ButtonBox()
        self.window.main = self
        self.dmxport = None

        # Initialize a default DMX 'universe', i.e. an addressable space of
        # 8-bit registers.  The Enttec requires a minimum universe size of 25.
        self.universe = np.zeros((25), dtype=np.uint8)
        return

    def open_dmx_output(self, name):
        if self.dmxport is not None:
            self.dmxport.close()
            self.dmxport = None
            
        self.dmxport = QtSerialPort.QSerialPort()
        self.dmxport.setBaudRate(115200)
        self.dmxport.setPortName(name)
        if self.dmxport.open(QtCore.QIODevice.ReadWrite):
            self.window.write("Opened DMX port %s" % self.dmxport.portName())
            self.dmxport.readyRead.connect(self.dmx_data_received)
            
        else:
            self.window.write("Error opening DMX port %s" % self.dmxport.portName())
            self.dmxport = None

    def dmx_data_received(self):
        data = self.dmxport.readAll()
        if len(data) > 0:
            log.info("Received %d bytes from DMX device." % len(data))
        return

    def set_dmx_channel(self, channel, value):
        self.universe[channel] = value
        self.send_universe()
        
    def send_universe(self):
        """Issue a DMX universe update."""
        if self.dmxport is None:
            log.warning("DMX port not open for output.")
        else:
            message = np.ndarray((6 + self.universe.size), dtype=np.uint8)
            message[0:2] = [126, 6] # Send DMX Packet header
            message[2]   = (self.universe.size+1) % 256   # data length LSB
            message[3]   = (self.universe.size+1) >> 8    # data length MSB
            message[4]   = 0                              # zero 'start code' in first universe position
            message[5:5+self.universe.size] = self.universe
            message[-1]  = 231 # end of message delimiter
            log.debug("Sending to DMX: '%s'", message)
            self.dmxport.write(message.tobytes())
        return
            
################################################################

def main():
    # initialize the Qt system itself
    app = QtWidgets.QApplication(sys.argv)

    # create the main application controller
    main = MainApp()

    # run the event loop until the user is done
    log.info("Starting event loop.")
    sys.exit(app.exec_())

################################################################
# Main script follows.  This sequence is executed when the script is initiated from the command line.

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='Enable debugging logging to console.')
    args = parser.parse_args()

    if args.debug:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter('%(levelname)s:%(name)s: %(message)s'))
        logging.getLogger().addHandler(console_handler)
        logging.getLogger().setLevel(logging.DEBUG)

    main()
