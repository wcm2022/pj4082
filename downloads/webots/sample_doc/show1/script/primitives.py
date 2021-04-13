import csv, random, logging
import numpy as np
log = logging.getLogger('primitives')

################################################################
class MotionPrimitives(object):
    """Class to encapsulate the set of motion primitives available for this
    performance.  This also abstracts the basic interface to both motor and
    simulation and supports periodic execution.
    """

    def __init__(self, main, pose_csv_path='script/poses'):
        super().__init__()
        self.main  = main

        # global parameters
        self.tempo = 60.0     # beats per minute
        self.magnitude = 1.0
        self.frequency = 1.0
        self.damping_ratio = 1.0
        self.all_axes = range(4) # index list for updating all motors
        self.non_zero_velocity = False
        self.non_zero_velocity_timeout = 0.0
        
        # algorithmic generators
        self.random_mode = False
        self.random_mode_timer = 0
        
        # try reading the pose table
        self.poses = {}
        self.pose_csv_path = pose_csv_path
        with open(self.pose_csv_path, newline='') as posefile:
            posereader = csv.reader(posefile)
            for pose in posereader:
                if len(pose) > 0:
                    name = pose[0]
                    positions = [int(s) for s in pose[1:]]
                    self.poses[name] = positions
        log.debug("Read pose table: %s", self.poses)
        return
        
    #---- methods for distributing winch events across multiple winch sets and simulators ---------
    def set_freq_damping(self):
        for winch in self.main.winches:
            winch.set_freq_damping(self.all_axes, self.frequency, self.damping_ratio)
        for sim in self.main.sims:
            sim.set_freq_damping(self.all_axes, self.frequency, self.damping_ratio)
        self.main.window.set_status("Frequency: %f, damping ratio: %f" % (self.frequency, self.damping_ratio))
        return

    def increment_target(self, winch_index, steps):
        """Map a given winch index to the particular winch set."""
        set_index = winch_index // 4
        winch_id = winch_index % 4
        if set_index < self.main.num_winch_sets:
            self.main.winches[set_index].increment_target(winch_id, steps)
            self.main.sims[set_index].increment_target(winch_id, steps)
        return

    def increment_reference(self, winch_index, steps):
        """Map a given winch index to the particular winch set."""
        set_index = winch_index // 4
        winch_id = winch_index % 4
        if set_index < self.main.num_winch_sets:
            self.main.winches[set_index].increment_reference(winch_id, steps)
            self.main.sims[set_index].increment_reference(winch_id, steps)
        return
    
    def set_target(self, winch_index, steps):
        """Map a given winch index to the particular winch set."""
        set_index = winch_index // 4
        winch_id = winch_index % 4
        if set_index < self.main.num_winch_sets:
            self.main.winches[set_index].set_target(winch_id, steps)
            self.main.sims[set_index].set_target(winch_id, steps)
        return

    def set_speed(self, winch_index, steps):
        """Map a given winch index to the particular winch set."""
        set_index = winch_index // 4
        winch_id = winch_index % 4
        if set_index < self.main.num_winch_sets:
            self.main.winches[set_index].set_speed(winch_id, steps)
            self.main.sims[set_index].set_speed(winch_id, steps)
            self.main.window.set_status("Winch %d speed: %d" % (winch_index, steps))
        return

    def simulator_velocity(self):
        """Extract the current velocity vector from the simulator, which is not
        currently reported by the serial winches."""
        return np.array([simset.qd for simset in self.main.sims]).flatten()
        
    #--- methods for processing cue messages -------------------
    def set_frequency(self, f):
        self.frequency = f;
        self.set_freq_damping()
        return
    
    def set_damping(self, d):
        self.damping_ratio = d;
        self.set_freq_damping()
        return

    def set_pose(self, name):
        position = self.poses.get(name)
        if position is not None:
            for i, p in enumerate(position):
                self.set_target(i, p)

    def process_cue(self, args):
        if args[0] == 'pose':
            self.set_pose(args[1])
            
        elif args[0] == 'random':
            self.random_mode = args[1]

        elif args[0] == 'tempo':
            self.tempo = args[1]

        elif args[0] == 'magnitude':
            self.magnitude = args[1]
            
        elif args[0] == 'gains':
            self.frequency = args[1]
            self.damping   = args[2]
            self.set_freq_damping()

        elif args[0] == 'magnitude':
            self.magnitude = args[1]
            
        elif args[0] == 'gains':
            self.frequency = args[1]
            self.damping   = args[2]
            self.set_freq_damping()
        return

    def user_parameter_change(self, parameter, value):
        """Hook for user-controlled sliders, useful for debugging and tuning."""
        log.debug("Motion primitives user_parameter_change: %d, %f", parameter, value)
    
    #--- methods for periodic algorithmic activity -----------
    def update_for_interval(self, interval):
        # always poll the simulators
        vel = self.simulator_velocity()
        sqvelmag = vel.dot(vel)
        self.non_zero_velocity_timeout -= interval
        if self.non_zero_velocity_timeout < 0:
            if self.non_zero_velocity:
                if sqvelmag < 5.0:
                    self.non_zero_velocity = False
                    self.main.script.input.put(('status', 'stopped'))
                    log.debug("primitives issuing message ('status', 'stopped')")
                    self.non_zero_velocity_timeout = 0.1
            else:
                if sqvelmag > 10.0:
                    self.non_zero_velocity = True
                    self.main.script.input.put(('status', 'moving'))
                    log.debug("primitives issuing message ('status', 'moving')")                    
                    self.non_zero_velocity_timeout = 0.1

        # run the random generator if needed
        if self.random_mode:
            self.random_mode_timer -= interval
            if self.random_mode_timer < 0:
                self.random_mode_timer += self.tempo/60.0
                winch = random.randint(0,3)
                limit = int(800*self.magnitude)
                offset = random.randint(-limit, limit)
                self.increment_target(winch, offset)
        
