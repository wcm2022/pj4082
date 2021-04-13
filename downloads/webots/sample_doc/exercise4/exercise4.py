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
import os, sys, logging, functools, time, csv, random
import numpy as np

# for documentation on the PyQt5 API, see http://pyqt.sourceforge.net/Docs/PyQt5/index.html
from PyQt5 import QtCore, QtWidgets, QtGui

# documentation on pyqtgraph:  http://pyqtgraph.org/documentation/plotting.html
import pyqtgraph

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

# import the script procedure
import script.ex4demo

# set up logger for module
log = logging.getLogger('ex4')

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
        self.setWindowTitle("RCP System Controller: Exercise 4")
        self.statusbar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.statusbar)

        # set up tabbed page structure
        self.tabs = QtWidgets.QTabWidget()
        self.setCentralWidget(self.tabs)
        self.tabs.currentChanged.connect(self._tab_changed)

        # ================================================================
        # set up the graphics tab with the system visualizer
        self.graphicsTab = QtWidgets.QWidget(self)
        self.graphicsLayout = QtWidgets.QVBoxLayout(self.graphicsTab)
        self.tabs.addTab(self.graphicsTab, 'Graphics')

        # cartoon graphics using a QGraphicsScene and an optional OpenGL view
        upper_left  = (-100, -100)
        lower_right = ( 700,  700)
        scene_width  = lower_right[0] - upper_left[0]
        scene_height = lower_right[1] - upper_left[1]
        self.scene = QtWidgets.QGraphicsScene(upper_left[0], upper_left[1], scene_width, scene_height)
        self.view = QtWidgets.QGraphicsView(self.scene)
        self.view.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        # self.view.setViewport(QtWidgets.QOpenGLWidget())
        self.view.fitInView(QtCore.QRectF(upper_left[0], upper_left[1], scene_width, scene_height), QtCore.Qt.KeepAspectRatio)
        self.graphicsLayout.addWidget(self.view)

        self.winchSets = []
        for s in range(4):
            winchset = rcp.QtWinch.QtWinchSetItem(location=(0, 200*s))
            self.scene.addItem(winchset)
            self.winchSets.append(winchset)
        
        # ================================================================
        # plotting area with phase plot
        self.plotTab = QtWidgets.QWidget(self)
        self.plotLayout = QtWidgets.QVBoxLayout(self.plotTab)
        self.tabs.addTab(self.plotTab, 'Plot')

        self.configPlot = pyqtgraph.PlotWidget()
        self.plotLayout.addWidget(self.configPlot)

        self.config_data_1 = np.zeros((300, 2))
        self.config_plot_1 = pyqtgraph.ScatterPlotItem(size=len(self.config_data_1), brush=pyqtgraph.mkBrush(0, 255, 0, 255))
        self.config_plot_1.setSize(2)
        self.configPlot.addItem(self.config_plot_1)

        self.config_data_2 = np.zeros((300, 2))
        self.config_plot_2 = pyqtgraph.ScatterPlotItem(size=len(self.config_data_2), brush=pyqtgraph.mkBrush(0, 0, 255, 255))
        self.config_plot_2.setSize(2)
        self.configPlot.addItem(self.config_plot_2)

        self.configPlot.getPlotItem().setTitle(title='Configuration Space Plot')
        self.configPlot.getPlotItem().setLabel(axis='left', text='q1')
        self.configPlot.getPlotItem().setLabel(axis='bottom', text='q0')
        self.configPlot.getPlotItem().setYRange(-3.16, 3.16)
        self.configPlot.getPlotItem().setXRange(-3.16, 3.16)

        # ================================================================
        # scripting tab
        self.scriptTab = QtWidgets.QWidget(self)
        self.tabs.addTab(self.scriptTab, 'Script')
        self.scriptLayout = QtWidgets.QVBoxLayout(self.scriptTab)        
        self.scriptConsoleOutput = QtWidgets.QPlainTextEdit()     # scrolling text box for controller messages
        self.scriptLayout.addWidget(self.scriptConsoleOutput)

        # generate a row of buttons which act as command macros
        self.buttonLayout = QtWidgets.QHBoxLayout()
        for item in [["Reset", "reset"], ["Play", "play"], ["Stop", "stop"]]:
            button = QtWidgets.QPushButton()
            button.setText(item[0])
            button.pressed.connect(functools.partial(self.scriptButtonPressed, item[1]))
            self.buttonLayout.addWidget(button)
        self.scriptLayout.addLayout(self.buttonLayout)
        
        # generate a single-line text field for the command input
        commandbox = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel()
        label.setText("Script commands:")
        commandbox.addWidget(label)
        self.commandLine = QtWidgets.QLineEdit()
        commandbox.addWidget(self.commandLine)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.commandLine.sizePolicy().hasHeightForWidth())
        self.commandLine.setSizePolicy(sizePolicy)
        self.commandLine.returnPressed.connect(self.scriptCommandEntered)
        self.scriptLayout.addLayout(commandbox)

        # ================================================================
        # tab with array of general-purpose horizontal sliders
        self.sliderTab = QtWidgets.QWidget(self)
        self.sliderLayout = QtWidgets.QVBoxLayout(self.sliderTab)
        self.tabs.addTab(self.sliderTab, 'Sliders')

        self.sliderLayout.setContentsMargins(-1, -1, -1, 9)
        self.sliders = list()
        for i in range(8):
            box = QtWidgets.QHBoxLayout() # box for label and slider
            slider = QtWidgets.QSlider()
            slider.setMinimumSize(QtCore.QSize(60, 20))
            slider.setMaximum(1000)
            slider.setOrientation(QtCore.Qt.Horizontal)
            slider.valueChanged['int'].connect(functools.partial(self.sliderMoved, i))
            self.sliders.append(slider)
            label = QtWidgets.QLabel()
            label.setText("%d: " % (i))
            box.addWidget(label)
            box.addWidget(slider)
            self.sliderLayout.addLayout(box)

        # add a final empty widget to soak up space
        self.sliderLayout.addWidget(QtWidgets.QWidget())

        # ================================================================
        # winch MIDI input simulator tab
        self.midiTab = QtWidgets.QWidget(self)
        self.midiLayout = QtWidgets.QVBoxLayout(self.midiTab)
        self.winch_MIDI_controller = rcp.QtMPD218.QtMPD218()     # generate a simulated MPD218 controller
        self.midiLayout.addWidget(self.winch_MIDI_controller)
        self.tabs.addTab(self.midiTab, 'MIDI')

        # ================================================================
        # DMX controller tab
        self.dmxTab = QtWidgets.QWidget(self)
        self.dmxLayout = QtWidgets.QVBoxLayout(self.dmxTab)
        self.tabs.addTab(self.dmxTab, 'DMX')

        self.DMX_controller = rcp.QtDMX.QtDMXControls(channels = self.main.config['dmx'].getint('sliders'))
        self.dmxLayout.addWidget(self.DMX_controller)


        # ================================================================
        # configuration tab
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

        # ================================================================
        # set up the logging tab
        self.logDisplay = rcp.QtLog.QtLog(level=logging.INFO)
        self.tabs.addTab(self.logDisplay, 'Log')

        return

    # --- window and Qt event processing -------------------------------------------------------------
    def set_status(self, string):
        """Update the status bar at the bottom of the display to show the provided string."""
        self.statusbar.showMessage(string)
        return

    def scriptCommandEntered(self):
        """Callback invoked whenever command line text is entered on the script tab."""
        command = self.commandLine.text()
        self.commandLine.clear()
        self.writeScriptConsole('> ' + command)

        # send the form for evaluation
        self.main.script.input.put(('console', command))
        return

    def scriptButtonPressed(self, command):
        """Callback invoked whenever a script pushbutton is pressed."""
        self.writeScriptConsole('button: ' + command)

        # send the form for evaluation
        self.main.script.input.put(('console', command))        
        return

    def writeScriptConsole(self, string):
        """Write output to the console text area."""
        self.scriptConsoleOutput.appendPlainText(string.rstrip())
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
    
    def sliderMoved(self, slider, value):
        # send a message to the user controller object; this is really reaching across abstraction boundaries
        for controller in self.main.controllers:
            controller.user_parameter_change(slider, 0.001*value)
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
class MotionPrimitives(object):
    """Class to encapsulate the set of motion primitives available for this
    performance.  This also abstracts the basic interface to both motor and
    simulation and supports periodic execution.
    """

    def __init__(self, main):
        super().__init__()
        self.main  = main

        # global parameters
        self.tempo = 60.0     # beats per minute
        self.magnitude = 1.0
        self.frequency = 1.0
        self.damping_ratio = 1.0
        self.all_axes = range(4) # index list for updating all motors

        # algorithmic generators
        self.random_mode = False
        self.random_mode_timer = 0
        
        # try reading the pose table
        self.poses = {}
        self.pose_csv_path = 'exercise4.poses'
        with open(self.pose_csv_path, newline='') as posefile:
            posereader = csv.reader(posefile)
            for pose in posereader:
                if len(pose) > 0:
                    name = pose[0]
                    positions = [int(s) for s in pose[1:]]
                    self.poses[name] = positions
        log.debug("Read pose table: %s", self.poses)
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

    def set_target(self, winch_index, steps):
        """Map a given winch index to the particular winch set."""
        set_index = winch_index // 4
        winch_id = winch_index % 4
        if set_index < self.main.num_winch_sets:
            self.main.winches[set_index].set_target(winch_id, steps)
            self.main.sims[set_index].set_target(winch_id, steps)
        return

    def set_velocity(self, winch_index, steps):
        """Map a given winch index to the particular winch set."""
        set_index = winch_index // 4
        winch_id = winch_index % 4
        if set_index < self.main.num_winch_sets:
            self.main.winches[set_index].set_velocity(winch_id, steps)
            self.main.sims[set_index].set_velocity(winch_id, steps)
        return
    
    #--- methods for processing cue messages -------------------
    def set_frequency(self, f):
        self.frequency = f;
        self.set_freq_damping()
        return
    
    def set_damping(self, d):
        self.damping_ratio = d;
        self.set_freq_damping()
        return

    def set_pose(self, name):
        position = self.poses.get(name)
        if position is not None:
            for i, p in enumerate(position):
                self.set_target(i, p)
        
    def process_cue(self, args):
        if args[0] == 'pose':
            self.set_pose(args[1])
            
        elif args[0] == 'random':
            self.random_mode = args[1]

        elif args[0] == 'tempo':
            self.tempo = args[1]

        elif args[0] == 'magnitude':
            self.magnitude = args[1]
            
        elif args[0] == 'gains':
            self.frequency = args[1]
            self.damping   = args[2]
            self.set_freq_damping()
        return

    #--- methods for periodic algorithmic activity -----------
    def update_for_interval(self, interval):
        if self.random_mode:
            self.random_mode_timer -= interval
            if self.random_mode_timer < 0:
                self.random_mode_timer += self.tempo/60.0
                winch = random.randint(0,3)
                limit = int(800*self.magnitude)
                offset = random.randint(-limit, limit)
                self.increment_target(winch, offset)
        
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
            # Each pair of pads maps to a single winch.  Each bank can address up to 8 winches (two sets).
            winch_index = 8*bank + 4*(row // 2) + col

            # Apply a non-linear scaling to the velocity.
            delta = int(velocity**1.6 * 0.125)
            if row == 1 or row == 3:
                delta = -delta
            self.primitives.increment_target(winch_index, delta)

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

        # Initialize the motion primitive system.
        self.primitives = MotionPrimitives(self)
        
        # Initialize the MIDI input system for controlling winches.
        self.winch_midi_logic = WinchMIDILogic(self)
        self.winch_midi_listener = rcp.midi.QtMIDIListener()
        self.winch_midi_listener.connect_midi_processor(self.winch_midi_logic)

        # Initialize the OSC message listener and dispatch system.
        self.osc_listener = rcp.osc.QtOSCListener()

        # Add endpoints to the OSC listener dispatch system.
        self.osc_listener.map_handler("/cue", self._received_remote_cue)

        # Initialize the MIDI output system.
        self.midi_sender = rcp.midi.QtMIDISender()

        # Initialize the OSC message sender.
        self.osc_sender = rcp.osc.QtOSCSender()

        # Initialize the hardware winch system.
        self.winches = [rcp.winch.QtSerialWinch() for i in range(self.num_winch_sets)]

        # Initialize the DMX lighting output system.
        self.dmx = rcp.dmx.QtDMXUSBPro()
        self.dmx.set_size(self.config['dmx'].getint('channels'))

        # Create the script object.
        self.script = script.ex4demo.Ex4DemoScript()

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
        self.script.start()        # start the script thread
        return
    
    def app_is_exiting(self):
        self.dmx.close()
        for winch in self.winches:
            winch.close()
        super().app_is_exiting()
        return
    
    # ---- process OSC network messages ---------------------------------------
    def _received_remote_cue(self, msgaddr, *args):
        """Process OSC messages received to the /cue address."""
        log.info("remote cue: %s", " ".join([str(arg) for arg in args]))
        self.primitives.process_cue(args)
        return

    #---- methods related to DMX -------------------------------------
    def dmx_slider_change(self, channel, value):
        """Callback invoked when a DMX channel strip slider is moved."""
        self.dmx.set_channel(channel, value)

    #---- methods related to the performance script -------------------------------------
    def poll_script_queues(self):
        while not self.script.output.empty():
            item = self.script.output.get()
            tag = item[0]
            if tag == 'console':
                self.window.writeScriptConsole(item[1])
                
            elif tag == 'cue':
                self.primitives.process_cue(item[1:])
        
    #--- generate graphics animation updates ---------------------------------------------------
    def frame_timer_tick(self):
        # Method called at intervals by the animation timer to update the model and graphics.
        self.poll_script_queues()
        self.primitives.update_for_interval(self.frame_interval)
        
        # update the winch simulation
        for sim in self.sims:
            sim.update_for_interval(self.frame_interval)
            
        # update the target winch positions reported by the simulation
        for winch_cartoon, sim in zip(self.window.winchSets, self.sims):
            winch_cartoon.update_targets(sim.positions())

        # update the actual winch positions reported by the hardware
        for winch_cartoon, winch_hardware in zip(self.window.winchSets, self.winches):
            winch_cartoon.update_winches(winch_hardware.winch_positions)
        

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
