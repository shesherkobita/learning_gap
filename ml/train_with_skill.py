import time
import pandas as pd
from pathlib import Path
from sklearn.model_selection import GroupKFold, cross_validate
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import make_pipeline

data = pd.read_csv(Path(__file__).parent / "skill_builder_features.csv")

history = ["n_prev", "prev_acc", "last_correct", "last3_acc"]
X = data[history + ["skill_id"]]
y = data["correct"]
groups = data["user_id"]

# One-hot encode skill_id; the encoder is fitted on the training part only
skill_only = make_pipeline(
    ColumnTransformer([("skill", OneHotEncoder(handle_unknown="ignore"), ["skill_id"])]),
    LogisticRegression(max_iter=1000),
)
history_only = make_pipeline(
    ColumnTransformer([("hist", "passthrough", history)]),
    LogisticRegression(max_iter=1000),
)
history_and_skill = make_pipeline(
    ColumnTransformer([("hist", "passthrough", history),
                       ("skill", OneHotEncoder(handle_unknown="ignore"), ["skill_id"])]),
    LogisticRegression(max_iter=1000),
)

models = {
    "Baseline (always predict correct)": DummyClassifier(strategy="most_frequent"),
    "Skill only": skill_only,
    "History only (Step 6)": history_only,
    "History + skill": history_and_skill,
}

cv = GroupKFold(n_splits=5)
scoring = ["accuracy", "roc_auc"]
for name, model in models.items():
    start = time.time()
    res = cross_validate(model, X, y, groups=groups, cv=cv, scoring=scoring)
    print(f"\n{name} ({time.time() - start:.0f} s)")
    for m in scoring:
        s = res["test_" + m]
        print(f"  {m}: {s.mean():.3f} (+/- {s.std():.3f})")