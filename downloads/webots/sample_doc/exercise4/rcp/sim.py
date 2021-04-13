"""Simulators for offline motion control testing.
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
import logging, math

# other library modules
from . import path

# set up logger for module
log = logging.getLogger('sim')

# filter out most logging; the default is NOTSET which passes along everything
# log.setLevel(logging.WARNING)

################################################################
class SimWinch(object):
    """Representation of a current multi-axis physical winch set.  This object is
    analogous to QtSerialWinch and implements the same command API.  Note that a
    larger performance setup could use multiple winch sets or simulators in
    coordination.

    This simulator does not calculate any line or fabric dynamics, it only
    runs dynamic path generators comparable to those in the firmware.
    """

    def __init__(self, count=4):
        self.paths = [path.Path() for i in range(count)]
        return

    def update_for_interval(self, interval):
        """Run the simulators for the given interval, which may include one or more integration steps."""
        for gen in self.paths:
            gen.update_for_interval(interval)
        return

    def positions(self):
        """Return a list of the current winch positions."""
        return [path.q for path in self.paths]

    #------------------------------------------------------------------------------
    # The command API follows which mimics the interface to the actual winches.

    def set_target(self, axis, position):
        """Set the target position of one or more axes.  N.B. that capstan winches can slip, so there is no
        guarantee of an repeatable line position, just the capstan itself.

        :param axis: either a integer axis number or list of axis numbers
        :param positions: either a integer step position or list of step positions
        """
        if isinstance(axis, int):
            self.paths[axis].set_target(position)
        else:
            for i, p in zip(axis, position):
                self.paths[i].set_target(p)

    def increment_target(self, axis, offset):
        """Add a signed offset to one or more target positions.  The units are dimensionless
        'steps'.  If using a microstepping driver, these may be less than a
        physical motor step.

        :param axis: either a integer axis number or list of axis numbers
        :param position: either a integer step offset or list of step offsets
        """
        if isinstance(axis, int):
            self.paths[axis].increment_target(offset)
        else:
            for i, d in zip(axis, offset):
                self.paths[i].increment_target(d)

    def set_velocity(self, axis, velocity):
        """Set the constant velocity of one or more targets.

        :param axis: either a integer axis number or list of axis numbers
        :param velocity: either an integer velocity or list of integer velocities
        """
        if isinstance(axis, int):
            self.paths[axis].set_velocity(velocity)
        else:
            for i, v in zip(axis, velocity):
                self.paths[i].set_velocity(v)


    def set_freq_damping(self, axis, freq, ratio):
        """Set the second order model resonance parameters for one or more path
        generators.  Note that the same parameters are applied to all specified
        axes, unlike the target setting functions.

        :param axis: either a integer axis number or list of axis numbers
        :param freq: scalar specifying the frequency in Hz
        :param ratio: scalar specifying the damping ratio, e.g. 1.0 at critical damping.
        """
        if isinstance(axis, int):
            self.paths[axis].set_freq_damping(freq, ratio)
        else:
            for i in axis:
                self.paths[i].set_freq_damping(freq, ratio)
        return

################################################################
