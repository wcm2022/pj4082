import numpy as np # Scientific computing library
 
# Project: Coding Denavit-Hartenberg Tables Using Python - 6DOF Robotic Arm
#          This code excludes the servo motor that controls the gripper.
# Author: Addison Sears-Collins
# Date created: August 22, 2020
 
# Link lengths in centimeters
a1 = 1 # Length of link 1
a2 = 1 # Length of link 2
a3 = 1 # Length of link 3
a4 = 1 # Length of link 4
a5 = 1 # Length of link 5
a6 = 1 # Length of link 6
 
# Initialize values for the joint angles (degrees)
theta_1 = 0 # Joint 1
theta_2 = 0 # Joint 2
theta_3 = 0 # Joint 3
theta_4 = 0 # Joint 4
theta_5 = 0 # Joint 5
 
# Declare the Denavit-Hartenberg table. 
# It will have four columns, to represent:
# theta, alpha, r, and d
# We have the convert angles to radians.
d_h_table = np.array([[np.deg2rad(theta_1), np.deg2rad(90), 0, a1],
                      [np.deg2rad(theta_2), 0, a2, 0],
                      [np.deg2rad(theta_3), 0, a3, 0],
                      [np.deg2rad(theta_4 + 90), np.deg2rad(90), a5,0],
                      [np.deg2rad(theta_5), 0, 0, a4 + a6]]) 
 
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
 
# Homogeneous transformation matrix from frame 3 to frame 4
i = 3
homgen_3_4 = np.array([[np.cos(d_h_table[i,0]), -np.sin(d_h_table[i,0]) * np.cos(d_h_table[i,1]), np.sin(d_h_table[i,0]) * np.sin(d_h_table[i,1]), d_h_table[i,2] * np.cos(d_h_table[i,0])],
                      [np.sin(d_h_table[i,0]), np.cos(d_h_table[i,0]) * np.cos(d_h_table[i,1]), -np.cos(d_h_table[i,0]) * np.sin(d_h_table[i,1]), d_h_table[i,2] * np.sin(d_h_table[i,0])],
                      [0, np.sin(d_h_table[i,1]), np.cos(d_h_table[i,1]), d_h_table[i,3]],
                      [0, 0, 0, 1]])  
 
# Homogeneous transformation matrix from frame 4 to frame 5
i = 4
homgen_4_5 = np.array([[np.cos(d_h_table[i,0]), -np.sin(d_h_table[i,0]) * np.cos(d_h_table[i,1]), np.sin(d_h_table[i,0]) * np.sin(d_h_table[i,1]), d_h_table[i,2] * np.cos(d_h_table[i,0])],
                      [np.sin(d_h_table[i,0]), np.cos(d_h_table[i,0]) * np.cos(d_h_table[i,1]), -np.cos(d_h_table[i,0]) * np.sin(d_h_table[i,1]), d_h_table[i,2] * np.sin(d_h_table[i,0])],
                      [0, np.sin(d_h_table[i,1]), np.cos(d_h_table[i,1]), d_h_table[i,3]],
                      [0, 0, 0, 1]])  
 
homgen_0_5 = homgen_0_1 @ homgen_1_2 @ homgen_2_3 @ homgen_3_4 @ homgen_4_5 
 
# Print the homogeneous transformation matrices
g.es("Homogeneous Matrix Frame 0 to Frame 5:")
g.es(homgen_0_5)