
from __future__ import annotations

from typing import List, Optional

import pandas as pd

from decision_engine import (
    DEFAULT_DELAY_HOURS,
    DEFAULT_DRIVER_PENALTY,
    rank_routes,
)

DEFAULT_VOT_SWEEP = [50, 100, 150, 200, 300]


def run_sensitivity_analysis(
    routes: pd.DataFrame,
    shipment_id: str,
    vot_values: Optional[List[float]] = None,
    delay_hours: float = DEFAULT_DELAY_HOURS,
    driver_penalty: float = DEFAULT_DRIVER_PENALTY,
) -> pd.DataFrame:
    """Re-run route ranking across a sweep of VoT values for one shipment."""
    if vot_values is None:
        vot_values = DEFAULT_VOT_SWEEP

    rows = []
    previous_winner = None
    for vot in vot_values:
        ranked = rank_routes(
            routes, shipment_id, vot=vot, delay_hours=delay_hours,
            driver_penalty=driver_penalty,
        )
        winner = ranked.iloc[0]
        changed = previous_winner is not None and winner["route_id"] != previous_winner
        rows.append({
            "VoT": vot,
            "winning_route": winner["route_id"],
            "archetype": winner["archetype"],
            "money_score": winner["calculated_money_score"],
            "winner_changed": changed,
        })
        previous_winner = winner["route_id"]

    return pd.DataFrame(rows)


def run_sensitivity_all_shipments(
    shipments: pd.DataFrame,
    routes: pd.DataFrame,
    vot_values: Optional[List[float]] = None,
) -> pd.DataFrame:
    """Scan across ALL shipments to see how often the VoT assumption
    actually changes the outcome - a useful diagnostic for how much this
    single parameter matters in practice."""
    if vot_values is None:
        vot_values = DEFAULT_VOT_SWEEP

    summary_rows = []
    for sid in shipments["shipment_id"]:
        if (routes["shipment_id"] == sid).sum() < 2:
            continue  # sensitivity is meaningless with a single candidate route
        sens = run_sensitivity_analysis(routes, sid, vot_values=vot_values)
        summary_rows.append({
            "shipment_id": sid,
            "sensitive_to_vot": bool(sens["winner_changed"].any()),
        })

    return pd.DataFrame(summary_rows)
