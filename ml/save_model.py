import joblib
import pandas as pd
from pathlib import Path
from sklearn.ensemble import HistGradientBoostingClassifier

folder = Path(__file__).parent
df = pd.read_csv(folder / "skill_builder_cleaned.csv")  # sorted by student, skill, attempt
g = df.groupby(["user_id", "skill_id"])

df["n_prev"] = g.cumcount()
df["prev_correct"] = g["correct"].cumsum() - df["correct"]
df["prev_acc"] = df["prev_correct"] / df["n_prev"]
df["last_correct"] = g["correct"].shift(1)
df["last3_acc"] = g["correct"].transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())

def prev_streak(s):
    out, run = [], 0
    for v in s.values:
        out.append(run)
        run = run + 1 if v == 1 else 0
    return pd.Series(out, index=s.index)
df["prev_streak"] = g["correct"].transform(prev_streak)

data = df[df["n_prev"] >= 1].copy()
features = ["n_prev", "prev_acc", "last_correct", "last3_acc", "prev_streak", "skill_id"]

skills = sorted(data["skill_id"].unique().tolist())
X = data[features].copy()
X["skill_id"] = pd.Categorical(X["skill_id"], categories=skills)
y = data["correct"]

# Train on ALL rows for the final saved model (performance was measured earlier by cross-validation)
model = HistGradientBoostingClassifier(categorical_features="from_dtype", random_state=42).fit(X, y)

joblib.dump({"model": model, "features": features, "skills": skills}, folder / "skill_model.joblib")
print("Saved skill_model.joblib")
print("Trained on", len(data), "rows,", len(skills), "skills")