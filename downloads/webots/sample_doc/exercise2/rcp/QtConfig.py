"""PyQt5 widgets to create configuration fields and forms.
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
import os, logging

# for documentation on the PyQt5 API, see http://pyqt.sourceforge.net/Docs/PyQt5/index.html
from PyQt5 import QtCore, QtGui, QtWidgets

# set up logger for module
log = logging.getLogger('QtConfig')

# filter out most logging; the default is NOTSET which passes along everything
log.setLevel(logging.INFO)

################################################################
class QtConfigForm(QtWidgets.QWidget):
    """Composite widget to display a form of user-configuration entries."""

    def __init__(self):
        super().__init__()
        self.fields = list()
        self._grid = QtWidgets.QGridLayout()
        self.setLayout(self._grid)
        return

    def addField(self, prompt, widget):
        """Add a row to the configuration form.

        :param prompt: string of text to display on the left
        :param widget: a widget to both display status and receive and validate input
        """
        row = len(self.fields)

        label = QtWidgets.QLabel()
        label.setText(prompt)

        self._grid.addWidget(label, row, 0, 1, 1)
        self._grid.addWidget(widget, row, 1, 1, 1)
        self._grid.setRowStretch(row, 0)
        self.fields.append((label, widget))

        # keep adding a dummy widget at bottom to absorb vertical stretch
        self._grid.addWidget(QtWidgets.QWidget(), row+1, 0, 1, 1)
        self._grid.setRowStretch(row+1, 1)
        return

################################################################
class QtConfigText(QtWidgets.QLineEdit):
    """Composite widget enabling a user to configure an field of unvalidated text.

    :param callback: function called with argument (string)
    :param value: initial string, defaults to None which shows as blank
    """
    def __init__(self, callback, value=None):
        super().__init__()
        self.callback = callback
        self.value = value
        self.setText(value if value is not None else "")
        self.returnPressed.connect(self.validate_input)
        return

    def validate_input(self):
        """Called when the user finishes entering text into the line editor."""
        self.callback(self.text())
        return

################################################################
class QtConfigOSCPort(QtWidgets.QLineEdit):
    """Composite widget enabling a user to configure an address:portnum field.

    :param callback: function called with arguments (address-string, port-integer)
    :param address: host address string, defaults to 'localhost'
    :param portnum: UDP port integer, defaults to 3761
    """
    def __init__(self, callback=None, address='localhost', portnum=3761):
        super().__init__()
        self.callback = callback
        self.address = address
        self.portnum = portnum
        self.setText("%s:%d" % (address, portnum))
        self.returnPressed.connect(self.validate_input)
        return

    def set_OSC_port(self, address, portnum):
        """Set the network address and port display as if entered, validating the result and applying the callback."""
        log.debug("OSC address configured to %s:%d", address, portnum)
        self.setText("%s:%d" % (address, portnum))
        self.validate_input()

    def get_OSC_port(self):
        return self.address, self.portnum

    def validate_input(self):
        """Called when the user finishes entering text into the line editor."""
        name = self.text()
        if ':' in name:
            self.address, port = name.split(':', 1)
            portnum = int(port)
            if portnum >= 2048 and portnum < 65536:
                self.portnum = portnum
        else:
            self.address = name

        # normalize the text field
        self.setText('%s:%d' % (self.address, self.portnum))
        if self.callback is not None:
            self.callback(self.address, self.portnum)
        return

################################################################
class QtConfigComboBox(QtWidgets.QComboBox):
    """Composite widget enabling a user to select an item from a drop down list.

    :param callback: function called with argument (string)
    :param default: name of initial selection, defaults to '<no selection>'
    """

    def __init__(self, callback=None, default='<no selection>'):
        super().__init__()
        self.callback = callback
        self.default = default
        if self.default is not None:
            self.addItem(self.default)
        self.activated['QString'].connect(self._choose_item)
        return

    def set_items(self, names):
        self.clear()
        if self.default is not None:
            self.addItem(self.default)
        for name in names:
            self.addItem(name)
        return

    def _choose_item(self, name):
        """Called when the user selects an item name."""
        if self.callback is not None:
            self.callback(name)
        return

    def select_item(self, name):
        """Called to programmatically select an item; updates the display and applies the callback."""
        self.setCurrentText(name)
        self._choose_item(name)

    def current_item(self):
        return self.currentText()

################################################################
class QtConfigFileButtons(QtWidgets.QWidget):
    """Composite widget with buttons to control loading and saving a configuration file."""
    def __init__(self, delegate=None, path=None, extension = "config"):
        super().__init__()

        self.delegate = delegate
        self.path = path
        self.extension = extension

        self._layout = QtWidgets.QHBoxLayout()

        self.loadButton = QtWidgets.QPushButton()
        self.loadButton.setText("Load")

        self.reloadButton = QtWidgets.QPushButton()
        self.reloadButton.setText("Reload")

        self.saveButton = QtWidgets.QPushButton()
        self.saveButton.setText("Save")

        self.saveAsButton = QtWidgets.QPushButton()
        self.saveAsButton.setText("Save As...")

        self.loadButton.pressed.connect(self._load_pressed)
        self.reloadButton.pressed.connect(self._reload_pressed)
        self.saveButton.pressed.connect(self._save_pressed)
        self.saveAsButton.pressed.connect(self._saveas_pressed)

        self._layout.addWidget(self.loadButton)
        self._layout.addWidget(self.reloadButton)
        self._layout.addWidget(self.saveButton)
        self._layout.addWidget(self.saveAsButton)

        self.setLayout(self._layout)
        return

    # ---- button signal callbacks -----------------------------------------------------
    def _load_pressed(self):
        # open a modeless file open dialog for the user to select a configuration file to load
        folder = os.path.dirname(self.path) if self.path is not None else '.'
        self.load_dialog = QtWidgets.QFileDialog(parent=self, caption='Choose file', directory=folder, filter="*." + self.extension)
        self.load_dialog.fileSelected.connect(self._load_selected)
        if self.path is not None:
            self.load_dialog.selectFile(self.path)
        self.load_dialog.show()
        return

    def _reload_pressed(self):
        if self.delegate is not None:
            self.delegate.load_configuration()

    def _save_pressed(self):
        if self.delegate is not None:
            self.delegate.save_configuration()

    def _saveas_pressed(self):
        # open a modeless file save dialog for the user to select a path in which to save a configuration file
        folder = os.path.dirname(self.path) if self.path is not None else '.'
        self.save_dialog = QtWidgets.QFileDialog(parent=self, caption='Save configuration as...', directory=folder, filter="*." + self.extension)
        self.save_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        self.save_dialog.fileSelected.connect(self._save_selected)
        if self.path is not None:
            self.save_dialog.selectFile(self.path)
        self.save_dialog.show()
        return

    # ---- dialog signal callbacks -----------------------------------------------------
    def _load_selected(self, path):
        log.debug("configuration load selected: %s", path)
        self.path = path
        if self.delegate is not None:
            self.delegate.load_configuration(self.path)
        self.load_dialog.destroy()
        self.load_dialog = None

    def _save_selected(self, path):
        log.debug("configuration 'save as' selected: %s", path)
        basename, extension = os.path.splitext(path)
        self.path = basename + '.' + self.extension
        if self.delegate is not None:
            self.delegate.save_configuration(self.path)
        self.save_dialog.destroy()
        self.save_dialog = None


################################################################
