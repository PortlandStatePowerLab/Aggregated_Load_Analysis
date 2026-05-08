# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import os
import csv
import time

start_time = time.time()

############################################################################
#                           INPUTS                                         #
############################################################################

last_rows = 9999

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
OCHRE_WORKING_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "ochre_working")

mean_file  = os.path.join(OCHRE_WORKING_DIR, "N_10000", "hpwh_Mean_AL_10000_for_controlled.csv")
p95_file   = os.path.join(OCHRE_WORKING_DIR, "N_10000", "hpwh_975th_AL_10000_for_controlled.csv")
p05_file   = os.path.join(OCHRE_WORKING_DIR, "N_10000", "hpwh_025th_AL_10000_for_controlled.csv")

output_file = os.path.join(OCHRE_WORKING_DIR, "N_10000", "P_mean_controlled_AL_10000.csv")

############################################################################
#                        HELPERS                                           #
############################################################################

def fix_time_columns(df):
    df.columns = [
        pd.to_datetime(col).strftime("%H:%M") if col != "Unnamed: 0" else col
        for col in df.columns
    ]
    return df

############################################################################
#                        LOAD DATA                                         #
############################################################################

mean_df = fix_time_columns(pd.read_csv(mean_file))
p95_df  = fix_time_columns(pd.read_csv(p95_file))
p05_df  = fix_time_columns(pd.read_csv(p05_file))

for df in [mean_df, p95_df, p05_df]:
    if "Unnamed: 0" in df.columns:
        df.drop("Unnamed: 0", axis=1, inplace=True)

mean_df = mean_df.tail(last_rows)
p95_df  = p95_df.tail(last_rows)
p05_df  = p05_df.tail(last_rows)

############################################################################
#                        TIME GRID                                         #
############################################################################

time_grid = [f"{h:02d}:{m:02d}" for h in range(24) for m in [0, 15, 30, 45]]

############################################################################
#                        OUTPUT CSV                                        #
############################################################################

with open(output_file, "w", newline="") as f:
    writer = csv.writer(f)

    # SAME HEADER AS YOUR ORIGINAL SCRIPT
    writer.writerow(["time", "P_mean_kW", "95th", "5th"])

    for i in range(96):

        time_select = time_grid[i]

        mean_data = mean_df[time_select]
        p95_data  = p95_df[time_select]
        p05_data  = p05_df[time_select]

        # ✔ EXACT SAME MATH AS YOUR PLOTTING SCRIPT
        P_mean_value = float(mean_data.mean())
        P_95_value   = float(p95_data.mean())
        P_05_value   = float(p05_data.mean())

        writer.writerow([
            time_select,
            P_mean_value,
            P_95_value,
            P_05_value
        ])

############################################################################
#                        DONE                                              #
############################################################################

print("CSV written (statistically equivalent to plotting script).")
print("Runtime:", time.time() - start_time)