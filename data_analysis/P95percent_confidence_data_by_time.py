# -*- coding: utf-8 -*-
"""
Created on Wed Sep 24 08:57:35 2025

@author: Joe_admin
@modified: Jeff Dinsmore, Josephine DeLine
@modified date: 04/22/2026
"""

import pandas as pd
import time
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score
import os
import csv

start_time = time.time()

############################################################################
#                           Enter inputs here                              #
############################################################################

last_rows = 9999         # Need data - 1. If 1000 points of data, 1000 - 1 = 999
baseline_name = "final_aggregated_baseline_15min.csv"
controlled_name = "final_aggregated_controlled_15min.csv"

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
OCHRE_WORKING_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "ochre_working")

ready_csv = os.path.join(OCHRE_WORKING_DIR, "Ready_data", controlled_name)

output_file =os.path.join(OCHRE_WORKING_DIR, "N_10000", "P_mean_controlled_PU_10000.csv")

# enter in the input and output file names.
ninety_fifth_file_name = os.path.join(OCHRE_WORKING_DIR, "N_10000", "hpwh_975th_PU_10000_for_controlled.csv")
mean_file_name = os.path.join(OCHRE_WORKING_DIR, "N_10000", "hpwh_Mean_PU_10000_for_controlled.csv")
fifth_file_name = os.path.join(OCHRE_WORKING_DIR, "N_10000", "hpwh_025th_PU_10000_for_controlled.csv")

time_select = '21:45'
hour = 00
minute = '00'

############################################################################
#                             Program Start                                #
############################################################################

# read data 
ninety_fifth_df = pd.read_csv(ninety_fifth_file_name)
mean_df         = pd.read_csv(mean_file_name)
fifth_df        = pd.read_csv(fifth_file_name)


# get housing number
file_df = pd.read_csv(ready_csv)
N_rows_in_file = file_df.shape[0]
print("N_rows_in_file =", N_rows_in_file)

# remove the columns we dont need
ninety_fifth_df = ninety_fifth_df.drop(['Unnamed: 0'], axis=1)
mean_df         = mean_df.drop(['Unnamed: 0'], axis=1)
fifth_df        = fifth_df.drop(['Unnamed: 0'], axis=1)

mean_df.columns = pd.to_datetime(mean_df.columns, errors='coerce').strftime('%H:%M')
ninety_fifth_df.columns = pd.to_datetime(ninety_fifth_df.columns, errors='coerce').strftime('%H:%M')
fifth_df.columns = pd.to_datetime(fifth_df.columns, errors='coerce').strftime('%H:%M')


# cut off the early data
ninety_fifth_df = ninety_fifth_df.tail(last_rows)
mean_df         = mean_df.tail(last_rows)
fifth_df        = fifth_df.tail(last_rows)

