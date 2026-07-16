from __future__ import annotations

import json

import pandas as pd
import streamlit as st

import data_utils
import decision_engine as engine
import sensitivity as sens
from explainer import generate_scenario_analysis, generate_template_explanation


st.set_page_config(page_title="OpS4f1R1", page_icon="", layout="centered")

if "messages" not in st.session_state:
    st.session_state.messages = []


def _classify_files(files):
    found = {"shipments": None, "routes": None, "legs": None}
    for file in files:
        filename = file.name.lower()
        if "leg" in filename:
            found["legs"] = file
        elif "route" in filename:
            found["routes"] = file
        elif "shipment" in filename:
            found["shipments"] = file
    return found


def _build_answer(shipments_df: pd.DataFrame, routes_df: pd.DataFrame, legs_df: pd.DataFrame):
    validation_report = data_utils.validate_data(shipments_df, routes_df, legs_df)
    shipment_details, summary_rows = [], []
    for shipment_id in shipments_df["shipment_id"]:
        if not (routes_df["shipment_id"] == shipment_id).any():
            continue
        ranked = engine.rank_routes(routes_df, shipment_id)
        decision = engine.build_decision_json(shipments_df, routes_df, shipment_id)
        stable = not bool(sens.run_sensitivity_analysis(routes_df, shipment_id)["winner_changed"].any())
        winner = ranked.iloc[0]
        summary_rows.append({
            "shipment_id": shipment_id,
            "selected_route": winner["route_id"],
            "money_score_kvnd": winner["calculated_money_score"],
            "candidate_routes": len(ranked),
            "stable_across_vot": stable,
        })
        shipment_details.append({
            "shipment_id": shipment_id,
            "ranked": ranked,
            "decision": decision,
            "explanation": generate_template_explanation(decision),
            "scenario_analysis": generate_scenario_analysis(decision, stable),
        })
    return validation_report, pd.DataFrame(summary_rows), shipment_details


def _render_answer(payload: dict, key_prefix: str):
    summary, details = payload["summary_df"], payload["shipment_details"]
    warnings = [message for status, message in payload["validation_report"] if status != "ok"]
    if warnings:
        with st.expander("Data notes"):
            for warning in warnings:
                st.warning(warning)
    if summary.empty:
        st.write("No eligible shipment routes were found.")
        return

    st.write(f"I reviewed {len(summary)} shipment{'s' if len(summary) != 1 else ''}. Here is the recommendation for each one.")
    for index, detail in enumerate(details):
        decision = detail["decision"]
        winner = detail["ranked"].iloc[0]
        with st.expander(f"{detail['shipment_id']} | {decision['origin']} to {decision['destination']}", expanded=index == 0):
            st.markdown(f"**Recommended route: {winner['route_id']}**")
            st.write(detail["explanation"])
            st.markdown("**Scenario analysis**")
            for recommendation in detail["scenario_analysis"]:
                st.write(f"- {recommendation}")
            st.download_button(
                "Download decision",
                json.dumps(decision, indent=2, default=str),
                f"{detail['shipment_id']}_decision.json",
                "application/json",
                key=f"{key_prefix}_{detail['shipment_id']}",
            )


st.markdown("""
<style>
    .stApp { background: #F6F8FC; color: #172033; }
    .block-container { max-width: 860px; padding-top: 2.25rem; padding-bottom: 7rem; }
    h1 { font-size: 1.65rem !important; letter-spacing: -.03em; margin-bottom: 2rem !important; }
    [data-testid="stChatMessage"] { border: 1px solid #E6EAF0; border-radius: 16px; background: #FFFFFF; padding: .5rem .7rem; margin-bottom: 1rem; box-shadow: 0 2px 12px rgba(27, 39, 68, .035); }
    [data-testid="stExpander"] { border: 1px solid #E6EAF0; border-radius: 11px; background: #FBFCFE; margin-top: .75rem; }
    [data-testid="stExpander"] details summary { color: #26334C; font-weight: 650; }
    [data-testid="stChatInput"] { border-radius: 14px; box-shadow: 0 -4px 22px rgba(27, 39, 68, .07); }
    .stDownloadButton button { border-radius: 8px; color: #186F65; border-color: #9DD8D1; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

st.title("OpS4f1R1")

for index, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        if message["kind"] == "answer":
            _render_answer(message["payload"], f"history_{index}")
        elif message["role"] == "user":
            st.write(message["payload"])
        else:
            st.error(message["payload"])

prompt = st.chat_input("Attach files or enter 'demo'...", accept_file="multiple", file_type=["csv"])
if prompt:
    text = (prompt.text or "").strip()
    files = list(prompt.files) if prompt.files else []
    user_note = ", ".join(file.name for file in files) if files else (text or "demo")
    try:
        if files:
            classified = _classify_files(files)
            if not classified["shipments"] or not classified["routes"]:
                raise ValueError("Please attach both a shipments CSV and a routes CSV.")
            shipments_df, routes_df, legs_df = data_utils.load_csvs(classified["shipments"], classified["routes"], classified["legs"])
        elif text.lower() in {"demo", "sample", "demo data"}:
            shipments_df, routes_df, legs_df = data_utils.generate_sample_data(n_shipments=6)
        else:
            raise ValueError("Attach shipment and route CSV files, or enter demo.")
        report, summary, details = _build_answer(shipments_df, routes_df, legs_df)
        st.session_state.messages = [
            {"role": "user", "kind": "text", "payload": user_note},
            {"role": "assistant", "kind": "answer", "payload": {"validation_report": report, "summary_df": summary, "shipment_details": details}},
        ]
    except Exception as error:
        st.session_state.messages = [
            {"role": "user", "kind": "text", "payload": user_note},
            {"role": "assistant", "kind": "text", "payload": f"Unable to process the request: {error}"},
        ]
    st.rerun()
