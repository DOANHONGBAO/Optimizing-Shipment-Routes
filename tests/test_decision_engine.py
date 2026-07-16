
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import data_utils
import decision_engine as engine
import sensitivity as sens


def _sample():
    return data_utils.generate_sample_data(n_shipments=6, seed=42)


def test_generate_sample_data_shapes():
    shipments, routes, legs = _sample()
    assert len(shipments) == 6
    assert len(routes) >= 6
    assert set(engine.REQUIRED_SCORE_COLS).issubset(routes.columns)


def test_validate_data_passes_on_generated_data():
    shipments, routes, legs = _sample()
    report = data_utils.validate_data(shipments, routes, legs)
    assert all(status == "ok" for status, _ in report)


def test_money_score_matches_precomputed_default_params():
    shipments, routes, legs = _sample()
    scored = engine.calculate_money_score(routes)
    diff = (routes["money_score_kvnd"] - scored).abs().max()
    assert diff < 1e-6


def test_rank_routes_orders_best_first():
    shipments, routes, legs = _sample()
    sid = shipments["shipment_id"].iloc[0]
    ranked = engine.rank_routes(routes, sid)
    scores = ranked["calculated_money_score"].tolist()
    assert scores == sorted(scores)
    assert ranked["rank"].tolist() == list(range(1, len(ranked) + 1))


def test_build_decision_json_structure():
    shipments, routes, legs = _sample()
    sid = shipments["shipment_id"].iloc[0]
    decision = engine.build_decision_json(shipments, routes, sid)
    assert decision["shipment_id"] == sid
    assert decision["selected_route"] == decision["ranking"][0]["route_id"]
    assert "comparison" in decision and "runner_ups" in decision["comparison"]


def test_sensitivity_analysis_runs():
    shipments, routes, legs = _sample()
    sid = shipments["shipment_id"].iloc[0]
    sdf = sens.run_sensitivity_analysis(routes, sid)
    assert len(sdf) == len(sens.DEFAULT_VOT_SWEEP)
    assert "winner_changed" in sdf.columns
