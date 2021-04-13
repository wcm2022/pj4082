#!/usr/bin/env python3
"""A utility to receive OSC messages over UDP and display them in a PyQt5 GUI text box."""
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
import os, sys, struct, time, logging, functools

# for documentation on the PyQt5 API, see http://pyqt.sourceforge.net/Docs/PyQt5/index.html
from PyQt5 import QtCore, QtGui, QtWidgets, QtNetwork

# This uses python-osc to decode UDP packets containing OSC messages.
#   installation:      pip3 install python-osc
#   source code:       https://github.com/attwad/python-osc
#   pypi description:  https://pypi.org/project/python-osc/
import pythonosc.dispatcher

################################################################
class OSCDisplay(QtWidgets.QMainWindow):
    """A custom main window which provides all GUI controls."""

    def __init__( self, *args, **kwargs):
        super(OSCDisplay,self).__init__()

        # create the GUI elements
        self.setupUi()

        # finish initialization
        self.show()
        return

    # ------------------------------------------------------------------------------------------------
    def setupUi(self):
        self.setWindowTitle("OSC Display")
        self.resize(500, 300)

        self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralwidget)
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setContentsMargins(-1, -1, -1, 9) # left, top, right, bottom

        # generate fields for configuring the OSC listener
        self.hostFieldLayout = QtWidgets.QHBoxLayout()
        self.hostFieldLabel = QtWidgets.QLabel()
        self.hostFieldLabel.setText("OSC message listener address:port  ")
        self.hostField = QtWidgets.QLineEdit()
        self.hostField.setText("localhost:3761")
        self.hostFieldLayout.addWidget(self.hostFieldLabel)
        self.hostFieldLayout.addWidget(self.hostField)
        self.verticalLayout.addLayout(self.hostFieldLayout)
        self.hostField.returnPressed.connect(self.setListenerHostname)

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

    def write(self, string):
        """Write output to the console text area."""
        self.consoleOutput.appendPlainText(string.rstrip())
        return

    def quitSelected(self):
        self.write("User selected quit.")
        self.close()

    def closeEvent(self, event):
        self.write("Received window close event.")
        super(OSCDisplay,self).closeEvent(event)

    # --------------------------------------------------------------------------------------------------
    def setListenerHostname(self):
        """Called when the user finishes entering text into the host interface line editor."""
        name = self.hostField.text()
        if ':' in name:
            self.main.listener_address, port = name.split(':', 1)
            portnum = int(port)
            if portnum < 2048 or portnum > 65535:
                self.show_status("Port number %d out of valid range, ignoring new value." % portnum)
            else:
                self.main.listener_portnum = portnum
                self.show_status("Set new listener address and port.")
        else:
            self.main.listener_address = name
            self.show_status("Set new listener address.")

        # normalize the text field
        self.hostField.setText('%s:%d' % (self.main.listener_address, self.main.listener_portnum))
        self.main.open_receiver()
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
        self.window = OSCDisplay()
        self.window.main = self

        # Initialize the OSC message dispatch system.
        self.dispatcher = pythonosc.dispatcher.Dispatcher()
        # dispatch.map("/display/*", self.display_message)
        self.dispatcher.set_default_handler(self.unknown_message)
        
        # open socket and provide an initial status message
        self.open_receiver()

        return

    def open_receiver(self):
        # create a UDP socket to send and receive messages from the client
        if self.port is not None:
            self.port.close()

        self.port = QtNetwork.QUdpSocket()
        success = self.port.bind(QtNetwork.QHostAddress(self.listener_address), self.listener_portnum)
        if not success:
            self.window.show_status("Failed to bind listener socket.")
            self.port.close()
            self.port = None
        else:
            self.port.readyRead.connect(self.message_received)
            self.window.show_status("Ready to go, listening for OSC UDP packets on %s:%d..." % (self.listener_address, self.listener_portnum))
        return

    def message_received(self):
        # the host is an instance of QHostAddress
        msg, host, port = self.port.readDatagram(20000)
        # self.window.write("Received UDP packet from %s port %d with %d bytes." % (host.toString(), port, len(msg)))
        self.dispatcher.call_handlers_for_packet(msg, host)
        return

    def unknown_message(self, msgaddr, *args):
        """Default handler for unrecognized OSC messages."""
        self.window.write("%s: %s" % (msgaddr, " ".join([str(arg) for arg in args])))
    
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
