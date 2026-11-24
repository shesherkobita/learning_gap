import joblib
import pandas as pd
from pathlib import Path

bundle = joblib.load(Path(__file__).parent / "skill_model.joblib")
MODEL, FEATURES, SKILLS = bundle["model"], bundle["features"], bundle["skills"]


def predict_correct_probability(skill_id, previous_results):
    """Chance (0 to 1) that the student's NEXT answer on this skill is correct.

    skill_id: the skill's id (int)
    previous_results: list of earlier answers on this skill, oldest first, 1 = correct, 0 = wrong
    """
    if len(previous_results) < 1:
        raise ValueError("Need at least one earlier answer on this skill")
    if skill_id not in SKILLS:
        raise ValueError(f"Unknown skill_id {skill_id}")
    if any(r not in (0, 1) for r in previous_results):
        raise ValueError("previous_results must contain only 0 or 1")

    n = len(previous_results)
    streak = 0
    for r in reversed(previous_results):
        if r == 1:
            streak += 1
        else:
            break
    row = {
        "n_prev": n,
        "prev_acc": sum(previous_results) / n,
        "last_correct": previous_results[-1],
        "last3_acc": sum(previous_results[-3:]) / len(previous_results[-3:]),
        "prev_streak": streak,
        "skill_id": pd.Categorical([skill_id], categories=SKILLS)[0],
    }
    X = pd.DataFrame([row], columns=FEATURES)
    X["skill_id"] = pd.Categorical(X["skill_id"], categories=SKILLS)
    return float(MODEL.predict_proba(X)[0, 1])


if __name__ == "__main__":
    skill = SKILLS[0]
    print("Skill", skill)
    for hist in ([0], [0, 0, 1], [1, 1, 1], [1, 1, 1, 1, 1, 1], [0, 0, 0, 0]):
        print(f"  earlier answers {hist} -> chance next is correct: {predict_correct_probability(skill, hist):.2f}")
    for bad in ([], [2, 1]):
        try:
            predict_correct_probability(skill, bad)
        except ValueError as e:
            print("  rejected", bad, "->", e)