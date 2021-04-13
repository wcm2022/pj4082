# Standard library modules.
import math, time, threading, queue, logging

# Third-party library modules.
import numpy as np

# set up logger for module
log = logging.getLogger(__file__)

################################################################
class DoublePendulumController(object):
    """Prototype for a double-pendulum controller.  This class is typically subclassed to customize the control strategy and the subclass passed into the common application framework.

    :ivar initial_state: four-element numpy array used to initialize the simulator state: [q1, q2, qd1, qd2]
    :ivar kp: two-element numpy array with default proportional position gains 
    :ivar ki: two-element numpy array with default integral gains
    :ivar kd: two-element numpy array with default velocity damping gain
    :ivar identity: zero-based serial number identifying the instance in the case of multiple simulations
    """
    def __init__(self):

        # delegate object to which debugging and status messages can be printed; it must implement write()
        self.console = None

        # delegate object to query for kinematics parameters and solutions
        self.model = None

        # zero-based serial number identifying the instance from multiple simulations
        self.identity = 0

        # world object to query for other system information
        self.world = None
        
        # fixed controller parameters
        self.initial_state = np.array([0.0, 0.0, 0.0, 0.0])
        self.d_state       = np.array((1.0, 0.5*math.pi, 0.0, 0.0))
        self.kp      = np.array((16.0, 8.0))
        self.ki      = np.array((4.0, 2.0))
        self.kd      = np.array((4.0, 2.0))
        
        return

    #================================================================
    def connect_console(self, console):
        """Attach a console object to be used for debugging output.  The object needs to implement write()."""
        self.console = console
        return

    def set_identity(self, serial_number):
        """Set the specific identification number for this controller out of multiples.""" 
        self.identity = serial_number

    def set_world(self, world):
        """Set the 'world' object which can answer global information queries.  This is a deliberately abstract interface between sub-classes
and the application framework."""
        self.world = world
        
    def write(self, string):
        """Write a message to the debugging console.  If console is not available, writes to the log as an info message."""
        if self.console is not None:
            self.console.write(string)
        else:
            log.info(string)
        return
    
    def setup(self):
        """Hook for final one-time object configuration.  This is called once prior to the start of the simulation.  The default implementation does nothing."""
        pass

    def user_parameter_change(self, parameter, value):
        """Hook for interactive parameter changes (e.g. GUI sliders).  The default implementation does nothing.

        :param parameter: integer index of parameter, starting with zero
        :param value: dimensionless parameter value, ranges from zero to one inclusive.
        """
        pass
    #================================================================
    def apply_configuration(self, config):
        """Hook for applying parameters saved in a configuration file. The default implementation does nothing.

        :param config: configparser object (which implements the mapping protocol)
        """
        pass

    def gather_configuration(self, config):
        """Hook for saving parameters in a configuration file. The default implementation does nothing.

        :param config: configparser object (which implements the mapping protocol)
        """
        pass
    
    #================================================================
    def compute_control(self, t, dt, state, tau):
        """Method called from numerical pendulum simulation to calculate the next step of applied torques.  This is usually overridden in a subclass, but the default implementation applies a fixed-target PD position control.

        :param t: time in seconds since simulation began
        :param state: four element ndarray of joint positions q and joint velocities qd as [q1, q2, qd1, qd2], expressed in radians and radians/sec
        :param tau: two element ndarray to fill in with joint torques to apply
        """
        # convenience variables to notate the state variables
        q1  = state[0]  # 'shoulder' angle in radians
        q2  = state[1]  # 'elbow' angle in radians
        qd1 = state[2]  # 'shoulder' velocity in radians/second
        qd2 = state[3]  # 'elbow' velocity in radians/second

        # calculate position and velocity error as difference from reference state
        qerr = self.d_state - state

        # apply PD control to reach the pose (no integral term)
        tau[0] = (self.kp[0] * qerr[0]) + (self.kd[0] * qerr[2])
        tau[1] = (self.kp[1] * qerr[1]) + (self.kd[1] * qerr[3])

        return

