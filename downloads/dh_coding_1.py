import numpy as np # Scientific computing library
 
# Project: Coding Denavit-Hartenberg Tables Using Python - Cartesian Robot
#          This only looks at frame 0 to frame 1.
# Author: Addison Sears-Collins
# Date created: August 21, 2020
 
# Link lengths in centimeters
a1 = 1 # Length of link 1
a2 = 1 # Length of link 2
a3 = 1 # Length of link 3
 
# Initialize values for the displacements
d1 = 1 # Displacement of link 1
d2 = 1 # Displacement of link 2
d3 = 1 # Displacement of link 3
 
# Declare the Denavit-Hartenberg table. 
# It will have four columns, to represent:
# theta, alpha, r, and d
# We have the convert angles to radians.
d_h_table = np.array([[np.deg2rad(90), np.deg2rad(90), 0, a1 + d1],
                      [np.deg2rad(90), np.deg2rad(-90), 0, a2 + d2],
                      [0, 0, 0, a3 + d3]]) 
 
# Create the homogeneous transformation matrix
homgen_0_1 = np.array([[np.cos(d_h_table[0,0]), -np.sin(d_h_table[0,0]) * np.cos(d_h_table[0,1]), np.sin(d_h_table[0,0]) * np.sin(d_h_table[0,1]), d_h_table[0,2] * np.cos(d_h_table[0,0])],
                      [np.sin(d_h_table[0,0]), np.cos(d_h_table[0,0]) * np.cos(d_h_table[0,1]), -np.cos(d_h_table[0,0]) * np.sin(d_h_table[0,1]), d_h_table[0,2] * np.sin(d_h_table[0,0])],
                      [0, np.sin(d_h_table[0,1]), np.cos(d_h_table[0,1]), d_h_table[0,3]],
                      [0, 0, 0, 1]])  
 
# Print the homogeneous transformation matrix from frame 1 to frame 0.
print(homgen_0_1)
# g.es() for inside leo editor only, es represents echo string
# press ctrl + b to execute
g.es(homgen_0_1)