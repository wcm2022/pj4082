"""Objects related to MIDI event processing.
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

# for documentation on the PyQt5 API, see http://pyqt.sourceforge.net/Docs/PyQt5/index.html
from PyQt5 import QtCore

# for documentation on python-rtmidi: https://pypi.org/project/python-rtmidi/
import rtmidi

# MIDI message reference:
#   https://www.midi.org/specifications/item/table-1-summary-of-midi-message

# set up logger for module
log = logging.getLogger('midi')

# filter out most logging; the default is NOTSET which passes along everything
log.setLevel(logging.INFO)

################################################################
class MIDIProcessor(object):
    """Abstract class for processing MIDI events.  Provides a callback for the
    specific MIDI events we use in our systems so this may be subclassed to
    implement a MIDI stream processor.  This defines an informal protocol for
    MIDI input.  This may be extended to more event times as needed.
    """

    def __init__(self):
        log.debug("Entering midi.MIDIProcessor.__init__")
        super().__init__()
        self.MIDI_notes_active = set()
        return

    def note_off(self, channel, key, velocity):
        """Function to receive messages starting with 0x80 through 0x8F.

        :param channel: integer from 1 to 16
        :param key: integer from 0 to 127
        :param velocity: integer from 0 to 127
        """
        pass

    def note_on(self, channel, key, velocity):
        """Function to receive messages starting with 0x90 through 0x9F.

        :param channel: integer from 1 to 16
        :param key: integer from 0 to 127
        :param velocity: integer from 0 to 127
        """
        pass

    def polyphonic_key_pressure(self, channel, key, value):
        """Function to receive messages starting with 0xA0 through 0xAF.

        :param channel: integer from 1 to 16
        :param key: integer from 0 to 127
        :param value: integer from 0 to 127
        """
        pass

    def control_change(self, channel, control, value):
        """Function to receive messages starting with 0xB0 through 0xBF.

        :param channel: integer from 1 to 16
        :param control: integer from 0 to 127; some have special meanings
        :param value: integer from 0 to 127
        """
        pass

    def channel_pressure(self, channel, value):
        """Function to receive messages starting with 0xD0 through 0xDF.

        :param channel: integer from 1 to 16
        :param value: integer from 0 to 127
        """
        pass

    def decode_message(self, message):
        """Decode a MIDI message expressed as a list of integers and perform callbacks
        for recognized message types.

        :param message: list of integers containing a single MIDI message
        """
        if len(message) > 0:
            status = message[0] & 0xf0
            channel = (message[0] & 0x0f) + 1

            if len(message) == 2:
                if status == 0xd0: # == 0xdx, channel pressure, any channel
                    return self.channel_pressure(channel, message[1])

            elif len(message) == 3:
                if status == 0x90: # == 0x9x, note on, any channel
                    return self.note_on(channel, message[1], message[2])

                elif status == 0x80: # == 0x8x, note off, any channel
                    return self.note_off(channel, message[1], message[2])

                elif status == 0xb0: # == 0xbx, control change, any channel
                    return self.control_change(channel, message[1], message[2])

                elif status == 0xa0: # == 0xax, polyphonic key pressure, any channel
                    return self.polyphonic_key_pressure(channel, message[1], message[2])

    def decode_mpd218_key(self, key):
        """Interpret a MPD218 pad event key value as a row, column, and bank position.
        Row 0 is the front/bottom row (Pads 1-4), row 3 is the back/top row (Pads 13-16).
        Column 0 is the left, column 3 is the right.
        Bank 0 is the A bank, bank 1 is the B bank, bank 2 is the C bank.

        :param key: an integer MIDI note value
        :return: (row, column, bank)
        """
        # Decode the key into coordinates on the 4x4 pad grid.
        bank = (key - 36) // 16
        pos = (key - 36) % 16
        row = pos // 4
        col = pos % 4
        return row, col, bank

    def decode_mpd218_cc(self, cc):
        """Interpret a MPD218 knob control change event as a knob index and bank position.
        The MPD218 uses a non-contiguous set of channel indices so this normalizes the result.
        The knob index ranges from 1 to 6 matching the knob labels.
        Bank 0 is the A bank, bank 1 is the B bank, bank 2 is the C bank.

        :param cc: an integer MIDI control channel identifier
        :return: (knob, bank)
        """
        if cc < 16:
            knob = {3:1, 9:2, 12:3, 13:4, 14:5, 15:6}.get(cc)
            bank = 0
        else:
            knob = 1 + ((cc - 16) % 6)
            bank = 1 + ((cc - 16) // 6)
        return knob, bank

################################################################
class QtMIDIListener(QtCore.QObject):
    """Object to manage a MIDI input connection."""

    # class variable with Qt signal used to communicate between MIDI thread and main thread
    _midiReady = QtCore.pyqtSignal(tuple, name='midiReady')

    def __init__(self):
        super(QtMIDIListener,self).__init__()
        self.processor = None
        # Initialize the MIDI input system and read the currently available ports.
        self.midi_in = rtmidi.MidiIn()
        return

    def get_midi_port_names(self):
        """Return a list of unique names for the current MIDI input ports.  Duplicate
        names are modified to guarantee the uniqueness condition.
        """
        unique_names = set()
        result = list()
        for name in self.midi_in.get_ports():
            while name in unique_names:
                log.debug("Making MIDI port name %s unique.", name)
                name += '+'
            unique_names.add(name)
            result.append(name)
        return result

    def connect_midi_processor(self, processor):
        """Attach an object to receive MIDI input events, generally a subclass of MIDIProcessor."""
        self.processor = processor

    def open_MIDI_input(self, name):
        """Open the MIDI in port with the given name (a string).  If the port is already
        open, this will close it first.
        """
        if self.midi_in.is_port_open():
            self.midi_in.close_port()
            log.info("Closed MIDI input port.")
            self.midi_in = rtmidi.MidiIn()

        midi_port_names = self.get_midi_port_names()

        if name == "<no selection>":
            log.debug("User picked the null MIDI port entry.")

        elif name not in midi_port_names:
            log.warning("MIDI port name %s not found.", name)

        else:
            log.debug("Opening MIDI input port %s", name)
            idx = midi_port_names.index(name)
            self.midi_in.open_port(idx)
            self._midiReady.connect(self._midi_received_main)
            self.midi_in.set_callback(self._midi_received_background)
            log.info("Opened MIDI input port %s", name)

    #================================================================
    def _midi_received_background(self, data, unused):
        """Callback to receive a MIDI message on the background thread, then send it as
        a signal to a slot on the main thread."""
        log.debug("_midi_received")
        self._midiReady.emit(data)
        return

    @QtCore.pyqtSlot(tuple)
    def _midi_received_main(self, data):
        """Slot to receive MIDI data on the main thread."""
        if self.processor is not None:
            msg, delta_time = data
            self.processor.decode_message(msg)

################################################################
class MIDIEncoder(object):
    """Abstract class for composing MIDI messages."""

    def __init__(self):
        pass

    def message(self, message):
        """Overridable method to output a single MIDI message.

        :param message: list of integers constituting a MIDI message
        """
        pass


    def note_on(self, channel, note, velocity):
        """Send a Note On message.

        :param channel:  MIDI channel, integer on [1,16]
        :param note:     MIDI note, integer on [0,127]
        :param velocity: MIDI velocity, integer on [0,127]
        """
        if channel >= 1 and channel <= 16 and note >= 0 and note <= 127 and velocity >= 0 and velocity <= 127:
            self.message([0x90 | ((channel-1)&0x0f), note, velocity])

    def note_off(self, channel, note, velocity=0):
        """Send a Note On message.

        :param channel:  MIDI channel, integer on [1,16]
        :param note:     MIDI note, integer on [0,127]
        :param velocity: optional MIDI velocity, integer on [0,127], normally zero, default zero
        """
        if channel >= 1 and channel <= 16 and note >= 0 and note <= 127 and velocity >= 0 and velocity <= 127:
            self.message([0x80 | ((channel-1)&0x0f), note, velocity])

    def polyphonic_key_pressure(self, channel, key, pressure):
        """Send a Polyphonic Key Pressure message.

        :param channel:  MIDI channel, integer on [1,16]
        :param note:     MIDI note, integer on [0,127]
        :param pressure: MIDI aftertouch, integer on [0,127]
        """
        if channel >= 1 and channel <= 16 and note >= 0 and note <= 127 and pressure >= 0 and pressure <= 127:
            self.message([0xA0 | ((channel-1)&0x0f), note, pressure])

    def control_change(self, channel, controller, value):
        """Send a Controller Change message.

        :param channel:    MIDI channel, integer on [1,16]
        :param controller: MIDI controller index, integer on [0,127]
        :param value:   MIDI value, integer on [0,127]
        """
        if channel >= 1 and channel <= 16 and controller >= 0 and controller <= 127 and value >= 0 and value <= 127:
            self.message([0xb0 | ((channel-1)&0x0f), controller, value])

    def channel_pressure(self, channel, value):
        """Send a Channel Pressure (aftertouch) message.

        :param channel:    MIDI channel, integer on [1,16]
        :param value:   MIDI value, integer on [0,127]
        """
        if channel >= 1 and channel <= 16 and value >= 0 and value <= 127:
            self.message([0xd0 | ((channel-1)&0x0f), value])

################################################################
class QtMIDISender(MIDIEncoder):
    """Object to manage a MIDI output connection using rtmidi."""

    def __init__(self):
        super(QtMIDISender,self).__init__()
        # Initialize the MIDI output system and read the currently available ports.
        self.midi_out = rtmidi.MidiOut()
        return

    def get_midi_port_names(self):
        """Return a list of names of the current MIDI output ports."""
        return self.midi_out.get_ports()

    def open_MIDI_output(self, name):
        """Open the MIDI out port with the given name (a string).  If the port is already
        open, this will close it first.
        """
        if self.midi_out.is_port_open():
            self.midi_out.close_port()
            log.info("Closed MIDI output port.")
            self.midi_out = rtmidi.MidiOut()

        midi_port_names = self.get_midi_port_names()

        if name == "<no selection>":
            log.debug("User picked the null MIDI port entry.")

        elif name not in midi_port_names:
            log.warning("MIDI port name %s not found.", name)

        else:
            log.debug("Opening MIDI output port %s", name)
            idx = midi_port_names.index(name)
            self.midi_out.open_port(idx)
            log.info("Opened MIDI output port %s", name)

    #================================================================
    def message(self, message):
        """Send a single MIDI message.

        :param message: list of integers constituting a MIDI message
        """
        if self.midi_out.is_port_open():
            self.midi_out.send_message(message)


################################################################
