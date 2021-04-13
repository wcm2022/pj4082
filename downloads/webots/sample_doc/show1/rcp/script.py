"""Objects related to performance scripting.
"""
################################################################
# Written in 2019 by Garth Zeglin <garthz@cmu.edu>

# To the extent possible under law, the author has dedicated all copyright
# and related and neighboring rights to this software to the public domain
# worldwide. This software is distributed without any warranty.

# You should have received a copy of the CC0 Public Domain Dedication along with this software.
# If not, see <http://creativecommons.org/publicdomain/zero/1.0/>.

################################################################
# standard Python libraries
import math, logging, functools, time, queue, threading

# set up logger for module.
log = logging.getLogger('script')
# N.B. the normal logger doesn't yet work from background threads since the
# default formatter writes to a Qt object only available on the main thread.

# filter out most logging; the default is NOTSET which passes along everything
log.setLevel(logging.INFO)

################################################################
class ScriptTimeoutException(Exception):
    pass

class ScriptStopException(Exception):
    pass

################################################################
class Script(object):
    """A script is a procedure run as a separate thread which is permitted to block.
    This supports a simpler notation for linear action sequences as normal
    procedures instead of callback state machines.  The script thread
    communicates with the main thread solely using message queues to avoid
    synchronization problems.

    :ivars input:  unified input queue; each item is a tuple in which the first keyword identifies the message type
    :ivars output: unified output queue; each item is a tuple in which the first keyword identifies the message type
    """

    def __init__(self):
        self.input  = queue.Queue()
        self.output = queue.Queue()
        return

    def start(self):
        """Start the script process in the background so will run asynchronously.  This
        function returns immediately."""
        self.thread = threading.Thread(target=self.script_task)
        self.thread.daemon = True
        self.thread.start()
        return

    def write(self, string):
        """Internal method to send a console message to the main thread."""
        self.output.put(('console', string))

    def script_task(self):
        """Entry point for the script to run on a background thread.  The default
        implementation does nothing, this should be overridden in child
        classes.
        """
        pass

    # ===============================================================
    def event_wait(self, predicate, timeout):
        """Consume input messages until one is received which satisfies the predicate or
        the timeout is reached.  Returns the non-False value of the predicate or
        the string 'timeout'.
        """
        start = time.time()
        remaining = timeout
        while remaining > 0:
            try:
                command = self.input.get(block=True, timeout=remaining)

                # apply the predicate and return any non-False value
                value = predicate(command)
                if value is not False:
                    return value

                self.write("event_wait ignoring message " + repr(command))
                remaining = start + timeout - time.time()
                
            except queue.Empty:
                # if the queue 'get' timed out, fall out of the loop
                remaining = 0
                
        return 'timeout'

    # ===============================================================            
    def _user_stop_predicate(self, command):
        if command[0] == 'console' and command[1] == 'stop':
            return 'user_stop'
        else:
            return False
    
    def sleep(self, duration):
        """Sleep for a given duration unless the user issues a stop command.  Returns
        nothing or raises a ScriptStopException."""
        value = self.event_wait(self._user_stop_predicate, duration)
        if value == 'user_stop':
            raise ScriptStopException
        else:
            return

    def _motion_stop_predicate(self, command):
        if command[0] == 'status' and command[1] == 'stopped':
            return 'motion_stop'
        else:
            return False
        
    def wait_until_stopped(self, timeout = 20.0):
        """Sleep until the motion generator reports a stopped status or the timeout is reached."""
        predicate = lambda command: self._user_stop_predicate(command) or self._motion_stop_predicate(command)
        value = self.event_wait(predicate, timeout)
        if value == 'user_stop':
            raise ScriptStopException
        elif value == 'motion_stop':
            return
        else:
            raise ScriptTimeoutException

################################################################