for i in range (96):
    if len(str(hour)) == 1:
        tempHour = '0' + str(hour)
    else:
        tempHour = str(hour)
    time_select = tempHour + ':' + minute
    print(f"Time select: ", time_select)
    ninety_fifth_data = ninety_fifth_df[time_select]
    mean_data         = mean_df[time_select]
    fifth_data        = fifth_df[time_select]

    # Create the figure and plot the initial data
    A = 16
    fig = plt.figure(figsize=(9, 7))
    ax1 = fig.add_subplot()

    # plot each data in grey
    #X = mean_data.index.to_numpy()
    X = np.arange(1, len(mean_data) + 1)
    #X = mean_df["N"].tail(last_rows).to_numpy()
    

    # 97.5th percentile
    ax1.plot(X, ninety_fifth_data.values, color='gray', alpha=1, linewidth=3)
    ax1.fill_between(X, ninety_fifth_data.values, mean_data.values, color='pink', alpha=0.3)

    # mean
    ax1.plot(X, mean_data.values, color='blue', alpha=1, linewidth=3)

    # 2.5th percentile
    ax1.plot(X, fifth_data.values, color='gray', alpha=1, linewidth=3)
    ax1.fill_between(X, fifth_data.values, mean_data.values, color='pink', alpha=0.3)

    # plot the numpy polynomial model best fit for the mean
    z = np.polyfit(X, mean_data.values, 1) # R values still > 0.99 when the number of units is 1000.
    f = np.poly1d(z)
    print("f: ", f)
    coefficient_of_dermination = r2_score(mean_data.values, f(X))
    print("coeff of derm", coefficient_of_dermination)

    # ax1.plot(X, f(X), color='green', linewidth=2)
    ax1.plot(X, f(X), label='ax + b fit', color='red', linewidth=1.5)

    # annotate the best fit line
    arc = 0.18
    P_mean_value = float(mean_data.mean())
    print(f"Mean_df: {P_mean_value} 95th: {ninety_fifth_data.mean()} 5th: {fifth_data.mean()}")

    new_row = {
        "time": time_select,
        "P_mean_kW": P_mean_value   # whatever scalar you computed
    }
    print(f"P_mean {P_mean_value}")
    file_exists = os.path.exists(output_file)

    with open(output_file, "a", newline="") as file:
        w = csv.writer(file)
        if not file_exists:
            w.writerow(["time", "P_mean_kW", "95th", "5th"])   # header once
        w.writerow([time_select, P_mean_value, ninety_fifth_data.mean(), fifth_data.mean()])          # ONE new row

    ax1.annotate(r'$P_{mean} = 0.1507N + 0.1501$', xy=(280, 42), xytext=(110, 65), fontsize=A, color='red', 
                bbox=dict(boxstyle='round,pad=0.2', fc='grey', alpha=0.3),
                arrowprops=dict(arrowstyle="->",color='k' ,linewidth=2.5,connectionstyle=f"arc3,rad={arc}"))  
    
    ax1.text(110, 59, r'$R^2 = 0.999$', fontsize=A, color='red',
            bbox=dict(boxstyle='round,pad=0.2', fc='grey', alpha=0.3))

    # Create a secondary y-axis that shares the same x-axis
    ax2 = ax1.twinx()

    # plot the uncertainty as  proportion of the mean
    CI_width = ( ninety_fifth_df[time_select] - fifth_df[time_select] ) / mean_df[time_select] * 100
    x_target = 409

    # Convert to numpy for safety
    X_arr  = X
    CI_arr = CI_width.to_numpy(dtype=float)

    idx = np.where(X_arr == x_target)[0]

    if idx.size == 0:
        raise ValueError("x_target not found in X")

    y_target = CI_arr[idx[0]]
    """CI_arr = CI_width.to_numpy(dtype=float)

    # Find where X == 409
    idx = np.where(X_arr == x_target)[0]

    if idx.size > 0:
        y_at_409 = CI_arr[idx[0]]
        print(f"Green curve value at x={x_target}: {y_at_409:.2f}%")
    else:
        print("x=409 not found exactly in X")"""
    target = 20.0  # percent threshold

    CI = pd.to_numeric(CI_width, errors="coerce").to_numpy(dtype=float)

    # mask out invalid or divide-by-zero situations
    y_mean = pd.to_numeric(mean_df[time_select], errors="coerce").to_numpy(dtype=float)
    valid = np.isfinite(CI) & np.isfinite(y_mean) & (y_mean != 0)

    # default in case we never cross the threshold
    x_star = None
    ci_star = None

    if np.any(valid):
        CIv = CI[valid]
        Xv = X[valid]  # uses the same X you're plotting on the x-axis

        # find first index where CI drops below target
        below = np.where(CIv <= target)[0]
        if below.size > 0:
            k = below[0]
            x_star = Xv[k]
            ci_star = CIv[k]

    ax2.plot(X, CI_width, color='green', linewidth=2)

    ax2.axhline(y=y_target, color='g', linestyle='--', alpha=0.5)
    ax1.axvline(x=N_rows_in_file, color='g', linestyle='--', alpha=0.5)
    ax2.plot(N_rows_in_file, y_target, 'o', color='k')
    #ax2.plot(430, 20, 'o', color='k')
    
    ax2.text(351, y_target+6, r'$N \approx$'+str(N_rows_in_file), fontsize=A, color='k',
            bbox=dict(boxstyle='round,pad=0.2', fc='grey', alpha=0.3))



    # Set y scale to exponential if needed
    '''
    ax1.set_yscale('log', base=10) # original log scale
    ax2.set_yscale('log', base=10) # original log scale
    ax1.set_xscale('log', base=10) # original log scale
    '''

    # Create formatted strings for the fit and R^2 value
    a = f.c[0]
    b = f.c[1]
    fit_text = rf"$P_{{mean}} = {a:.4e}x + {b:.4f}$"
    #fit_text = f
    r2_text  = rf"$R^2 = {coefficient_of_dermination:.4f}$"
    #rmse = np.sqrt(np.mean((y - yhat)**2))
    #print("RMSE [kW]:", rmse)
    #nrmse = rmse / np.mean(y)
    #print("NRMSE:", nrmse)
    # Place equation in upper-left corner of the axes
    ax1.text(
        0.25, 0.95,          # X,Y in axes fraction space
        fit_text,
        transform=ax1.transAxes,   # <-- this makes it axes-relative
        fontsize=A,
        color='blue',
        va='top',
        bbox=dict(boxstyle='round,pad=0.3', fc='grey', alpha=0.3)
    )

    # Place R² just below it
    """ax1.text(
        0.25, 0.88,
        r2_text,
        transform=ax1.transAxes,
        fontsize=A,
        color='blue',
        va='top',
        bbox=dict(boxstyle='round,pad=0.3', fc='grey', alpha=0.3)
    )"""

    ax1.set_title(
    f'Baseline Mean HPWH Load vs. Units at {time_select}',
    fontsize=A+2,
    pad=12
)
    # ax.set(ylim=(.255,0.262))
    ax1.grid(True, alpha=0.4)
    ax1.set_ylabel('Power [kW]', fontsize=A)
    ax2.set_ylabel('95% CI / Mean [%]', fontsize=A, color='green')
    ax2.set_ylim(-4.5, 100)
    ax1.set_xlabel('Units [N]', fontsize=A)
    ax1.tick_params(axis='x', labelsize=A)
    ax1.tick_params(axis='y', labelsize=A)
    ax2.tick_params(axis='y', labelsize=A, colors='g', grid_color='g')

    # print out the time it took to run the program
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Execution time: {execution_time} seconds")
    execution_min = execution_time/60
    print(f"Execution time: {execution_min} minutes")
    
    #plt.show()
    #plt.savefig('control_10000_' + time_select +'.png')
    if minute == '45':
        hour+=1
    match i % 4:
        case 0:
            minute = '15'
        case 1:
            minute = '30'
        case 2:
            minute = '45'
        case 3:
            minute = '00'
    