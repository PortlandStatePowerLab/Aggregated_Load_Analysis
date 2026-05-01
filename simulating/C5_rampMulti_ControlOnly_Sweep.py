# -*- coding: utf-8 -*-
"""
Created on Mon Nov 10 12:06:45 2025

@author: danap
@edited by: jdeline
"""

# work on makign it so i dsimulated builidngs in csv anf chnage the path that was changed in ochre inpout file 
import os
import shutil
import datetime as dt
import pandas as pd
from ochre import Dwelling
from ochre.utils.schedule import ALL_SCHEDULE_NAMES
from ochre.utils import default_input_path
import concurrent.futures
import random
import time
import datetime
import numpy as np
import re


print(datetime.datetime.fromtimestamp(time.time(), datetime.timezone.utc).astimezone().strftime('%Y-%m-%d %H:%M:%S %Z'))


start_time = time.time()


#########################################
# USER SETTINGS
#########################################


level = 8

baseLVL = level    # normal operation
shedLVL = level    # tighter HP window during shed (more ER fallback)
loadLVL = level    # more aggressive HP window during load-up (optional)

input_file = "OR_upgrade06_2022.1.csv" # this is the file that contains the list of buildings to simulate. It should be in the up06 folder.
bldg_folder = "bldg_files"

upgrade = 6  
relase = "resstock_tmy3_release_1"
year = "2022"

DEFAULT_DIR = os.path.join(default_input_path, "Input Files")
INPUT_DIR = os.path.join(DEFAULT_DIR, bldg_folder)
WEATHER_DIR = os.path.join(os.path.dirname(DEFAULT_DIR), "Weather")
WEATHER_FILE = os.path.join(WEATHER_DIR, "USA_OR_Portland.Intl.AP.726980_TMY3.epw")

# 2. Define the Results folder next to the Input folder
# This points to .../ochre/defaults/Results
RESULTS_DIR = os.path.join(os.path.dirname(DEFAULT_DIR), "Results")


# Simulation parameters
Start = dt.datetime(2018, 1, 13, 0, 0)
Duration = 2  # days
t_res = 15  # minutes
jitter_min = 5

# HPWH control parameters (°F) 
Tcontrol_SHEDF = 126 #F Shed setpoint
Tcontrol_LOADF = 130 #F Load up setpoint
Tcontrol_LOADdeadbandF = 2 #F Load up deadband
TbaselineF = 130 #F Baseline setpoint
TdeadbandF = 7 #F baseline deadband
shed_deadbandF = 10 #shed deadband
Tinit = 128 #F

# Base schedule template
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

LVL = {1:0, 2:0.14, 3:0.29,
        4:0.43, 5:0.57, 6:0.71,
        7:0.857, 8:1, 9:10} # 7:1, 8:1.14, 9:10

EFF_BASELINE = LVL[baseLVL] 
EFF_SHED = LVL[shedLVL]
EFF_LOAD = LVL[loadLVL]



# Randomization bins
M_LU_weights = [14, 28, 34, 41, 46, 46, 41, 33, 30, 31, 35, 30]
M_LU_bins = pd.date_range("03:00", periods=len(M_LU_weights), freq="15min").strftime("%H:%M").tolist()


E_ALU_weights = [17, 21, 27, 37, 40, 46, 40, 42, 36, 32, 33, 38]
E_ALU_bins = pd.date_range("14:00", periods=len(E_ALU_weights), freq="15min").strftime("%H:%M").tolist()


#########################################
# TEMPERATURE CONVERSIONS F to C
#########################################
 
def f_to_c(temp_f): 
    return (temp_f - 32) * 5/9

def f_to_c_DB(temp_f):
    return 5/9 * temp_f

Tcontrol_SHEDC = f_to_c(Tcontrol_SHEDF)
# Tcontrol_deadbandC = Tcontrol_dbF * 5/9
Tcontrol_LOADC = f_to_c(Tcontrol_LOADF)
Tcontrol_LOADdeadbandC = f_to_c_DB(Tcontrol_LOADdeadbandF)
TbaselineC = f_to_c(TbaselineF)
TdeadbandC = f_to_c_DB(TdeadbandF)
TinitC = f_to_c(Tinit)

