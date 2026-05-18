import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
OCHRE_WORKING_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "ochre_working")

input_csv_mean = os.path.join(
    OCHRE_WORKING_DIR,
    "N_10000",
    "hpwh_Mean_AL_10000_for_baseline.csv"
)

input_csv_5th = os.path.join(
    OCHRE_WORKING_DIR,
    "N_10000",
    "hpwh_025th_AL_10000_for_baseline.csv"
)

input_csv_95th = os.path.join(
    OCHRE_WORKING_DIR,
    "N_10000",
    "hpwh_975th_AL_10000_for_baseline.csv"
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
    'total_power_kW': summed_mean.values,
    '5th_percentile': summed_5th.values,
    '95th_percentile': summed_95th.values
})

# Save CSV
result_df.to_csv('summed_power_by_time_baseline.csv', index=False)

print("Process complete. Saved as 'summed_power_by_time_baseline.csv'")
print(result_df.head())


# ==========================================
#              PLOTTING SECTION
# ==========================================

# 1. Convert time strings to datetime objects so matplotlib can format the axis properly
plot_time = pd.to_datetime(result_df['time'])

# 2. Plot the curves
plt.plot(plot_time, result_df['total_power_kW'], label='Mean Power (kW)', color='blue', linewidth=2)
plt.plot(plot_time, result_df['5th_percentile'], label='5th Percentile', color='orange', linestyle='--', alpha=0.8)
plt.plot(plot_time, result_df['95th_percentile'], label='95th Percentile', color='green', linestyle='--', alpha=0.8)

# 3. Optional: Shade the area between 5th and 95th percentile curves for better visualization
plt.fill_between(plot_time, result_df['5th_percentile'], result_df['95th_percentile'], color='gray', alpha=0.15, label='5th-95th Range')

# 4. Labeling and formatting
plt.title('Controlled Total Power and Percentiles Over Time', fontsize=14, fontweight='bold')
plt.xlabel('Time of Day', fontsize=12)
plt.ylabel('Power (kW)', fontsize=12)
plt.legend(loc='upper right')

# 5. Clean up X-axis time ticks (shows a tick mark every 2 hours)
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))
plt.xticks(rotation=45)
plt.grid(True, linestyle='--', alpha=0.5)

# 6. Adjust layout and save the figure image
plt.tight_layout()
plt.savefig('summed_power_baseline_plot.png', dpi=150)

print("Plot successfully generated and saved as 'summed_power_baseline_plot.png'")