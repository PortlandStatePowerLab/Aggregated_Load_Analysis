import pandas as pd
import matplotlib.pyplot as plt
import os

# ---------------------------
# USER SETTINGS
# ---------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
OCHRE_WORKING_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "ochre_working")

base_dir = os.path.join(OCHRE_WORKING_DIR, "N_10000")

baseline_csv = os.path.join(base_dir, "P_Mean_baseline_AL_10000.csv")
controlled_csv = os.path.join(base_dir, "P_Mean_controlled_AL_10000.csv")

output_folder = os.path.join(base_dir, "images")
os.makedirs(output_folder, exist_ok=True)

output_name = os.path.join(output_folder, "AL_baseline_control_CI_schedule.png")

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

df["baseline_mean"] = df_base["P_mean_kW"]
df["baseline_5th"] = df_base["5th"]
df["baseline_95th"] = df_base["95th"]

df["ctrl_mean"] = df_ctrl["P_mean_kW"]
df["ctrl_5th"] = df_ctrl["5th"]
df["ctrl_95th"] = df_ctrl["95th"]

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
# PLOT
# ---------------------------
plt.figure(figsize=(12, 6))
ax = plt.gca()

# ---------------------------
# CI BANDS
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
# MEAN LINES
# ---------------------------
ax.plot(df["baseline_mean"], label="Baseline Mean", linewidth=2, color='blue')
ax.plot(df["ctrl_mean"], label="Controlled Mean", linewidth=2, color='magenta')

# ---------------------------
# SCHEDULE SHADING
# ---------------------------

# LOAD UP (GREEN)
lu_start = time_to_index(my_schedule['M_LU_time'])
lu_end = lu_start + my_schedule['M_LU_duration'] * 4
ax.axvspan(lu_start, lu_end, color='green', alpha=0.15, label="Load Up")

elu_start = time_to_index(my_schedule['E_ALU_time'])
elu_end = elu_start + my_schedule['E_ALU_duration'] * 4
ax.axvspan(elu_start, elu_end, color='green', alpha=0.15)

# SHED (YELLOW)
s1_start = time_to_index(my_schedule['M_S_time'])
s1_end = s1_start + my_schedule['M_S_duration'] * 4
ax.axvspan(s1_start, s1_end, color='yellow', alpha=0.2, label="Shed")

s2_start = time_to_index(my_schedule['E_S_time'])
s2_end = s2_start + my_schedule['E_S_duration'] * 4
ax.axvspan(s2_start, s2_end, color='yellow', alpha=0.2)

# ---------------------------
# LABELS
# ---------------------------
plt.xlabel("Time")
plt.ylabel("Power [kW]")
plt.title("Aggregated Baseline vs Controlled CI (10,000 Units) ")
plt.grid(True)
plt.legend()

# ---------------------------
# X AXIS
# ---------------------------
tick_positions = range(0, len(df), 4)
plt.xticks(
    ticks=tick_positions,
    labels=[f"{i//4:02d}:00" for i in tick_positions],
    rotation=45
)

plt.tight_layout()
plt.savefig(output_name, dpi=300)
plt.close()

print(f"Saved plot to: {output_name}")