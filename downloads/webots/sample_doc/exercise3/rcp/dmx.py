"""Objects related to DMX lighting control.
"""
################################################################
# Written in 2019 by Garth Zeglin <garthz@cmu.edu>

# To the extent possible under law, the author has dedicated all copyright
# and related and neighboring rights to this software to the public domain
# worldwide. This software is distributed without any warranty.

# You should have received a copy of the CC0 Public Domain Dedication along with this software.
# If not, see <http://creativecommons.org/publicdomain/zero/1.0/>.

################################################################
# standard Python libraries
import math, logging
import numpy as np

# for documentation on the PyQt5 API, see http://pyqt.sourceforge.net/Docs/PyQt5/index.html
from PyQt5 import QtCore, QtSerialPort

# set up logger for module
log = logging.getLogger('dmx')

# filter out most logging; the default is NOTSET which passes along everything
# log.setLevel(logging.INFO)

################################################################
class QtDMXUSBPro(object):
    """Class to manage a serial connection to an ENTTEC DMXUSB PRO for DMX lighting
    control output.  Uses the Qt QSerialPort object for data transport.  This
    currently only supports output, although the device is capable of receiving
    DMX.  For details on the device, please see https://www.enttec.com/range/controls/dmx-usb-interfaces/
    """

    def __init__(self):
        self._portname = None
        self._port = None
        # Initialize a default DMX 'universe', i.e. an addressable space of
        # 8-bit registers.  The Enttec requires a minimum universe size of 25.
        self._universe = np.zeros((25), dtype=np.uint8)
        return

    def set_size(self, channels):
        """Set the size of the DMX 'universe'.  The value is limited to the valid range
        of [25,512].  Each channel is an 8-bit value transmitted on the DMX bus;
        typically each fixture occupies several sequential channels at a start
        address configured on the fixture.
        """
        new_size = min(max(channels, 25), 512)
        self._universe = np.resize(self._universe, new_size)
        log.info("Resized DMX universe to %d channels." % new_size)
        return

    def available_ports(self):
        """Return a list of names of available serial ports."""
        return [port.portName() for port in QtSerialPort.QSerialPortInfo.availablePorts()]
        return

    def set_port(self, name):
        if name == "<no selection>":
            log.debug("User picked the null serial port entry.")
            self._portname = None
        else:
            self._portname = name

    def open(self):
        """Open the serial port and initialize communications.  If the port is already
        open, this will close it first.  If the current name is None, this will not open
        anything.  Returns True if the port is open, else False."""
        if self._port is not None:
            self.close()

        if self._portname is None:
            log.debug("No port name provided so not opening port.")
            return False
            return

        self._port = QtSerialPort.QSerialPort()
        self._port.setBaudRate(115200)
        self._port.setPortName(self._portname)

        # open the serial port
        if self._port.open(QtCore.QIODevice.ReadWrite):
            log.info("Opened DMX serial port %s", self._port.portName())
            # always process data as it becomes available
            self._port.readyRead.connect(self._read_input)
            return True

        else:
            # Error codes: https://doc.qt.io/qt-5/qserialport.html#SerialPortError-enum
            errcode = self._port.error()
            if errcode == QtSerialPort.QSerialPort.PermissionError:
                log.warning("Failed to open DMX serial port %s with a QSerialPort PermissionError, which could involve an already running control process, a stale lock file, or dialout group permissions.", self._port.portName())
            else:
                log.warning("Failed to open DMX serial port %s with a QSerialPort error code %d.", self._port.portName(), errcode)
            self._port = None
            return False

    def set_and_open_port(self, name):
        self.set_port(name)
        self.open()

    def close(self):
        """Shut down the serial connection to the DMX device."""
        if self._port is not None:
            log.info("Closing DMX serial port %s", self._port.portName())
            self._port.close()
            self._port = None
        return

    # === internals =======================================================
    def _read_input(self):
        # Read as much input as available; callback from Qt event loop.
        data = self._port.readAll()
        if len(data) > 0:
            log.debug("Received %d bytes from DMX interface." % len(data))
        return

    def _send_universe(self):
        """Issue a DMX universe update."""
        if self._port is None:
            log.debug("DMX port not open for output during send.")
        else:
            universe_size = min(512, self._universe.size)
            message = np.ndarray((6 + universe_size), dtype=np.uint8)
            message[0:2] = [126, 6] # Send DMX Packet header
            message[2]   = (universe_size+1) % 256   # data length LSB
            message[3]   = (universe_size+1) >> 8    # data length MSB
            message[4]   = 0                         # zero 'start code' in first universe position
            message[5:5+universe_size] = self._universe[0:universe_size]
            message[-1]  = 231 # end of message delimiter
            # log.debug("Sending to DMX: '%s'", message)
            self._port.write(message.tobytes())

    # ================================================================
    def set_channel(self, channel, value):
        """Set a single channel value and update the hardware.

        :param start: zero-based index of channel to update
        :param value: 8-bit integer value
        """
        self._universe[channel] = value
        self._send_universe()
        return

    def set_channels(self, start, values):
        """Set a range of channels and update the hardware.

        :param start: zero-based index of first channel to update
        :param values: list or numpy array of 8-bit integer values
        """

        size = min(self._universe.size - start, len(values))
        self._universe[start:start+size] = values[0:size]
        self._send_universe()
        return