#########################################
# HPWH CONTROL FUNCTION
#########################################

def determine_hpwh_control(sim_time, current_temp_c, sched_cfg, shed_deadbandC, **kwargs):
    ctrl_signal = {
        'Water Heating': {
            'Setpoint': TbaselineC,
            'Deadband': TdeadbandC,
            'Load Fraction': 1,
            'Efficiency Coefficient': EFF_BASELINE,
        }
    }

    base_date = sim_time.date()
    def get_time_range(key_prefix):
        start = pd.to_datetime(f"{base_date} {sched_cfg[f'{key_prefix}_time']}")
        end = start + pd.Timedelta(hours=sched_cfg[f'{key_prefix}_duration'])
        return start, end

    ranges = {
        'M_LU': get_time_range('M_LU'),
        'M_S': get_time_range('M_S'),
        'E_ALU': get_time_range('E_ALU'),
        'E_S': get_time_range('E_S'),
    }

    if ranges['M_LU'][0] <= sim_time < ranges['M_LU'][1] or ranges['E_ALU'][0] <= sim_time < ranges['E_ALU'][1]:
        ctrl_signal['Water Heating'].update({
            'Setpoint': Tcontrol_LOADC,
            'Deadband': Tcontrol_LOADdeadbandC,
            'Efficiency Coefficient': EFF_LOAD
        })
    elif ranges['M_S'][0] <= sim_time < ranges['M_S'][1] or ranges['E_S'][0] <= sim_time < ranges['E_S'][1]:
        ctrl_signal['Water Heating'].update({
            'Setpoint': Tcontrol_SHEDC,
           'Deadband': shed_deadbandC,
           'Efficiency Coefficient': EFF_SHED
        })

    return ctrl_signal

#########################################
# SCHEDULE FILTERING
#########################################

def filter_schedules(home_path):
    orig_sched_file = os.path.join(home_path, 'schedules.csv')
    filtered_sched_file = os.path.join(home_path, 'filtered_schedules.csv')

    df_sched = pd.read_csv(orig_sched_file)
    valid_schedule_names = set(ALL_SCHEDULE_NAMES.keys())

    # Keep all HPWH custom columns too
    hpwh_cols = ['M_LU_time','M_LU_duration','M_S_time','M_S_duration',
                 'E_ALU_time','E_ALU_duration','E_S_time','E_S_duration']
    filtered_columns = [col for col in df_sched.columns if col in valid_schedule_names or col in hpwh_cols]

    dropped_columns = [col for col in df_sched.columns if col not in filtered_columns]
    if dropped_columns:
        print(f"Dropped invalid schedules for {home_path}: {dropped_columns}")

    df_sched_filtered = df_sched[filtered_columns]
    df_sched_filtered.to_csv(filtered_sched_file, index=False)
    return filtered_sched_file


#########################################
# SIMULATION FUNCTION
#########################################

