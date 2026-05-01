# -*- coding: utf-8 -*-
"""
Created on Tue Sep 23 11:54:29 2025

@author: Joe_admin
@modified by: Jeff Dinsmore
@modified by : jdeline
@modified date: 4/14/2026

"""

import pandas as pd
import time
import numpy as np
import os
#from tqdm import tqdm

start_time = time.time()

import sys

def print_progress(current, total, bar_length=40):
    """
    Print a simple progress bar like:
    [##########----------] 25.0% (250/1000)
    """
    fraction = current / total
    percent = fraction * 100
    filled_len = int(bar_length * fraction)
    bar = "#" * filled_len + "-" * (bar_length - filled_len)
    sys.stdout.write(f"\r[{bar}] {percent:5.1f}% ({current}/{total})")
    sys.stdout.flush()


def sample_data(input_df, units):
    # Randomly sample N rows with replacement
    df_sampled = input_df.sample(n=units, replace=True) # remove the random state when done testing! 
    
    #before returning, remove the site ID column and sort
    df_sampled = df_sampled.drop(['building_id'], axis=1)
    return df_sampled
    
def get_MCS_run(N, input_df):
    num = 0
    for j, M in enumerate(np.arange(1, MCS_runs+1)):
        # sample the data
        df_sampled = sample_data(input_df, N)
        
        # get the aggragate load of the sample set
        agg_sample = df_sampled.sum()
        
        # add the agg load to the MSC_table
        MCS_table.loc[j] = agg_sample # this is one row of the MCS table!
    
    return MCS_table

def get_stats(input_df):
    # Compute the statistics
    summary_df = pd.DataFrame({
        '0.975 Quant': input_df.quantile(0.975),
        'Mean': input_df.mean(),
        '0.025 Quant': input_df.quantile(0.025),
        #'Variance' : input_df.var(ddof=0),
        #'Std Dev' : input_df.std(),
        #'Skew' : input_df.skew()
        }).T  # Transpose to get rows as statistics
    
    return summary_df
    
############################################################################
#                           Enter inputs here                              #
############################################################################

# enter in the input and output file names.   
file = "final_aggregated_controlled_15min.csv" 

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
OCHRE_WORKING_DIR = os.path.join( os.path.dirname(CURRENT_DIR), "ochre_working")
    
input_file_name  = os.path.join(OCHRE_WORKING_DIR, "Ready_data", file)
    
upper_quant_output_file  = os.path.join(OCHRE_WORKING_DIR, "N_10000", "hpwh_975th_AL_10000_for_controlled.csv")
mean_output_file         = os.path.join(OCHRE_WORKING_DIR, "N_10000", "hpwh_Mean_AL_10000_for_controlled.csv")
lower_quant_output_file  = os.path.join(OCHRE_WORKING_DIR, "N_10000", "hpwh_025th_AL_10000_for_controlled.csv")
#variance_output_file     = os.path.join(OCHRE_WORKING_DIR, "N_10000", "hpwh_var_AL_10000_for_controlled.csv")
#standard_dev_output_file = os.path.join(OCHRE_WORKING_DIR, "N_10000", "hpwh_sdev_AL_10000_for_controlled.csv")
#skew_output_file         = os.path.join(OCHRE_WORKING_DIR, "N_10000", "hpwh_skew_AL_10000_for_controlled.csv")

unit_runs = 10000
MCS_runs = 1000 

############################################################################
#                             Program Start                                #
############################################################################

# read data 
df = pd.read_csv(input_file_name)

# crease an arraw for the number of units
units_arr = np.arange(1, unit_runs+1)

# get the times 
times = df.drop(['building_id'], axis=1).columns # this was changed from ee_site)id

# initialize MSC table
MCS_table = pd.DataFrame(np.nan, index=range(MCS_runs), columns=times)

# initialize stats tables
upper_quant_df  = pd.DataFrame(np.nan, index=range(unit_runs), columns=times)
mean_df         = pd.DataFrame(np.nan, index=range(unit_runs), columns=times)
lower_quant_df  = pd.DataFrame(np.nan, index=range(unit_runs), columns=times)
#variance_df     = pd.DataFrame(np.nan, index=range(unit_runs), columns=times)
#std_dev_df      = pd.DataFrame(np.nan, index=range(unit_runs), columns=times)
#skew_df         = pd.DataFrame(np.nan, index=range(unit_runs), columns=times)

total_iterations = unit_runs

for i, N in enumerate(range(1, unit_runs + 1), start=1):
    print_progress(i, total_iterations)
    # get the table that contains each MCS run 
    MCS_table = get_MCS_run(N, df)
    
    # scale the aggreagte load profiles to PU values
    # MCS_table = MCS_table.div(0.5 * N)  # 0.5 for HPWH , 4.5 for ER
    
    # find the 95th, mean, 5th percentile values at each time step
    stats_df = get_stats(MCS_table)
    
    # save those stats to three seperate tables. 
    upper_quant_df.loc[i]  = stats_df.loc['0.975 Quant']
    mean_df.loc[i]         = stats_df.loc['Mean']
    lower_quant_df.loc[i]  = stats_df.loc['0.025 Quant']
    #variance_df.loc[i]     = stats_df.loc['Variance']
    #std_dev_df.loc[i]      = stats_df.loc['Std Dev']
    #skew_df.loc[i]         = stats_df.loc['Skew']

# results_df.to_csv(output_file_name, index=True)
upper_quant_df.to_csv(upper_quant_output_file, index=True)
mean_df.to_csv(mean_output_file, index=True)
lower_quant_df.to_csv(lower_quant_output_file, index=True)
#variance_df.to_csv(variance_output_file, index=True)
#std_dev_df.to_csv(standard_dev_output_file, index=True)
#skew_df.to_csv(skew_output_file, index=True)

# maximum widths of the 95th CI
width_df = upper_quant_df - lower_quant_df
result = pd.DataFrame({
    'max_value': width_df.max(axis=1),
    'max_column': width_df.idxmax(axis=1)
})

# print out the time it took to run the program
end_time = time.time()
execution_time = end_time - start_time
print(f"Execution time: {execution_time} seconds")
execution_min = execution_time/60
print(f"Execution time: {execution_min} minutes")




