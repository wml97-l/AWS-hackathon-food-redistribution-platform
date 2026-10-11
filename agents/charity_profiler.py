import pandas as pd
import json
import os

# Define paths
DATA_PATH = "/Users/nickvishnoi/Documents/AWS Hackathon/Datasets/foodcloud_master_dataset.csv"
OUTPUT_PATH = "/Users/nickvishnoi/Documents/AWS Hackathon/agentic/charity_profiles.json"

def clean_category(cat):
    """Clean category strings to remove prefixes like 'Ambient - '"""
    if pd.isna(cat):
        return "Unknown"
    # Common prefixes to remove based on EDA
    prefixes = ["Ambient - ", "Chilled - ", "Frozen - ", "ESF - ", "SMD "]
    cleaned = str(cat)
    for p in prefixes:
        cleaned = cleaned.replace(p, "").replace(p.upper(), "")
    return cleaned.strip()

def main():
    print(f"Loading data from {DATA_PATH}...")
    try:
        df = pd.read_csv(DATA_PATH)
    except FileNotFoundError:
        print("Error: Dataset not found.")
        return

    # Basic cleaning
    # Ensure relevant columns exist
    required_cols = ['charity_name', 'location', 'category', 'food_distributed_kg']
    for col in required_cols:
        if col not in df.columns:
            print(f"Error: Missing column {col}")
            return

    print("Grouping by Charity and Category...")
    
    # 1. Location Mapping (Most frequent location per charity)
    charity_locations = df.groupby('charity_name')['location'].agg(lambda x: x.mode()[0] if not x.mode().empty else "Unknown")
    
    # 2. Preferences (Top categories by volume)
    # Filter for distributed items only (where they actually took the food)
    distributed_df = df[df['food_distributed_kg'] > 0].copy()
    
    # Clean categories
    distributed_df['clean_cat'] = distributed_df['category'].apply(clean_category)
    
    # Aggegrate volume per charity-category
    cat_volumes = distributed_df.groupby(['charity_name', 'clean_cat'])['food_distributed_kg'].sum().reset_index()
    
    # Sort and pick top 5
    top_cats = cat_volumes.sort_values(['charity_name', 'food_distributed_kg'], ascending=[True, False])
    top_cats_grouped = top_cats.groupby('charity_name').head(5)
    
    # 3. Average Order Size
    avg_order = distributed_df.groupby('charity_name')['food_distributed_kg'].mean()
    
    # 4. Load Active Requests & Tiers
    requests_path = "/Users/nickvishnoi/Documents/AWS Hackathon/Datasets/requests.csv"
    active_requests_map = {}
    membership_map = {}
    
    print(f"Loading requests from {requests_path}...")
    try:
        req_df = pd.read_csv(requests_path)
        # Create a dictionary for quick lookup of active requests per charity
        # Structure: { "Charity Name": [ {"category": "DAIRY", "quantity": 50, "date": "..."} ] }
        for _, row in req_df.iterrows():
            c_name = row['charity_name']
            if c_name not in active_requests_map:
                active_requests_map[c_name] = []
            
            active_requests_map[c_name].append({
                "category": row['requested_category'],
                "quantity": float(row['quantity_kg']),
                "date": row['request_date']
            })
            
            # Update membership tier (assume latest row is source of truth or just take any)
            membership_map[c_name] = row['membership_tier']
            
    except FileNotFoundError:
        print(f"Warning: {requests_path} not found. Proceeding without active requests.")
    except Exception as e:
        print(f"Warning: Error reading requests.csv: {e}")

    # Construct JSON structure
    profiles = {}
    
    all_charities = df['charity_name'].unique()
    
    print(f"Building profiles for {len(all_charities)} charities...")
    
    for charity in all_charities:
        if pd.isna(charity):
            continue
            
        # Get location
        loc = charity_locations.get(charity, "Unknown")
        
        # Get top preferences
        charity_cats = top_cats_grouped[top_cats_grouped['charity_name'] == charity]
        preferences = charity_cats['clean_cat'].tolist()
        
        # Get avg order
        avg_kg = avg_order.get(charity, 0.0)
        
        # Get Membership Tier (Default: Bronze)
        tier = membership_map.get(charity, "Bronze")
        
        # Get Active Requests
        active_reqs = active_requests_map.get(charity, [])
        
        profiles[charity] = {
            "location": loc,
            "membership_tier": tier,
            "active_requests": active_reqs,
            "preferences": preferences,
            "avg_order_kg": round(float(avg_kg), 2)
        }
        
    # Save to file
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(profiles, f, indent=4)
        
    print(f"Successfully saved profiles to {OUTPUT_PATH}")
    print("Sample Profile (SVP Dublin):")
    # Quick debug print if key exists, else print first key
    sample_key = next((k for k in profiles.keys() if "SVP" in k and "Dublin" in k), None)
    if not sample_key and profiles:
        sample_key = list(profiles.keys())[0]
        
    if sample_key:
        print(f"{sample_key}: {json.dumps(profiles[sample_key], indent=2)}")

if __name__ == "__main__":
    main()
