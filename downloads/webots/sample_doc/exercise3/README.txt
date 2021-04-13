README.txt for sample code for IDeATe 16-375 Robotics for Creative Practice

These generic instructions are included in many of the packages of sample code.
The general guide to all of the sample code including detailed documentation can
be found on the course web site:

 https://courses.ideate.cmu.edu/16-375/f2019/text/code/index.html

**** Running on an IDeATe MacBook Pro ****

The Python sample code uses several optional Python packages, notably PyQt5,
pyqtgraph, python-rtmidi, and python-osc.  Within IDeATe, these are best
supported on the MacBook Pro laptops.  However, these laptops have several
different Python systems installed, so running the sample code requires a little
care.  The following example is based on the exercise1.zip package; running other
samples will be similar.  If you are reading this locally, you may already have
completed the first two steps.

1. Please download the package (e.g. exercise1.zip) to whatever location is
   convenient (e.g. Desktop or Downloads).  This package can be found at:

   https://courses.ideate.cmu.edu/16-375/f2019/zip/exercise1.zip

2. Double-clicking the exercise1.zip file under macOS will unpack it to a new folder
   named exercise1.

3. Within the new folder is the dblpend.py script file and a rcp folder which
   contains the library modules.

4. The recommended method for running it is to use the Terminal command line.
   E.g., if the package was unpacked on the Desktop, the following Terminal
   commands would launch exercise1:

  cd ~/Desktop/exercise1
  /opt/local/bin/python3.5 dblpend.py

Currently, IDLE 3.5 is not working, but in the future we hope to make it
possible to launch the sample code directly from the editor.

******* Running via the Finder ***************************************************

It is possible to launch the script by doubl-clicking on it in the Finder, but
is some one-time configuration required to set up the Python system.

1. Double-clicking on the dblpend.py script will not run it, but will instead open
   it in some version of the IDLE Python editor.

2. Right-clicking or control-clicking on dblpend.py will bring up a context
   menu. Within that menu is the 'Open With' submenu. Please select 'Python
   Launcher (3.5.4)' from this submenu.

3. The first launch will probably fail. Please bring forward the Python Launcher
   application and open its Preferences pane. For Interpreter, please enter:

      /opt/local/bin/python3.5

   This is the specific interpreter which includes the libraries required by
   the course software.

4. Subsequent launches using 'Open With/Python Launcher' should work.

**** Running on IDEATE-WS-01 under Ubuntu Linux ****

The desktop in the A5 lab area is an Ubuntu Linux computer.  It already has the
appropriate Python packages installed in the default python3 system.

The most reliable way to launch a Python script is to open a terminal window and
run it using python3, e.g.:

  cd ~/Desktop/exercise1
  python3 dblpend.py