################################################################
class ColorInterpolator(object):
    def __init__(self, fixtures, channels_per_fixture):
        # opacity of cue updates
        self.alpha = 1.0

        # transition time constant in seconds
        self.duration = 1.0

        # array sizes
        self.fixtures = fixtures
        self.channels_per_fixture = channels_per_fixture

        # initialize the color vectors
        self.target_colors  = np.zeros((self.fixtures, self.channels_per_fixture))
        self.current_colors = np.zeros((self.fixtures, self.channels_per_fixture))
        self.color_velocity = np.zeros((self.fixtures, self.channels_per_fixture))

        # flag for culling null outputs
        self.colors_changed = False

        return

    def current_dmx_values(self):
        """Return a universe of 8-bit integer DMX values with the current colors mapped to the
        specific fixture channel configuration."""
        return np.round(self.current_colors).astype(np.uint8).flatten()

    def current_rgb_values(self):
        """Return a list of 8-bit integer (red, green, blue) values with the current color for each fixture."""
        return np.round(self.current_colors[:,0:3]).astype(np.uint8)

    def update_for_interval(self, interval):
        """Polling function to update internal state.  Returns true if the DMX outputs should be updated."""
        # compute any difference between actual and target colors
        errors = self.target_colors - self.current_colors

        if errors.any():
            # calculate the maximum possible change, bound it to the actual error, then apply it
            delta = interval * self.color_velocity
            abserror = np.abs(errors)
            bounded_delta = np.minimum(abserror, np.maximum(-abserror, delta))
            self.current_colors += bounded_delta
            self.colors_changed = True

        value = self.colors_changed
        self.colors_changed = False
        return value

    def set_color_target(self, fixture, color):
        """Update the color target for the given fixture using the current opacity.  The
        output will change to the new targets over the current transition
        interval.  Note that the opacity blends between the current color and
        the given color, not the current target and the given color.
        """
        if fixture < self.fixtures:
            channels = min(len(color), self.channels_per_fixture)
            newcolor = np.array(color[0:channels])
            blended = (self.alpha * newcolor) + ((1 - self.alpha) * self.current_colors[fixture,0:channels])
            self.target_colors[fixture,0:channels] = blended
            difference = self.target_colors[fixture] - self.current_colors[fixture]
            duration = max(self.duration, 0.020)
            self.color_velocity[fixture] = difference / duration
        return

    def set_channel_target(self, fixture, channel, value):
        """Update a specific color channel target for the given fixture using the
        current opacity.  The output will change to the new target over the
        current transition interval.  Note that the opacity blends between the
        current color and the given color, not the current target and the given
        color.
        """
        if fixture < self.fixtures and channel < self.channels_per_fixture:
            blended = (self.alpha * value) + ((1 - self.alpha) * self.current_colors[fixture, channel])
            self.target_colors[fixture,channel] = blended
            difference = blended - self.current_colors[fixture, channel]
            duration = max(self.duration, 0.020)
            self.color_velocity[fixture, channel] = difference / duration
        return

    def set_current_color(self, fixture, color):
        """Set a fixture to the given color without a transition.  The next update cycle will output the color."""
        if fixture < self.fixtures:
            channels = min(len(color), self.channels_per_fixture)
            self.target_colors [fixture, 0:channels] = color[0:channels]
            self.current_colors[fixture, 0:channels] = color[0:channels]
            self.color_velocity[fixture,:] = 0.0
            self.colors_changed = True
        return

    def set_dmx_value(self, channel, value):
        """Set a single DMX channel to the given value without a transition.  The next
        update cycle will output the color.  This function performs the inverse
        of the fixture->DMX mapping in current_dmx_values().
        """
        fixture = channel // self.channels_per_fixture
        color = channel % self.channels_per_fixture
        if fixture < self.fixtures and color < self.channels_per_fixture:
            self.current_colors[fixture,color] = value
            self.target_colors[fixture,color] = value
            self.colors_changed = True
        return

################################################################
