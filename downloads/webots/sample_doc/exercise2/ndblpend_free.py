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
from rcp.ex.ndblpend import main
import numpy as np

################################################################
class PendulumController(rcp.doublependulum.DoublePendulumController):
    def __init__(self):
        super().__init__()

        # override the default initial state
        self.initial_state = np.array([3.0, 0.0, 0.0, 0.0])
        return

    #================================================================
    # Specialize this particular controller when a member of an ensemble.
    def set_identity(self, serial_number):
        super().set_identity(serial_number)
        # perturb the initial state
        self.initial_state[0] += self.identity * 0.05
        return
    
    #================================================================
    def setup(self):
        if self.identity == 0:
            self.write("""Passive double-pendulum simulation.
A zero torque vector is applied to the joints so they swing freely.  The underlying simulation has frictionless joints so the behavior is chaotic. It is ultimately unstable due to accumulated numerical error.\n""")

        return
    #================================================================
    def compute_control(self, t, dt, state, tau):
        """Method called from simulator to calculate the next step of applied torques.

        :param t: time in seconds since simulation began
        :param state: four element numpy array with joint positions ``q`` and joint velocities ``qd`` as ``[q0, q1, qd0, qd1]``, expressed in radians and radians/sec
        :param tau: two element numpy array to fill in with the joint torques to apply ``[tau0, tau1]``
        """
        tau[0:2] = (0,0)

        # temporary kinematics test
        # elbow, end = self.model.forwardKinematics(state[0:2])
        # s1, s2 = self.model.endpointIK(end)
        # print("q:", state[0], state[1], "elbow:", elbow, "end:", end, "solution1: ", s1, "solution2:", s2)
        # print("q:", state[0], state[1], "end:", end, "solution1: ", s1, "solution2:", s2)
        
        return

################################################################$
if __name__ == "__main__":
    main(PendulumController)