def simulate_home(home_path, weather_file_path, schedule_cfg, shed_deadbandF):
    shed_deadbandC = f_to_c_DB(shed_deadbandF)

    filtered_sched_file = filter_schedules(home_path)
    hpxml_file = os.path.join(home_path, 'in.XML')
    results_dir = os.path.join(home_path, "Results")
    os.makedirs(results_dir, exist_ok=True)

    # Standard configuration for both runs
    dwelling_args_local = {
        "start_time": Start,
        "time_res": dt.timedelta(minutes=t_res),
        "duration": dt.timedelta(days=Duration), # Ensure Duration is 3 for a 48hr post-warmup run
        "hpxml_file": hpxml_file,
        "hpxml_schedule_file": filtered_sched_file,
        "weather_file": weather_file_path,
        "verbosity": 7,
        "Equipment": {
            "Water Heating": {
                "Initial Temperature (C)": TinitC, 
                "hp_only_mode": False, 
                "Max Tank Temperature": 70,
                "Upper Node": 3,
                "Lower Node": 10,
                "Upper Node Weight": 0.75,   
            },
        }
    }

    # Define the columns we want to keep
    COLS_TO_KEEP = ["Time", "Total Electric Power (kW)",
                    "Total Electric Energy (kWh)",
                    "Water Heating Electric Power (kW)",
                    "Water Heating COP (-)",
                    "Water Heating Deadband Upper Limit (C)",
                    "Water Heating Deadband Lower Limit (C)",
                    "Water Heating Control Temperature (C)",
                    "Hot Water Outlet Temperature (C)"]

    # --- 1. RUN BASELINE ---
    # This simulates the house as if no special control logic was applied
    base_dwelling = Dwelling(name="HPWH Baseline", **dwelling_args_local)
    for t_base in base_dwelling.sim_times:
        base_ctrl = {"Water Heating": {"Setpoint": TbaselineC, "Deadband": TdeadbandC, "Load Fraction": 1}}
        base_dwelling.update(control_signal=base_ctrl)
    
    df_base, _, _ = base_dwelling.finalize()
    df_base = remove_first_day(df_base, Start)
    df_base = df_base[[c for c in COLS_TO_KEEP if c in df_base.columns]]
    
    df_base.to_parquet(os.path.join(results_dir, 'hpwh_baseline.parquet'), index=False)

    # --- 2. RUN CONTROLLED ---
    # This simulates the house using your custom determine_hpwh_control logic
    sim_dwelling = Dwelling(name="HPWH Controlled", **dwelling_args_local)
    hpwh_unit = sim_dwelling.get_equipment_by_end_use('Water Heating')
    
    for sim_time in sim_dwelling.sim_times:
        # Day 1: Warm-up period (Standard Baseline Control)
        if sim_time < Start + pd.Timedelta(days=1):
            control_cmd = {
                'Water Heating': {
                    'Setpoint': TbaselineC,
                    'Deadband': TdeadbandC,
                    'Load Fraction': 1,
                }
            }
        # Day 2 & 3: Apply your custom control logic
        else:
            current_setpt = hpwh_unit.schedule.loc[sim_time, 'Water Heating Setpoint (C)']
            control_cmd = determine_hpwh_control(
                sim_time=sim_time, 
                current_temp_c=current_setpt, 
                sched_cfg=schedule_cfg, 
                shed_deadbandC=shed_deadbandC
            )
        
        sim_dwelling.update(control_signal=control_cmd)

    df_ctrl, _, _ = sim_dwelling.finalize()
    df_ctrl = remove_first_day(df_ctrl, Start)
    df_ctrl = df_ctrl[[c for c in COLS_TO_KEEP if c in df_ctrl.columns]]
    
    df_ctrl.to_parquet(os.path.join(results_dir, 'hpwh_controlled.parquet'), index=False)

    return df_ctrl

#########################################
# FIND ALL HOMES
#########################################

def find_all_homes(base_dir):
    homes = []
    for item in os.listdir(base_dir):
        home_path = os.path.join(base_dir, item)
        if os.path.isdir(home_path):
            if os.path.isfile(os.path.join(home_path, 'in.XML')) and \
               os.path.isfile(os.path.join(home_path, 'schedules.csv')):
                homes.append(home_path)
    return homes

#########################################
# DELETE FIRST DAY ONLY
#########################################

def remove_first_day(df, start_date):
    if 'Time' not in df.columns:
        df = df.reset_index()
        if 'index' in df.columns:
            df.rename(columns={'index': 'Time'}, inplace=True)
    df['Time'] = pd.to_datetime(df['Time'], errors='coerce')
    first_day_end = start_date + pd.Timedelta(days=1)
    return df[df['Time'] >= first_day_end].copy()

#########################################
# CLEAN UP FILES
#########################################

