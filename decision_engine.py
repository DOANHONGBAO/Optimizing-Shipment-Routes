

from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd

# Default Money Score parameters (units: thousand VND, hours, probability).
DEFAULT_VOT = 100             # Value of Time, kVND / hour
DEFAULT_DELAY_HOURS = 3       # Assumed hours lost when a delay occurs
DEFAULT_DRIVER_PENALTY = 500  # kVND penalty scaling for driver risk

REQUIRED_SCORE_COLS = {
    "total_cost_kvnd", "total_time_h", "delay_probability",
    "expected_risk_hours", "driver_score",
}


def calculate_money_score(
    routes: pd.DataFrame,
    vot: float = DEFAULT_VOT,
    delay_hours: float = DEFAULT_DELAY_HOURS,
    driver_penalty: float = DEFAULT_DRIVER_PENALTY,
) -> pd.Series:
    """Compute the Money Score for every row of `routes`. Lower is better."""
    missing = REQUIRED_SCORE_COLS - set(routes.columns)
    if missing:
        raise ValueError(f"routes is missing required columns: {missing}")

    score = (
        routes["total_cost_kvnd"]
        + vot * routes["total_time_h"]
        + vot * routes["delay_probability"] * delay_hours
        + vot * routes["expected_risk_hours"]
        + driver_penalty * (1 - routes["driver_score"])
    )
    return score.round(2)


def rank_routes(
    routes: pd.DataFrame,
    shipment_id: str,
    vot: float = DEFAULT_VOT,
    delay_hours: float = DEFAULT_DELAY_HOURS,
    driver_penalty: float = DEFAULT_DRIVER_PENALTY,
) -> pd.DataFrame:
    """Return the candidate routes for one shipment, ranked best-first
    (rank 1 = lowest / best Money Score)."""
    candidates = routes.loc[routes["shipment_id"] == shipment_id].copy()
    if candidates.empty:
        raise ValueError(f"No routes found for shipment_id={shipment_id!r}")

    candidates["calculated_money_score"] = calculate_money_score(
        candidates, vot=vot, delay_hours=delay_hours, driver_penalty=driver_penalty,
    )
    candidates = candidates.sort_values(
        "calculated_money_score", ascending=True
    ).reset_index(drop=True)
    candidates["rank"] = candidates.index + 1
    return candidates


def compare_routes(ranked: pd.DataFrame) -> Dict:
    """Compute the deltas between the winning route and every runner-up.
    This is the raw material for "how much better is the chosen route".
    """
    best = ranked.iloc[0]
    comparisons = []
    for _, row in ranked.iloc[1:].iterrows():
        comparisons.append({
            "route_id": row["route_id"],
            "archetype": row["archetype"],
            "money_score_delta_kvnd": round(
                row["calculated_money_score"] - best["calculated_money_score"], 2
            ),
            "cost_delta_kvnd": round(row["total_cost_kvnd"] - best["total_cost_kvnd"], 2),
            "time_delta_h": round(row["total_time_h"] - best["total_time_h"], 2),
            "delay_probability_delta": round(
                row["delay_probability"] - best["delay_probability"], 3
            ),
            "driver_score_delta": round(row["driver_score"] - best["driver_score"], 3),
        })
    return {"best_route_id": best["route_id"], "runner_ups": comparisons}


def build_decision_json(
    shipments: pd.DataFrame,
    routes: pd.DataFrame,
    shipment_id: str,
    vot: float = DEFAULT_VOT,
    delay_hours: float = DEFAULT_DELAY_HOURS,
    driver_penalty: float = DEFAULT_DRIVER_PENALTY,
) -> Dict:
    """Assemble the single structured JSON object that fully describes the
    decision for one shipment — every number a downstream explanation
    (human or LLM) could need, and nothing it should have to invent."""
    ranked = rank_routes(
        routes, shipment_id, vot=vot, delay_hours=delay_hours, driver_penalty=driver_penalty,
    )
    comparison = compare_routes(ranked)
    best = ranked.iloc[0]

    shipment_row = shipments.loc[shipments["shipment_id"] == shipment_id].iloc[0]

    decision = {
        "shipment_id": shipment_id,
        "origin": shipment_row["origin"],
        "destination": shipment_row["destination"],
        "selected_route": best["route_id"],
        "selected_archetype": best["archetype"],
        "money_score": float(best["calculated_money_score"]),
        "ranking": ranked[[
            "rank", "route_id", "archetype", "calculated_money_score",
            "total_cost_kvnd", "total_time_h", "delay_probability",
            "expected_risk_hours", "driver_score",
        ]].to_dict(orient="records"),
        "comparison": comparison,
        "parameters": {
            "VoT": vot,
            "DelayHours": delay_hours,
            "DriverPenalty": driver_penalty,
        },
    }
    return decision
