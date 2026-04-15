import os
import pandas as pd
from ochre.utils import default_input_path

# --- DYNAMIC PATH SETUP ---
# 1. Get the folder where THIS script is (e.g., .../ochre_working/simulating)
CURRENT_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Go UP one level to get to 'ochre_working'
OCHRE_WORKING_DIR = os.path.join(os.path.dirname(CURRENT_SCRIPT_DIR), "ochre_working")

# 3. Go INTO 'Ready_data'
READY_DATA_DIR = os.path.join(OCHRE_WORKING_DIR, "Ready_data")
os.makedirs(READY_DATA_DIR, exist_ok=True)

# --- DATA SOURCE (The OCHRE Library) ---
INPUT_DIR = os.path.join(default_input_path, "Input Files") 

def aggregate_ochre_results():
    if not os.path.exists(INPUT_DIR):
        print(f"❌ Error: OCHRE input directory not found at {INPUT_DIR}")
        return

    homes = [os.path.join(INPUT_DIR, d) for d in os.listdir(INPUT_DIR) 
             if os.path.isdir(os.path.join(INPUT_DIR, d))]
    
    print(f"Aggregator Location: {CURRENT_SCRIPT_DIR}")
    print(f"Target Save Location: {READY_DATA_DIR}")
    print(f"Processing {len(homes)} buildings...")

    run_types = {
        'baseline': 'hpwh_baseline.parquet',
        'controlled': 'hpwh_controlled.parquet'
    }

    for label, filename in run_types.items():
        print(f"\nMerging {label.upper()} data...")
        final_data = []

        for home_path in homes:
            res_path = os.path.join(home_path, "Results", filename)
            
            if os.path.exists(res_path):
                try:
                    df = pd.read_parquet(res_path)
                    if 'Time' in df.columns:
                        df['Time'] = pd.to_datetime(df['Time'])
                    
                    # 15-minute power sum
                    series = df.resample('15min', on='Time')['Water Heating Electric Power (kW)'].sum()
                    
                    row = series.to_frame().T
                    row.index = [os.path.basename(home_path)]
                    final_data.append(row)
                except Exception as e:
                    print(f"  ⚠️ Error in {os.path.basename(home_path)}: {e}")

        if final_data:
            output_csv = os.path.join(READY_DATA_DIR, f"final_aggregated_{label}_15min.csv")
            pd.concat(final_data).to_csv(output_csv, index_label='building_id')
            print(f"✅ Success! Created: {output_csv}")
        else:
            print(f"❌ No {label} files found. Make sure the simulation finished!")

if __name__ == "__main__":
    aggregate_ochre_results()