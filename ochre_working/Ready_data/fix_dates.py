import os
import csv
from datetime import datetime

input_file = r"c:\Users\josep\Aggregated_Load_Analysis\ochre_working\Ready_data\final_aggregated_baseline_15min.csv"
temp_file = r"c:\Users\josep\Aggregated_Load_Analysis\ochre_working\Ready_data\output.csv"

with open(input_file, "r", newline="") as infile, open(temp_file, "w", newline="") as outfile:
    reader = csv.reader(infile)
    writer = csv.writer(outfile)

    try:
        header = next(reader)
    except StopIteration:
        raise ValueError("Input file is empty")

    new_header = []
    for item in header:
        try:
            dt = datetime.strptime(item.strip(), "%Y-%m-%d %H:%M:%S")
            new_header.append(dt.strftime("%H:%M"))
        except:
            new_header.append(item)

    writer.writerow(new_header)

    for row in reader:
        writer.writerow(row)

# Replace original file
os.replace(temp_file, input_file)

print("Done! File safely updated.")