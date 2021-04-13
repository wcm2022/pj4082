"""Interfaces to hardware winch systems.  Uses the QtSerialPort module for
communication event processing using the Qt event loop.
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
import logging

# for documentation on the PyQt5 API, see http://pyqt.sourceforge.net/Docs/PyQt5/index.html
from PyQt5 import QtCore, QtSerialPort

# set up logger for module
log = logging.getLogger('winch')

# filter out most logging; the default is NOTSET which passes along everything
# log.setLevel(logging.WARNING)

################################################################
class QtSerialWinch(object):
    """Class to manage a serial connection to a hardware winch system using Qt
    QSerialPort object for data transport.  The data protocol is based on the
    StepperWinch Arduino sketch.
    """

    def __init__(self):
        self._portname = None
        self._buffer = b''
        self._port = None

        self.winch_time = -1
        self.winch_positions = [0,0,0,0]
        self._last_report_time = -1
        return

    def status_message(self):
        if self._port is None:
            return "<not open>"
        else:
            return "%6.2f: %d %d %d %d" % (1e-6*self.winch_time, self.winch_positions[0], self.winch_positions[1], self.winch_positions[2], self.winch_positions[3])

    def available_ports(self):
        """Return a list of names of available serial ports."""
        return [port.portName() for port in QtSerialPort.QSerialPortInfo.availablePorts()]

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

        # open the serial port, which should also reset the Arduino
        if self._port.open(QtCore.QIODevice.ReadWrite):
            log.info("Opened winch serial port %s", self._port.portName())
            # always process data as it becomes available
            self._port.readyRead.connect(self.read_input)
            return True

        else:
            # Error codes: https://doc.qt.io/qt-5/qserialport.html#SerialPortError-enum
            errcode = self._port.error()
            if errcode == QtSerialPort.QSerialPort.PermissionError:
                log.warning("Failed to open winch serial port %s with a QSerialPort PermissionError, which could involve an already running control process, a stale lock file, or dialout group permissions.", self._port.portName())
            else:
                log.warning("Failed to open winch serial port %s with a QSerialPort error code %d.", self._port.portName(), errcode)
            self._port = None
            return False

    def set_and_open_port(self, name):
        self.set_port(name)
        self.open()

    def close(self):
        """Shut down the serial connection to the Arduino."""
        if self._port is not None:
            log.info("Closing winch serial port %s", self._port.portName())
            self._port.close()
            self._port = None
        return

    def write(self, data):
        if self._port is not None:
            self._port.write(data)
        else:
            log.debug("Winch serial port not open during write.")

    def read_input(self):
        # Read as much input as available; callback from Qt event loop.
        data = self._port.readAll()
        if len(data) > 0:
            self.data_received(data)
        return

    def _parse_status_line(self, data):
        # parse a single line of status input provided as a bytestring
        tokens = data.split()
        if len(tokens) == 6:
            if tokens[0] == b'txyza':
                self.winch_positions = [int(x) for x in tokens[2:]]
                new_time = int(tokens[1])
                if new_time < self.winch_time or new_time > (self._last_report_time + 5e6):
                    log.info("Received winch time stamp: %d microseconds, position: %s", new_time, self.winch_positions)
                    self._last_report_time = new_time
                self.winch_time = new_time
                return
        log.debug("Unrecognized winch status: %s", tokens)

    def data_received(self, data):
        # Manage the possibility of partial reads by appending new data to any previously received partial line.
        # The data arrives as a PyQT5.QtCore.QByteArray.
        self._buffer += bytes(data)
        while b'\n' in self._buffer:
            first, self._buffer = self._buffer.split(b'\n', 1)
            first = first.rstrip()
            self._parse_status_line(first)

    def _send_command(self, string):
        log.debug("Sending to winch: %s", string)
        self.write(string.encode()+b'\n')
        return

    def _map_axis_to_mask(self, axis):
        # map an axis index or list of indices to a mask string
        axisnames = "xyza"
        if isinstance(axis, int):
            return axisnames[axis]
        else:
            return "".join([axisnames[i] for i in axis])

    def _map_positions_to_string(self, position):
        # map an position value or list of values to a string of numbers
        if isinstance(position, int):
            return str(position)
        else:
            return " ".join([str(x) for x in position])

    # --- ad hoc winch protocol API: this should be kept compatible with the simulator ------------
    # This generates messages following the command protocol in StepperWinch.ino

    def ping(self):
        self._send_command("version")
        return

    def motor_enable( self, value=True):
        """Issue a command to enable or disable the stepper motor drivers."""
        self._send_command( "enable 1" if value is True else "enable 0" )
        return

    def set_target(self, axis, position):
        """Set the absolute target position for one or more winch axes.

        :param axis: either a integer axis number or list of axis numbers
        :param positions: either a integer step position or list of step positions
        """
        self._send_command("a %s %s" % (self._map_axis_to_mask(axis), self._map_positions_to_string(position)))
        return

    def increment_target(self, axis, offset):
        """Add a signed offset to one or more winch target positions.

        :param axis: either a integer axis number or list of axis numbers
        :param offset: either a integer step offset or list of step offsets
        """
        self._send_command("d %s %s" % (self._map_axis_to_mask(axis), self._map_positions_to_string(offset)))
        return

    def increment_reference(self, axis, offset):
        """Add a signed offset to one or more winch reference positions.

        :param axis: either a integer axis number or list of axis numbers
        :param offset: either a integer step offset or list of step offsets
        """
        self._send_command("r %s %s" % (self._map_axis_to_mask(axis), self._map_positions_to_string(offset)))
        return

    def set_velocity(self, axis, velocity):
        """Set the constant velocity of one or more target positions.
        Note: this is currently ignored by the winch firmware.

        :param axis: either a integer axis number or list of axis numbers
        :param velocity: either an integer velocity or list of integer velocities
        """
        self._send_command("v %s %s" % (self._map_axis_to_mask(axis), self._map_positions_to_string(velocity)))
        return

    def set_speed(self, axis, speed):
        """Set the ramp speed for one or more target positions.  Speeds less than or equal to zero
        are treated as infinite on the winch.

        :param axis: either a integer axis number or list of axis numbers
        :param speed: either an integer speed or list of integer velocities
        """
        self._send_command("s %s %s" % (self._map_axis_to_mask(axis), self._map_positions_to_string(speed)))
        return

    def set_freq_damping(self, axis, freq, ratio):
        """Set the second order model resonance parameters for one or more path
        generators.  Note that the same parameters are applied to all specified
        axes, unlike the target setting functions.

        :param axis: either a integer axis number or list of axis numbers
        :param freq: scalar specifying the frequency in Hz
        :param ratio: scalar specifying the damping ratio, e.g. 1.0 at critical damping.
        """
        self._send_command("g %s %2.6f %2.6f" % (self._map_axis_to_mask(axis), freq, ratio))
        return
