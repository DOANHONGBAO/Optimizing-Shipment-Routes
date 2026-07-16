from __future__ import annotations

from typing import Dict, List


def _money(value: float) -> str:
    return f"{value:,.0f} kVND"


def generate_template_explanation(decision: Dict) -> str:
    """Create a consultant-style, evidence-based explanation from the decision output."""
    route = decision["selected_route"]
    ranking = decision["ranking"]
    winner = ranking[0]
    runner_ups = decision["comparison"]["runner_ups"]
    opening = (
        f"For shipment {decision['shipment_id']} from {decision['origin']} to {decision['destination']}, "
        f"{route} ({decision['selected_archetype']}) is recommended because it produces the lowest composite "
        f"Money Score at {_money(decision['money_score'])}. The recommendation combines direct transportation "
        f"cost with travel time, delay exposure, and driver reliability rather than optimizing a single measure."
    )
    if not runner_ups:
        return opening + " It is the only feasible candidate in the supplied network, so expanding route options would be the principal opportunity for further optimization."
    closest = min(runner_ups, key=lambda item: item["money_score_delta_kvnd"])
    cost_position = "lower direct cost" if closest["cost_delta_kvnd"] >= 0 else "higher direct cost"
    time_position = "faster transit" if closest["time_delta_h"] >= 0 else "slower transit"
    risk_position = "lower delay risk" if closest["delay_probability_delta"] >= 0 else "higher delay risk"
    comparison = (
        f"Against the closest alternative, {closest['route_id']}, the selected route has {cost_position} and {time_position}; "
        f"it also carries {risk_position}. This balance creates a {_money(closest['money_score_delta_kvnd'])} score advantage."
    )
    network = (
        f"The route uses {winner['total_time_h']:.1f} hours of transit with a {winner['delay_probability']:.1%} delay probability and "
        f"{winner['expected_risk_hours']:.1f} expected risk hours. Operationally, this allocation directs demand to the network option "
        f"with the strongest overall efficiency; the primary bottleneck to monitor is delay exposure, especially if service commitments tighten."
    )
    return " ".join([opening, comparison, network])


def generate_scenario_analysis(decision: Dict, is_stable: bool) -> List[str]:
    """Return model-aware recommendations without changing the optimization model."""
    winner = decision["ranking"][0]
    alternatives = decision["ranking"][1:]
    recommendations = []
    if alternatives:
        fastest = min(alternatives, key=lambda route: route["total_time_h"])
        lowest_cost = min(alternatives, key=lambda route: route["total_cost_kvnd"])
        if fastest["total_time_h"] < winner["total_time_h"]:
            recommendations.append(f"If service-level requirements become stricter, reassess {fastest['route_id']}: it is {winner['total_time_h'] - fastest['total_time_h']:.1f} hours faster, although its total score is currently less favorable.")
        if lowest_cost["total_cost_kvnd"] < winner["total_cost_kvnd"]:
            recommendations.append(f"If transportation pricing becomes the dominant objective, {lowest_cost['route_id']} deserves review because its direct cost is {_money(winner['total_cost_kvnd'] - lowest_cost['total_cost_kvnd'])} lower than the selected route.")
    if winner["delay_probability"] >= 0.20:
        recommendations.append("The selected route has material delay exposure; add milestone monitoring or contingency capacity before relying on it for time-critical demand.")
    else:
        recommendations.append("The selected route has comparatively controlled delay exposure, so it is a suitable baseline while demand and carrier conditions remain consistent.")
    recommendations.append("The recommendation is stable across tested time-value assumptions." if is_stable else "The winning route changes across tested time-value assumptions; rerun the decision when the value of delivery speed changes materially.")
    return recommendations[:3]
