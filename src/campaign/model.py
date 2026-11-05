"""Targeting model: who is most likely to subscribe if we call them?"""

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

# Only things the bank knows BEFORE picking up the phone.
# Left out on purpose:
#   call_seconds - only known after the call (leaks the answer)
#   month, year, interest rates, employment - same for everyone called in a
#     given month, so they can't help rank clients against each other, and they
#     mostly encode "when" rather than "who"
CATEGORICAL = ["job", "marital", "education", "credit_default", "housing_loan",
               "personal_loan", "contact_type", "previous_outcome"]
NUMERIC = ["age", "previous_contacts", "never_contacted_before"]
FEATURES = CATEGORICAL + NUMERIC
TARGET = "subscribed"

# train on calls before this month, test on everything after
SPLIT_MONTH = "2009-07-01"


def time_split(df: pd.DataFrame, split_month: str = SPLIT_MONTH):
    cut = pd.Timestamp(split_month)
    train = df[df["month_start"] < cut]
    test = df[df["month_start"] >= cut]
    return train, test


def logistic_model() -> Pipeline:
    pre = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
        ("num", StandardScaler(), NUMERIC),
    ])
    return Pipeline([("pre", pre), ("clf", LogisticRegression(max_iter=2000, class_weight="balanced"))])


def boosting_model(seed: int = 42) -> Pipeline:
    pre = ColumnTransformer([
        ("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), CATEGORICAL),
        ("num", "passthrough", NUMERIC),
    ])
    clf = HistGradientBoostingClassifier(
        categorical_features=list(range(len(CATEGORICAL))),
        max_depth=4, learning_rate=0.05, max_iter=300, l2_regularization=1.0, random_state=seed,
    )
    return Pipeline([("pre", pre), ("clf", clf)])


def gains_table(y_true, scores, bins: int = 10) -> pd.DataFrame:
    """Sort clients by score and show what share of subscribers each decile captures."""
    df = pd.DataFrame({"y": np.asarray(y_true, dtype=int), "s": np.asarray(scores, dtype=float)})
    df = df.sort_values("s", ascending=False, kind="mergesort").reset_index(drop=True)
    df["decile"] = (np.arange(len(df)) * bins // len(df)) + 1
    g = df.groupby("decile").agg(clients=("y", "size"), subscribers=("y", "sum"))
    g["conversion_rate"] = g["subscribers"] / g["clients"]
    g["cum_clients_pct"] = g["clients"].cumsum() / g["clients"].sum()
    g["cum_subscribers_pct"] = g["subscribers"].cumsum() / g["subscribers"].sum()
    g["lift"] = g["conversion_rate"] / (g["subscribers"].sum() / g["clients"].sum())
    return g.reset_index()
