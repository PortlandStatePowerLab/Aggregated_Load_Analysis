# =============================================================================
# Title: HPWH Aggregate Power Comparison & Percentile Visualization
# Author: Jeff Dinsmore
# Date: 01/25/2026
#
# Description:
# This script compares baseline and controlled HPWH aggregate load profiles.
# It scales per-unit Monte Carlo results to a specified fleet size (N_units),
# computes differences between baseline and controlled cases, and generates
# multiple plots including:
#   - Controlled minus Baseline
#   - Baseline minus Controlled
#   - Direct Baseline vs Controlled comparison
#
# The script dynamically scales power units (kW, MW, GW) based on magnitude
# and formats output titles using comma-separated fleet sizes.
# =============================================================================



import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
#import helpers
from helpers import kwh_from_power_csv, power_units_scale, plot_segment_energy, compute_segment_energy, with_commas, get_csv_data

# -----------------------------------------------------------------------------
# USER INPUTS
# -----------------------------------------------------------------------------

# Number of HPWH units to scale results to
N_units = 1

# Default units (will be adjusted dynamically)
units = "kW"
base = 1

#file_name = "P_mean_baseline_minus_control_1000.csv"

#df_minus = pd.read_csv(file_name)




# ---------------------------------------------------------------------
# USER INPUT
# ---------------------------------------------------------------------
file_name = "P_mean_baseline_minus_control_10000.csv"
dt_minutes = 15

# ---------------------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------------------
df = pd.read_csv(file_name)

time = df.iloc[:, 0]
P_mean = pd.to_numeric(df.iloc[:, 1], errors="coerce")

# Convert to kWh
dt_hr = dt_minutes / 60
E_kWh = P_mean * dt_hr

# ---------------------------------------------------------------------
# PLOT
# ---------------------------------------------------------------------
"""
x = np.arange(len(time))

plt.figure(figsize=(14,6))
plt.bar(x, E_kWh)

# Show every hour (every 4 intervals)
plt.xticks(x[::4], time[::4], rotation=45)

plt.xlabel("Time")
plt.ylabel("Energy (kWh)")
plt.title("Energy Consumption per 15-Minute Interval (1 Unit)")
plt.grid(axis="y")

plt.tight_layout()
"""

# ---------------------------------------------------------------------
# PRINT TOTAL DAILY ENERGY
# ---------------------------------------------------------------------
total_energy = E_kWh.sum()
print(f"Total Daily Energy = {total_energy:.2f} kWh")

# -----------------------------------------------------------------------------
# FUNCTION: Dynamic Power Unit Scaling
# Determines appropriate engineering units (kW, MW, GW)
# based on magnitude of power value.
# -----------------------------------------------------------------------------




df_energy = compute_segment_energy("P_mean_baseline_10000.csv")
# -----------------------------------------------------------------------------
# FUNCTION: Format integers with commas (for titles)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# LOAD MONTE CARLO RESULTS
# Uses larger dataset if fleet exceeds 3000 units
# -----------------------------------------------------------------------------
if N_units > 3000:
    df = pd.read_csv("P_mean_baseline_10000.csv")
    df_control = pd.read_csv("P_mean_control_10000.csv")
    df_control_baseline = pd.read_csv("P_mean_baseline_minus_control_10000.csv")
else:
    df = pd.read_csv("P_mean_baseline_1000.csv")
    df_control = pd.read_csv("P_mean_control_1000.csv")


time, P_mean, P_97, P_2 = get_csv_data(df, N_units)

# y data
y = P_mean.to_numpy()

# numeric x in hours: 0, 0.25, ..., 23.75  (96 points)
x = np.arange(len(y)) * 0.25
T = 24.0
N = 4  # number of harmonics (try 3, 4, 6)

dt_hr = 15/60  # 0.25 hours
area_kWh = P_mean.sum() * dt_hr
print("areay under curve P_mean", area_kWh)

# Daily statistics
P_mean_avg = P_mean.mean()
P_mean_max = P_mean.max()
#print(f"Pmean max = {P_mean_max}- Pavg = {P_mean.mean()}")

omega = 2 * np.pi / T

# Build design matrix: [1, cos(1ωx), sin(1ωx), cos(2ωx), sin(2ωx), ...]
cols = [np.ones_like(x)]
for k in range(1, N + 1):
    cols.append(np.cos(k * omega * x))
    cols.append(np.sin(k * omega * x))
X = np.column_stack(cols)

# Least squares fit
beta, *_ = np.linalg.lstsq(X, y, rcond=None)

def f(xx):
    xx = np.asarray(xx)
    yhat = beta[0] * np.ones_like(xx, dtype=float)
    idx = 1
    for k in range(1, N + 1):
        yhat += beta[idx] * np.cos(k * omega * xx); idx += 1
        yhat += beta[idx] * np.sin(k * omega * xx); idx += 1
    return yhat

