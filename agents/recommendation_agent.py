from strands import Agent
from strands.models import BedrockModel
import json
import os

# Load Charity Profiles
PROFILES_PATH = "charity_profiles.json"
try:
    with open(PROFILES_PATH, 'r') as f:
        CHARITY_PROFILES = f.read()
except FileNotFoundError:
    print(f"Error: {PROFILES_PATH} not found. Please run charity_profiler.py first.")
    exit(1)

# Initialize Bedrock Model
# Note: Ensure AWS credentials are set in your environment
bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-3-5-sonnet-20240620-v1:0", # Updating to a likely valid model ID for 3.5 Sonnet
    region_name="us-east-1"
)

# Define System Prompt with Context Injection
SYSTEM_PROMPT = f"""
You are an intelligent Distribution Assistant for FoodCloud.
Your goal is to recommend the best charity to receive a specific donation based on their location, historic preferences, and order size.

You have access to the following Charity Profiles (JSON format):
<charity_profiles>
{CHARITY_PROFILES}
</charity_profiles>

INSTRUCTIONS:
1. Receive an input describing the stock available (Category, Quantity, Location).
2. Filter charities that match the stock's Location (DUBLIN, CORK, or GALWAY).
3. From those, rank charities based on:
    - **Preference Match**: Does the charity explicitly prefer this category?
    - **Capacity**: Is the quantity similar to their 'avg_order_kg'? (Avoid sending 1000kg to a charity that averages 5kg).
4. Output your recommendation in STRICT JSON format:
{{
    "recommended_charities": [
        {{
            "name": "Charity Name",
            "reason": "Concise reason why they are a good match (e.g., 'Matches preference for DAIRY in DUBLIN').",
            "score": "High"
        }},
        ... (top 3)
    ]
}}
Do NOT output any conversational text outside the JSON.
"""

# Create Agent
agent = Agent(
    model=bedrock_model,
    system_prompt=SYSTEM_PROMPT
)

def run_agent_interactive():
    print("--- FoodCloud Recommendation Agent ---")
    print("Enter stock details (e.g., '200kg of Yoghurt in Dublin') or 'q' to quit.")
    
    while True:
        user_input = input("\n> ")
        if user_input.lower() in ['q', 'quit', 'exit']:
            break
            
        try:
            response = agent(user_input)
            print("\nRecommendation:")
            print(response)
        except Exception as e:
            print(f"Error invoking agent: {e}")

if __name__ == "__main__":
    run_agent_interactive()
