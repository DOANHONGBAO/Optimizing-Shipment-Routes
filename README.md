# Intelligent Shipment Route Recommendation Engine

An intelligent **chat-based logistics assistant** that recommends the optimal shipment route from uploaded CSV files. Users simply upload their shipment data in the chat window, and the system automatically analyzes every candidate route, ranks them using a deterministic scoring model, and recommends the best option with a human-readable explanation.

Unlike AI-powered decision systems, **the routing decision is entirely deterministic** and implemented with Python and pandas, ensuring every recommendation is reproducible, transparent, and explainable.

---

## ✨ Features

- 💬 Chat-based interaction
- 📂 Upload CSV datasets directly through the chat interface
- 🚚 Automatic route recommendation for every shipment
- 💰 Cost-aware Money Score evaluation
- 📊 Route comparison table
- 🌍 Interactive shipment map
- 📝 Natural language explanation of every recommendation
- 📈 What-if sensitivity analysis
- 📥 Export recommendation results as CSV and JSON
- ⚡ No GPU required
- 🔒 No API Key required

---

# Project Structure

```
safiri-app/
│
├── app.py
├── decision_engine.py
├── explainer.py
├── sensitivity.py
├── data_loader.py
├── requirements.txt
├── sample_data/
├── tests/
└── README.md
```

---

# Installation

## Clone the repository

```bash
git clone <repository-url>
cd safiri-app
```

---

## Create a Conda Environment

```bash
conda create -n safiri python=3.11
conda activate safiri
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

## Run the Application

```bash
streamlit run app.py
```

The application will be available at

```
http://localhost:8501
```

---

# Testing the System

There are **two ways** to evaluate the application.

---

## Option 1 — Demo Mode (Recommended)

Simply type

```
demo
```

into the chat box.

The application will automatically generate realistic logistics data and perform the complete optimization workflow.

This mode is ideal for quickly demonstrating the system without preparing datasets.

---

## Option 2 — Upload Your Own Dataset

Upload

```
shipments.csv
routes.csv
```

Optionally

```
legs.csv
```

The system automatically:

- validates the datasets
- computes Money Score
- ranks all candidate routes
- selects the optimal route
- generates explanations
- performs sensitivity analysis

No parameters need to be configured manually.

---

# Running Unit Tests

```bash
pytest tests -v
```

The tests verify

- dataset validation
- Money Score calculation
- ranking correctness
- decision generation
- explanation generation
- sensitivity analysis

---

# Input Dataset

## shipments.csv

| Column | Description |
|----------|-------------|
| shipment_id | Shipment identifier |
| origin | Origin location |
| destination | Destination location |

---

## routes.csv

| Column | Description |
|----------|-------------|
| route_id | Route identifier |
| shipment_id | Shipment identifier |
| archetype | Transportation mode |
| total_cost_kvnd | Transportation cost |
| total_time_h | Total travel time |
| delay_probability | Probability of delay |
| expected_risk_hours | Expected disruption hours |
| driver_score | Driver reliability score |

---

## legs.csv (Optional)

Provides detailed information for every transportation segment.

```
leg_id
route_id
from
to
mode
cost_kvnd
time_h
delay_probability
risk_extra_h
```

---

# Decision Engine

Every candidate route is converted into a unified **Money Score**, allowing different factors to be compared using the same monetary unit.

The optimization objective is

```
Minimize Money Score
```

where

```
Money Score =
Transportation Cost
+ Value of Time × Travel Time
+ Value of Time × Delay Probability × Delay Hours
+ Value of Time × Expected Risk Hours
+ Driver Penalty × (1 − Driver Score)
```

The route with the **lowest Money Score** is selected as the recommendation.

Unlike machine learning models, this scoring mechanism is fully deterministic and always produces identical results for identical inputs.

---

# Recommendation Workflow

```
Upload Dataset
        │
        ▼
Validate CSV Files
        │
        ▼
Compute Money Score
        │
        ▼
Rank Candidate Routes
        │
        ▼
Select Best Route
        │
        ▼
Sensitivity Analysis
        │
        ▼
Generate Explanation
        │
        ▼
Display Recommendation
```

---

# Explanation Module

The explanation is intentionally separated from the optimization engine.

The recommendation is generated first.

Only after the optimal route has been selected does the explanation module summarize **why** that route was preferred.

The explanation discusses:

- transportation cost
- travel time
- delay risk
- driver reliability
- trade-offs among candidate routes
- overall logistics efficiency

This separation guarantees that explanations never influence the optimization result.

---

# Sensitivity Analysis

To evaluate the robustness of each recommendation, the system automatically performs sensitivity analysis by varying the **Value of Time (VoT)** parameter.

The application checks whether the recommended route remains optimal when transportation time becomes more or less important.

Possible outcomes include:

- ✅ Recommendation remains unchanged under all tested scenarios.
- ⚠️ Recommendation changes when travel time becomes significantly more valuable.
- ⚠️ Lower transportation cost may become preferable if time importance decreases.

This analysis helps users understand how stable the recommendation is under changing business priorities.

---

# User Interface

The dashboard provides:

- Shipment summary
- Recommendation overview
- Route ranking table
- Interactive transportation map
- Optimization explanation
- Scenario analysis
- Download buttons for CSV and JSON outputs

Everything is accessible directly from the chat interface.

---

# Demonstration

A complete demonstration of the system is available in the accompanying video.

The demo covers

1. Launching the application
2. Running Demo Mode
3. Uploading custom datasets
4. Route recommendation
5. Money Score calculation
6. Explanation generation
7. Sensitivity analysis
8. Exporting recommendation results

> 📹 **Demo Video:** *(Add your video link here)*

---

# Technologies

- Python
- Streamlit
- Pandas
- NumPy
- Plotly

---

# Future Improvements

Potential future extensions include

- Large Language Model explanations
- Multi-objective optimization
- Carbon emission optimization
- Vehicle capacity constraints
- Live traffic integration
- Dynamic shipment scheduling
- Reinforcement Learning-based routing

---

# License

This project was developed as part of the **SAFiRi AI Technical Assessment**.