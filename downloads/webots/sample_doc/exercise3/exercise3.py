#!/usr/bin/env python3
"""A show control system with GUI."""

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
import os, sys, logging
import numpy as np

# for documentation on the PyQt5 API, see http://pyqt.sourceforge.net/Docs/PyQt5/index.html
from PyQt5 import QtCore, QtWidgets, QtGui

# This uses several modules from the course library.
import rcp.QtWinch
import rcp.QtMPD218
import rcp.QtDMX
import rcp.QtConfig
import rcp.QtLog

import rcp.app
import rcp.dmx
import rcp.midi
import rcp.osc
import rcp.path
import rcp.winch
import rcp.sim

# set up logger for module
log = logging.getLogger('ex3')

################################################################
class AppWindow(QtWidgets.QMainWindow):
    """A custom main window which provides all GUI controls.  This generally follows
    a model-view-controller convention in which this window provides the views,
    passing events to the application controller via callbacks.
    """

    def __init__(self, main):
        super().__init__()

        # This GUI controller assumes it has access to an application controller with the methods of rcp.app.MainApp.
        self.main = main

        # create the GUI elements
        self._setupUi()

        # finish initialization
        self.show()

        return

    def connect_callbacks(self):
        """Finish initializing the GUI by connecting all callbacks from GUI elements to
        application controller methods.  This allows the log window to be set up
        early to capture any messages from the initialization of other object.
        """
        self.winch_MIDI_controller.connect_midi_processor(self.main.winch_midi_logic)

        self.DMX_controller.connect_callback(self.main.dmx_slider_change)
        self.dmxSelect.callback = self.main.dmx.set_and_open_port
        self.dmxSelect.set_items(self.main.dmx.available_ports())

        self.winchMidiInputCombo.callback = self.main.winch_midi_listener.open_MIDI_input
        self.winchMidiInputCombo.set_items(self.main.winch_midi_listener.get_midi_port_names())

        self.midiOutputCombo.callback = self.main.midi_sender.open_MIDI_output
        self.midiOutputCombo.set_items(self.main.midi_sender.get_midi_port_names())

        self.oscListenerConfig.callback = self.main.osc_listener.set_OSC_port
        self.oscSenderConfig.callback = self.main.osc_sender.set_OSC_port

        for winch, selector in zip(self.main.winches, self.winchSelects):
            selector.callback = winch.set_and_open_port
            selector.set_items(winch.available_ports())

        return

    # ------------------------------------------------------------------------------------------------
    def _setupUi(self):

        # basic window setup
        self.setWindowTitle("RCP System Controller: Exercise 3")
        self.statusbar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.statusbar)

        # set up tabbed page structure
        self.tabs = QtWidgets.QTabWidget()
        self.setCentralWidget(self.tabs)
        self.tabs.currentChanged.connect(self._tab_changed)

        # generate an array of winch cartoons
        self.winchTab = QtWidgets.QWidget(self)
        self.winchTabLayout = QtWidgets.QVBoxLayout(self.winchTab)
        self.tabs.addTab(self.winchTab, 'Motors')
        self.winchSets = list()
        for i in range(self.main.num_winch_sets):
            winchSet = rcp.QtWinch.QtWinchSet()
            self.winchTabLayout.addWidget(winchSet)
            self.winchSets.append(winchSet)

        # set up the winch MIDI input simulator tab
        self.mainTab = QtWidgets.QWidget(self)
        self.mainLayout = QtWidgets.QVBoxLayout(self.mainTab)
        self.winch_MIDI_controller = rcp.QtMPD218.QtMPD218()     # generate a simulated MPD218 controller
        self.mainLayout.addWidget(self.winch_MIDI_controller)
        self.tabs.addTab(self.mainTab, 'MIDI')
            
        # generate a DMX controller tab
        self.dmxTab = QtWidgets.QWidget(self)
        self.dmxLayout = QtWidgets.QVBoxLayout(self.dmxTab)
        self.dmxIndicators = QtWidgets.QHBoxLayout()
        self.dmxOpacityIndicator = QtWidgets.QLabel()
        self.dmxTempoIndicator = QtWidgets.QLabel()
        labelFont = QtGui.QFont("Sans Serif", 14)
        self.dmxOpacityIndicator.setFont(labelFont)
        self.dmxTempoIndicator.setFont(labelFont)
        self.dmxIndicators.addWidget(self.dmxTempoIndicator)
        self.dmxIndicators.addWidget(self.dmxOpacityIndicator)
        self.dmxIndicators.addWidget(QtWidgets.QWidget()) # to fill empty space on right
        self.dmxLayout.addLayout(self.dmxIndicators)
        self.DMX_controller = rcp.QtDMX.QtDMXControls(channels = self.main.config['dmx'].getint('sliders'))
        self.dmxLayout.addWidget(self.DMX_controller)
        self.tabs.addTab(self.dmxTab, 'DMX')

        # set up the configuration tab
        self.configForm = rcp.QtConfig.QtConfigForm()
        self.tabs.addTab(self.configForm, 'Config')

        self.configFileButtons = rcp.QtConfig.QtConfigFileButtons(delegate=self.main, path=self.main.configuration_file_path)
        self.configForm.addField("Configuration file:", self.configFileButtons)

        self.oscListenerConfig = rcp.QtConfig.QtConfigOSCPort()
        self.configForm.addField("OSC message listener address:port", self.oscListenerConfig)

        self.winchMidiInputCombo = rcp.QtConfig.QtConfigComboBox()
        self.configForm.addField("Winch MIDI input", self.winchMidiInputCombo)

        self.winchSelects = list()
        for i in range(self.main.num_winch_sets):
            winchSelect = rcp.QtConfig.QtConfigComboBox()
            self.configForm.addField("Winch %d output serial port" % (i+1), winchSelect)
            self.winchSelects.append(winchSelect)

        self.midiOutputCombo = rcp.QtConfig.QtConfigComboBox()
        self.configForm.addField("MIDI output", self.midiOutputCombo)

        self.dmxSelect = rcp.QtConfig.QtConfigComboBox()
        self.configForm.addField("DMX output serial port", self.dmxSelect)

        self.oscSenderConfig = rcp.QtConfig.QtConfigOSCPort()
        self.configForm.addField("OSC destination adddress:port", self.oscSenderConfig)

        # set up the logging tab
        self.logDisplay = rcp.QtLog.QtLog(level=logging.INFO)
        self.tabs.addTab(self.logDisplay, 'Log')

        return

    # --- window and Qt event processing -------------------------------------------------------------
    def set_status(self, string):
        """Update the status bar at the bottom of the display to show the provided string."""
        self.statusbar.showMessage(string)
        return

    def update_opacity_indicator(self, opacity):
        self.dmxOpacityIndicator.setText("Opacity = %5.1f%%" % (100*opacity))
        return

    def update_tempo_indicator(self, tempo):
        self.dmxTempoIndicator.setText("Tempo = %d" % tempo)
        return

    def _tab_changed(self, index):
        log.debug("Tab changed to %d", index)
        return

    def closeEvent(self, event):
        """Qt callback received before windows closes."""
        log.info("Received window close event.")
        self.main.app_is_exiting()
        super().closeEvent(event)
        return

    # ---- configuration management --------------------------------------------------------------------
    def apply_user_configuration(self, config):
        """Apply the persistent configuration values from a configparser section proxy object."""
        self.logDisplay.set_logging_level(config['log'].get('logging_level', fallback='Verbose'))

        # MIDI
        self.winchMidiInputCombo.select_item(config['midi'].get('winch_midi_input', fallback='<no selection>'))
        self.midiOutputCombo.select_item(config['midi'].get('midi_output', fallback='<no selection>'))

        # OSC
        oscdef = config['osc']
        self.oscListenerConfig.set_OSC_port(oscdef.get('listener_addr', fallback='localhost'),
                                            oscdef.getint('listener_port', fallback=3751))

        self.oscSenderConfig.set_OSC_port(oscdef.get('sender_addr', fallback='localhost'),
                                          oscdef.getint('sender_port', fallback=3752))

        # DMX
        self.dmxSelect.select_item(config['dmx'].get('dmx_output_serial_port', fallback='<no selection>'))

        # winches
        for i, winchSelect in enumerate(self.winchSelects):
            key = "winch_%d_output_serial_port" % (i+1)
            winchSelect.select_item(config['winches'].get(key, fallback = '<no selection>'))
        return

    def gather_configuration(self, config):
        """Update the persistent configuration values in a configparser section proxy object."""
        config['log']['logging_level'] = self.logDisplay.get_logging_level()

        # MIDI
        config['midi']['winch_midi_input'] = self.winchMidiInputCombo.current_item()
        config['midi']['midi_output'] = self.midiOutputCombo.current_item()

        # OSC
        addr, port = self.oscListenerConfig.get_OSC_port()
        config['osc']['listener_addr'] = addr
        config['osc']['listener_port'] = str(port)
        addr, port = self.oscSenderConfig.get_OSC_port()
        config['osc']['sender_addr'] = addr
        config['osc']['sender_port'] = str(port)

        # DMX
        config['dmx']['dmx_output_serial_port']  = self.dmxSelect.current_item()

        # winches
        for i, winchSelect in enumerate(self.winchSelects):
            key = "winch_%d_output_serial_port" % (i+1)
            config['winches'][key] = winchSelect.current_item()

        return
    # --------------------------------------------------------------------------------------------------

