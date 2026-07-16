# 🚚 SAFiRi AI — Route Recommendation Chatbot

**Chat with your logistics data — the bot picks the optimal route and explains why.**

## 📖 Overview

**SAFiRi AI** is a chat-based assistant that recommends the **optimal shipping route** from CSV data. Just attach your files in the chat box — the bot automatically computes a monetized **Money Score** for every candidate route, selects the best one for each shipment, and replies with a comparison table plus a plain-language explanation of exactly where the chosen route **wins** (cost, time, delay risk, driver reliability).

The routing decision runs entirely on **pure Python/pandas** — deterministic, 100% reproducible, no black box, no GPU, no API key required.

## 🎬 Demo

📹 **Demo video:** [zzz](zzz)

## ⚙️ Environment Setup

```bash
git clone <repository-url>
cd safiri-app

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

| Component | Requirement |
|---|---|
| Python | ≥ 3.9 (3.10–3.12 recommended) |
| streamlit | ≥ 1.43 |
| pandas | ≥ 2.0 |
| numpy | ≥ 1.24 |
| plotly | ≥ 5.20 |

**Run the app:**

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

## 📂 Test Data

Sample dataset for testing: [xxx](xxx)

Don't have data on hand? Type **`demo`** in the chat box and the bot will generate synthetic data and answer right away.

## 💬 How to Use

1. Open the app — the bot greets you and asks for a file.
2. Attach `shipments.csv` + `routes.csv` (optionally `legs.csv`) to the chat input and send.
3. The bot automatically replies with:
   - A summary table of the recommended route for every shipment
   - A detailed ranking table + comparison chart for each shipment
   - A plain-language explanation, plus a stability check on the recommendation
   - Download buttons for the results (CSV / JSON)

Nothing to configure — everything runs automatically.

<details>
<summary><b>📋 Input data schema</b></summary>

**shipments.csv**: `shipment_id, origin, destination`

**routes.csv**: `route_id, shipment_id, archetype, total_cost_kvnd, total_time_h, delay_probability, expected_risk_hours, driver_score`

**legs.csv** *(optional)*: `leg_id, route_id, from, to, mode, cost_kvnd, time_h, delay_probability, risk_extra_h`

</details>

## 🧪 Unit Tests

```bash
pytest tests/ -v
```

## 🚀 Deploy to Streamlit Community Cloud

Push the repo to GitHub → [share.streamlit.io](https://share.streamlit.io) → **New app** → select the repo, branch `main`, main file `app.py` → **Deploy**. No secrets or API keys needed.

---

*Built as part of the **SAFiRi AI Technical Assessment**.*