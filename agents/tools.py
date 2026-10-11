from strands import tool
import json
import os

# Load charity profiles
current_dir = os.path.dirname(os.path.abspath(__file__))
PROFILES_PATH = os.path.join(current_dir, "charity_profiles.json")

def _load_profiles():
    """Load charity profiles from JSON file."""
    try:
        with open(PROFILES_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

@tool
def get_charities_by_location(location: str) -> str:
    """Get charities filtered by location.

    Args:
        location: The location to filter by (DUBLIN, CORK, or GALWAY)

    Returns:
        JSON string with matching charities and their details
    """
    profiles = _load_profiles()
    location_upper = location.upper()

    matches = {
        name: data for name, data in profiles.items()
        if data.get('location', '').upper() == location_upper
    }

    if not matches:
        return json.dumps({"message": f"No charities found in {location}", "charities": []})

    # Return summary of matches
    summary = []
    for name, data in matches.items():
        summary.append({
            "name": name,
            "tier": data.get('membership_tier', 'Bronze'),
            "avg_order_kg": data.get('avg_order_kg', 0),
            "preferences": data.get('preferences', []),
            "has_active_requests": len(data.get('active_requests', [])) > 0
        })

    return json.dumps({"location": location_upper, "count": len(summary), "charities": summary}, indent=2)


@tool
def get_active_requests(category: str = None) -> str:
    """Get active charity requests, optionally filtered by category.

    Args:
        category: Optional category to filter by (e.g., DAIRY, TINNED, DRINKS, SMD, OTHER FOOD)

    Returns:
        JSON string with active requests
    """
    profiles = _load_profiles()

    all_requests = []
    for charity_name, data in profiles.items():
        for req in data.get('active_requests', []):
            req_entry = {
                "charity_name": charity_name,
                "location": data.get('location', 'Unknown'),
                "tier": data.get('membership_tier', 'Bronze'),
                "category": req.get('category'),
                "quantity_kg": req.get('quantity'),
                "date": req.get('date')
            }

            if category:
                if req.get('category', '').upper() == category.upper():
                    all_requests.append(req_entry)
            else:
                all_requests.append(req_entry)

    if not all_requests:
        msg = f"No active requests found" + (f" for category {category}" if category else "")
        return json.dumps({"message": msg, "requests": []})

    return json.dumps({"count": len(all_requests), "requests": all_requests}, indent=2)


@tool
def get_charity_details(charity_name: str) -> str:
    """Get detailed profile for a specific charity.

    Args:
        charity_name: The name of the charity to look up (partial match supported)

    Returns:
        JSON string with charity details
    """
    profiles = _load_profiles()

    # Try exact match first
    if charity_name in profiles:
        return json.dumps({charity_name: profiles[charity_name]}, indent=2)

    # Try partial match (case-insensitive)
    matches = {
        name: data for name, data in profiles.items()
        if charity_name.lower() in name.lower()
    }

    if not matches:
        return json.dumps({"error": f"No charity found matching '{charity_name}'"})

    return json.dumps(matches, indent=2)


@tool
def search_charities(category: str = None, location: str = None, min_capacity_kg: float = None) -> str:
    """Search for charities matching multiple criteria.

    Args:
        category: Optional food category preference (e.g., DAIRY, TINNED, DRINKS)
        location: Optional location filter (DUBLIN, CORK, GALWAY)
        min_capacity_kg: Optional minimum average order capacity in kg

    Returns:
        JSON string with matching charities ranked by relevance
    """
    profiles = _load_profiles()

    results = []
    for name, data in profiles.items():
        score = 0
        reasons = []

        # Location filter
        if location:
            if data.get('location', '').upper() != location.upper():
                continue
            score += 10
            reasons.append(f"Located in {location}")

        # Category preference match
        if category:
            prefs = [p.upper() for p in data.get('preferences', [])]
            if category.upper() in prefs:
                score += 20
                reasons.append(f"Prefers {category}")

            # Check active requests
            for req in data.get('active_requests', []):
                if req.get('category', '').upper() == category.upper():
                    score += 30
                    reasons.append(f"Has active request for {category}")
                    break

        # Capacity check
        if min_capacity_kg:
            avg_order = data.get('avg_order_kg', 0)
            if avg_order >= min_capacity_kg:
                score += 10
                reasons.append(f"Can handle {avg_order}kg orders")
            elif avg_order < min_capacity_kg * 0.5:
                continue  # Skip if way under capacity

        # Tier bonus
        tier = data.get('membership_tier', 'Bronze')
        tier_scores = {'Gold': 15, 'Silver': 10, 'Bronze': 5}
        score += tier_scores.get(tier, 0)
        reasons.append(f"{tier} member")

        if score > 0:
            results.append({
                "name": name,
                "score": score,
                "tier": tier,
                "location": data.get('location'),
                "avg_order_kg": data.get('avg_order_kg', 0),
                "reasons": reasons
            })

    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)

    return json.dumps({"count": len(results), "matches": results[:10]}, indent=2)
