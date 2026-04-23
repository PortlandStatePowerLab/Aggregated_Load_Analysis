# -*- coding: utf-8 -*-
"""
Created on Wed Sep 24 08:57:35 2025

@author: Joe_admin
"""

import pandas as pd
import time
import numpy as np
import matplotlib.pyplot as plt
import os

start_time = time.time()

############################################################################
#                           Enter inputs here                              #
############################################################################

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
OCHRE_WORKING_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "ochre_working")

ninety_fifth_file_name  = os.path.join(OCHRE_WORKING_DIR, "N_10000", "hpwh_975th_AL_10000_for_baseline.csv")
mean_file_name          = os.path.join(OCHRE_WORKING_DIR, "N_10000", "hpwh_Mean_AL_10000_for_baseline.csv")
fifth_file_name         = os.path.join(OCHRE_WORKING_DIR, "N_10000", "hpwh_025th_AL_10000_for_baseline.csv")

############################################################################
#                             Program Start                                #
############################################################################

ninety_fifth_df = pd.read_csv(ninety_fifth_file_name)
mean_df         = pd.read_csv(mean_file_name)
fifth_df        = pd.read_csv(fifth_file_name)

# remove unused column
ninety_fifth_df = ninety_fifth_df.drop(['Unnamed: 0'], axis=1)
mean_df         = mean_df.drop(['Unnamed: 0'], axis=1)
fifth_df        = fifth_df.drop(['Unnamed: 0'], axis=1)

############################################################################
# FIX: stable grid definition
############################################################################

x_labels = ninety_fifth_df.columns.tolist()
x = np.arange(len(x_labels))

# FIX: use explicit row count (not pandas index object)
y = np.arange(ninety_fifth_df.shape[0])

X, Y = np.meshgrid(x, y)

############################################################################
# data
############################################################################

Z_95th = ninety_fifth_df.to_numpy()
Z_Mean = mean_df.to_numpy()
Z_5th  = fifth_df.to_numpy()

############################################################################
# Plotting
############################################################################

fig = plt.figure(figsize=(8, 7))
ax = fig.add_subplot(111, projection='3d')

# Normalize
y_min = Y.min()
y_max = Y.max()
norm = plt.Normalize(y_min, y_max)

colors = plt.cm.Greys_r(norm(Y))

# 95th percentile
ax.plot_surface(
    X, Y, Z_95th,
    facecolors=colors,
    rcount=20,
    ccount=96,
    alpha=0.5,
    edgecolor='k',
    linewidth=0.0,
    zorder=3
)

# mean
mean_colors = plt.cm.Blues_r(norm(Y))
ax.plot_surface(
    X, Y, Z_Mean,
    facecolors=mean_colors,
    rcount=20,
    ccount=96,
    alpha=0.6,
    edgecolor='blue',
    linewidth=0.0,
    zorder=3
)

# 5th percentile
ax.plot_surface(
    X, Y, Z_5th,
    facecolors=colors,
    rcount=20,
    ccount=96,
    alpha=0.5,
    edgecolor='k',
    linewidth=0.0,
    zorder=2
)

############################################################################
# FIX: correct highlight indexing
############################################################################

highlight_row = -1  # last row safely

ax.plot(x, y[highlight_row], Z_95th[highlight_row], color='k', linewidth=2.2, zorder=1001)
ax.plot(x, y[highlight_row], Z_Mean[highlight_row], color='blue', linewidth=2.2, zorder=1001)
ax.plot(x, y[highlight_row], Z_5th[highlight_row], color='k', linewidth=2.2, zorder=1001)

############################################################################
# time slice highlight (unchanged logic, safer indexing)
############################################################################

time_target = '23:45'

matching_cols = [c for c in ninety_fifth_df.columns if time_target in str(c)]

if len(matching_cols) == 0:
    raise ValueError(f"{time_target} not found in columns")

t_idx = ninety_fifth_df.columns.get_loc(matching_cols[0])

ax.plot(x[t_idx], y, Z_95th[:, t_idx], color='k', linewidth=2.2, zorder=1000)
ax.plot(x[t_idx], y, Z_Mean[:, t_idx], color='blue', linewidth=2.2, zorder=1000)
ax.plot(x[t_idx], y, Z_5th[:, t_idx], color='k', linewidth=2.2, zorder=1000)

############################################################################
# axes formatting (unchanged)
############################################################################

ax.set_xlim(ax.get_xlim()[::-1])

ax.set_xticks(range(96)[::8])
ax.set_xticklabels(x_labels[::8], rotation=45, ha='right')

ax.set_ylabel('Units [N]')
ax.zaxis.set_rotate_label(False)
ax.set_zlabel('Power [kW]', rotation=90)

ax.view_init(elev=20, azim=125)

plt.show()

############################################################################
# timing
############################################################################

end_time = time.time()
print(f"Execution time: {end_time - start_time} seconds")
print(f"Execution time: {(end_time - start_time)/60} minutes")