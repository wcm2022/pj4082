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
import math
import numpy as np

import rcp.doublependulum
from rcp.ex.ndblpend import main

################################################################
class PendulumController(rcp.doublependulum.DoublePendulumController):
    def __init__(self):
        super().__init__()
        self.timestep = 0

        # set stiffer position and damping gains
        self.kp      = np.array((100.0, 50.0))
        self.kd      = np.array((16.0,  8.0))

        return
    
    #================================================================
    def setup(self):
        if self.identity == 0:
            self.write("""Pair of double-pendulum simulations.

One moves the endpoint along a circular path, while the other tries to follow.
""")
        return
    #================================================================
    def compute_control(self, t, dt, state, tau):
        """Method called from simulator to calculate the next step of applied torques.

        :param t: time in seconds since simulation began
        :param state: four element numpy array with joint positions ``q`` and joint velocities ``qd`` as ``[q0, q1, qd0, qd1]``, expressed in radians and radians/sec
        :param tau: two element numpy array to fill in with the joint torques to apply ``[tau0, tau1]``
        """

        if self.identity == 0:
            # the first robot chooses a target pose in robot coordinates based
            # on the inverse kinematics solution for a spiral path

            # phase cycles one revolution of the circular path angle every 8 seconds
            phase = 0.25 * np.pi * t

            # radius slowly cycles up and down again
            radius = 0.1 + 0.5 * abs(math.sin(0.05 * t))

            # end is the world-coordinate location of a point traveling around the spiral centered between the two arms
            end = np.array((1.0 + radius * np.cos(phase), radius * np.sin(phase)))

            # solve for the joint angles for the given endpoint
            s1, s2 = self.model.endpointIK(end)

            # arbitrarily one solution as the target pose
            pose = s1

            if self.timestep % 1000 == 0:
                self.write("Time: %f  endpoint: %s" % (t, end))
            self.world.set_marker(0, end)
            
        else:
            # the other robot observes the first and tries to track the endpoint
            end0 = self.world.dblpend_endpoint(0)
            s1, s2 = self.model.endpointIK(end0)
            pose = s2
            
        # create a target state by extending the pose to include velocity
        target = np.concatenate((pose, np.zeros(2)))

        # calculate position and velocity error as difference from reference state
        qerr = target - state

        # apply PD control to reach the pose (no integral term)
        tau[0] = (self.kp[0] * qerr[0]) + (self.kd[0] * qerr[2])
        tau[1] = (self.kp[1] * qerr[1]) + (self.kd[1] * qerr[3])

        self.timestep += 1        
        return

################################################################$
if __name__ == "__main__":
    main(PendulumController)