#def f(x):
 #   return a0 + a1*np.cos(omega*x) + b1*np.sin(omega*x)

# R^2 on the original x points
y_pred = f(x)
ss_res = np.sum((y - y_pred) ** 2)
ss_tot = np.sum((y - y.mean()) ** 2)
r2 = 1 - ss_res / ss_tot
print(f"Fourier N={N}, R^2 = {r2:.4f}")

# -----------------------------------------------------------------------------
# EXTRACT CONTROLLED DATA AND SCALE TO N_units
# -----------------------------------------------------------------------------
time_c = df_control.iloc[:, 0]          # time strings
P_mean_c = df_control.iloc[:, 1] * N_units
P_97_c = df_control.iloc[:, 2] * N_units
P_2_c = df_control.iloc[:, 3] * N_units

# Daily statistics
P_mean_avg_c = P_mean_c.mean()
P_mean_max_c = P_mean_c.max()
#print(f"Pmean max_c = {P_mean_max_c}- Pavg = {P_mean_c.mean()}")

# -----------------------------------------------------------------------------
# DIFFERENCE CALCULATIONS
# -----------------------------------------------------------------------------

# Baseline minus Controlled
P_mean_adj = P_mean - P_mean_c
P_97_adj = P_97 - P_2_c
P_2_adj = P_2 - P_97_c

# Daily statistics
P_mean_avg_adj = P_mean_adj.mean()
P_mean_max_adj = P_mean_adj.max()
P_mean_min_adj = P_mean_adj.min()
#print(f"Pmean max_adj = {P_mean_max_adj} & Pavg = {P_mean_adj.mean()}")

# Controlled minus Baseline
P_mean_adj2 = P_mean_c - P_mean
P_97_adj2 = P_97_c - P_2
P_2_adj2 = P_2_c - P_97
P_mean_avg_adj2 = P_mean_adj2.mean()
P_mean_max_adj2 = P_mean_adj2.max()
P_mean_min_adj2 = P_mean_adj2.min()
#print(f"Pmean max_adj2 = {P_mean_max_adj2} & Pavg2 = {P_mean_adj2.mean()}")

E_base_kWh = P_mean.sum() * 0.25
E_ctrl_kWh = P_mean_c.sum() * 0.25
print("Area baseline vs control", E_base_kWh, E_ctrl_kWh, E_base_kWh - E_ctrl_kWh)

area_diff_kWh = (P_mean - P_mean_c).abs().sum() * 0.25
print("area between curves", area_diff_kWh)

# Convert to energy if desired (kWh)
E_mean = P_mean_adj/ base / 4
E_97   = P_97_adj / base / 4
E_2    = (P_2_adj) / base / 4

# Differences for shading
upper_diff = E_97 - E_mean
lower_diff = E_mean - E_2

#time = df_minus.iloc[:, 0]
#P_mean = pd.to_numeric(df_minus.iloc[:, 1], errors="coerce")
#ninety_seventh = pd.to_numeric(df_minus.iloc[:, 2], errors="coerce")


# -----------------------------------------------------------------------------
# PLOT: BAR - BASELINE MINUS CONTROLLED
# -----------------------------------------------------------------------------
x = np.arange(len(time))
width = 0.8  # width of each bar

# Build "edges" so the step lines align with bar edges
edges = np.arange(len(time) + 1) - 0.5

# For step plotting, we need one extra value at the end
E97_step = np.r_[E_97.to_numpy(), E_97.to_numpy()[-1]]
E2_step  = np.r_[E_2.to_numpy(),  E_2.to_numpy()[-1]]

plt.figure(figsize=(14, 6))

# Mean bars
mean_bars = plt.bar(
    x,
    E_mean,
    width=0.8,
    color="royalblue",
    alpha=0.9,
    label="Mean",
    zorder=1
)

# Shaded confidence band
ci_band = plt.fill_between(
    edges,
    E2_step,
    E97_step,
    step="post",
    color="#E8D8B8",
    alpha=0.35,
    label="95% Band",
    zorder=2
)

# Step lines ON TOP
# 97.5th step line (GREEN)
line97, = plt.step(
    edges,
    E97_step,
    where="post",
    linewidth=2.5,
    color="green",
    label="97.5th",
    zorder=3
)
# 2.5th step line (DARK GREEN)
line2, = plt.step(
    edges,
    E2_step,
    where="post",
    linewidth=2.5,
    color="orange",
    label="2.5th",
    zorder=3
)

#plt.bar(x - width, E_2, width=width, color="lightgreen")
#plt.bar(x - width, E_mean, bottom=E_2, label="Mean", color="blue")
#plt.bar(x - width, E_97, bottom=E_mean, color="orange")

