


from sklearn.metrics import r2_score
import matplotlib.pyplot as plt
from docx.shared import Inches
from datetime import datetime
from docx import Document
from pathlib import Path
import pandas as pd
import numpy as np
import time
import os
import csv

def with_commas(x):
    return f"{x:,}"

def power_units_scale(P_max):
    print(P_max)
    if abs(P_max) >= 1_000_000:
        units = "GW"
        base = 1_000_000
    elif abs(P_max) >= 1_000:
        units = "MW"
        base = 1_000
    else:
        units = "kW"
        base = 1
    print(P_max, units, base)
    return units, base


def kwh_from_power_csv(
    csv_path: str,
    dt_minutes: float = 15.0,
):
    """
    Reads a CSV with columns:
      [time, P_mean_kW, P_95, P_5]  (time in 15-min increments, powers in kW)
    Returns a dict of energies in kWh for each power column.
    """
    df = pd.read_csv(csv_path)

    # Grab columns by position (matches your description)
    p_mean = pd.to_numeric(df.iloc[:, 1], errors="coerce")
    p_95   = pd.to_numeric(df.iloc[:, 2], errors="coerce")
    p_5    = pd.to_numeric(df.iloc[:, 3], errors="coerce")

    dt_hr = dt_minutes / 60.0

    energies = {
        "rows": len(df),
        "dt_hr": dt_hr,
        "E_mean_kWh": p_mean.sum() * dt_hr,
        "E_95_kWh":   p_95.sum() * dt_hr,
        "E_5_kWh":    p_5.sum() * dt_hr,
    }

    return energies

def plot_segment_energy(df):
    plt.figure(figsize=(14,6))

    plt.bar(df.iloc[:, 0], df["E_mean_kWh"])

    # Reduce x clutter (show every hour)
    idx = range(0, len(df), 4)
    plt.xticks(
        [df.iloc[i, 0] for i in idx],
        rotation=45
    )

    plt.xlabel("Time")
    plt.ylabel("Energy per 15-min (kWh)")
    plt.title("Energy Consumption per 15-Minute Interval")
    plt.grid(axis="y")

    plt.tight_layout()


def compute_segment_energy(csv_path, output_csv="segment_energy_baseline.csv"):
    df = pd.read_csv(csv_path)

    dt_hr = 0.25  # 15 minutes

    # Compute kWh per segment
    df["E_mean_kWh"] = pd.to_numeric(df.iloc[:, 1], errors="coerce") * dt_hr
    df["E_95_kWh"]   = pd.to_numeric(df.iloc[:, 2], errors="coerce") * dt_hr
    df["E_5_kWh"]    = pd.to_numeric(df.iloc[:, 3], errors="coerce") * dt_hr

    # Save CSV
    df.to_csv(output_csv, index=False)

    return df

# -----------------------------------------------------------------------------
# EXTRACT BASELINE DATA AND SCALE TO N_units
# -----------------------------------------------------------------------------
def get_csv_data(input_file, N_units):
    time = input_file.iloc[:, 0]          # time strings
    P_mean = input_file.iloc[:, 1] * N_units
    P_97 = input_file.iloc[:, 2] * N_units
    P_2 = input_file.iloc[:, 3] * N_units
    return time, P_mean, P_97, P_2

