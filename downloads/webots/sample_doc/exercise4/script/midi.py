# MIDI input logic.  This interprets user MIDI performance input into script and motion primitive commands.

import logging
import numpy as np

# Modules from the course library.
import rcp.midi

# set up logger for module
log = logging.getLogger('midi1')

################################################################
class WinchMIDILogic(rcp.midi.MIDIProcessor):
    """Core performance logic for processing MIDI input into winch commands."""
    def __init__(self, main):
        super().__init__()
        self.main  = main
        self.primitives = main.primitives
        return

    #---- methods to process MIDI messages -------------------------------------
    def note_on(self, channel, key, velocity):
        """Process a MIDI Note On event."""
        log.debug("WinchMIDILogic received note on: %d, %d", key, velocity)
        row, col, bank = self.decode_mpd218_key(key)
        # log.debug("WinchMIDILogic decoded note to: %d, %d, %d", row, col, bank)
        
        if bank < 2:
            # Each bank controls one set of four winches.
            # Rows 0 and 1 are forward/reverse steps.
            # Rows 2 and 3 are forward/reverse impulses.
            winch_index = 4*bank + col
            if row < 2:
                # Apply a non-linear scaling to the velocity to calculate a displacement.
                delta = int(velocity**1.6 * 0.5)
                if row == 1:  delta = -delta
                self.primitives.increment_target(winch_index, delta)
                
            else:
                # Apply a non-linear scaling to the velocity to calculate a displacement.
                delta = int(velocity**1.6 * 0.5)
                if row == 3:  delta = -delta
                self.primitives.increment_reference(winch_index, delta)

        else:
            # Pad bank C maps to named poses
            names = ['reset', 'lead1', 'lead2', 'lead3']
            self.primitives.set_pose(names[col])
                
        return

    def note_off(self, channel, key, velocity):
        """Process a MIDI Note Off event."""
        log.debug("WinchMIDILogic received note off: %d, %d", key, velocity)
        row, col, bank = self.decode_mpd218_key(key)
        return

    def control_change(self, channel, cc, value):
        """Process a MIDI Control Change event."""
        knob, bank = self.decode_mpd218_cc(cc)
        log.debug("Winch control change %d on knob %d bank %d", cc, knob, bank)

        if knob == 1: # Knob #1 on MPD218, use to control resonant frequency
            self.primitives.set_frequency(0.05 + 0.1 * value)

        elif knob == 2: # Knob #2 on on MPD218, use to control damping ratio
            self.primitives.set_damping(0.05 + 0.01 * value)

        else: # Knob #3 through 6 control ramp speed
            winch_index = knob - 3
            if value == 127:
                speed = 0          # infinite speed, i.e. a step
            else:
                speed = 1 + int(value**1.6 * 2.0)
            self.primitives.set_speed(winch_index, speed)
            
    def channel_pressure(self, channel, pressure):
        """Process a MIDI Channel Pressure event."""
        log.debug("channel aftertouch: %d", pressure)
        return

