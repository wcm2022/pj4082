#!/usr/bin/env python3
"""Prototype Python 3 script for the 16-375 double-pendulum control exercise."""

################################################################
# Written in 2018-2019 by Garth Zeglin <garthz@cmu.edu>

# To the extent possible under law, the author has dedicated all copyright
# and related and neighboring rights to this software to the public domain
# worldwide. This software is distributed without any warranty.

# You should have received a copy of the CC0 Public Domain Dedication along with this software.
# If not, see <http://creativecommons.org/publicdomain/zero/1.0/>.

################################################################

import rcp.doublependulum
from rcp.ex.dblpend import main

################################################################
class PendulumController(rcp.doublependulum.DoublePendulumController):
    def __init__(self):
        super().__init__()
        
        # initialize any fixed controller parameters
        self.friction_damping = -0.2
        self.velocity_gain    = 2.0
        
        return

    #================================================================
    def setup(self):
        self.write("""Swing-up control demonstration using single 'shoulder' actuator.

Applies one of several policies, depending on state:
        at the bottom, applies a small constant torque to 'shoulder' joint 0 to perturb away from zero;
        near the bottom, applies unstable positive velocity feedback to shoulder to 'pump' motion;
        else only applies friction.

The 'elbow' joint 1 always receives a small damping torque to simulate friction.

The parameter 0 slider controls the joint friction.
""")
        return

    #================================================================
    def user_parameter_change(self, parameter, value):
        if parameter == 0:
            self.friction_damping = -1.0 * value
            self.write("Set friction_damping to %f" % (self.friction_damping))

    def apply_configuration(self, config):
        if 'swingup' in config:
            self.friction_damping = config['swingup'].getfloat('friction_damping', fallback = -0.2)
        return

    def gather_configuration(self, config):
        if 'swingup' not in config:
            config['swingup'] = {}
        config['swingup']['friction_damping'] = str(self.friction_damping)
        return
        
    #================================================================
    def compute_control(self, t, dt, state, tau):
        """Method called from simulator to calculate the next step of applied torques.

        :param t: time in seconds since simulation began
        :param state: four element numpy array with joint positions ``q`` and joint velocities ``qd`` as ``[q0, q1, qd0, qd1]``, expressed in radians and radians/sec
        :param tau: two element numpy array to fill in with the joint torques to apply ``[tau0, tau1]``
        """
        # convenience variables to notate the state variables
        q0  = state[0]  # 'shoulder' angle in radians
        q1  = state[1]  # 'elbow' angle in radians
        qd0 = state[2]  # 'shoulder' velocity in radians/second
        qd1 = state[3]  # 'elbow' velocity in radians/second

        # pump the swinging motion only the 'shoulder' joint q0 and tau0
        # if completely at rest, add a slight perturbation to kick-start the process
        if abs(qd0) < 0.01 and abs(q0) < 0.01:
            tau[0] = 1.0

        # apply unstable positive velocity feedback near bottom
        elif abs(q0) < 0.5:
            tau[0] = self.velocity_gain * qd0

        else: # else coast, applying simulated friction
            tau[0] = self.friction_damping * qd0

        # assume the elbow is unpowered, but add simulated friction
        tau[1] = self.friction_damping * qd1
        
        return

################################################################$
if __name__ == "__main__":
    main(PendulumController)
