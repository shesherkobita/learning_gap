import time
import pandas as pd
from pathlib import Path
from sklearn.model_selection import GroupKFold, cross_validate
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import make_pipeline

df = pd.read_csv(Path(__file__).parent / "skill_builder_cleaned.csv")  # sorted by student, skill, attempt
g = df.groupby(["user_id", "skill_id"])

# ---- features: only earlier attempts on the same skill ----
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
history = ["n_prev", "prev_acc", "last_correct", "last3_acc", "prev_streak"]
y = data["correct"]
groups = data["user_id"]
print("Rows:", len(data), "| students:", groups.nunique())

# ---- the three models ----
logreg = make_pipeline(
    ColumnTransformer([("hist", "passthrough", history),
                       ("skill", OneHotEncoder(handle_unknown="ignore"), ["skill_id"])]),
    LogisticRegression(max_iter=1000),
)
Xg = data[history + ["skill_id"]].copy()
Xg["skill_id"] = Xg["skill_id"].astype("category")
gboost = HistGradientBoostingClassifier(categorical_features="from_dtype", random_state=42)

cv = GroupKFold(n_splits=5)
scoring = ["accuracy", "f1", "roc_auc"]
runs = [
    ("Baseline (always predict correct)", DummyClassifier(strategy="most_frequent"), Xg),
    ("Logistic Regression", logreg, Xg),
    ("Gradient Boosting", gboost, Xg),
]
for name, model, X in runs:
    start = time.time()
    res = cross_validate(model, X, y, groups=groups, cv=cv, scoring=scoring)
    print(f"\n{name} ({time.time() - start:.0f} s)")
    for m in scoring:
        s = res["test_" + m]
        print(f"  {m}: {s.mean():.3f} (+/- {s.std():.3f})")