# -*- coding: utf-8 -*-
"""
Created on Wed Sep 24 08:57:35 2025

@author: Joe_admin
"""

import pandas as pd
import time
import numpy as np
import matplotlib.pyplot as plt

start_time = time.time()

############################################################################
#                           Enter inputs here                              #
############################################################################

# enter in the input and output file names.   
ninety_fifth_file_name  = "C:/Users/Joe_admin/Documents/IEEE_2026_paper/ML_files/hpwh_975th_300_04.csv"
mean_file_name          = "C:/Users/Joe_admin/Documents/IEEE_2026_paper/ML_files/hpwh_Mean_300_04.csv"
fifth_file_name         = "C:/Users/Joe_admin/Documents/IEEE_2026_paper/ML_files/hpwh_025th_300_04.csv"


write_percent_error = False
############################################################################
#                             Program Start                                #
############################################################################

# read data 
ninety_fifth_df = pd.read_csv(ninety_fifth_file_name)
mean_df         = pd.read_csv(mean_file_name)
fifth_df        = pd.read_csv(fifth_file_name)

# remove the columns we dont need
ninety_fifth_df = ninety_fifth_df.drop(['Unnamed: 0'], axis=1)
mean_df         = mean_df.drop(['Unnamed: 0'], axis=1)
fifth_df        = fifth_df.drop(['Unnamed: 0'], axis=1)

# then later apply the strings as x tick labels. 
x_labels = ninety_fifth_df.columns.tolist()
x = np.arange(len(x_labels))

y = ninety_fifth_df.index
X,Y = np.meshgrid(x,y)

# get values for 95th percentile
Z_95th = ninety_fifth_df.values

# get values for the mean
Z_Mean = mean_df.values

# get values for 5th percentile
Z_5th = fifth_df.values

# Plotting
fig = plt.figure(figsize=(8, 7))
ax = fig.add_subplot(111, projection='3d')

# Normalize X values for coloring
y_min = Y.min()
y_max = Y.max()
norm = plt.Normalize(y_min, y_max)
colors = plt.cm.Greys_r(norm(Y))  # use for color mapping

# Plot the 95th percentile
ax.plot_surface(X, Y, Z_95th, facecolors=colors, rcount=20, ccount=96, alpha=0.5, edgecolor='k', linewidth=0.0, zorder=3) 

# plot the mean
norm = plt.Normalize(y_min, y_max+200)
mean_colors = plt.cm.Blues_r(norm(Y))
ax.plot_surface(X, Y, Z_Mean,  facecolors=mean_colors, rcount=20, ccount=96, alpha=0.6, edgecolor='blue', linewidth=0.0, zorder=3) 

# plot the 5the percentile
norm = plt.Normalize(y_min, y_max)
colors = plt.cm.Greys_r(norm(Y))
ax.plot_surface(X, Y, Z_5th,  facecolors=colors, rcount=20, ccount=96, alpha=0.5, edgecolor='k', linewidth=0.0, zorder=2) 

# Highlight N = 300
highlight_loc = ninety_fifth_df.tail(1).index
ax.plot(x, highlight_loc, ninety_fifth_df.loc[highlight_loc].values, color='k', linewidth=2.2, zorder=1001)
ax.plot(x, highlight_loc, mean_df.loc[highlight_loc].values, color='blue', linewidth=2.2, zorder=1001)
ax.plot(x, highlight_loc, fifth_df.loc[highlight_loc].values, color='k', linewidth=2.2, zorder=1001)

# Highlight t = 22:00
ax.plot(95, y, ninety_fifth_df['23:45'].values, color='k', linewidth=2.2, zorder=1000)
ax.plot(95, y, mean_df['23:45'].values, color='blue', linewidth=2.2, zorder=1000)
ax.plot(95, y, fifth_df['23:45'].values, color='k', linewidth=2.2, zorder=1000)

# Flip the Y axis
ax.set_xlim(ax.get_xlim()[::-1])

# update the x ticks
tick_labels_x   = ninety_fifth_df.columns[::8]
ax.set_xticks(range(96)[::8])
ax.set_xticklabels(tick_labels_x , rotation=45, ha='right')

# update the y ticks
tick_labels_y   = ninety_fifth_df.index.to_numpy() + 1

# Labels and colorbar
ax.set_ylabel('Units [N]')
ax.zaxis.set_rotate_label(False) 
ax.set_zlabel('Power [kW]', rotation=90)

# set the view
ax.view_init(elev=20, azim=125)
plt.show()

# print out the time it took to run the program
end_time = time.time()
execution_time = end_time - start_time
print(f"Execution time: {execution_time} seconds")
execution_min = execution_time/60
print(f"Execution time: {execution_min} minutes")
