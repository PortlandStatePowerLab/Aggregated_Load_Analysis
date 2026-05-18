import os
import numpy as np
import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
OCHRE_WORKING_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "ochre_working")

input_delta_csv = os.path.join(
    OCHRE_WORKING_DIR,
    "N_10000",
    "P_summed_AL_control_minus_baseline_10000.csv"
)

input_baseline_mean_csv = os.path.join(
    OCHRE_WORKING_DIR,
    "N_10000",
    "summed_power_by_time_baseline.csv"
)

# Load Dataframes
df_delta = pd.read_csv(input_delta_csv)
df_base = pd.read_csv(input_baseline_mean_csv)

# Convert time (NOW handles full datetime)
for df in [df_delta, df_base]:
    df['time_dt'] = pd.to_datetime(df['time'])  # <-- FIXED
    df['hours'] = (
        df['time_dt'].dt.hour +
        df['time_dt'].dt.minute / 60.0
    )

def get_window_energy_total(df, column, start_h, end_h):
    mask = (df['hours'] >= start_h) & (df['hours'] <= end_h)
    window_df = df[mask].sort_values('hours')
    if window_df.empty:
        return 0
    return np.trapz(window_df[column].values, window_df['hours'].values)

# Define Windows
windows = [
    ("Morning Load Up", 3, 5),
    ("Morning Shed", 6, 10),
    ("Afternoon Load Up", 16, 17),
    ("Afternoon Shed", 17, 20)
]

results = []

for label, start, end in windows:
    # Delta (Control - Baseline)
    e_delta = get_window_energy_total(df_delta, 'P_mean', start, end)
    e_bestcase = get_window_energy_total(df_delta, 'best_case', start, end)
    e_worstcase = get_window_energy_total(df_delta, 'worst_case', start, end)
    
    # Baseline (MAKE SURE THESE MATCH YOUR CSV COLUMN NAMES)
    e_base_total = get_window_energy_total(df_base, 'total_power_kW', start, end)
    e_base_5th = get_window_energy_total(df_base, '5th_percentile', start, end)
    e_base_95th = get_window_energy_total(df_base, '95th_percentile', start, end)
    
    # Percent reduction (Baseline - Control) / Baseline
    percent_reduction_mean = (e_delta / e_base_total) * 100 if e_base_total != 0 else 0

    results.append({
        "Event": label,
        "Time Range": f"{int(start):02d}:00 - {int(end):02d}:00",
        "Energy Impact (kWh)": round(e_delta, 2),
        "Baseline Energy (kWh)": round(e_base_total, 2),
        "Best Case Energy (kWh)": round(e_bestcase, 2),
        "Worst Case Energy (kWh)": round(e_worstcase, 2),
        "Percent Load Reduction (Mean)": f"{round(percent_reduction_mean, 2)}%"
    })

final_table = pd.DataFrame(results)

print(final_table)