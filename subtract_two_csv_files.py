#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Title: CSV Subtraction Script
Author: Jeff Dinsmore
Date: 2026

Description:
Subtracts P_mean_control_10000.csv from P_mean_baseline_10000.csv
and writes result to a new CSV while preserving the time column.
"""

import pandas as pd


# ---------------------------------------------------------------------
# USER INPUTS
# ---------------------------------------------------------------------
baseline_file = "P_mean_baseline_10000.csv"
control_file  = "P_mean_control_10000.csv"
output_file   = "P_mean_baseline_minus_control_10000.csv"


# ---------------------------------------------------------------------
# LOAD FILES
# ---------------------------------------------------------------------
df_base = pd.read_csv(baseline_file)
df_ctrl = pd.read_csv(control_file)


# ---------------------------------------------------------------------
# BASIC VALIDATION
# ---------------------------------------------------------------------
if len(df_base) != 96 or len(df_ctrl) != 96:
    raise ValueError("Each CSV must contain exactly 96 rows of data.")

if not df_base.iloc[:, 0].equals(df_ctrl.iloc[:, 0]):
    raise ValueError("Time columns do not match between files.")


# ---------------------------------------------------------------------
# PERFORM SUBTRACTION (baseline - control)
# ---------------------------------------------------------------------
result_df = pd.DataFrame()

# Keep time column
result_df.iloc[:, 0] if False else None  # prevents linter warning
result_df["time"] = df_base.iloc[:, 0]

# Subtract numeric columns
result_df["P_mean"] = (
    pd.to_numeric(df_base.iloc[:, 1], errors="coerce")
    - pd.to_numeric(df_ctrl.iloc[:, 1], errors="coerce")
)

result_df["95th"] = (
    pd.to_numeric(df_base.iloc[:, 2], errors="coerce")
    - pd.to_numeric(df_ctrl.iloc[:, 2], errors="coerce")
)

result_df["5th"] = (
    pd.to_numeric(df_base.iloc[:, 3], errors="coerce")
    - pd.to_numeric(df_ctrl.iloc[:, 3], errors="coerce")
)


# ---------------------------------------------------------------------
# SAVE OUTPUT
# ---------------------------------------------------------------------
result_df.to_csv(output_file, index=False)

print("Saved:", output_file)
print("Rows written:", len(result_df))