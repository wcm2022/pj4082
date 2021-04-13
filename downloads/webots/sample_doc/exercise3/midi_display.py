#!/usr/bin/env python3
"""A utility to receive MIDI messages and display them in a PyQt5 GUI text box."""
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
import os, sys, struct, time, logging, functools, queue

# for documentation on the PyQt5 API, see http://pyqt.sourceforge.net/Docs/PyQt5/index.html
from PyQt5 import QtCore, QtGui, QtWidgets, QtNetwork

# for documentation on python-rtmidi: https://pypi.org/project/python-rtmidi/
import rtmidi

################################################################
class MIDIDisplay(QtWidgets.QMainWindow):
    """A custom main window which provides all GUI controls."""

    def __init__( self, *args, **kwargs):
        super(MIDIDisplay,self).__init__()

        # create the GUI elements
        self.setupUi()

        # finish initialization
        self.show()

        # manage the console output across threads
        self.console_queue = queue.Queue()
        self.console_timer = QtCore.QTimer()
        self.console_timer.timeout.connect(self._poll_console_queue)
        self.console_timer.start(50)  # units are milliseconds
        
        return

    # ------------------------------------------------------------------------------------------------
    def setupUi(self):
        self.setWindowTitle("MIDI Display")
        self.resize(500, 300)

        self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralwidget)
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setContentsMargins(-1, -1, -1, 9) # left, top, right, bottom

        # generate fields for configuring the MIDI listener
        self.inputSelectorLayout = QtWidgets.QHBoxLayout()
        self.inputSelectorLabel = QtWidgets.QLabel()
        self.inputSelectorLabel.setText("MIDI source:")
        self.inputSelector = QtWidgets.QComboBox()
        self.inputSelector.addItem("<no source selected>")
        self.inputSelectorLayout.addWidget(self.inputSelectorLabel)
        self.inputSelectorLayout.addWidget(self.inputSelector)
        self.verticalLayout.addLayout(self.inputSelectorLayout)
        self.inputSelector.activated['QString'].connect(self.chooseInput)
        
        # generate a text area
        self.consoleOutput = QtWidgets.QPlainTextEdit()
        self.consoleOutput.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.verticalLayout.addWidget(self.consoleOutput)

        # set up the status bar which appears at the bottom of the window
        self.statusbar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.statusbar)

        # set up the main menu
        self.menubar = QtWidgets.QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 500, 22))
        self.menubar.setNativeMenuBar(False)
        self.menubar.setObjectName("menubar")
        self.menuTitle = QtWidgets.QMenu(self.menubar)
        self.setMenuBar(self.menubar)
        self.actionQuit = QtWidgets.QAction(self)
        self.menuTitle.addAction(self.actionQuit)
        self.menubar.addAction(self.menuTitle.menuAction())
        self.menuTitle.setTitle("File")
        self.actionQuit.setText("Quit")
        self.actionQuit.setShortcut("Ctrl+Q")
        self.actionQuit.triggered.connect(self.quitSelected)

        return

    # --- window and qt event processing -------------------------------------------------------------
    def show_status(self, string):
        self.statusbar.showMessage(string)

    def _poll_console_queue(self):
        """Write any queued console text to the console text area from the main thread."""
        while not self.console_queue.empty():
            string = str(self.console_queue.get())
            self.consoleOutput.appendPlainText(string)
        return
    
    def write(self, string):
        """Write output to the console text area in a thread-safe way.  Qt only allows
        calls from the main thread, but the service routines run on separate threads."""
        self.console_queue.put(string)
        return

    def quitSelected(self):
        self.write("User selected quit.")
        self.close()

    def closeEvent(self, event):
        self.write("Received window close event.")
        super(MIDIDisplay,self).closeEvent(event)

    # --------------------------------------------------------------------------------------------------
    def chooseInput(self, name):
        """Called when the user selects a MIDI source."""
        self.show_status("Listening to %s." % name)
        self.main.open_input(name)
        return

################################################################
class MainApp(object):
    """Main application object holding any non-GUI related state."""

    def __init__(self):

        # global state
        self.listener_address = "localhost"
        self.listener_portnum = 3761
        self.port = None

        # create the interface window
        self.window = MIDIDisplay()
        self.window.main = self

        # Initialize the MIDI input system and read the currently available ports.
        self.midi_in = rtmidi.MidiIn()
        self.midi_ports = self.midi_in.get_ports()

        for port in self.midi_ports:
            self.window.inputSelector.addItem(port)

        self.window.show_status("Please choose a source to display MIDI.")
        return

    def open_input(self, name):
        if self.midi_in.is_port_open():
            self.midi_in.close_port()
            self.midi_in = rtmidi.MidiIn()
            self.midi_ports = self.midi_in.get_ports()
            
        idx = self.midi_ports.index(name)
        self.midi_in.open_port(idx)
        self.midi_in.set_callback(self.midi_received)

    def midi_received(self, data, unused):
        msg, delta_time = data
        self.window.write("%f: %s" % (delta_time, str(msg)))

################################################################

def main():
    # initialize the Qt system itself
    app = QtWidgets.QApplication(sys.argv)

    # create the main application controller
    main = MainApp()

    # run the event loop until the user is done
    logging.info("Starting event loop.")
    sys.exit(app.exec_())

################################################################
# Main script follows.  This sequence is executed when the script is initiated from the command line.

if __name__ == "__main__":
    main()

