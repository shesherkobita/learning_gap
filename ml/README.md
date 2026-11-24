# ML component: next-answer prediction

This folder predicts whether a student's next answer on a mathematics skill will be correct, using only their earlier answers on that same skill.

## Data

ASSISTments 2009-2010 Skill Builder dataset, corrected version.
Official page: https://sites.google.com/site/assistmentsdata/home/2009-2010-assistment-data/skill-builder-data-2009-2010

The data files are not included because they are large (19 to 63 MB). Download the corrected file and place it in this folder as `skill_builder_data_corrected.csv`.

## Requirements

Python packages: pandas, scikit-learn, joblib

## Order of the scripts

1. `inspect_skillbuilder.py` loads the data and prints its shape.
2. `check_skillbuilder.py` checks missing values and repeated rows.
3. `make_clean.py` keeps main problems that have a skill and saves `skill_builder_cleaned.csv`.
4. `make_features.py` builds features from earlier attempts and saves `skill_builder_features.csv`.
5. `train_baseline.py` compares an always-correct baseline with Logistic Regression.
6. `train_with_skill.py` compares skill-only, history-only and combined models.
7. `check_mastery.py` checks how often sequences end after three correct answers in a row.
8. `train_final.py` compares the baseline, Logistic Regression and Gradient Boosting.
9. `save_model.py` trains Gradient Boosting on all rows and saves `skill_model.joblib`.
10. `predict_demo.py` loads the saved model and gives the chance that the next answer is correct.

## Limitations

- The data comes from US students, not the Bangladeshi NCTB curriculum.
- It has no question text or misconception labels, so the model estimates correctness only. It does not detect misconceptions.
- Students often stop a skill after three correct answers in a row, which may affect the model.