#plt.plot(time, E_97, label="97th Percentile", linestyle="--")
#plt.plot(time, E_2, label="2.5th Percentile", linestyle="--")

# Optional shaded percentile band
#plt.fill_between(time, E_2, E_97, alpha=0.2, label="2.5–97.5% Range")

#plt.bar(x,         E_97,   width=width, label="97.5th", color="red")
#plt.bar(x + width, E_2,    width=width, label="2.5th", color="green")

# Reduce x clutter (hourly labels)
plt.xticks(x[::4], time.iloc[::4], rotation=45)


plt.xlabel("Time")
plt.ylabel(f"Energy (kWh)")
plt.title("Baseline Minus Controlled Energy by Time Interval With Confidence Envelope (1 Unit)")
plt.legend()
plt.grid(axis="y")

plt.tight_layout()

top5 = df_energy.sort_values("E_mean_kWh", ascending=False).head(5)

print(top5[["time", "E_mean_kWh"]])

total_energy = df_energy["E_mean_kWh"].sum()
print(f"Total Daily Energy = {total_energy:.2f} kWh")
#units, base = power_units_scale(P_mean_max)

"""
# Create plot
plt.figure(figsize=(12, 6))

plt.plot(time, P_mean / base, label=(f"Mean Power ({units})"), linewidth=2)
plt.plot(time, P_97 / base, label="97th Percentile", linestyle="--")
plt.plot(time, P_2 / base, label="2.5th Percentile", linestyle="--")

# Optional shaded percentile band
plt.fill_between(time, P_2 / base, P_97 / base, alpha=0.2, label="2.5–97.5% Range")

# Formatting
plt.xlabel("Time")
plt.ylabel(f"Power ({units})")
plt.title("Baseline Mean Power with 2.5th–97th Percentile Range")
plt.legend()
plt.grid(True)

# Reduce x-axis clutter (show every N labels)
N = 4  # every hour if 15-min increments
plt.xticks(ticks=range(0, len(time), N),
           labels=time.iloc[::N],
           rotation=45)

units, base = power_units_scale(P_mean_max_c)

plt.figure(figsize=(12, 6))

plt.plot(time_c, P_mean_c / base, label=(f"Mean Power ({units})"), linewidth=2)
plt.plot(time_c, P_97_c / base, label="97.5th Percentile", linestyle="--")
plt.plot(time_c, P_2_c / base, label="2.5th Percentile", linestyle="--")

# Optional shaded percentile band
plt.fill_between(time_c, P_2_c / base, P_97_c / base, alpha=0.2, label="2.5–97.5% Range")

# Formatting
plt.xlabel("Time")
plt.ylabel(f"Power ({units})")
plt.title("Controlled Mean Power with 2.5th–97th Percentile Range")
plt.legend()
plt.grid(True)

# Reduce x-axis clutter (show every N labels)
N = 4  # every hour if 15-min increments
plt.xticks(ticks=range(0, len(time_c), N),
           labels=time_c.iloc[::N],
           rotation=45)
"""

# -----------------------------------------------------------------------------
# PLOT: CONTROLLED MINUS BASELINE
# -----------------------------------------------------------------------------
"""def plot_power(
    time,
    y,
    title="Power Plot",
    ylabel="Power (kW)",
    show_mean=False,
    figsize=(12,6),
    minimum,
    maximum
):
    units, base = power_units_scale(minimum if abs(maximum) < abs(minimum) else maximum)
    plt.figure(figsize=figsize)

    plt.plot(time, y, linewidth=2, label="Power")

    if show_mean:
        y_avg = y.mean()
        plt.axhline(
            y=y_avg,
            linestyle=":",
            linewidth=2,
            label=f"Mean = {y_avg:.2f}"
        )

    if len(time) == 96:
        plt.xticks(range(0, len(time), 4), time.iloc[::4], rotation=45)

    plt.xlabel("Time")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
"""
units, base = power_units_scale(P_mean_min_adj2 if abs(P_mean_max_adj2) < abs(P_mean_min_adj2) else P_mean_max_adj2)

# -----------------------------------------------------------------------------
# PLOT: CONTROLLED MINUS BASELINE
# -----------------------------------------------------------------------------
"""

# Create plot
plt.figure(figsize=(12, 6))
# Daily average reference line
plt.axhline(
    y=P_mean_avg_adj2 / base,
    linestyle=":",
    linewidth=2,
    label=f"Daily Avg = {P_mean_avg_adj2/base:.2f} kW"
)

plt.plot(time, P_mean_adj2 / base, label=(f"Mean Power ({units})"), linewidth=2)
plt.plot(time, P_97_adj2 / base, label="97th Percentile", linestyle="--")
plt.plot(time, P_2_adj2 / base, label="2.5th Percentile", linestyle="--")


# Optional shaded percentile band
plt.fill_between(time, P_2_adj2 / base, P_97_adj2 / base, alpha=0.2, label="2.5–97.5% Range")

# Formatting
plt.xlabel("Time")
plt.ylabel(f"Power ({units})")
plt.title(f"Controlled Minus Baseline Mean Power with 2.5th–97th Percentile Range ({with_commas(N_units)} Units)")
plt.legend()
plt.grid(True)

# Reduce x-axis clutter (show every N labels)
N = 4  # every hour if 15-min increments
plt.xticks(ticks=range(0, len(time), N),
           labels=time.iloc[::N],
           rotation=45)
"""
# -----------------------------------------------------------------------------
# PLOT: BASELINE MINUS CONTROLLED
# -----------------------------------------------------------------------------

