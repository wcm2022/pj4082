"""Objects related to OSC messaging.
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
import math, logging

# for documentation on the PyQt5 API, see http://pyqt.sourceforge.net/Docs/PyQt5/index.html
from PyQt5 import QtCore, QtNetwork

# This uses python-osc to decode UDP packets containing OSC messages.
#   installation:      pip3 install python-osc
#   source code:       https://github.com/attwad/python-osc
#   pypi description:  https://pypi.org/project/python-osc/
import pythonosc.dispatcher
import pythonosc.udp_client

# set up logger for module
log = logging.getLogger('osc')

# filter out most logging; the default is NOTSET which passes along everything
# log.setLevel(logging.WARNING)

################################################################
class QtOSCListener(QtCore.QObject):
    """Object to manage a OSC network input.  This uses a Qt QUdpSocket to receive
    messages from the main Qt event loop and a pythonosc dispatcher to decode
    OSC messages and distribute them to callbacks.  Messages are delivered on
    the main thread.  This requires a pythonosc version of at least 1.7.0 so the
    dispatcher can be used in this way.

    :param port: optional UDP port number to which to receive, defaults to 3761
    :param host: optional hostname or IP address to which to receive, defaults to localhost

    """

    def __init__(self, port=3762, host='localhost'):
        super(QtOSCListener,self).__init__()

        # global state
        self.listener_address = "localhost"
        self.listener_portnum = 3761
        self.port = None

        # Initialize the OSC message dispatch system.
        self.dispatcher = pythonosc.dispatcher.Dispatcher()
        self.dispatcher.set_default_handler(self.unknown_message)
        return

    def map_handler(self, address, callback):
        """Add an address template string to the dispatch map."""
        self.dispatcher.map(address, callback)
        return

    def set_OSC_port(self, address, portnum):
        """Called to configure a new network address.  If the port is already open it is
        closed and a new port opened with the new address."""
        self.listener_address = address
        self.listener_portnum = portnum
        if self.port is not None:
            self.open_receiver()
        return

    def open_receiver(self):
        """Create a UDP socket, bind it to the desired port, and set up callbacks to
        process messages upon receipt.  This may be called again after the port
        address has changed and will create a new socket.
        """

        # create a UDP socket to send and receive messages from the client
        if self.port is not None:
            self.port.close()

        self.port = QtNetwork.QUdpSocket()
        success = self.port.bind(QtNetwork.QHostAddress(self.listener_address), self.listener_portnum)
        if not success:
            log.warning("Failed to bind listener socket.")
            self.port.close()
            self.port = None
        else:
            self.port.readyRead.connect(self.message_received)
            log.info("OSC receiver ready to go, listening for OSC UDP packets on %s:%d" % (self.listener_address, self.listener_portnum))
        return

    def message_received(self):
        """Callback attached to the port readyRead signal to process incoming UDP packets."""
        # the host is an instance of QHostAddress
        msg, host, port = self.port.readDatagram(20000)
        self.dispatcher.call_handlers_for_packet(msg, host)
        return

    def unknown_message(self, msgaddr, *args):
        """Default handler for unrecognized OSC messages."""
        log.debug("Unhandled OSC message: %s %s" % (msgaddr, " ".join([str(arg) for arg in args])))
        return

################################################################
class QtOSCSender(QtCore.QObject):
    """Object to manage a OSC network output.  This is a thin wrapper around the
    pythonosc SimpleUDPClient to allow this object to close and reopen the port
    at will while retaining its identity in the application.

    :param port: optional UDP port number to which to send, defaults to 3762
    :param host: optional hostname or IP address to which to send, defaults to localhost
    """

    def __init__(self, port=3762, host='localhost'):
        super(QtOSCSender,self).__init__()

        # global state
        self.destination_address = host
        self.destination_portnum = port
        self._port = None
        return

    def set_OSC_port(self, address, portnum):
        """Called to configure a new destination network address.  If the port is already open it is
        closed and a new port opened with the new address."""
        self.destination_address = address
        self.destination_portnum = portnum
        if self._port is not None:
            self.open_sender()
        return

    def open_sender(self):
        """Create a UDP client with the chosen destination address.  This may be called
        again after the port address has changed and will create a new socket.
        """
        # create a new UDP socket to send messages to a server
        self._port = pythonosc.udp_client.SimpleUDPClient(self.destination_address, self.destination_portnum)
        log.info("OSC sender ready to go, configured for OSC UDP packets to %s:%d" % (self.destination_address, self.destination_portnum))
        return

    def send(self, address, *args):
        """Send a UDP packet containing a single OSC message to the predesignated host address and UDP port number.

        :param address: an OSC 'address' string beginning with a forward slash
        :param args: optional arguments, which must be primitive types convertible to OSC message data types
        """

        if self._port is not None:
            self._port.send_message(address, args)

################################################################
