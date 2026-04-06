# -*- coding: utf-8 -*-
"""
Created on Wed Sep 24 14:46:47 2025

@author: Joe_admin
@modified by: Jeff Dinsmore
@modified date: 12/14/2025
"""


import pandas as pd
from datetime import datetime
import csv
import os

# Converts the datetime information in the HEMS data to usable datetimes
def convert_custom_datetime(series):
    return series.apply(lambda x: datetime.strptime(x, "%d/%m/%Y %H:%M"))


############################################################################
#                           Enter inputs here                              #
############################################################################

# enter in the input and output file names.   
input_file_name  = "/home/sladefox/ochre_working/180111_1_15_NR_controlled.csv"
output_file_name  = "/home/sladefox/ochre_working/Ready_data/180111_1_15_NR_Controlled_ready_data.csv"
folder_path = "/home/sladefox/ochre_working/Ready_data"

############################################################################
#                             Create Folder                                #
############################################################################

# Check for file path and create if does not exist
if not os.path.exists(folder_path):
    os.makedirs(folder_path) # os.mkdir() creates only one level; os.makedirs() creates intermediate parents
    print(f"Directory created: {folder_path}")
else:
    print(f"Directory already exists: {folder_path}")

############################################################################
#                             Program Start                                #
############################################################################

# read data 
df = pd.read_csv(input_file_name)

# remove any NAN values that will mess up the datetime conversion. 
df = df.dropna(axis=0)

reader = csv.DictReader(input_file_name)

# Access the columns attribute
print("Column Titles:")
# The .columns attribute returns an Index object, which can be printed directly or iterated
for col in df.columns:
    print(f"- {col}")
# convert time column to a usable datetime fomat
df['time'] = pd.to_datetime(df['Time'], errors='coerce')
#df['time'] = convert_custom_datetime(df['Time'])

# Create column that contains hour and minute data
df['hr_min'] = df['time'].dt.strftime('%H:%M')

# drop unwanted columns
df = df.drop(['Time', 'Total Electric Power (kW)', 'Total Electric Energy (kWh)', 'Water Heating COP (-)', 
              'Water Heating Deadband Upper Limit (C)', 'Water Heating Deadband Lower Limit (C)', 'Water Heating Heat Pump COP (-)', 
              'Hot Water Outlet Temperature (C)', 'Temperature - Indoor (C)', 'time'], axis=1)


# pivot the table
df_pivot = df.pivot_table(index = 'Home', columns = 'hr_min', values = 'Water Heating Electric Power (kW)')

# write data to csv
df_pivot.to_csv(output_file_name, index=True)
