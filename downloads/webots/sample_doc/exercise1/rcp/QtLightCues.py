"""PyQt5 GUI objects for editing DMX lighting cues."""
################################################################
# Written in 2019 by Garth Zeglin <garthz@cmu.edu>

# To the extent possible under law, the author has dedicated all copyright
# and related and neighboring rights to this software to the public domain
# worldwide. This software is distributed without any warranty.

# You should have received a copy of the CC0 Public Domain Dedication along with this software.
# If not, see <http://creativecommons.org/publicdomain/zero/1.0/>.

################################################################
# documentation references:
#   https://doc.qt.io/qt-5/qabstracttablemodel.html
#   https://doc.qt.io/qt-5/qabstractitemmodel.html
#   https://doc.qt.io/qt-5/qt.html#ItemDataRole-enum

#   https://doc.qt.io/qt-5/qtableview.html
#   https://doc.qt.io/qt-5/qabstractitemview.html

#   https://doc.qt.io/qt-5/qcolordialog.html
################################################################
# standard Python libraries
from __future__ import print_function
import os, logging, functools, csv, itertools
import numpy as np

# for documentation on the PyQt5 API, see http://pyqt.sourceforge.net/Docs/PyQt5/index.html
from PyQt5 import QtCore, QtGui, QtWidgets
from . import QtConfig

# set up logger for module
log = logging.getLogger('QtLightingCues')

# filter out most logging; the default is NOTSET which passes along everything
# log.setLevel(logging.WARNING)