################################################################
class DoublePendulumSimulator(object):
    """Numerical dynamic simulation of a frictionless double pendulum.  It
    communicates with a user-supplied control object to compute applied joint
    torques.

    :ivar t: simulated time in seconds
    :ivar state: four-element vector of dynamic state [q1 q2 qd1 qd2] (position and velocity)
    :ivar origin: two-element vector locating the pendulum base in world coordinates
    """

    def __init__(self):
        # the object used to calculate joint torques
        self.control = None

        # set default dynamics
        self.set_default_dynamic_parameters()

        # configure transient state
        self.reset()

        return

    def connect_controller(self, controller):
        """Attach a controller object used to compute joint torques and set the initial state."""
        self.control = controller
        controller.model = self
        self.reset()
        return
    
    def reset(self):
        """Reset or initialize all simulator state variables."""
        self.t     = 0.0
        self.dt    = 0.001
        self.origin = np.zeros(2)

        if self.control is not None:
            self.state = self.control.initial_state.copy()
        else:
            self.state = np.array([0.0, 0.0, 0.0, 0.0])
        self.tau   = np.array([0.0, 0.0])
        self.dydt  = np.ndarray((4,))
        return
    
    def set_default_dynamic_parameters(self):
        """Set the default dynamics coefficients defining the rigid-body model physics."""
        self.l1   = 1.0    # proximal link length, link1
        self.l2   = 1.0    # distal link length, link2
        self.lc1  = 0.5    # distance from proximal joint to link1 COM
        self.lc2  = 0.5    # distance from distal joint to link2 COM
        self.m1   = 1.0    # link1 mass
        self.m2   = 1.0    # link2 mass
        self.I1   = (self.m1 * self.l1**2) / 12  # link1 moment of inertia
        self.I2   = (self.m2 * self.l2**2) / 12  # link2 moment of inertia
        self.gravity  = -9.81
        return

    #================================================================
    def deriv(self):
        """Calculate the accelerations for a rigid body double-pendulum dynamics model.

        :returns: system derivative vector as a numpy ndarray
        """
        q1  = self.state[0]
        q2  = self.state[1]
        qd1 = self.state[2]
        qd2 = self.state[3]
        LC1 = self.lc1
        LC2 = self.lc2
        L1 = self.l1
        M1 = self.m1
        M2 = self.m2

        d11 = M1*LC1*LC1  + M2*(L1*L1 + LC2*LC2 + 2*L1*LC2*math.cos(q2)) + self.I1 + self.I2
        d12 = M2*(LC2*LC2 + L1*LC2*math.cos(q2)) + self.I2
        d21 = d12
        d22 = M2*LC2*LC2  + self.I2

        h1 = -M2*L1*LC2*math.sin(q2)*qd2*qd2 - 2*M2*L1*LC2*math.sin(q2)*qd2*qd1
        h2 = M2*L1*LC2*math.sin(q2)*qd1*qd1

        phi1 = -M2*LC2*self.gravity*math.sin(q1+q2)  - (M1*LC1 + M2*L1) * self.gravity * math.sin(q1)
        phi2 = -M2*LC2*self.gravity*math.sin(q1+q2)

        # now solve the equations for qdd:
        #  d11 qdd1 + d12 qdd2 + h1 + phi1 = tau1
        #  d21 qdd1 + d22 qdd2 + h2 + phi2 = tau2

        rhs1 = self.tau[0] - h1 - phi1
        rhs2 = self.tau[1] - h2 - phi2

        # Apply Cramer's Rule to compute the accelerations using
        # determinants by solving D qdd = rhs.  First compute the
        # denominator as the determinant of D:
        denom = (d11 * d22) - (d21 * d12)

        # the derivative of the position is trivially the current velocity
        self.dydt[0] = qd1
        self.dydt[1] = qd2

        # the derivative of the velocity is the acceleration.
        # the numerator of qdd[n] is the determinant of the matrix in
        # which the nth column of D is replaced by RHS
        self.dydt[2] = ((rhs1 * d22 ) - (rhs2 * d12)) / denom
        self.dydt[3] = (( d11 * rhs2) - (d21  * rhs1)) / denom
        return self.dydt

    #================================================================
    def timer_tick(self, delta_t):
        """Run the simulation for an interval.

        :param delta_t: length of interval in simulated time seconds
        """
        while delta_t > 0:

            # calculate next control outputs
            self.control.compute_control(self.t, self.dt, self.state, self.tau)

            # calculate dynamics model
            qd = self.deriv()

            # Euler integration
            self.state = self.state + self.dt * qd
            delta_t -= self.dt
            self.t += self.dt

    #================================================================
    def forwardKinematics(self, q):
        """Compute the forward kinematics.  Returns the world-coordinate Cartesian position of the elbow
and endpoint for a given joint angle vector.

        :param q: two-element list or ndarray with [q1, q2] joint angles
        :return: tuple (elbow, end) of two-element ndarrays with [x,y] locations
        """

        elbow = self.origin + np.array((self.l1 * math.sin(q[0]), -self.l1 * math.cos(q[0])))
        end   = elbow + np.array((self.l2 * math.sin(q[0]+q[1]), -self.l2 * math.cos(q[0]+q[1])))
        return elbow, end
            
    #================================================================
    def endpointIK(self, target):
        """Compute two inverse kinematics solutions for a target end position.  The
        target is a Cartesian position vector (two-element ndarray) in world coordinates,
        and the result vectors are joint angles as ndarrays [q0, q1].
        If the target is out of reach, returns the closest pose.
        """

        # translate the target vector into body coordinates
        target = target - self.origin
        
        # find the position of the point in polar coordinates
        radiussq = np.dot(target, target)
        radius   = math.sqrt(radiussq)

        # theta is the angle of target point w.r.t. -Y axis, same origin as arm
        theta    = math.atan2(target[0], -target[1]) 

        # use the law of cosines to compute the elbow angle
        #   R**2 = l1**2 + l2**2 - 2*l1*l2*cos(pi - elbow)
        #   both elbow and -elbow are valid solutions
        acosarg = (radiussq - self.l1**2 - self.l2**2) / (-2 * self.l1 * self.l2)
        if acosarg < -1.0:  elbow_supplement = math.pi
        elif acosarg > 1.0: elbow_supplement = 0.0
        else:               elbow_supplement = math.acos(acosarg)

        # use the law of sines to find the angle at the bottom vertex of the triangle defined by the links
        #  radius / sin(elbow_supplement)  = l2 / sin(alpha)
        if radius > 0.0:
            alpha = math.asin(self.l2 * math.sin(elbow_supplement) / radius)
        else:
            alpha = 0.0
            
        #  compute the two solutions with opposite elbow sign
        soln1 = np.array((theta - alpha, math.pi - elbow_supplement))
        soln2 = np.array((theta + alpha, elbow_supplement - math.pi))

        return soln1, soln2
    
################################################################