def cleanup_results_dir(results_dir, keep_files=None):
    if keep_files is None:
        keep_files = []

    for item in os.listdir(results_dir):
        path = os.path.join(results_dir, item)
        if os.path.isfile(path) and item not in keep_files:
            try:
                os.remove(path)
            except Exception as e:
                print(f"Could not delete {path}: {e}")
        elif os.path.isdir(path):
            try:
                shutil.rmtree(path)
            except Exception as e:
                print(f"Could not delete folder {path}: {e}")
                
                





#########################################
# MAIN EXECUTION
#########################################

if __name__ == "__main__":
    # Ensure the library's results folder exists
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # Discover homes directly from the library path
    homes = [os.path.join(INPUT_DIR, d) for d in os.listdir(INPUT_DIR) 
             if os.path.isdir(os.path.join(INPUT_DIR, d))]
    print(f"Found {len(homes)} homes in {INPUT_DIR}")

    
    # -----------------------------
    # Assign schedules to homes
    # -----------------------------
    home_schedules = {}
    fmt = "%H:%M"

    # Weighted pools
    M_LU_weighted_pool = [bin_time for bin_time, weight in zip(M_LU_bins, M_LU_weights) for _ in range(weight)]
    random.shuffle(M_LU_weighted_pool)

    MS_bins = pd.date_range("10:00", "13:45", freq="15min")
    MS_weights = [20, 23, 24, 23, 22, 22, 25, 26, 26, 29, 29, 29, 29, 27, 28, 27]
    MS_offsets = [(t - pd.Timestamp("10:00")).total_seconds()/3600 for t in MS_bins]
    MS_weighted_pool = [offset for offset, w in zip(MS_offsets, MS_weights) for _ in range(w)]
    random.shuffle(MS_weighted_pool)

    E_ALU_weighted_pool = [bin_time for bin_time, weight in zip(E_ALU_bins, E_ALU_weights) for _ in range(weight)]
    random.shuffle(E_ALU_weighted_pool)

    ES_bins = pd.date_range("20:00", "23:45", freq="15min")
    ES_weights = [17, 21, 24, 25, 26, 24, 24, 23, 23, 23, 23, 25, 28, 30, 33, 40]
    ES_offsets = [(t - pd.Timestamp("20:00")).total_seconds()/3600 for t in ES_bins]
    ES_weighted_pool = [offset2 for offset2, m in zip(ES_offsets, ES_weights) for _ in range(m)]
    random.shuffle(ES_weighted_pool)

    # Assign schedules
    for home in homes:
        sched = my_schedule.copy()

        # -----------------------------
        # M_LU_time with jitter
        # -----------------------------
        if M_LU_weighted_pool:
            M_LU_base = M_LU_weighted_pool.pop()
        else:
            M_LU_base = random.choice(M_LU_bins)
        t_base = pd.to_datetime(M_LU_base, format=fmt)
        jitter = pd.Timedelta(minutes=random.uniform(-jitter_min, jitter_min))
        t_jittered = t_base + jitter
        sched['M_LU_time'] = t_jittered.strftime(fmt)

        # -----------------------------
        # M_S_time and M_LU_duration with jitter
        # -----------------------------
        t_MS_start = pd.to_datetime(my_schedule['M_S_time'], format=fmt)
        t_MS_start += pd.Timedelta(minutes=random.uniform(-jitter_min, jitter_min))
        sched['M_S_time'] = t_MS_start.strftime(fmt)

        t_MLU_start = pd.to_datetime(sched['M_LU_time'], format=fmt)
        t_MLU_end = t_MS_start
        if t_MLU_end <= t_MLU_start:
            t_MLU_end += pd.Timedelta(days=1)
        sched['M_LU_duration'] = max(1, (t_MLU_end - t_MLU_start).total_seconds() / 3600)

        if MS_weighted_pool:
            n = MS_weighted_pool.pop()
        else:
            n = random.choice(MS_offsets)
        sched['M_S_duration'] = 4 + n

        # -----------------------------
        # Evening Schedule Assignment
        # -----------------------------
        if E_ALU_weighted_pool:
            E_ALU_base = E_ALU_weighted_pool.pop()
        else:
            E_ALU_base = random.choice(E_ALU_bins)
        t_E_ALU_start = pd.to_datetime(E_ALU_base, format=fmt)
        t_E_ALU_start += pd.Timedelta(minutes=random.uniform(-jitter_min, jitter_min))
        sched['E_ALU_time'] = t_E_ALU_start.strftime(fmt)

        t_ES_start = pd.to_datetime(my_schedule['E_S_time'], format=fmt)
        t_ES_start += pd.Timedelta(minutes=random.uniform(-jitter_min, jitter_min))
        sched['E_S_time'] = t_ES_start.strftime(fmt)

        if t_ES_start <= t_E_ALU_start:
            t_ES_start += pd.Timedelta(days=1)
        sched['E_ALU_duration'] = max(1, (t_ES_start - t_E_ALU_start).total_seconds() / 3600)

        if ES_weighted_pool:
            n = ES_weighted_pool.pop()
        else:
            n = random.choice(ES_offsets)
        sched['E_S_duration'] = 3 + n

        # Save schedule
        home_schedules[home] = sched

    # -----------------------------
    # Execution Loop
    # -----------------------------
    shed_dbF = shed_deadbandF
    print(f"\nRunning simulation | DB = {shed_dbF} F")

    all_ctrl = []
    
    def simulate_home_safe(home_path, weather_file, sched_cfg, shed_dbF):
        try:
            # This calls your simulate_home which saves to home_path/Results
            return simulate_home(home_path, weather_file, sched_cfg, shed_dbF)
        except Exception as e:
            print(f"⚠️ Failed: {os.path.basename(home_path)}: {e}")
            return None
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(simulate_home_safe, h, WEATHER_FILE, home_schedules[h], shed_dbF)
            for h in homes
        ]
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res is not None: all_ctrl.append(res)

    # ---------------------------------------------------------
    # 1. AGGREGATE BASELINE (Run this once)
    # ---------------------------------------------------------
    print("\nAggregating Baseline Results...")
    baseline_data = []
    for home_path in homes:
        res_path = os.path.join(home_path, "Results", "hpwh_baseline.parquet")
        if os.path.exists(res_path):
            df = pd.read_parquet(res_path)
            df['Time'] = pd.to_datetime(df['Time'])
            series = df.resample('15min', on='Time')['Water Heating Electric Power (kW)'].sum()
            
            row = series.to_frame().T
            row.index = [os.path.basename(home_path)]
            baseline_data.append(row)

    if baseline_data:
        baseline_csv = os.path.join(RESULTS_DIR, "final_aggregated_baseline_15min.csv")
        pd.concat(baseline_data).to_csv(baseline_csv)
        print(f"✅ Baseline Matrix created at: {baseline_csv}")

    # ---------------------------------------------------------
    # 2. AGGREGATE CONTROLLED (Inside or after the deadband loop)
    # ---------------------------------------------------------
    # If you are only running ONE deadband, this can stay here. 
    # If running multiple, move this inside the 'for shed_dbF in Tcontrol_dbF' loop.
    print("\nAggregating Controlled Results...")
    controlled_data = []
    for home_path in homes:
        res_path = os.path.join(home_path, "Results", "hpwh_controlled.parquet")
        if os.path.exists(res_path):
            df = pd.read_parquet(res_path)
            df['Time'] = pd.to_datetime(df['Time'])
            series = df.resample('15min', on='Time')['Water Heating Electric Power (kW)'].sum()
            
            row = series.to_frame().T
            row.index = [os.path.basename(home_path)]
            controlled_data.append(row)

    if controlled_data:
        controlled_csv = os.path.join(RESULTS_DIR, f"final_aggregated_controlled_DB{int(shed_dbF)}_15min.csv")
        pd.concat(controlled_data).to_csv(controlled_csv)
        print(f"✅ Controlled Matrix created at: {controlled_csv}")






end_time = time.time()
execution_time = end_time - start_time
execution_min = execution_time/60
print(f"Execution time: {execution_min} minutes")
