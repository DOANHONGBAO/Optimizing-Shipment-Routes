
from __future__ import annotations

import io
from typing import List, Tuple

import numpy as np
import pandas as pd

RANDOM_SEED = 42

REQUIRED_SHIPMENT_COLS = {"shipment_id", "origin", "destination"}
REQUIRED_ROUTE_COLS = {
    "route_id", "shipment_id", "archetype",
    "total_cost_kvnd", "total_time_h", "delay_probability",
    "expected_risk_hours", "driver_score",
}
REQUIRED_LEG_COLS = {
    "leg_id", "route_id", "from", "to", "mode",
    "cost_kvnd", "time_h", "delay_probability", "risk_extra_h",
}


def generate_sample_data(n_shipments: int = 6, seed: int = RANDOM_SEED):
    """Deterministically generate a small synthetic dataset with the same
    schema as a real SAFiRi export. Returns (shipments_df, routes_df, legs_df).
    """
    rng = np.random.default_rng(seed)

    cities = ["Hanoi", "Da Nang", "Ho Chi Minh City", "Hai Phong",
              "Can Tho", "Nha Trang", "Vinh", "Quy Nhon"]
    archetypes = ["Road Only", "Rail + Road", "Sea + Road", "Air + Road"]
    modes_by_archetype = {
        "Road Only": ["Truck"],
        "Rail + Road": ["Rail", "Truck"],
        "Sea + Road": ["Ship", "Truck"],
        "Air + Road": ["Air", "Truck"],
    }

    shipments, routes, legs = [], [], []
    leg_counter, route_counter = 1, 1

    for s_idx in range(1, n_shipments + 1):
        shipment_id = f"SHP-{s_idx:03d}"
        origin, destination = rng.choice(cities, 2, replace=False)
        shipments.append({
            "shipment_id": shipment_id,
            "origin": origin,
            "destination": destination,
        })

        n_routes = rng.integers(2, 4)
        chosen_archetypes = rng.choice(archetypes, n_routes, replace=False)

        for archetype in chosen_archetypes:
            route_id = f"RT-{route_counter:04d}"
            route_counter += 1
            modes = modes_by_archetype[archetype]

            leg_rows = []
            for mode in modes:
                leg_id = f"LEG-{leg_counter:05d}"
                leg_counter += 1

                base_cost = {"Truck": 15, "Rail": 10, "Ship": 6, "Air": 45}[mode]
                base_time = {"Truck": 8, "Rail": 14, "Ship": 60, "Air": 4}[mode]
                base_delay_p = {"Truck": 0.15, "Rail": 0.10,
                                 "Ship": 0.30, "Air": 0.08}[mode]
                base_risk = {"Truck": 1.0, "Rail": 1.5,
                             "Ship": 6.0, "Air": 0.5}[mode]

                cost = base_cost * rng.uniform(0.85, 1.25)
                time_h = base_time * rng.uniform(0.85, 1.25)
                delay_p = np.clip(base_delay_p * rng.uniform(0.7, 1.3), 0, 1)
                risk_extra_h = base_risk * rng.uniform(0.7, 1.3)

                leg = {
                    "leg_id": leg_id,
                    "route_id": route_id,
                    "from": origin,
                    "to": destination,
                    "mode": mode,
                    "cost_kvnd": round(cost, 2),
                    "time_h": round(time_h, 2),
                    "delay_probability": round(delay_p, 3),
                    "risk_extra_h": round(risk_extra_h, 2),
                }
                legs.append(leg)
                leg_rows.append(leg)

            total_cost = sum(r["cost_kvnd"] for r in leg_rows)
            total_time = sum(r["time_h"] for r in leg_rows)
            # P(at least one delay) = 1 - Product(1 - p_i)
            combined_delay_p = 1 - np.prod([1 - r["delay_probability"] for r in leg_rows])
            expected_risk_hours = sum(r["risk_extra_h"] for r in leg_rows)
            driver_score = round(rng.uniform(0.65, 0.99), 2)

            route = {
                "route_id": route_id,
                "shipment_id": shipment_id,
                "archetype": archetype,
                "total_cost_kvnd": round(total_cost, 2),
                "total_time_h": round(total_time, 2),
                "delay_probability": round(combined_delay_p, 3),
                "expected_risk_hours": round(expected_risk_hours, 2),
                "driver_score": driver_score,
            }
            # money_score_kvnd precomputed with DEFAULT params, same formula
            # as decision_engine.calculate_money_score.
            route["money_score_kvnd"] = round(
                route["total_cost_kvnd"]
                + 100 * route["total_time_h"]
                + 100 * route["delay_probability"] * 3
                + 100 * route["expected_risk_hours"]
                + 500 * (1 - route["driver_score"]),
                2,
            )
            routes.append(route)

    shipments_df = pd.DataFrame(shipments)
    routes_df = pd.DataFrame(routes)
    legs_df = pd.DataFrame(legs)
    return shipments_df, routes_df, legs_df


