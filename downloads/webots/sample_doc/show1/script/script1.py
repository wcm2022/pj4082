"""Demonstration script class for show1.py showing a self-contained process
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

################################################################
class Script(rcp.script.Script):

    def __init__(self):
        super().__init__()
        return

    def script_task(self):
        """Entry point for the script to run on a background thread."""
        self.write("Script thread waking up.")

        # top-level event loop to wait for a play or reset command
        while True:
            try:
                command = self.input.get()
                if command[0] == 'console':
                    self.write("Script thread received user command: %s" % command[1])
                    if command[1] == 'reset':
                        self.send_reset_cue()

                    elif command[1] == 'play':
                        self.sequence()

                elif command[0] == 'script':
                    self.write("Script thread received network command: %s" % command[1])
                    if command[1] == 'start':
                        self.sequence()

                elif command[0] == 'status':
                    self.write("Script thread received status: %s" % repr(command))

            except rcp.script.ScriptStopException:
                self.write("Script stopped and idle.")

            except rcp.script.ScriptTimeoutException:
                self.write("Warning: script step timed out.  Script idle.")


    def send_show(self, *args):
        self.output.put(('show',) + args)
        self.write('Issuing show message: ' + repr(args))
        return

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
        self.sleep(1.0)

        self.send_pose('lead1')
        self.wait_until_stopped()

        self.send_pose('lead2')
        self.wait_until_stopped()

        self.send_pose('lead3')
        self.wait_until_stopped()

        self.send_cue('random', True)
        self.sleep(5.0)

        self.send_cue('magnitude', 5.0)
        self.sleep(5.0)

        self.send_cue('tempo', 120)
        self.sleep(5.0)

        self.send_cue('random', False)
        self.wait_until_stopped()

        self.send_pose('reset')
        self.sleep(5.0)

        self.send_show('done')
        self.write("Script done.")
        return

################################################################
