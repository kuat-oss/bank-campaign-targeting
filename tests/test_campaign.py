import numpy as np
import pandas as pd
import pytest

from campaign.data import connect, load_calls
from campaign.model import FEATURES, gains_table, time_split
from campaign.scorecard import score


@pytest.fixture(scope="module")
def calls():
    return load_calls()


def test_row_counts_match_uci_documentation(calls):
    assert len(calls) == 41188
    assert calls["subscribed"].sum() == 4640


def test_years_reconstructed_in_order(calls):
    counts = calls.groupby("campaign_year").size().to_dict()
    assert counts == {2008: 27690, 2009: 11440, 2010: 2058}
    # month_start never goes backwards when rows are read in file order
    assert calls["month_start"].is_monotonic_increasing


def test_model_features_exclude_leaky_columns():
    for col in ["call_seconds", "month", "campaign_year", "euribor3m", "subscribed"]:
        assert col not in FEATURES


def test_time_split_has_no_overlap(calls):
    train, test = time_split(calls)
    assert train["month_start"].max() < test["month_start"].min()
    assert len(train) + len(test) == len(calls)


def test_gains_table_perfect_ranking():
    y = [1, 1, 0, 0, 0, 0, 0, 0, 0, 0]
    s = [0.9, 0.8, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
    g = gains_table(y, s, bins=5)
    assert g.loc[0, "cum_subscribers_pct"] == pytest.approx(1.0)
    assert g["clients"].sum() == 10


def test_gains_table_random_scores_capture_about_proportional():
    rng = np.random.default_rng(0)
    y = rng.random(20000) < 0.1
    g = gains_table(y, rng.random(20000))
    assert g.loc[4, "cum_subscribers_pct"] == pytest.approx(0.5, abs=0.03)


def test_scorecard_values():
    df = pd.DataFrame({
        "previous_outcome": ["success", "failure", "nonexistent"],
        "contact_type": ["cellular", "telephone", "cellular"],
        "job": ["student", "admin.", "admin."],
        "age": [22, 40, 61],
    })
    assert score(df).tolist() == [5, -1, 2]


def test_data_quality_view_runs():
    dq = connect().sql("select * from dq_report").df()
    assert dq.loc[dq.check_name == "Rows", "result"].item() == "41188"
