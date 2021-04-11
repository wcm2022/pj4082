import numpy as np # Scientific computing library
 
# Project: Coding Denavit-Hartenberg Tables Using Python - Cartesian Robot
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
 
# Homogeneous transformation matrix from frame 0 to frame 1
i = 0
homgen_0_1 = np.array([[np.cos(d_h_table[i,0]), -np.sin(d_h_table[i,0]) * np.cos(d_h_table[i,1]), np.sin(d_h_table[i,0]) * np.sin(d_h_table[i,1]), d_h_table[i,2] * np.cos(d_h_table[i,0])],
                      [np.sin(d_h_table[i,0]), np.cos(d_h_table[i,0]) * np.cos(d_h_table[i,1]), -np.cos(d_h_table[i,0]) * np.sin(d_h_table[i,1]), d_h_table[i,2] * np.sin(d_h_table[i,0])],
                      [0, np.sin(d_h_table[i,1]), np.cos(d_h_table[i,1]), d_h_table[i,3]],
                      [0, 0, 0, 1]])  
 
# Homogeneous transformation matrix from frame 1 to frame 2
i = 1
homgen_1_2 = np.array([[np.cos(d_h_table[i,0]), -np.sin(d_h_table[i,0]) * np.cos(d_h_table[i,1]), np.sin(d_h_table[i,0]) * np.sin(d_h_table[i,1]), d_h_table[i,2] * np.cos(d_h_table[i,0])],
                      [np.sin(d_h_table[i,0]), np.cos(d_h_table[i,0]) * np.cos(d_h_table[i,1]), -np.cos(d_h_table[i,0]) * np.sin(d_h_table[i,1]), d_h_table[i,2] * np.sin(d_h_table[i,0])],
                      [0, np.sin(d_h_table[i,1]), np.cos(d_h_table[i,1]), d_h_table[i,3]],
                      [0, 0, 0, 1]])  
 
# Homogeneous transformation matrix from frame 2 to frame 3
i = 2
homgen_2_3 = np.array([[np.cos(d_h_table[i,0]), -np.sin(d_h_table[i,0]) * np.cos(d_h_table[i,1]), np.sin(d_h_table[i,0]) * np.sin(d_h_table[i,1]), d_h_table[i,2] * np.cos(d_h_table[i,0])],
                      [np.sin(d_h_table[i,0]), np.cos(d_h_table[i,0]) * np.cos(d_h_table[i,1]), -np.cos(d_h_table[i,0]) * np.sin(d_h_table[i,1]), d_h_table[i,2] * np.sin(d_h_table[i,0])],
                      [0, np.sin(d_h_table[i,1]), np.cos(d_h_table[i,1]), d_h_table[i,3]],
                      [0, 0, 0, 1]])  
 
homgen_0_3 = homgen_0_1 @ homgen_1_2 @ homgen_2_3
 
# Print the homogeneous transformation matrices
g.es("Homogeneous Matrix Frame 0 to Frame 1:")
g.es(homgen_0_1)
g.es()
g.es("Homogeneous Matrix Frame 1 to Frame 2:")
g.es(homgen_1_2)
g.es()
g.es("Homogeneous Matrix Frame 2 to Frame 3:")
g.es(homgen_2_3)
g.es()
g.es("Homogeneous Matrix Frame 0 to Frame 3:")
g.es(homgen_0_3)
g.es()