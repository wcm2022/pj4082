"""Path generator objects for simulating low-level motion control.
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
import math

################################################################
class Path(object):
    """Representation of the current path generator for a single winch.  This keeps
    the physical calculations separate from the graphics.  This reimplements the
    functionality of Path.h and Path.cpp in the StepperWinch Arduino sketch.
    The model is based on a second-order simple harmonic oscillator.

    The command API should be kept compatible with the winch interface class which
    transmits commands over a serial port to an Arduino-based winch.
    """

    def __init__(self):
        # Model based on StepperWinch/Path.  Units are 800 steps/rev.
        self.q = 0.0    	   # current model position, in dimensionless units (e.g. step or encoder counts)
        self.qd = 0.0   	   # current model velocity in units/sec
        self.qdd = 0.0  	   # current model acceleration, in units/sec/sec
        self.q_d = 0.0  	   # current model target position in dimensionless units
        self.qd_d = 0.0            # current model target velocity in dimensionless units/sec
        self.t = 0.0    	   # elapsed model time, in seconds
        self.k = 4*math.pi*math.pi # proportional feedback gain, in (units/sec/sec)/(units), which is (1/sec^2)
        self.b = 1.0    	   # derivative feedback gain, in (units/sec/sec)/(units/sec), which is (1/sec)
        self.qd_max = 3500.0       # maximum allowable speed in units/sec
        self.qdd_max = 35000.0     # maximum allowable acceleration in units/sec/sec
        return

    def update_for_interval(self, interval):
        """Run the simulator for the given interval, which may include one or more integration steps."""
        while interval > 0.0:
            dt = min(interval, 0.005)
            interval -= dt
            self.step(dt)

    def step(self, dt):
        # Model based on StepperWinch/Path.  Units are 800 steps/rev.
        # calculate the derivatives
        self.qdd = self.k * (self.q_d - self.q) + self.b * (self.qd_d - self.qd)

        # clamp the acceleration within range for safety
        self.qdd = min(self.qdd_max, max(self.qdd, -self.qdd_max))

        # integrate one time step
        self.q   += self.qd  * dt
        self.qd  += self.qdd * dt
        self.q_d += self.qd_d * dt # integrate the target velocity into the target position
        self.t   += dt

        # clamp the model velocity within range for safety
        self.qd = min(self.qd_max, max(self.qd, -self.qd_max))

        return

    #------------------------------------------------------------------------------
    # The command API follows which mimics the interface to the actual winches.
    def set_target(self, position):
        """Set the absolute target position in dimensionless units."""
        self.q_d = position
        return

    def increment_target(self, offset):
        """Add a signed offset to the target position.  The units are dimensionless
        'steps'.  If using a microstepping driver, these may be less than a
        physical motor step.
        """
        self.q_d += offset
        return

    def set_velocity(self, velocity):
        """Set the constant velocity of the target in units/sec"""
        self.qd_d = velocity
        return

    def set_freq_damping(self, freq, damping):
        """Convenience function to set second order model gains in terms of natural
        frequency and damping ratio.  The frequency is in Hz, the damping ratio
        is 1.0 at critical damping.
        """
        self.k = freq * freq * 4 * math.pi * math.pi
        self.b = 2 * math.sqrt(self.k) * damping
        return


################################################################