################################################################
class WinchMIDILogic(rcp.midi.MIDIProcessor):
    """Core performance logic for processing MIDI input into winch commands."""
    def __init__(self, main):
        super().__init__()
        self.main  = main

        # global parameters
        self.frequency = 1.0
        self.damping_ratio = 1.0
        self.all_axes = range(4) # index list for updating all motors

        return

    #---- methods for distributing winch events across multiple winch sets and simulators ---------
    def set_freq_damping(self):
        for winch in self.main.winches:
            winch.set_freq_damping(self.all_axes, self.frequency, self.damping_ratio)
        for sim in self.main.sims:
            sim.set_freq_damping(self.all_axes, self.frequency, self.damping_ratio)
        self.main.window.set_status("Frequency: %f, damping ratio: %f" % (self.frequency, self.damping_ratio))
        return

    def increment_target(self, winch_index, steps):
        """Map a given winch index to the particular winch set."""
        set_index = winch_index // 4
        winch_id = winch_index % 4
        if set_index < self.main.num_winch_sets:
            self.main.winches[set_index].increment_target(winch_id, steps)
            self.main.sims[set_index].increment_target(winch_id, steps)
        return

    #---- methods to process MIDI messages -------------------------------------
    def note_on(self, channel, key, velocity):
        """Process a MIDI Note On event."""
        log.debug("WinchMIDILogic received note on: %d, %d", key, velocity)
        row, col, bank = self.decode_mpd218_key(key)

        # Each pair of pads maps to a single winch.  Each bank can address up to 8 winches (two sets).
        winch_index = 8*bank + 4*(row // 2) + col

        # Apply a non-linear scaling to the velocity.
        delta = int(velocity**1.6 * 0.125)
        if row == 1 or row == 3:
            delta = -delta
        self.increment_target(winch_index, delta)
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
            self.frequency = 0.05 + 0.1 * value
            self.set_freq_damping()

        elif knob == 2: # Knob #2 on on MPD218, use to control damping ratio
            self.damping_ratio = 0.05 + 0.01 * value
            self.set_freq_damping()

    def channel_pressure(self, channel, pressure):
        """Process a MIDI Channel Pressure event."""
        log.debug("channel aftertouch: %d", pressure)
        return

################################################################
class MainApp(rcp.app.MainApp):
    """Main application controller object holding any non-GUI related state."""

    def __init__(self):
        log.debug("Entering MainApp.__init__")

        # rcp.app.MainApp initialization, including the creation of the self.config object
        super().__init__()

        # load the configuration if available; this allows basic window setup to be specified
        self.load_configuration()
        self.num_winch_sets = self.config['winches'].getint('winch_sets', fallback=4)

        # create the interface window
        self.window = AppWindow(self)

        # initialize the winch set simulators
        self.sims = [rcp.sim.SimWinch() for i in range(self.num_winch_sets)]

        # Initialize the MIDI input system for controlling winches.
        self.winch_midi_logic = WinchMIDILogic(self)
        self.winch_midi_listener = rcp.midi.QtMIDIListener()
        self.winch_midi_listener.connect_midi_processor(self.winch_midi_logic)

        # Initialize the OSC message listener and dispatch system.
        self.osc_listener = rcp.osc.QtOSCListener()

        # Add endpoints to the OSC listener dispatch system.
        self.osc_listener.map_handler("/midi", self._received_remote_midi)
        self.osc_listener.map_handler("/dmx/*", self._received_remote_dmx)

        # Initialize the MIDI output system.
        self.midi_sender = rcp.midi.QtMIDISender()

        # Initialize the OSC message sender.
        self.osc_sender = rcp.osc.QtOSCSender()

        # Initialize the hardware winch system.
        self.winches = [rcp.winch.QtSerialWinch() for i in range(self.num_winch_sets)]

        # Initialize the DMX lighting output system.
        self.dmx = rcp.dmx.QtDMXUSBPro()
        self.dmx.set_size(self.config['dmx'].getint('channels'))

        # Finish connecting the window callbacks.
        self.window.connect_callbacks()

        # start the graphics animation timer
        self.frame_interval = 0.040
        self.frame_timer = QtCore.QTimer()
        self.frame_timer.start(1000*self.frame_interval)  # units are milliseconds
        self.frame_timer.timeout.connect(self.frame_timer_tick)

        return

    # ---- configuration management -------------------------------------------------
    def initialize_default_configuration(self):
        # Extend the default implementation to add application-specific defaults.
        super().initialize_default_configuration()
        self.config['log'] = {}
        self.config['osc'] = {}
        self.config['midi'] = { }
        self.config['dmx'] = {'channels' : 4, 'fixtures' : 1, 'channels_per_fixture' : 1, 'sliders' : 4}
        self.config['winches'] = {}
        return

    def save_configuration(self, path=None):
        # Extend the default implementation to gather up configuration values.
        self.window.gather_configuration(self.config)
        try:
            super().save_configuration(path)
        except PermissionError:
            log.warning("Unable to write configuration to %s", self.configuration_file_path)

    def apply_configuration(self):
        self.window.apply_user_configuration(self.config)

    # ---- application event handlers -----------------------------------------------
    def app_has_started(self):
        super().app_has_started()
        self.apply_configuration()
        self.osc_listener.open_receiver()
        self.osc_sender.open_sender()

    def app_is_exiting(self):
        self.dmx.close()
        for winch in self.winches:
            winch.close()
        super().app_is_exiting()

    # ---- process OSC network messages ---------------------------------------
    # The midi_osc_bridge.py tool can tunnel MIDI messages over the network as
    # OSC packets.  This routes any bridged MIDI data into the same performance
    # logic.
    def _received_remote_midi(self, msgaddr, *args):
        log.debug("remote midi: %s", " ".join([str(arg) for arg in args]))
        self.decode_message(args)
        return

    def _received_remote_dmx(self, msgaddr, *args):
        # This receives OSC messages prefixed with /dmx intended for direct
        # application to the DMX output, bypassing the control logic.
        log.debug("remote DMX: %s %s", msgaddr, " ".join([str(arg) for arg in args]))
        if msgaddr=='/dmx/fixture' and len(args) == 4:
            fixture = args[0]
            self.dmx_remote_update(fixture, args[1:])

    #---- methods related to DMX -------------------------------------
    def dmx_slider_change(self, channel, value):
        """Callback invoked when a DMX channel strip slider is moved."""
        self.dmx.set_channel(channel, value)

    #--- generate graphics animation updates ---------------------------------------------------
    def frame_timer_tick(self):
        # Method called at intervals by the animation timer to update the model and graphics.
        for winchset, sim in zip(self.window.winchSets, self.sims):
            sim.update_for_interval(self.frame_interval)
            positions = sim.positions()
            for pos, cartoon in zip(positions, winchset.winches()):
                cartoon.update_position(pos)


################################################################
def _main():
    # temporary increase in debugging output
    # rcp.app.add_console_log_handler()

    # capture log messages generated before the window opens
    mem_log_handler = rcp.app.add_memory_log_handler()

    # initialize the Qt system itself
    app = QtWidgets.QApplication(sys.argv)

    # create the main application controller
    main = MainApp()

    # finish the memory handler
    main.window.logDisplay.flush_and_remove_memory_handler(mem_log_handler)

    # Send a signal to be received after the application event loop starts.
    QtCore.QTimer.singleShot(0, main.app_has_started)

    # run the event loop until the user is done
    log.info("Starting event loop.")
    sys.exit(app.exec_())


################################################################
# Main script follows.  This sequence is executed when the script is initiated from the command line.

if __name__ == "__main__":
    _main()
