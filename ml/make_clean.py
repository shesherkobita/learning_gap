import pandas as pd
from pathlib import Path

folder = Path(__file__).parent
file_path = folder / "skill_builder_data_corrected.csv"
try:
    df = pd.read_csv(file_path, encoding="utf-8-sig", low_memory=False)
except UnicodeDecodeError:
    df = pd.read_csv(file_path, encoding="ISO-8859-15", low_memory=False)
df.columns = [c.replace("\ufeff", "").replace("ï»¿", "") for c in df.columns]

print("Start rows:", len(df), "| students:", df["user_id"].nunique())

# Decision 1: keep main problems only (original == 1), drop hint/scaffolding steps
main = df[df["original"] == 1]
print("After keeping main problems:", len(main), "| students:", main["user_id"].nunique())

# Decision 2: keep only rows that have a skill_id
cleaned = main[main["skill_id"].notna()].copy()
cleaned["skill_id"] = cleaned["skill_id"].astype(int)
print("After keeping rows with a skill:", len(cleaned), "| students:", cleaned["user_id"].nunique())

# Keep only the columns we need, in time order inside each student and skill
cols = ["order_id", "user_id", "problem_id", "skill_id", "skill_name",
        "correct", "attempt_count", "opportunity", "ms_first_response", "hint_count"]
cleaned = cleaned[cols].sort_values(["user_id", "skill_id", "opportunity"]).reset_index(drop=True)

print("\nDistinct student-skill pairs:", cleaned.groupby(["user_id", "skill_id"]).ngroups)
print("Distinct interactions (order_id):", cleaned["order_id"].nunique())
print("Share correct:", round(cleaned["correct"].mean(), 4))
print("Repeated (student, skill, opportunity):", cleaned.duplicated(["user_id", "skill_id", "opportunity"]).sum())

cleaned.to_csv(folder / "skill_builder_cleaned.csv", index=False)
print("\nSaved skill_builder_cleaned.csv")