################################################################$
class LightingCueModel(QtCore.QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self.cues = [['Blackout', [0, 0, 0], [0, 0, 0]],
                     ['Red', [255, 0, 0], [255, 0, 0]],
                     ['Green', [0, 255, 0], [0, 255, 0]],
                     ['Blue', [0, 0, 255], [0, 0, 255]],
                     ['Half', [128, 128, 128], [128, 128, 128]],
                     ['White', [255, 255, 255], [255, 255, 255]],
                     ]

        return

    def cue_name(self, index):
        """Return the cue name for a given row index."""
        return self.cues[index][0]

    def cue_colors(self, index):
        """Return a list of (R,G,B) color tuples for a given ow index.  Returns None if the index is invalid."""
        if index < 0 or index >= len(self.cues):
            return None
        else:
            return self.cues[index][1:]

    def set_cues(self, new_cues):
        self.beginResetModel()
        self.cues = new_cues
        self.endResetModel()

    def rowCount(self, parent=None):
        return len(self.cues)

    def columnCount(self, parent=None):
        return len(self.cues[0])

    def set_color(self, current, color):
        row = current.row()
        col = current.column()
        self.cues[row][col] = (color.red(), color.green(), color.blue())
        self.dataChanged.emit(current, current)

    def data(self, index, role):
        row = index.row()
        col = index.column()

        if role == QtCore.Qt.DisplayRole:
            if col == 0:
                return self.cues[row][0]
            else:
                # showing an individual light cue color as a hex number
                colors = self.cues[row][col]
                return "%02x%02x%02x" % tuple(colors)

        elif role == QtCore.Qt.DecorationRole:
            if col > 0:
                # showing an individual light cue as a color sample next to the text
                colors = self.cues[row][col]
                return QtGui.QColor(*colors)

        return QtCore.QVariant()

    # ------------------------------------------------------------------------------
    def _translate_color(self, name):
        # translate a user-provided string designating a color into an integer (R, G, B) color tuple or None

        # ad hoc table of convenient shortcut names
        shortcuts = {'r':'#ff0000', 'o':'#ffa500', 'y':'#ffff00', 'g':'#00ff00', 'b':'#0000ff', 'i':'#4b0082', 'v':'#ee82ee',
                     'w':'#ffffff', 'z':'#000000'}

        # first try the shortcut list to translate to a canonical hex name
        if name in shortcuts:
            name = shortcuts[name]
            log.debug("Found shortcut: %s", name)

        # then try the Qt presets
        color = QtGui.QColor(name)
        if color.isValid():
            return color.red(), color.green(), color.blue()

        # test for three-letter hex RGB values
        if len(name) == 3:
            try:
                value = int(name, base=16)
                return (value & 0xf00) >> 4, (value & 0x0f0), (value & 0x00f) << 4
            except ValueError:
                pass

        # test for six-letter hex RGB values
        if len(name) == 6:
            try:
                value = int(name, base=16)
                return (value & 0xff0000) >> 16, (value & 0x00ff00) >> 8, (value & 0x0000ff)
            except ValueError:
                pass

        # if all else fails
        return None

    # ------------------------------------------------------------------------------
    def setData(self, index, value, role):
        row = index.row()
        col = index.column()
        log.debug("LightingCueModel setData for %d, %d, role %d == %s", row, col, role, value)
        if role == QtCore.Qt.EditRole:
            if col == 0:
                # update the cue name
                self.cues[row][0] = value
                self.dataChanged.emit(index, index)
                return True
            else:
                rgb = self._translate_color(value)
                log.debug("setData translated %s to %s", value, rgb)
                if rgb is not None:
                    self.cues[row][col] = rgb
                    self.dataChanged.emit(index, index)
                    return True

        # if not accepted, return False
        return False

    def flags(self, index):
        # every data field can be selected or edited
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable

    def headerData(self, section, orientation, role):
        # log.debug("LightingCueModel headerData requested for section %d role %d", section, role)

        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                # provide column names across the top
                if section == 0:
                    return "Cue Name"
                else:
                    return "Light %d" % section

            elif orientation == QtCore.Qt.Vertical:
                # visually number the rows starting with one
                return section+1

        elif role == QtCore.Qt.InitialSortOrderRole and section == 0:
            return QtCore.Qt.AscendingOrder

        elif role == QtCore.Qt.TextAlignmentRole:
            return QtCore.Qt.AlignCenter

        # else no valid value
        return QtCore.QVariant()

################################################################
class LightingCueTableView(QtWidgets.QTableView):

    # class variable with Qt signal used to broadcast cue selection changed
    currentCueChanged = QtCore.pyqtSignal(int, name='currentCueChanged')

    def __init__(self):
        super().__init__()
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
        self.setSortingEnabled(False)

    def currentChanged(self, current, previous):
        # log.debug("Current cue item now %d, %d", current.row(), current.column())
        super().currentChanged(current, previous)
        self.currentCueChanged.emit(current.row())

    def _set_current_color(self, color):
        current = self.currentIndex()
        if current.isValid():
            if current.column() > 0:
                self.model().set_color(current, color)
                self.currentCueChanged.emit(current.row())

################################################################
class QtLightingCuePanel(QtWidgets.QWidget):
    """A composite window providing a lighting cue table with associated controls.
    """

    # class variable with Qt signal used to broadcast cue changes
    cueChanged = QtCore.pyqtSignal(tuple, name='cueChanged')

    def __init__(self):
        super().__init__()

        self._layout = QtWidgets.QVBoxLayout()
        self.setLayout(self._layout)

        # Path name of current cue set, or None.
        self.cue_file_path = None

        # create the GUI elements
        self._setupUi()
        self.show()
        return

    def set_cue_file_path(self, path):
        log.debug("default_cue_file_path: %s", path)
        self.cueFileButtons.path = path
        self.cue_file_path = path
        self.cueFileLabel.setText(path)
        return

    # ---- color cue access methods -------------------------------------------------------------------------------
    def get_cue_name(self, cuenum):
        """Return the user-specified descriptor for the given cue number.
        The cues are sequentially numbered by table row starting with zero."""
        return self.cueTable.model().cue_name(cuenum)

    def get_cue_colors(self, cuenum):
        """Return a list of integer (red, green, blue) tuples for the given cue number.
        The cues are sequentially numbered by table row starting with zero."""
        return self.cueTable.model().cue_colors(cuenum)

    # ------------------------------------------------------------------------------------------------
    def _setupUi(self):

        self.cueFileButtons = QtConfig.QtConfigFileButtons(delegate=self, extension="csv")
        labelbox = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel()
        label.setText("Lighting Cue Path:")
        labelbox.addWidget(label)
        self.cueFileLabel = QtWidgets.QLabel()
        self.cueFileLabel.setText("<none set>")
        labelbox.addWidget(self.cueFileLabel)
        labelbox.addStretch(1) # absorb empty space on right to keep filename left-justified

        # Create a table with a default cue list.
        self.cueTable = LightingCueTableView()
        self.cueTable.setModel(LightingCueModel())
        self.cueTable.resizeColumnsToContents()
        self.cueTable.currentCueChanged.connect(self._current_cue_changed)
        self.cueTable.model().dataChanged.connect(self._cue_data_changed)
        self.buttonRow = QtWidgets.QHBoxLayout()
        self.buttonRow.setContentsMargins(20, 0, 11, 0)
        self.lightingCuePickerButton = QtWidgets.QPushButton()
        self.lightingCuePickerButton.setText("Show Color Picker")
        self.lightingCuePickerButton.pressed.connect(self._show_color_picker)
        self.buttonRow.addWidget(QtWidgets.QWidget())
        self.buttonRow.addWidget(self.lightingCuePickerButton)
        self.buttonRow.addWidget(QtWidgets.QWidget())

        self._layout.addLayout(labelbox)
        self._layout.addWidget(self.cueFileButtons)
        self._layout.addWidget(self.cueTable)
        self._layout.addLayout(self.buttonRow)

        # create a persistent color dialog but don't show it yet
        self.color_picker = QtWidgets.QColorDialog(self)
        self.color_picker.setOption(QtWidgets.QColorDialog.NoButtons)
        self.color_picker.currentColorChanged.connect(self._set_current_color)

        return

    # --- cue panel events ----------------------------------------------------------------------------
    def _set_current_color(self, color):
        self.cueTable._set_current_color(color)

    def _show_color_picker(self):
        if self.color_picker.isHidden():
            self.color_picker.show()

    def _cue_data_changed(self, ul, lr):
        idx = ul.row()
        log.debug("Cue %d updated.", idx)
        self.cueChanged.emit((self.get_cue_colors(idx), self.get_cue_name(idx), idx))

    def _current_cue_changed(self, idx):
        log.debug("Cue %d now current.", idx)
        self.cueChanged.emit((self.get_cue_colors(idx), self.get_cue_name(idx), idx))

    # --- cue list file I/O --------------------------------------------------------------------------
    def _parse_value(self, field):
        try:
            return int(field)
        except ValueError:
            return 0

    def load_configuration(self, path=None):
        log.debug("Cue panel load_configuration: %s", path)
        if path is not None:
            self.cue_file_path = path
        try:
            with open(self.cue_file_path, newline='') as csvfile:
                cuereader = csv.reader(csvfile)
                header = next(cuereader)
                channels = (len(header) - 1) // 3
                cues = list()
                for cue in cuereader:
                    if len(cue) > 0:
                        record = [cue[0]]
                        values = [self._parse_value(s) for s in cue[1:]]
                        colors = [c for c in zip(values[0::3], values[1::3], values[2::3])]
                        if len(colors) < channels:
                            colors += [(0,0,0)] * (channels - len(colors)) # pad with black
                        elif len(colors) > channels:
                            colors = colors[0:channels]  # truncate excess
                        record.extend(colors)
                        cues.append(record)

                self.cueTable.model().set_cues(cues)
        except:
            log.warning("Unable to load %s", self.cue_file_path)

    def save_configuration(self, path=None):
        log.debug("Cue panel save_configuration: %s", path)
        if path is not None:
            self.cue_file_path = path
        try:
            with open(self.cue_file_path, 'w', newline='') as csvfile:
                cuewriter = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
                model = self.cueTable.model()

                channels = model.columnCount() - 1
                # generate CSV header row
                header = ["Cue Name"]
                for i in range(channels):
                    header.extend(["red%d" % (i+1), "green%d" % (i+1), "blue%d" % (i+1)])
                cuewriter.writerow(header)

                # clumsy
                for row in range(model.rowCount()):
                    colors = model.cue_colors(row)  # list of color tuples
                    data = [model.cue_name(row)]
                    data.extend(itertools.chain(*colors))
                    cuewriter.writerow(data)

        except PermissionError:
            log.warning("Unable to write lighting cues to %s", self.cue_file_path)
