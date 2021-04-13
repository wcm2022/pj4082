"""Objects related to the application event loop and life cycle.  This uses
QtCore but not QtGui so this functionality is compatible with non-graphical
command-line programs.
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
import os, sys, logging, signal, configparser
import logging.handlers

# for documentation on the PyQt5 API, see http://pyqt.sourceforge.net/Docs/PyQt5/index.html
from PyQt5 import QtCore

# set up logger for module
log = logging.getLogger('app')

# filter out most logging; the default is NOTSET which passes along everything
# log.setLevel(logging.INFO)

################################################################
class MainApp(object):
    """Root application class for managing common elements of our applications.
    This is intended to be inherited by an top-level application controller
    along with other root classes which define specific interface API.

    :ivar config: configuration parser object to hold persistent user selections
    :ivar configuration_file_path: path of current configuration file, possibly not yet existing
    """

    def __init__(self):
        log.debug("Entered app.MainApp.__init__.")
        super().__init__()

        # Attach a handler to the keyboard interrupt (control-C).
        signal.signal(signal.SIGINT, self._sigint_handler)

        # Send a signal to be received after the application event loop starts.
        # N.B. the timing of this is platform-dependent, this was arriving too early on macOS.
        # QtCore.QTimer.singleShot(0, self.app_has_started)

        # Set the default location for loading and saving a configuration file, which may or may not exist yet.
        root, ext = os.path.splitext(sys.argv[0])
        self.configuration_file_path = root + '.config'
        log.debug("Assumed configuration path: %s", self.configuration_file_path)

        # Set up a global configuration object.
        self.config = configparser.ConfigParser()
        self.initialize_default_configuration()

        log.debug("Exiting app.MainApp.__init__.")
        return

    def app_has_started(self):
        """Callback to be invoked right after the main event loop begins.  This may be
        extended in child classes to implement startup behaviors which require a
        running event loop.
        """
        log.info("Application has started.")
        return

    def app_is_exiting(self):
        """Callback invoked right before the program ends, either from a keyboard
        interrupt window close.  This may be extended in child classes to clean
        up external resources, e.g., close any serial ports to remove associated
        lock files.
        """
        log.info("Application is exiting.")
        return

    def _sigint_handler(self, signal, frame):
        print("Keyboard interrupt caught, running close handlers...")
        self.app_is_exiting()
        sys.exit(0)

    def initialize_default_configuration(self):
        """Method to add default configuration values.  This is intended to be extended
        in child classes.  It is called during object initialization.
        """
        pass

    def load_configuration(self, path=None):
        """Method to load the current configuration file if it exists.  This is not
        called by default, it must be invoked explicitly by child classes."""
        if path is not None:
            self.configuration_file_path = path
        files_read = self.config.read(self.configuration_file_path)
        if len(files_read) > 0:
            log.info("Read configuration from %s", files_read)
        else:
            log.info("Unable to read configuration from %s", self.configuration_file_path)
        return

    def save_configuration(self, path=None):
        """Method to save the current configuration file.  This is not called by
        default, it must be invoked explicitly by child classes.
        """
        if path is not None:
            self.configuration_file_path = path
        with open(self.configuration_file_path, 'w') as configfile:
            self.config.write(configfile)
        log.info("Wrote configuration to %s", self.configuration_file_path)
        return

################################################################
def add_console_log_handler(level=logging.DEBUG):
    """Add an additional root log handler to stream messages to the console."""
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter('%(levelname)s:%(name)s: %(message)s'))
    logging.getLogger().addHandler(console_handler)
    if logging.getLogger().level > level:
        logging.getLogger().setLevel(level)

def add_file_log_handler(path, level=logging.DEBUG):
    """Add an additional root log handler to stream messages to a file."""
    file_handler = logging.FileHandler(path)
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S"))
    logging.getLogger().addHandler(file_handler)
    if logging.getLogger().level > level:
        logging.getLogger().setLevel(level)

def add_memory_log_handler(level=logging.DEBUG):
    """Add an additional root log handler to capture messages in memory.  Returns
    the handler object.  No default target handler is set.  This is intended to
    capture the early startup log before normal output (e.g. logging window) is
    established.
    """
    memory_handler = logging.handlers.MemoryHandler(capacity=1000, flushLevel=logging.ERROR+10)
    memory_handler.setLevel(level)
    logging.getLogger().addHandler(memory_handler)
    if logging.getLogger().level > level:
        logging.getLogger().setLevel(level)
    return memory_handler

################################################################
