"""Demonstration script class for exercise4.py showing a self-contained process
for sequencing events over time.  The inputs and outputs are deliberately
constrained to message queues to preclude synchronization problems and maintain
compatibility with network communication.
"""

################################################################
# Written in 2019 by Garth Zeglin <garthz@cmu.edu>

# To the extent possible under law, the author has dedicated all copyright
# and related and neighboring rights to this software to the public domain
# worldwide. This software is distributed without any warranty.

# You should have received a copy of the CC0 Public Domain Dedication along with this software.
# If not, see <http://creativecommons.org/publicdomain/zero/1.0/>.

################################################################

import time, queue
import rcp.script

class ScriptStopException(Exception):
    pass

class Ex4DemoScript(rcp.script.Script):
    
    def __init__(self):
        super().__init__()
        return
    
    def sleep_unless_stop(self, duration):
        """Sleep for a given duration unless the user issues a stop command."""
        start = time.time()
        now = start
        while True:
            try:
                timeout = (start+duration-now)
                if timeout < 0:
                    return
                command = self.input.get(block=True, timeout=timeout)
                # if a message is received, ignore it unless it is the stop command
                if command[0] == 'console' and command[1] == 'stop':
                    self.write("User requested stop.")
                    raise ScriptStopException
                self.write("sleep_unless_stop ignoring message " + repr(command))
                now = time.time()
                
            except queue.Empty:
                # if the queue get timed out, the sleep is over
                return
        
    def script_task(self):
        """Entry point for the script to run on a background thread."""
        self.write("Ex4Demo script thread waking up.")

        # top-level event loop to wait for a play or reset command
        while True:
            command = self.input.get()
            if command[0] == 'console':
                self.write("Script thread received command: %s" % command[1])
                if command[1] == 'reset':
                    self.send_reset_cue()
                    
                elif command[1] == 'play':
                    try:
                        self.sequence()
                    except ScriptStopException:
                        self.write('Script sequence stopped.')

    def send_cue(self, *args):
        self.output.put(('cue',) + args)
        self.write('Issuing cue: ' + repr(args))
        return

    def send_pose(self, name):
        self.send_cue('pose',name)
        
    def send_reset_cue(self):
        self.write("Sending reset cue.")
        self.send_cue('gains', 0.5, 1.0)
        self.send_cue('pose', 'reset')
        self.send_cue('random', False)
        self.send_cue('tempo', 60.0)
        self.send_cue('magnitude', 1.0)
        return
        
    def sequence(self):
        """Demonstration sequence.  This could be decomposed further into subroutines."""
        
        self.write("Script starting.")
        self.send_cue('gains', 0.5, 1.0)        
        self.send_pose('reset')
        self.sleep_unless_stop(1)

        self.send_pose('lead1')
        self.sleep_unless_stop(1)

        self.send_pose('lead2')
        self.sleep_unless_stop(1)

        self.send_pose('lead3')
        self.sleep_unless_stop(1)

        self.send_cue('random', True)
        self.sleep_unless_stop(4)

        self.send_cue('magnitude', 5.0)
        self.sleep_unless_stop(4)

        self.send_cue('tempo', 120)
        self.sleep_unless_stop(4)

        self.send_cue('random', False)
        self.sleep_unless_stop(4)

        self.send_pose('reset')
        self.sleep_unless_stop(1)
        
        self.write("Script done.")
        return

################################################################
        
