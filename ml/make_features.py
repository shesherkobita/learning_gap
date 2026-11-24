import pandas as pd
from pathlib import Path

folder = Path(__file__).parent
df = pd.read_csv(folder / "skill_builder_cleaned.csv")

# Already sorted by student, skill, attempt order. Work inside each (student, skill) group.
g = df.groupby(["user_id", "skill_id"])

# Features use ONLY the attempts BEFORE the current one (no peeking at the answer)
df["n_prev"] = g.cumcount()                               # how many earlier attempts
df["prev_correct"] = g["correct"].cumsum() - df["correct"]  # how many earlier attempts were right
df["prev_acc"] = df["prev_correct"] / df["n_prev"]          # accuracy so far (empty on 1st attempt)
df["last_correct"] = g["correct"].shift(1)                  # was the previous attempt right?
df["last3_acc"] = g["correct"].transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())

print("All rows:", len(df))
print("First attempts (no history, cannot predict):", (df["n_prev"] == 0).sum())

# Rows we can predict: the student has at least one earlier attempt on this skill
data = df[df["n_prev"] >= 1].copy()
print("Rows with history:", len(data), "| students:", data["user_id"].nunique(),
      "| skills:", data["skill_id"].nunique())
print("Share correct among these rows:", round(data["correct"].mean(), 4))
print("Baseline accuracy (always predict 'correct'):", round(data["correct"].mean(), 4))

print("\nFeature check (one ordinary student-skill sequence):")
sizes = data.groupby(["user_id", "skill_id"]).size()
for pair in sizes[sizes == 7].index:
    sample = data[(data["user_id"] == pair[0]) & (data["skill_id"] == pair[1])]
    if list(sample["opportunity"]) == list(range(2, 9)) and sample["correct"].nunique() == 2:
        break
print(sample[["opportunity", "correct", "n_prev", "prev_correct", "prev_acc", "last_correct", "last3_acc"]].round(2).to_string(index=False))

data.to_csv(folder / "skill_builder_features.csv", index=False)
print("\nSaved skill_builder_features.csv")