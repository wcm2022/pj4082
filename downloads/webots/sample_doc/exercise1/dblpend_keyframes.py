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
from rcp.ex.dblpend import main

################################################################
class PendulumController(rcp.doublependulum.DoublePendulumController):
    def __init__(self):
        super().__init__()

        # for this example, there are four fixed poses commanded a fixed intervals, expressed as a set of (q0, q1) pairs
        self.keyframes = np.zeros((4,2))
        self.last_frame = None
        return

    #================================================================
    def setup(self):
        self.write("""Keyframed position control demonstration.

Applies a sequence of joint targets to a position controller at fixed intervals.

The parameter sliders 0 and 1 control the 'shoulder' and 'elbow' angles for the first keyframe, 2 and 3 are the second keyframe, etc.

""")
        return

    #================================================================
    def user_parameter_change(self, parameter, value):
        pose = parameter // 2
        joint = parameter % 2
        if pose <  len(self.keyframes):
            self.keyframes[pose][joint] = 2 * math.pi * (value - 0.5)
            self.write("Set pose %d joint %d to angle %f" % (pose, joint, self.keyframes[pose][joint]))

    def apply_configuration(self, config):
        if 'keyframes' in config:
            for i in range(len(self.keyframes)):
                q0 = config['keyframes'].getfloat('keyframe-%d-q0' % i, fallback = 0.0)
                q1 = config['keyframes'].getfloat('keyframe-%d-q1' % i, fallback = 0.0)
                self.keyframes[i,:] = [q0, q1]
        return

    def gather_configuration(self, config):
        if 'keyframes' not in config:
            config['keyframes'] = {}
        for i in range(len(self.keyframes)):
            config['keyframes']['keyframe-%d-q0' % i] = str(self.keyframes[i, 0])
            config['keyframes']['keyframe-%d-q1' % i] = str(self.keyframes[i, 1])
        return

    #================================================================
    def compute_control(self, t, dt, state, tau):
        """Method called from simulator to calculate the next step of applied torques.

        :param t: time in seconds since simulation began
        :param state: four element numpy array with joint positions ``q`` and joint velocities ``qd`` as ``[q0, q1, qd0, qd1]``, expressed in radians and radians/sec
        :param tau: two element numpy array to fill in with the joint torques to apply ``[tau0, tau1]``
        """
        # select the current keyframe based on the time
        frame  = int(t // 1.5)
        if frame != self.last_frame:
            self.write("Starting frame %d" % frame)
        self.last_frame = frame

        # select the pose for the current keyframe, looping over the available poses
        pose = self.keyframes[frame % len(self.keyframes)]

        # create a target state by extending the pose to include velocity
        target = np.concatenate((pose, np.zeros(2)))

        # calculate position and velocity error as difference from reference state
        qerr = target - state

        # apply PD control to reach the pose (no integral term)
        tau[0] = (self.kp[0] * qerr[0]) + (self.kd[0] * qerr[2])
        tau[1] = (self.kp[1] * qerr[1]) + (self.kd[1] * qerr[3])

        return

################################################################$
if __name__ == "__main__":
    main(PendulumController)
