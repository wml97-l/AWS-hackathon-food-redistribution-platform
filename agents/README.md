# FoodCloud Agents - Documentation

## 1. Do these Satisfy the Requirements?

**Yes.** The solution consists of two components that directly address your requirements:

### Requirement 1: "Learn preferences of Charity Buying Habits"
- **Solution**: `charity_profiler.py`
- **How it works**: 
    - Analyzes `foodcloud_master_dataset.csv` for **Historic Habits** and **Capacity**.
    - Ingests `requests.csv` to capture **Active Requests** and **Membership Tiers**.
- **Result**: It produces a "Knowledge Base" (`charity_profiles.json`) containing all this intelligence.

### Requirement 2: "Recommend Food to charities based on habits"
- **Solution**: `agent.py` (Recommendation Agent)
- **How it works**: Uses **AWS Bedrock** (via Strands SDK) to act as an intelligent broker.
- **Logic**: It ranks charities using a cascading priority:
    1.  **Active Request Match** (Highest Priority).
    2.  **Membership Tier** (Gold > Silver > Bronze).
    3.  **Historic Preference** (Fallback/Tie-breaker).

---

## 2. Usage & Testing Guide (Local)

### Prerequisites
Run with your local venv:
```bash
# Example syntax
.venv/bin/python script.py
```

### Step 1: Learn Habits (Run Once)
Run the profiler to analyze data and build the profile database.
```bash
python agentic/charity_profiler.py
```
*Check `agentic/charity_profiles.json` to see the learned data.*

### Step 2: Make Recommendations (Run Anytime)
Run the agent with a specific stock query.
```bash
python agentic/agent.py "We have 1500kg of Bananas in Dublin"
```
*The agent will output a JSON recommendation listing the best charities for this specific stock.*

---

## 3. Component Documentation

### Agent 1: The Profiler (`charity_profiler.py`)
- **What it does**: Data Engineering & Analytics. Transforms raw logs + request sheets into structured profiles.
- **Rely on**: `pandas`.
- **How to use**: Run as a batch job whenever new data arrives.

### Agent 2: The Recommender (`agent.py`)
- **What it does**: Decision Support. Uses Claude 3.5 Sonnet to interpret the Profiles and User Query.
- **Rely on**: 
    - `strands` SDK (Framework).
    - `boto3` (AWS Access).
    - `charity_profiles.json` (Knowledge Base).
- **How to use**: Integrate into your WMS/Backend.

### Integration with Bedrock
This solution uses **Amazon Bedrock Runtime**.
- **Model**: `us.anthropic.claude-sonnet-4-5-20250929-v1:0`
- **Mechanism**: **Context Injection**. The agent is "fed" the profiles in its System Prompt context window, allowing it to reason about the entire charity network instantly without fine-tuning.
