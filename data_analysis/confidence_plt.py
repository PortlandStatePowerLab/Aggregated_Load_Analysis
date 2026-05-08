import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import os

# ---------------------------
# PATHS
# ---------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
OCHRE_WORKING_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "ochre_working")

input_csv = os.path.join(
    OCHRE_WORKING_DIR,
    "N_10000",
    "P_mean_PU_control_minus_baseline_10000.csv"
)

output_folder = os.path.join(OCHRE_WORKING_DIR, "N_10000", "images")
os.makedirs(output_folder, exist_ok=True)

output_name = os.path.join(output_folder, "FINAL_with_all_areas.png")

# ---------------------------
# LOAD DATA
# ---------------------------
df = pd.read_csv(input_csv)
df["time"] = df["time"].astype(str)

y_mean  = df["P_mean"].values
y_best  = df["best_case"].values
y_worst = df["worst_case"].values
x = np.arange(len(df))

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
# MAIN PLOT
# ---------------------------
ax.fill_between(x, y_mean, 0, where=(y_mean >= 0), alpha=0.3)
ax.fill_between(x, y_mean, 0, where=(y_mean < 0), alpha=0.3)

ax.plot(x, y_mean,  color="black", linewidth=2, label="Mean")
ax.plot(x, y_best,  linestyle="--", color="orange", label="Best Case")
ax.plot(x, y_worst, linestyle="--", color="blue", label="Worst Case")

ax.set_title("Per Unit Control Minus Baseline (10,000 Units)")
ax.set_ylabel("Power [p.u.]")
ax.grid(True)

# ---------------------------
# TIME LABELS (ON MAIN AXIS)
# ---------------------------
tick_positions = range(0, len(df), 4)

ax.set_xticks(tick_positions)
ax.set_xticklabels(
    [f"{i//4:02d}:00" for i in tick_positions],
    rotation=45
)

# hide duplicate labels on bottom axis
ax.tick_params(labelbottom=True)

# ---------------------------
# EVENT BAR (BELOW TIME)
# ---------------------------
ax2.set_ylim(0, 1)
ax2.set_yticks([])
ax2.set_frame_on(False)

schedule = [
    ("LOADUP",   "03:00", 3, "green"),
    ("SHED", "06:00", 4, "yellow"),
    ("LOADUP",   "16:00", 1, "green"),
    ("SHED", "17:00", 3, "yellow"),
]

def time_to_index(t):
    h, m = map(int, t.split(":"))
    return int((h * 60 + m) / 15)

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
# LEGEND
# ---------------------------
legend_elements = [
    Line2D([0], [0], color='black', lw=2, label='Mean'),
    Line2D([0], [0], linestyle='--', color='orange', label='Best Case'),
    Line2D([0], [0], linestyle='--', color='blue', label='Worst Case'),
]

ax.legend(handles=legend_elements, loc='lower right')

# ---------------------------
# SAVE
# ---------------------------
ax2.xaxis.set_visible(False)
plt.tight_layout()
plt.savefig(output_name, dpi=300, bbox_inches="tight")
plt.close()

print(f"Saved to: {output_name}")