def get_plot_mean_with_band(
    time,
    p_mean,
    p_upper,
    p_lower,
    title,
    units_base_func,
    daily_avg=None,
    ylabel_units_label="Power",
    n_units_for_title=None,
    with_commas_func=None,
    tick_every=4,          # every hour for 15-min data
    figsize=(12, 6),
    mean_label=None,
    upper_label="97th Percentile",
    lower_label="2.5th Percentile",
    band_label="2.5–97.5% Range",
):
    """
    Plot a mean curve with upper/lower percentile curves and a shaded band.

    Parameters
    ----------
    time : pd.Series | list-like
        Time labels (e.g., '00:00', '00:15', ...) length 96.
    p_mean, p_upper, p_lower : array-like
        Series/arrays of power values (kW, MW, etc. before scaling).
    title : str
        Plot title (full string). If you want "(N units)" appended, pass
        n_units_for_title + with_commas_func.
    units_base_func : callable
        Function like power_units_scale(P_max) -> (units, base).
        Used to scale plotted values.
    daily_avg : float | None
        If provided, draws a horizontal reference line at daily_avg.
    ylabel_units_label : str
        Prefix label for y-axis (default "Power").
    n_units_for_title : int | None
        Fleet size to append to title if with_commas_func provided.
    with_commas_func : callable | None
        Function like with_commas(N) -> "100,000".
    tick_every : int
        Show every Nth x tick label (default 4 = hourly for 15-min data).
    """

    # Convert inputs to numeric arrays/Series safely
    p_mean  = pd.to_numeric(pd.Series(p_mean), errors="coerce")
    p_upper = pd.to_numeric(pd.Series(p_upper), errors="coerce")
    p_lower = pd.to_numeric(pd.Series(p_lower), errors="coerce")

    # Determine scaling based on the largest magnitude among all series
    extrema = [
        np.nanmin(p_mean), np.nanmax(p_mean),
        np.nanmin(p_upper), np.nanmax(p_upper),
        np.nanmin(p_lower), np.nanmax(p_lower),
    ]
    # choose value with biggest absolute magnitude
    scale_ref = max(extrema, key=lambda v: abs(v) if np.isfinite(v) else -1)

    units, base = units_base_func(scale_ref)

    # Build final title if requested
    full_title = title
    if (n_units_for_title is not None) and (with_commas_func is not None):
        full_title = f"{title} ({with_commas_func(n_units_for_title)} Units)"

    plt.figure(figsize=figsize)

    # Daily average reference line (optional)
    if daily_avg is not None:
        plt.axhline(
            y=daily_avg / base,
            linestyle=":",
            linewidth=2,
            label=f"Daily Avg = {daily_avg/base:.2f} {units}"
        )

    # Main curves
    if mean_label is None:
        mean_label = f"Mean ({units})"

    plt.plot(time, p_mean / base, label=mean_label, linewidth=2)
    plt.plot(time, p_upper / base, label=upper_label, linestyle="--")
    plt.plot(time, p_lower / base, label=lower_label, linestyle="--")

    # Shaded band
    plt.fill_between(time, p_lower / base, p_upper / base, alpha=0.2, label=band_label)

    # Formatting
    plt.xlabel("Time")
    plt.ylabel(f"{ylabel_units_label} ({units})")
    plt.title(full_title)
    plt.legend()
    plt.grid(True)

    # Reduce x-axis clutter (works best when time is a pandas Series)
    if tick_every is not None and len(time) > 0:
        idx = list(range(0, len(time), tick_every))
        # if time is a pandas Series, time.iloc works; otherwise fall back to indexing
        labels = time.iloc[idx] if hasattr(time, "iloc") else [time[i] for i in idx]
        plt.xticks(ticks=idx, labels=labels, rotation=45)

    plt.tight_layout()
    return units, base  # handy if you want to reuse them

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


def build_energy_interval_table(time, E_mean, E_97, E_2, output_name):

    df = pd.DataFrame({
        "time": time,
        "E_mean": E_mean,
        "E_97": E_97,
        "E_2": E_2
    })

    # determine sign of E_mean
    sign = np.sign(df["E_mean"])

    # treat zeros as same sign as previous
    sign = sign.replace(0, np.nan).ffill().fillna(0)

    # detect where sign changes
    change = sign != sign.shift()

    # assign group numbers
    group_id = change.cumsum()

    results = []

    for _, group in df.groupby(group_id):

        start_time = group["time"].iloc[0]
        end_time   = group["time"].iloc[-1]

        total_E_mean = group["E_mean"].sum()
        total_E_97   = group["E_97"].sum()
        total_E_2    = group["E_2"].sum()

        duration_hours = len(group) * 0.25

        results.append({
            "start_time": start_time,
            "end_time": end_time,
            "duration_hours": duration_hours,
            "E_mean_total_kWh": total_E_mean,
            "E_97_total_kWh": total_E_97,
            "E_2_total_kWh": total_E_2
        })

    result_df = pd.DataFrame(results)

    # write CSV
    result_df.to_csv(output_name + ".csv", index=False)

    print("Saved:", output_name + ".csv")

    return result_df