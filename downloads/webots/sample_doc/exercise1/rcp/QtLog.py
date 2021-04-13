"""PyQt5 widgets to show and control logging output.
"""

################################################################
# Written in 2017-2019 by Garth Zeglin <garthz@cmu.edu>

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
from PyQt5 import QtCore, QtGui, QtWidgets

# set up logger for module
log = logging.getLogger('QtLog')

################################################################
class QtLog(QtWidgets.QWidget):
    """Composite widget including log text output and control widgets.

    :param level: initial logging level, defaults to logging.WARNING
    :param logger: logger object to which to attach, defaults to root logger
    """

    def __init__(self, level = None, logger = None):
        super().__init__()

        if logger is None:
            # if no logger provided, attach to the root logger
            self._logger = logging.getLogger()
        else:
            self._logger = logger

        self._handler = logging.StreamHandler(self)
        self._handler.setFormatter(logging.Formatter('%(levelname)s:%(name)s: %(message)s'))
        self._logger.addHandler(self._handler)

        if level not in (logging.WARNING, logging.INFO, logging.DEBUG):
             level = logging.WARNING

        # set the handler to the requested level, but turn off the logger level
        # filtering; the logger could be attached to other handlers, so this
        # will apply level filters at the handlers
        self._handler.setLevel(level)
        self._logger.setLevel(logging.NOTSET)

        self._layout = QtWidgets.QVBoxLayout()
        self.setLayout(self._layout)

        controls_box = QtWidgets.QHBoxLayout()
        self._layout.addLayout(controls_box)

        level_label = QtWidgets.QLabel()
        level_label.setText("Global log display level:")
        controls_box.addWidget(level_label)

        self.level_selector = QtWidgets.QComboBox()
        self.level_selector.addItem("Normal")
        self.level_selector.addItem("Verbose")
        self.level_selector.addItem("Debug")
        self.level_selector.setCurrentIndex({logging.WARNING:0, logging.INFO:1, logging.DEBUG:2}[level])
        controls_box.addWidget(self.level_selector)
        self.level_selector.activated['QString'].connect(self._set_logging_level)

        self.log_output = QtWidgets.QPlainTextEdit()
        self.log_output.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self._layout.addWidget(self.log_output)

        return

    def write(self, string):
        """Write output to the log text area.  This enables this object to be used as a stream for printing."""
        stripped = string.rstrip()
        if stripped != "":
            self.log_output.appendPlainText(stripped)
        return

    def _set_logging_level(self, title):
        # receive a signal when the user chooses an item, possibly unchanged
        log.info("Requested logging level: %s", title)
        levels = {'Normal': logging.WARNING,
                  'Verbose': logging.INFO,
                  'Debug': logging.DEBUG}
        level = levels.get(title, None)
        if level is not None:
            self._handler.setLevel(level)
            log.info("Set logging level to %r", level)

    def set_logging_level(self, title):
        """Set the current logging level and level display."""
        self._set_logging_level(title)
        self.level_selector.setCurrentText(title)

    def get_logging_level(self):
        return self.level_selector.currentText()

    def flush_and_remove_memory_handler(self, mem_handler):
        mem_handler.setTarget(self._handler)
        mem_handler.flush()
        self._logger.removeHandler(mem_handler)

################################################################
