import pandas as pd
from pathlib import Path

df = pd.read_csv(Path(__file__).parent / "skill_builder_cleaned.csv")  # sorted by student, skill, attempt
g = df.groupby(["user_id", "skill_id"])

# streak of consecutive correct answers just BEFORE each attempt
def prev_streak(s):
    out, run = [], 0
    for v in s.values:
        out.append(run)
        run = run + 1 if v == 1 else 0
    return pd.Series(out, index=s.index)

df["prev_streak"] = g["correct"].transform(prev_streak)

print("Attempts made when the student already had 3+ correct in a row:",
      (df["prev_streak"] >= 3).sum(), "of", len(df))

last = g.tail(1)
print("Student-skill sequences:", len(last))
print("Sequences whose LAST attempt completes a 3+ streak:",
      int(((last["prev_streak"] >= 2) & (last["correct"] == 1)).sum()))

print("\nShare correct by streak before the attempt:")
print(df.groupby(df["prev_streak"].clip(upper=5))["correct"].agg(["mean", "size"]).round(3))