def load_csvs(shipments_file, routes_file, legs_file=None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Read uploaded file-like objects (or paths) into DataFrames."""
    shipments_df = pd.read_csv(shipments_file)
    routes_df = pd.read_csv(routes_file)
    legs_df = pd.read_csv(legs_file) if legs_file is not None else pd.DataFrame(columns=list(REQUIRED_LEG_COLS))
    return shipments_df, routes_df, legs_df


def validate_data(shipments_df: pd.DataFrame, routes_df: pd.DataFrame,
                   legs_df: pd.DataFrame | None = None) -> List[Tuple[str, str]]:
    """Run schema + integrity checks. Returns a list of (status, message)
    tuples, status in {"ok", "warning", "error"}. Raises ValueError only
    for fatal referential-integrity problems that make the engine unusable.
    """
    report: List[Tuple[str, str]] = []

    # --- required columns present? ---
    missing_shipment_cols = REQUIRED_SHIPMENT_COLS - set(shipments_df.columns)
    missing_route_cols = REQUIRED_ROUTE_COLS - set(routes_df.columns)
    if missing_shipment_cols:
        raise ValueError(f"shipments.csv is missing required column(s): {sorted(missing_shipment_cols)}")
    if missing_route_cols:
        raise ValueError(f"routes.csv is missing required column(s): {sorted(missing_route_cols)}")
    report.append(("ok", "shipments.csv and routes.csv have all required columns"))

    # --- missing values ---
    for name, df in [("shipments", shipments_df), ("routes", routes_df)]:
        n_missing = int(df.isnull().sum().sum())
        status = "ok" if n_missing == 0 else "warning"
        report.append((status, f"{name}: {n_missing} missing value(s)"))

    # --- duplicated primary keys ---
    dup_routes = int(routes_df["route_id"].duplicated().sum())
    dup_shipments = int(shipments_df["shipment_id"].duplicated().sum())
    report.append(("ok" if dup_routes == 0 else "warning", f"duplicated route_id: {dup_routes}"))
    report.append(("ok" if dup_shipments == 0 else "warning", f"duplicated shipment_id: {dup_shipments}"))

    if legs_df is not None and not legs_df.empty and "leg_id" in legs_df.columns:
        dup_legs = int(legs_df["leg_id"].duplicated().sum())
        report.append(("ok" if dup_legs == 0 else "warning", f"duplicated leg_id: {dup_legs}"))

    # --- referential consistency: routes -> shipments (fatal) ---
    orphan_routes = set(routes_df["shipment_id"]) - set(shipments_df["shipment_id"])
    if orphan_routes:
        raise ValueError(f"routes.csv references unknown shipment_id(s): {sorted(orphan_routes)}")
    report.append(("ok", "every route references a known shipment_id"))

    # --- referential consistency: legs -> routes (warning only) ---
    if legs_df is not None and not legs_df.empty and "route_id" in legs_df.columns:
        orphan_legs = set(legs_df["route_id"]) - set(routes_df["route_id"])
        if orphan_legs:
            report.append(("warning", f"legs.csv references unknown route_id(s): {sorted(orphan_legs)}"))
        else:
            report.append(("ok", "every leg references a known route_id"))

    # --- every shipment should ideally have >= 1 candidate route ---
    shipments_without_routes = set(shipments_df["shipment_id"]) - set(routes_df["shipment_id"])
    if shipments_without_routes:
        report.append(("warning", f"shipments with no candidate routes: {sorted(shipments_without_routes)}"))
    else:
        report.append(("ok", "every shipment has at least one candidate route"))

    return report
