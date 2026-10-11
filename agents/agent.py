from strands import Agent
from strands.models import BedrockModel
import os
import sys
import json

# Import tools
from tools import (
    get_charities_by_location,
    get_active_requests,
    get_charity_details,
    search_charities
)

# Initialize Bedrock Model
bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    region_name="us-west-2"
)

# System Prompt with iterative behavior instructions
SYSTEM_PROMPT = """
You are an intelligent Distribution Assistant for FoodCloud's MealMap Intelligence system.
Your goal is to help users find the best charity matches for food donations and answer questions about charity needs.

## Available Tools
You have access to tools to query charity data:
- get_charities_by_location: Find charities in a specific location
- get_active_requests: Find active charity requests (optionally by category)
- get_charity_details: Get detailed info about a specific charity
- search_charities: Search with multiple criteria (category, location, capacity)

## Behavior Guidelines

1. **Use Tools First**: Always use tools to gather real data before answering. Don't rely on assumptions.

2. **Ask for Clarification**: If the user's query is ambiguous, ask a clarifying question.
   Examples of when to ask:
   - "Find matches for food" -> Ask: What type of food? What location?
   - "Help with a donation" -> Ask: What category? What quantity? What location?

3. **Self-Assess Completeness**: After forming an answer, verify it addresses the question fully.
   - Did you provide specific charity names?
   - Did you explain why they're good matches?
   - Did you address all parts of the query?

4. **Response Format**: Always respond with valid JSON in this structure:

For complete answers:
{
    "status": "complete",
    "recommended_charities": [
        {
            "name": "Charity Name",
            "tier": "Gold/Silver/Bronze",
            "reason": "Why they're a good match",
            "score": "Critical/High/Medium/Low"
        }
    ],
    "summary": "Brief summary of findings"
}

For clarification needed:
{
    "status": "needs_clarification",
    "question": "Your clarifying question here",
    "options": ["Option 1", "Option 2"],
    "context": "Why you need this information"
}

## Priority Logic for Recommendations
1. **PRIORITY 1**: Active Request Match - Charity has an active request for this category
2. **PRIORITY 2**: Membership Tier - Gold > Silver > Bronze
3. **PRIORITY 3**: Historic Preference - Category in their preferences list
4. **PRIORITY 4**: Capacity Match - Quantity aligns with their avg_order_kg

Always use tools to verify data before making recommendations.
"""

# Create Agent with tools
_agent = Agent(
    model=bedrock_model,
    system_prompt=SYSTEM_PROMPT,
    tools=[get_charities_by_location, get_active_requests, get_charity_details, search_charities]
)

# Store conversation history per session
_conversations = {}


def agent(query: str, session_id: str = None, history: list = None, action: str = "query") -> dict:
    """
    Query the agent with optional conversation history for multi-turn interactions.

    Args:
        query: The user's question or input
        session_id: Optional session identifier for conversation continuity
        history: Optional list of previous messages
        action: The type of action - 'query', 'refine', or 'clarify'

    Returns:
        dict with response data including status and content
    """
    # Build context from history if provided
    context_prompt = query

    if action == "refine" and history:
        context_prompt = f"""The user wants more detail on the previous response.
Previous context: {json.dumps(history[-2:]) if len(history) >= 2 else ''}
User request: {query}

Please provide a more detailed analysis using the tools available."""

    elif action == "clarify" and history:
        context_prompt = f"""The user is responding to your clarifying question.
Previous context: {json.dumps(history[-2:]) if len(history) >= 2 else ''}
User's clarification: {query}

Now provide a complete answer using this new information."""

    try:
        result = _agent(context_prompt)
        response_text = str(result) if result else ""

        # Try to parse as JSON
        try:
            clean_response = response_text.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]
            if clean_response.startswith('```'):
                clean_response = clean_response[3:]
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]
            clean_response = clean_response.strip()

            parsed = json.loads(clean_response)

            # Ensure status field exists
            if 'status' not in parsed:
                parsed['status'] = 'complete'

            return parsed

        except json.JSONDecodeError:
            # If not valid JSON, wrap in standard format
            return {
                "status": "complete",
                "text_response": response_text,
                "recommended_charities": []
            }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "recommended_charities": []
        }


def main():
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "We have 100kg of Bananas available in Dublin."

    print(f"Query: {query}")
    print("Thinking...")
    try:
        response = agent(query)
        print(json.dumps(response, indent=2))
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