units, base = power_units_scale(P_mean_min_adj if abs(P_mean_max_adj) < abs(P_mean_min_adj) else P_mean_max_adj)

# Create plot
plt.figure(figsize=(12, 6))
# Mean (average) line
plt.axhline(
    y=P_mean_avg_adj / base,
    linestyle=":",
    linewidth=2,
    label=f"Daily Avg = {P_mean_avg_adj/base:.2f} kW"
)

plt.plot(time, P_mean_adj / base, label=(f"Mean Power ({units})"), linewidth=2)
plt.plot(time, P_97_adj / base, label="97th Percentile", linestyle="--")
plt.plot(time, P_2_adj / base, label="2.5th Percentile", linestyle="--")


# Optional shaded percentile band
plt.fill_between(time, P_2_adj / base, P_97_adj / base, alpha=0.2, label="2.5–97.5% Range")

# Formatting
plt.xlabel("Time")
plt.ylabel(f"Power ({units})")
plt.title(f"Baseline Minus Controlled Mean Power with 2.5th–97th Percentile Range ({with_commas(N_units)} Units)")
plt.legend()
plt.grid(True)

# Reduce x-axis clutter (show every N labels)
N = 4  # every hour if 15-min increments
plt.xticks(ticks=range(0, len(time), N),
           labels=time.iloc[::N],
           rotation=45)


# -----------------------------------------------------------------------------
# PLOT: BASELINE VS CONTROLLED OVERLAY
# -----------------------------------------------------------------------------

units, base = power_units_scale(P_mean_max_c)
# Create plot
plt.figure(figsize=(12, 6))
# Mean (average) line
plt.axhline(
    y=P_mean_avg_c / base,
    linestyle="dashdot",
    linewidth=2,
    label=f"Daily Controlled Avg = {P_mean_avg_c / base:.2f} kW"
)
# Mean (average) line
plt.axhline(
    y=P_mean_avg / base,
    linestyle=":",
    linewidth=2,
    label=f"Daily Baseline Avg = {P_mean_avg / base:.2f} kW"
)
plt.plot(time, P_mean / base, label=(f"Baseline Mean Power ({units})"), linewidth=2)
plt.plot(time, P_97 / base, label="Baseline 97th Percentile", linestyle="--")
plt.plot(time, P_2 / base, label="Baseline 2.5th Percentile", linestyle="--")

plt.plot(time_c, P_mean_c / base, label=(f"Control Mean Power ({units})"), linewidth=2)
plt.plot(time_c, P_97_c / base, label="Control 97th Percentile", linestyle="--")
plt.plot(time_c, P_2_c / base, label="Control 2.5th Percentile", linestyle="--")

# Optional shaded percentile band
plt.fill_between(time, P_2 / base, P_97 / base, alpha=0.2, label="2.5–97.5% Baseline Range")

# Optional shaded percentile band
plt.fill_between(time_c, P_2_c / base, P_97_c / base, alpha=0.2, label="2.5–97.5% Controlled Range")

# Formatting
plt.xlabel("Time")
plt.ylabel(f"Power ({units})")
plt.title(f"Baseline & Controlled Mean Power with 2.5th–97th Percentile Range ({with_commas(N_units)} Units)")
plt.legend()
plt.grid(True)

# Reduce x-axis clutter (show every N labels)
N = 4  # every hour if 15-min increments
plt.xticks(ticks=range(0, len(time), N),
           labels=time.iloc[::N],
           rotation=45)

#plot_segment_energy(df_energy)
# smooth curve across full day
# Plot
"""x_fit = np.linspace(0, 23.75, 500)
plt.figure(figsize=(12, 6))
plt.plot(x, y, label="Data", linewidth=2)
plt.plot(x_fit, f(x_fit), label=f"Fourier fit (N={N})", linewidth=2)

tick_idx = np.arange(0, len(time), 4)  # every hour
plt.xticks(x[tick_idx], time.iloc[tick_idx], rotation=45)

plt.xlabel("Time")
plt.ylabel("Power (kW)")
plt.grid(True)
plt.legend()"""
plt.tight_layout()


plt.show()
