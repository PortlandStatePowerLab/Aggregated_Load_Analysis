import pandas as pd
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
OCHRE_WORKING_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "ochre_working")

input_csv_mean = os.path.join(
    OCHRE_WORKING_DIR,
    "N_10000",
    "hpwh_Mean_AL_10000_for_controlled.csv"
)

input_csv_5th = os.path.join(
    OCHRE_WORKING_DIR,
    "N_10000",
    "hpwh_025th_AL_10000_for_controlled.csv"
)

input_csv_95th = os.path.join(
    OCHRE_WORKING_DIR,
    "N_10000",
    "hpwh_975th_AL_10000_for_controlled.csv"
)

# Load CSVs
df_mean = pd.read_csv(input_csv_mean)
df_5th = pd.read_csv(input_csv_5th)
df_95th = pd.read_csv(input_csv_95th)

# Set index (remove run number column)
df_mean.set_index(df_mean.columns[0], inplace=True)
df_5th.set_index(df_5th.columns[0], inplace=True)
df_95th.set_index(df_95th.columns[0], inplace=True)

# Sum across runs → total load per timestep
summed_mean = df_mean.sum() / 1000
summed_5th = df_5th.sum() / 1000
summed_95th = df_95th.sum() / 1000

# Combine into one DataFrame
result_df = pd.DataFrame({
    'time': summed_mean.index,
    'total_power_MW': summed_mean.values,
    '5th_percentile': summed_5th.values,
    '95th_percentile': summed_95th.values
})

# Save
result_df.to_csv('summed_power_by_time_controlled.csv', index=False)

print("Process complete. Saved as 'summed_power_by_time_controlled.csv'")
print(result_df.head())