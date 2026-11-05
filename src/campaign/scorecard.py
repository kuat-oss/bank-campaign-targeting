"""A four-rule scorecard for deciding who to call first.

Every rule here is already visible in the 2008 data alone, and each one holds
in 2008, 2009 and 2010. Higher score = call earlier.
"""

import pandas as pd

RULES = [
    ("Subscribed in the previous campaign", 3),
    ("Turned down the previous campaign", -1),
    ("Has a mobile number (cellular)", 1),
    ("Student, retired, under 25 or 60+", 1),
]


def score(df: pd.DataFrame) -> pd.Series:
    s = (
        3 * (df["previous_outcome"] == "success").astype(int)
        - 1 * (df["previous_outcome"] == "failure").astype(int)
        + 1 * (df["contact_type"] == "cellular").astype(int)
        + 1 * (df["job"].isin(["student", "retired"]) | (df["age"] < 25) | (df["age"] >= 60)).astype(int)
    )
    return s.rename("score")
