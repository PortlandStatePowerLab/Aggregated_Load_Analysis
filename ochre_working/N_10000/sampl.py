import os
print("Python is currently looking inside this folder:", os.getcwd())
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

filename = "\\ochre_working\\N_10000\\hpwh_Mean_AL_10000_for_baseline.csv"
df = pd.read_csv(filename, index_col=0)

# Drop the first row if it's completely NaN
df = df.dropna(how='all')

# Sum the values for each column
sums = df.sum()

# Convert index to datetime for better plotting on x-axis
sums.index = pd.to_datetime(sums.index)

# Plotting using matplotlib without .figure()
plt.plot(sums.index, sums.values, color='tab:blue', linewidth=2, marker='o', markersize=3)
plt.title('Sum of Values by 15-Minute Time Interval\n(2018-01-14)', fontsize=14, fontweight='bold')
plt.xlabel('Time of Day', fontsize=12)
plt.ylabel('Total Sum', fontsize=12)

# Format the x-axis to show hours nicely
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2)) # Tick every 2 hours
plt.xticks(rotation=45)
plt.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig('sum_15min_intervals.png', dpi=150)
print("Plot successfully saved to sum_15min_intervals.png")
print("First few sums:")
print(sums.head())
print("Total number of time intervals plotted:", len(sums))