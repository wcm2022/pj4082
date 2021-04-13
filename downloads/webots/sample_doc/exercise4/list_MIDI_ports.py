#!/usr/bin/env python3

import rtmidi
midiout = rtmidi.MidiOut()
midiin = rtmidi.MidiIn()

print("Available output ports:")
for idx, port in enumerate(midiout.get_ports()):
    print("  %d: %s" % (idx, port))

print("Available input ports:")
for idx, port in enumerate(midiin.get_ports()):
    print("  %d: %s" % (idx, port))

