import pandas as pd
import numpy as np
import os

# ---------------------------
# LOAD DATA
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

df = pd.read_csv(input_csv)
y = df["P_mean"].values

dt_hours = 0.25  # 15-min interval

# ---------------------------
# ENERGY FUNCTION (TRAPZ ONLY)
# ---------------------------
def compute_energy(y_seg):
    pos = np.trapz(np.maximum(y_seg, 0), dx=dt_hours)
    neg = np.trapz(np.minimum(y_seg, 0), dx=dt_hours)
    net = pos + neg
    avg = np.mean(y_seg)
    return pos, neg, net, avg

# ---------------------------
# TIME → INDEX
# ---------------------------
def time_to_index(t):
    h, m = map(int, t.split(":"))
    return int((h * 60 + m) / 15)

# ---------------------------
# WINDOWS
# ---------------------------
schedule = [
    ("Morning LU", '03:00', 3),
    ("Morning Shed", '06:00', 4),
    ("Evening LU", '16:00', 1),
    ("Evening Shed", '17:00', 3),
]

rows = []

for name, t, dur in schedule:
    start = time_to_index(t)
    end = start + dur * 4

    y_seg = y[start:end]
    pos, neg, net, avg = compute_energy(y_seg)

    rows.append({
        "Event": name,
        "Duration (hr)": dur,
        "Positive Energy": pos,
        "Negative Energy": neg,
        "Net Energy": net,
        "Avg Power (p.u.)": avg
    })

# ---------------------------
# TOTAL (TRAPZ)
# ---------------------------
total_pos = np.trapz(np.maximum(y, 0), dx=dt_hours)
total_neg = np.trapz(np.minimum(y, 0), dx=dt_hours)
total_net = total_pos + total_neg

rows.append({
    "Event": "TOTAL",
    "Duration (hr)": len(y) * dt_hours,
    "Positive Energy": total_pos,
    "Negative Energy": total_neg,
    "Net Energy": total_net,
    "Avg Power (p.u.)": np.mean(y)
})

# ---------------------------
# SAVE
# ---------------------------
energy_df = pd.DataFrame(rows)

output_csv = os.path.join(output_folder, "PU_energy_summary.csv")
energy_df.to_csv(output_csv, index=False)

print("\nEnergy Summary Table:\n")
print(energy_df)
print(f"\nSaved to: {output_csv}")