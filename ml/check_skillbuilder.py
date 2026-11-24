import pandas as pd
from pathlib import Path

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 250)

file_path = Path(__file__).parent / "skill_builder_data_corrected.csv"
try:
    df = pd.read_csv(file_path, encoding="utf-8-sig", low_memory=False)
except UnicodeDecodeError:
    df = pd.read_csv(file_path, encoding="ISO-8859-15", low_memory=False)
df.columns = [c.replace("\ufeff", "").replace("ï»¿", "") for c in df.columns]

print("--- correct (1 = right, 0 = wrong) ---")
print(df["correct"].value_counts(dropna=False))

print("\n--- original (1 = main problem, 0 = hint/scaffolding step) ---")
print(df["original"].value_counts(dropna=False))

print("\n--- missing values in key columns ---")
print(df[["user_id", "problem_id", "correct", "skill_id", "skill_name"]].isna().sum())

print("\n--- repeated rows ---")
print("Distinct order_id:", df["order_id"].nunique())
print("Exact duplicate rows:", df.duplicated().sum())

print("\n--- interactions per student ---")
print(df.groupby("user_id").size().describe().round(1))

print("\n--- 10 most common skills ---")
print(df["skill_name"].value_counts().head(10))