import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
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

y = df["P_mean"].values
x = np.arange(len(df))

# ---------------------------
# TIME → INDEX
# ---------------------------
def time_to_index(t):
    h, m = map(int, t.split(":"))
    return int((h * 60 + m) / 15)

# ---------------------------
# SCHEDULE
# ---------------------------
schedule = [
    ("Morning LU", '03:00', 3, "green"),
    ("Morning Shed", '06:00', 4, "yellow"),
    ("Evening LU", '16:00', 1, "green"),
    ("Evening Shed", '17:00', 3, "yellow"),
]

# Convert schedule
windows = []
for name, t, dur, color in schedule:
    start = time_to_index(t)
    end = start + dur * 4
    windows.append((name, start, end, color))

# ---------------------------
# AREA FUNCTION
# ---------------------------

def compute_area(start, end):
    x_seg = x[start:end]
    y_seg = y[start:end]

    pos = np.trapz(np.maximum(y_seg, 0), x_seg)
    neg = np.trapz(np.minimum(y_seg, 0), x_seg)

    return pos, neg, pos + neg

# ---------------------------
# FIND POSITIVE REGIONS (BLUE)
# ---------------------------
def find_positive_regions(y):
    regions = []
    in_region = False
    start = 0

    for i in range(len(y)):
        if y[i] > 0 and not in_region:
            start = i
            in_region = True
        elif y[i] <= 0 and in_region:
            regions.append((start, i))
            in_region = False

    if in_region:
        regions.append((start, len(y)))

    return regions

# ---------------------------
# PLOT
# ---------------------------
plt.figure(figsize=(12, 6))
ax = plt.gca()

# --- SHADE ABOVE / BELOW ZERO ---
ax.fill_between(x, y, 0, where=(y >= 0), alpha=0.3)
ax.fill_between(x, y, 0, where=(y < 0), alpha=0.3)

# --- MAIN LINE ---
ax.plot(x, y, color="black", linewidth=2)

# ---------------------------
# SCHEDULE WINDOWS + LABELS INSIDE
# ---------------------------
for label, start, end, color in windows:
    ax.axvspan(start, end, color=color, alpha=0.15)
    threshold = 0.05
    pos, neg, net = compute_area(start, end)
    if abs(net) < threshold:
        continue
    mid = (start + end) // 2

    # place INSIDE region
    y_mid = np.mean(y[start:end]) + 0.05

    ax.text(
        mid,
        y_mid,
        f"{label}\nNet {net:.2f}",
        ha="center",
        fontsize=9,
        bbox=dict(facecolor="white", alpha=0.7, edgecolor="none")
    )

# ---------------------------
# BLUE REGION (POSITIVE) LABELS
# ---------------------------
positive_regions = find_positive_regions(y)

for start, end in positive_regions:
    pos, _, _ = compute_area(start, end)

    pos_rounded = round(pos, 2)

# Skip if it will DISPLAY as 0.00
    if pos_rounded == 0:
        continue

    mid = (start + end) // 2
    y_mid = np.mean(y[start:end]) -0.03

    ax.text(
        mid,
        y_mid,
        f"+{pos:.2f}",
        ha="center",
        fontsize=9,
        color="blue",
        bbox=dict(facecolor="white", alpha=0.6, edgecolor="none")
    )

# ---------------------------
# AXES
# ---------------------------
plt.xlabel("Time")
plt.ylabel("Power [p.u.]")
plt.title(" Per Unit Control Minus Baseline (10,000 Units)")
plt.grid(True)

# X ticks every hour
tick_positions = range(0, len(df), 4)
plt.xticks(
    ticks=tick_positions,
    labels=[f"{i//4:02d}:00" for i in tick_positions],
    rotation=45
)

legend_elements = [
    Line2D([0], [0], color='black', lw=2, label='Control - Baseline'),

    Patch(facecolor='green', alpha=0.15, label='Load Up Event'),
    Patch(facecolor='yellow', alpha=0.15, label='Shed Event'),
]
plt.legend(handles=legend_elements, loc='lower right')
plt.tight_layout()
plt.savefig(output_name, dpi=300)
plt.close()

print(f"Saved to: {output_name}")