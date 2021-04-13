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
import numpy as np

################################################################
class NPath(object):
    """Representation of a set of winch path generators. This keeps the physical
    calculations separate from the graphics.  This reimplements the
    functionality of Path.h and Path.cpp in the StepperWinch Arduino sketch.
    The model is based on a second-order simple harmonic oscillator.  The model
    is vectorized using numpy to calculate multiple models simultaneously.  It
    uses single-precision floating point to better simulate the Arduino model.

    The command API should be kept compatible with the winch interface class which
    transmits commands over a serial port to an Arduino-based winch.

    """

    def __init__(self, N=4):

        self.N = N                 # number of generators
        self.zeros = np.zeros(self.N, dtype=np.float32)    # constant array of zeros of the right length
        
        # Model based on StepperWinch/Path. 
        self.q    = np.zeros(self.N, dtype=np.float32)     # current model position, in dimensionless units (e.g. step or encoder counts)
        self.qd   = np.zeros(self.N, dtype=np.float32)     # current model velocity (units/sec)
        self.qdd  = np.zeros(self.N, dtype=np.float32)     # current model acceleration (units/sec/sec)
        self.q_d  = np.zeros(self.N, dtype=np.float32)     # current model reference position (units)
        self.qd_d = np.zeros(self.N, dtype=np.float32)     # current model reference velocity (units/sec)
        
        # The reference position trajectory is piecewise linear (steps or ramps), governed by the following.
        self.q_d_d = np.zeros(self.N, dtype=np.float32)               # target position specified by user (units)
        self.speed = np.inf * np.ones(self.N, dtype=np.float32)  # target speed specified by user (units/sec)

        # The PD gains determine the tracking dynamics.
        self.k = 4*math.pi*math.pi*np.ones(self.N, dtype=np.float32)  # proportional feedback gain, in (units/sec/sec)/(units), which is (1/sec^2)
        self.b = np.ones(self.N, dtype=np.float32)    	              # derivative feedback gain, in (units/sec/sec)/(units/sec), which is (1/sec)

        # Global model properties.  The limits are assumed to be a hardware property common to all axes.
        self.t = 0.0    	   # elapsed model time, in seconds        
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
        # Model based on StepperWinch/Path.

        # calculate the derivatives
        self.qdd = self.k * (self.q_d - self.q) + self.b * (self.qd_d - self.qd)

        # clamp the acceleration within range for safety
        self.qdd = np.minimum(self.qdd_max, np.maximum(self.qdd, -self.qdd_max))

        # integrate one time step
        self.q   += self.qd  * dt
        self.qd  += self.qdd * dt
        self.t   += dt

        # clamp the model velocity within range for safety
        self.qd = np.minimum(self.qd_max, np.maximum(self.qd, -self.qd_max))
        
        # Update the reference trajectory vectors using linear interpolation.
        # This can create steps or ramps.  This calculates the maximum desired step, bounds it to the
        # speed, then applies the sign to move in the correct direction.
        q_d_err   = self.q_d_d - self.q_d  # maximum error step
        q_d_sign  = np.sign(q_d_err)       # direction of error step
        q_d_mag   = np.abs(q_d_err)        # magnitude of error step    
        d_q_d_max = self.speed * dt        # maximum linear step
        d_q_d     = q_d_sign * np.minimum(d_q_d_max, q_d_mag) 
        self.q_d += d_q_d                  # update the reference position

        # set a zero reference velocity if either the error is zero or the speed is infinite,
        # else the reference velocity to the signed speed
        self.qd_d[:] = q_d_sign * np.where(np.isinf(self.speed), self.zeros, self.speed)

        return

    def positions(self):
        """Return a list of the current winch positions."""
        return self.q

    #------------------------------------------------------------------------------
    # The command API follows which mimics the interface to the actual winches.
    def set_target(self, axis, position):
        """Set the target position of one or more axes.

        :param axis: either a integer axis number or list of axis numbers
        :param position: either a integer step position or list of step positions
        """
        # In multiple-axis mode this takes advantange of the NumPy index array mechanism.
        self.q_d_d[axis] = position       

    def increment_target(self, axis, offset):
        """Add a signed offset to one or more target positions.  The units are dimensionless
        'steps'.  If using a microstepping driver, these may be less than a
        physical motor step.

        :param axis: either a integer axis number or list of axis numbers
        :param offset: either a integer step offset or list of step offsets
        """
        self.q_d_d[axis] += offset

    def increment_reference(self, axis, offset):
        """Add a signed offset to one or more reference positions.  This has the effect
        of applying a triangular impulse; the reference trajectory will make a
        step, then ramp back to the target vector.

        The units are dimensionless
        'steps'.  If using a microstepping driver, these may be less than a
        physical motor step.

        :param axis: either a integer axis number or list of axis numbers
        :param offset: either a integer step offset or list of step offsets

        """
        self.q_d[axis] += offset

    def set_speed(self, axis, speed):
        """Set the ramp speed of one or more targets in units/sec.  If a speed value
        is less than or equal to zero, it is treated as unlimited, and the
        reference position will move in steps instead of ramps.

        :param axis: either a integer axis number or list of axis numbers
        :param speed: either a ramp speed or list of ramp speeds

        """
        if isinstance(speed, np.ndarray):
            speed[speed <= 0] = np.inf
        else:
            if speed <= 0: speed = np.inf
        self.speed[axis] = speed
        return
    
    def set_freq_damping(self, axis, freq, damping):
        """Set the second order model resonance parameters for one or more path
        generators.  Note that the same parameters are applied to all specified
        axes, unlike the target setting functions.

        :param axis: either a integer axis number or list of axis numbers
        :param freq: scalar specifying the frequency in Hz
        :param damping: scalar specifying the damping ratio, e.g. 1.0 at critical damping.
        """
        new_k = freq * freq * 4 * math.pi * math.pi
        new_b = 2 * math.sqrt(new_k) * damping
        self.k[axis] = new_k
        self.b[axis] = new_b

################################################################
