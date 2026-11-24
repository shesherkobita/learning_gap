import time
import pandas as pd
from pathlib import Path
from sklearn.model_selection import GroupKFold, cross_validate
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression

data = pd.read_csv(Path(__file__).parent / "skill_builder_features.csv")

features = ["n_prev", "prev_acc", "last_correct", "last3_acc"]
target = "correct"

X = data[features]
y = data[target]
groups = data["user_id"]   # keep each student entirely in train OR test, never both

print("Rows:", len(data), "| students:", groups.nunique())
print("Missing values in features:", int(X.isna().sum().sum()))

cv = GroupKFold(n_splits=5)
scoring = ["accuracy", "f1", "roc_auc"]

models = {
    "Baseline (always predict correct)": DummyClassifier(strategy="most_frequent"),
    "Logistic Regression": LogisticRegression(max_iter=1000),
}

for name, model in models.items():
    start = time.time()
    res = cross_validate(model, X, y, groups=groups, cv=cv, scoring=scoring)
    print("\n" + name, f"({time.time() - start:.0f} s)")
    for m in scoring:
        s = res["test_" + m]
        print(f"  {m}: {s.mean():.3f} (+/- {s.std():.3f})")