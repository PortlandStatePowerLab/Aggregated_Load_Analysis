import pandas as pd
import matplotlib.pyplot as plt
import os

# ---------------------------
# USER SETTINGS
# ---------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
OCHRE_WORKING_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "ochre_working")

base_dir = os.path.join(OCHRE_WORKING_DIR, "N_10000")

baseline_csv = os.path.join(base_dir, "summed_power_by_time_baseline.csv")
controlled_csv = os.path.join(base_dir, "summed_power_by_time_controlled.csv")

output_folder = os.path.join(base_dir, "images")
os.makedirs(output_folder, exist_ok=True)

output_name = os.path.join(output_folder, "AL_baseline_control_CI.png")

# ---------------------------
# LOAD DATA
# ---------------------------
df_base = pd.read_csv(baseline_csv)
df_ctrl = pd.read_csv(controlled_csv)

df_base["time"] = df_base["time"].astype(str)
df_ctrl["time"] = df_ctrl["time"].astype(str)

# ---------------------------
# ALIGN DATA
# ---------------------------
df = pd.DataFrame()
df["time"] = df_base["time"]

df["baseline_mean"] = df_base["total_power_kW"]
df["baseline_5th"] = df_base["5th_percentile"]
df["baseline_95th"] = df_base["95th_percentile"]

df["ctrl_mean"] = df_ctrl["total_power_kW"]
df["ctrl_5th"] = df_ctrl["5th_percentile"]
df["ctrl_95th"] = df_ctrl["95th_percentile"]

# ---------------------------
# SCHEDULE
# ---------------------------
my_schedule = {
    'M_LU_time': '03:00',
    'M_LU_duration': 3,
    'M_S_time': '06:00',
    'M_S_duration': 4,
    'E_ALU_time': '16:00',
    'E_ALU_duration': 1,
    'E_S_time': '17:00',
    'E_S_duration': 3
}

def time_to_index(time_str):
    h, m = map(int, time_str.split(":"))
    return int((h * 60 + m) / 15)

# ---------------------------
# FIGURE (2 PANELS)
# ---------------------------
fig, (ax, ax2) = plt.subplots(
    2, 1,
    figsize=(12, 6),
    gridspec_kw={'height_ratios': [5, 1]},
    sharex=True
)

plt.subplots_adjust(hspace=0.05)

# ---------------------------
# CI BANDS (ON MAIN AXIS)
# ---------------------------
ax.fill_between(
    range(len(df)),
    df["baseline_5th"],
    df["baseline_95th"],
    alpha=0.2,
    label="Baseline CI", 
    color='blue'
)

ax.fill_between(
    range(len(df)),
    df["ctrl_5th"],
    df["ctrl_95th"],
    alpha=0.2,
    label="Controlled CI", 
    color='magenta'
)

# ---------------------------
# MEAN LINES (ON MAIN AXIS)
# ---------------------------
ax.plot(df["baseline_mean"], label="Baseline Mean", linewidth=2, color='blue')
ax.plot(df["ctrl_mean"], label="Controlled Mean", linewidth=2, color='magenta')

# ---------------------------
# LABELS & GRID
# ---------------------------
ax.set_ylabel("Power [kW]")
ax.set_title("Aggregated Baseline vs Controlled Confidence Intervals (10,000 Units) ")
ax.grid(True)
ax.legend()

# ---------------------------
# X AXIS / TIME LABELS
# ---------------------------
tick_positions = range(0, len(df), 4)
ax.set_xticks(tick_positions)
ax.set_xticklabels(
    [f"{i//4:02d}:00" for i in tick_positions],
    rotation=45
)
ax.tick_params(labelbottom=True)

# ---------------------------
# EVENT BAR (BELOW TIME)
# ---------------------------
ax2.set_ylim(0, 1)
ax2.set_yticks([])
ax2.set_frame_on(False)

schedule = [
    ("LOADUP", my_schedule['M_LU_time'], my_schedule['M_LU_duration'], "green"),
    ("SHED",    my_schedule['M_S_time'],  my_schedule['M_S_duration'],  "yellow"),
    ("LOADUP", my_schedule['E_ALU_time'], my_schedule['E_ALU_duration'], "green"),
    ("SHED",    my_schedule['E_S_time'],  my_schedule['E_S_duration'],  "yellow"),
]

for name, t, dur, color in schedule:
    start = time_to_index(t)
    end = start + dur * 4

    ax2.fill_between([start, end], 0, 1, color=color, alpha=0.6)

    ax2.text(
        (start + end) / 2,
        0.5,
        name,
        ha="center",
        va="center",
        fontsize=8
    )

# ---------------------------
# SAVE
# ---------------------------
ax2.xaxis.set_visible(False)
plt.tight_layout()
plt.savefig(output_name, dpi=300, bbox_inches="tight")
plt.close()

print(f"Saved plot to: {output_name}")