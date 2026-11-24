import pandas as pd
from pathlib import Path

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 250)

file_path = Path(__file__).parent / "skill_builder_data_corrected.csv"

# Try UTF-8 first, then the older encoding this dataset is known to use
try:
    df = pd.read_csv(file_path, encoding="utf-8-sig", low_memory=False)
except UnicodeDecodeError:
    df = pd.read_csv(file_path, encoding="ISO-8859-15", low_memory=False)

# Remove any invisible marker stuck to the first column name
df.columns = [c.replace("\ufeff", "").replace("ï»¿", "") for c in df.columns]

print("Rows and columns:", df.shape)
print("Expected rows for the corrected file: 401756")
print("\nStudents:", df["user_id"].nunique())
print("\nColumn names:")
print(df.columns.tolist())
print("\nFirst 3 rows (a few columns):")
print(df[["order_id", "user_id", "problem_id", "correct", "skill_id", "skill_name"]].head(3))