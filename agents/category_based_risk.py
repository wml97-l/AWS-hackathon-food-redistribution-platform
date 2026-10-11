import pandas as pd
import os
from datetime import datetime, timedelta
from strands import Agent, tool
from strands.models import BedrockModel

# 1. Initialize the Model
bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
)

# Column mapping for distribution_data.csv (no headers)
COLUMN_NAMES = [
    'line_id', 'category', 'subcategory', 'product_name', 'location',
    'units_in', 'initial_stock_kg', 'units_distributed', 'kg_distributed',
    'final_stock_kg', 'delta_units', 'delta_qty', 'unit_weight', 'value1',
    'value2', 'bestbeforedate', 'flag1', 'days_to_expiry', 'source_name',
    'extra1', 'source_type', 'created_date', 'updated_date'
]

# 2. ENHANCED TOOL: Habits + Scarcity + OVERSTOCK + EXPIRY
@tool
def get_charity_logistics_v2(charity_name: str, expiry_window_days: int = 30):
    """
    Comprehensive search of distribution_data.csv for:
    - Charity Habits: Historical preferences by location.
    - Understock: Items running low.
    - Overstock: Items with excessive inventory (> 2x average stock).
    - Expiry Risk: Items expiring within the specified window.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'distribution_data.csv')

    try:
        df = pd.read_csv(file_path, header=None, names=COLUMN_NAMES, low_memory=False)
        df['product_name'] = df['product_name'].astype(str).fillna('')
        df['location'] = df['location'].astype(str).fillna('')
        df['bestbeforedate'] = pd.to_datetime(df['bestbeforedate'], errors='coerce')
        df['final_stock_kg'] = pd.to_numeric(df['final_stock_kg'], errors='coerce').fillna(0)
    except Exception as e:
        return f"Error loading data: {e}"

    # --- A: HABITS (Search by location or product name) ---
    history = df[df['location'].str.contains(charity_name, case=False, na=False) |
                 df['product_name'].str.contains(charity_name, case=False, na=False)]
    habits = "No history" if history.empty else {
        "preferred_types": history['subcategory'].value_counts().head(3).index.tolist(),
        "frequent_items": history['product_name'].value_counts().head(3).index.tolist()
    }

    # --- B: EXPIRY RISK (Window Check) ---
    today = datetime.now()
    risk_date = today + timedelta(days=expiry_window_days)
    # Find items expiring soon that still have stock
    expiry_risk = df[(df['bestbeforedate'] <= risk_date) & (df['final_stock_kg'] > 0)]
    risk_list = expiry_risk[['product_name', 'final_stock_kg', 'bestbeforedate']].head(5).to_dict(orient='records')

    # --- C: OVERSTOCK & UNDERSTOCK (Using improved category-based method) ---
    stock_levels = calculate_stock_levels_by_category()
    
    return {
        "charity_habits": habits,
        "expiry_risks": risk_list,
        "warehouse_overstock": stock_levels.get("overstock_items", []),
        "warehouse_understock": stock_levels.get("understock_items", [])
    }

# 3. IMPROVED CATEGORY-BASED STOCK ANALYSIS
@tool
def calculate_stock_levels_by_category(overstock_threshold: float = 4.0, understock_threshold: float = 0.25, min_stock_kg: float = 1.0):
    """
    Improved stock level analysis using category-based comparison.
    
    Args:
        overstock_threshold: Ratio to category average to consider overstock (default: 4.0 = 4x average)
        understock_threshold: Ratio to category average to consider understock (default: 0.25 = 25% of average)
        min_stock_kg: Absolute minimum stock level to consider an item as understock (default: 1.0 kg)
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'distribution_data.csv')

    try:
        df = pd.read_csv(file_path, header=None, names=COLUMN_NAMES, low_memory=False)
        df['product_name'] = df['product_name'].astype(str).fillna('')
        df['category'] = df['category'].astype(str).fillna('Unknown')
        df['final_stock_kg'] = pd.to_numeric(df['final_stock_kg'], errors='coerce').fillna(0)
    except Exception as e:
        return {"error": f"Error loading data: {e}"}

    # Group by category and product to get total stock per product
    category_stats = df.groupby(['category', 'product_name'])['final_stock_kg'].sum().reset_index()
    
    # Calculate average stock per category
    category_avg = df.groupby('category')['final_stock_kg'].mean().reset_index()
    category_avg.columns = ['category', 'category_avg_stock']
    
    # Merge product stats with category averages
    merged = pd.merge(category_stats, category_avg, on='category', how='left')
    
    # Calculate ratio of product stock to category average
    merged['ratio_to_category_avg'] = merged['final_stock_kg'] / merged['category_avg_stock']
    
    # Identify overstock items (stock significantly above category average)
    overstock = merged[merged['ratio_to_category_avg'] > overstock_threshold].copy()
    overstock = overstock.sort_values(by='ratio_to_category_avg', ascending=False).head(10)
    
    # Identify understock items (stock significantly below category average OR very low absolute stock)
    understock = merged[(merged['ratio_to_category_avg'] < understock_threshold) | 
                       (merged['final_stock_kg'] < min_stock_kg)].copy()
    understock = understock.sort_values(by='final_stock_kg').head(10)
    
    # Add some statistics for context
    category_summary = {}
    for category in merged['category'].unique():
        cat_data = merged[merged['category'] == category]
        category_summary[category] = {
            'avg_stock_kg': round(cat_data['category_avg_stock'].iloc[0], 2),
            'num_products': len(cat_data),
            'total_stock_kg': round(cat_data['final_stock_kg'].sum(), 2)
        }
    
    return {
        "method": "Category-relative analysis",
        "overstock_threshold": f"{overstock_threshold}x category average",
        "understock_threshold": f"{understock_threshold}x category average",
        "minimum_stock_threshold_kg": min_stock_kg,
        "category_summary": category_summary,
        "overstock_items": overstock.to_dict(orient='records'),
        "understock_items": understock.to_dict(orient='records'),
        "analysis_summary": {
            "total_products_analyzed": len(merged),
            "total_categories": len(category_summary),
            "overstock_items_count": len(overstock),
            "understock_items_count": len(understock)
        }
    }

# 4. STANDALONE OVERSTOCK TOOL
@tool
def get_overstock_items(threshold_multiplier: float = 4.0, limit: int = 10):
    """
    Returns only overstock items from the warehouse using category-based analysis.
    
    Args:
        threshold_multiplier: How many times above category average to consider overstock
        limit: Number of top overstock items to return
    """
    result = calculate_stock_levels_by_category(
        overstock_threshold=threshold_multiplier,
        understock_threshold=0.25,  # Default, not used here
        min_stock_kg=1.0
    )
    
    if "error" in result:
        return result
    
    # Extract just the overstock items with limit applied
    overstock_items = result.get("overstock_items", [])
    limited_overstock = overstock_items[:limit] if limit < len(overstock_items) else overstock_items
    
    return {
        "overstock_items": limited_overstock,
        "overstock_threshold": result.get("overstock_threshold"),
        "analysis_summary": {
            "total_overstock_items": len(overstock_items),
            "items_returned": len(limited_overstock)
        }
    }

# 5. STANDALONE UNDERSTOCK TOOL
@tool
def get_understock_items(threshold_ratio: float = 0.25, min_stock_kg: float = 1.0, limit: int = 10):
    """
    Returns only understock items from the warehouse using category-based analysis.
    
    Args:
        threshold_ratio: Ratio to category average to consider understock
        min_stock_kg: Absolute minimum stock level to flag as understock
        limit: Number of top understock items to return
    """
    result = calculate_stock_levels_by_category(
        overstock_threshold=4.0,  # Default, not used here
        understock_threshold=threshold_ratio,
        min_stock_kg=min_stock_kg
    )
    
    if "error" in result:
        return result
    
    # Extract just the understock items with limit applied
    understock_items = result.get("understock_items", [])
    limited_understock = understock_items[:limit] if limit < len(understock_items) else understock_items
    
    return {
        "understock_items": limited_understock,
        "understock_threshold": f"{threshold_ratio}x category average OR < {min_stock_kg} kg",
        "analysis_summary": {
            "total_understock_items": len(understock_items),
            "items_returned": len(limited_understock)
        }
    }

# 6. ADDITIONAL TOOL: Get stock levels for specific category
@tool
def get_category_stock_levels(category_name: str):
    """
    Get detailed stock analysis for a specific category.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'distribution_data.csv')

    try:
        df = pd.read_csv(file_path, header=None, names=COLUMN_NAMES, low_memory=False)
        df['product_name'] = df['product_name'].astype(str).fillna('')
        df['category'] = df['category'].astype(str).fillna('Unknown')
        df['final_stock_kg'] = pd.to_numeric(df['final_stock_kg'], errors='coerce').fillna(0)
        df['units_distributed'] = pd.to_numeric(df['units_distributed'], errors='coerce').fillna(0)
        df['initial_stock_kg'] = pd.to_numeric(df['initial_stock_kg'], errors='coerce').fillna(0)
    except Exception as e:
        return {"error": f"Error loading data: {e}"}

    # Filter for specific category
    category_df = df[df['category'].str.contains(category_name, case=False, na=False)]
    
    if category_df.empty:
        return {"error": f"Category '{category_name}' not found"}
    
    # Group by product
    product_stats = category_df.groupby('product_name').agg({
        'final_stock_kg': 'sum',
        'units_distributed': 'sum',
        'initial_stock_kg': 'sum'
    }).reset_index()
    
    # Calculate category average
    category_avg = product_stats['final_stock_kg'].mean()
    
    # Calculate ratio to average
    product_stats['ratio_to_avg'] = product_stats['final_stock_kg'] / category_avg
    
    # Identify overstock and understock within this category
    overstock = product_stats[product_stats['ratio_to_avg'] > 4].sort_values(
        by='ratio_to_avg', ascending=False)
    
    understock = product_stats[(product_stats['ratio_to_avg'] < 0.25) | 
                              (product_stats['final_stock_kg'] < 1)].sort_values(
        by='final_stock_kg')
    
    return {
        "category": category_name,
        "category_average_stock_kg": round(category_avg, 2),
        "total_products_in_category": len(product_stats),
        "total_stock_kg": round(product_stats['final_stock_kg'].sum(), 2),
        "overstock_items": overstock.head(5).to_dict(orient='records'),
        "understock_items": understock.head(5).to_dict(orient='records'),
        "all_products": product_stats.sort_values(by='final_stock_kg', ascending=False).to_dict(orient='records')
    }

# 7. UPDATED SYSTEM PROMPT: Waste Prevention Logic
SYSTEM_PROMPT = """
You are the Foodcloud Waste Prevention Agent. 

Your goal is to match donations to charities while preventing food waste.
PRIORITY LOGIC:
1. CRITICAL: Item matches Charity Habit AND is in 'expiry_risks'. (Action: 'IMMEDIATE PUSH')
2. HIGH: Item is in 'expiry_risks' but no habit match. (Action: 'URGENT DONATION')
3. MEDIUM: Item matches Habit AND is in 'warehouse_overstock'. (Action: 'RESERVE LARGE QTY')
4. LOW: Item matches Habit but stock is normal. (Action: 'STANDARD RESERVE')

Return JSON only:
{
    "DECISION": "PUSH / RESERVE / ALERT",
    "URGENCY": "Critical/High/Medium/Low",
    "WASTE_RISK": "Days until expiry or Overstock level",
    "REASONING": "Explain the overlap between charity preference and warehouse risk."
}
"""

# Create agent with all tools
agent = Agent(model=bedrock_model, system_prompt=SYSTEM_PROMPT, 
              tools=[get_charity_logistics_v2, 
                     get_overstock_items, 
                     get_understock_items,
                     get_category_stock_levels])

# 8. FORMATTING FUNCTION - MOVE THIS BEFORE MAIN
def format_charity_decision(result):
    """Takes the JSON result and formats it nicely for console output"""
    
    # Extract the data from JSON
    decision = result.get("DECISION", "UNKNOWN")
    urgency = result.get("URGENCY", "Unknown")
    waste_risk = result.get("WASTE_RISK", "Unknown")
    reasoning = result.get("REASONING", "")
    
    # Clean formatting
    formatted_output = f"""
╔══════════════════════════════════════════════════════════════════╗
║                   FOOD DONATION DECISION                         ║
╠══════════════════════════════════════════════════════════════════╣
║  Decision: {decision:<45} ║
║  Urgency:  {urgency:<45} ║
║  Waste Risk: {waste_risk:<42} ║
╠══════════════════════════════════════════════════════════════════╣
║                         REASONING                                ║
╠══════════════════════════════════════════════════════════════════╣
"""
    
    # Split reasoning into lines and wrap text
    lines = reasoning.split('\n')
    for line in lines:
        # Wrap long lines
        if len(line) > 70:
            words = line.split()
            wrapped_lines = []
            current_line = ""
            for word in words:
                if len(current_line + " " + word) <= 70:
                    current_line += " " + word if current_line else word
                else:
                    wrapped_lines.append(current_line)
                    current_line = word
            wrapped_lines.append(current_line)
            
            for wrapped_line in wrapped_lines:
                formatted_output += f"║  {wrapped_line:<68} ║\n"
        else:
            formatted_output += f"║  {line:<68} ║\n"
    
    formatted_output += "╚══════════════════════════════════════════════════════════════════╝"
    return formatted_output

# 9. IMPROVED EXAMPLE USAGE WITH PROPER FORMATTING
if __name__ == "__main__":
    print("="*80)
    print(" " * 25 + "FOODCLOUD WASTE PREVENTION SYSTEM")
    print("="*80)
    
    # Test 1: Charity Analysis with Beautiful Formatting
    print("\n" + "═"*80)
    print("TEST 1: CHARITY DONATION MATCHING")
    print("═"*80)
    
    print("\n Analyzing: Boyne Valley Group for vegetable donations...")
    
    # Run the agent and capture the result
    agent_response = agent("""
    Charity: 'Boyne Valley Group'
    Incoming Item: vegetables.
    Check if this charity is a good fit, especially if we have an expiry or overstock issue with this product.
    """)
    
    # Format and display the result
    if isinstance(agent_response, dict):
        print(format_charity_decision(agent_response))
    else:
        print("Agent returned non-dict response:", agent_response)
    
    # Test 2: Warehouse Analysis
    print("\n" + "═"*80)
    print("TEST 2: WAREHOUSE INVENTORY ANALYSIS")
    print("═"*80)
    
    print("\n Top Overstock Items:")
    overstock_result = get_overstock_items(threshold_multiplier=4.0, limit=5)
    if isinstance(overstock_result, dict) and "overstock_items" in overstock_result:
        for i, item in enumerate(overstock_result["overstock_items"], 1):
            product = item.get("product_name", "Unknown")
            stock = item.get("final_stock_kg", 0)
            ratio = item.get("ratio_to_category_avg", 0)
            print(f"  {i}. {product}: {stock:,.0f} kg ({ratio:.1f}x category average)")
    else:
        print("  No overstock items found or error occurred")
    
    print("\n Top Understock Items:")
    understock_result = get_understock_items(threshold_ratio=0.25, min_stock_kg=1.0, limit=5)
    if isinstance(understock_result, dict) and "understock_items" in understock_result:
        for i, item in enumerate(understock_result["understock_items"], 1):
            product = item.get("product_name", "Unknown")
            stock = item.get("final_stock_kg", 0)
            ratio = item.get("ratio_to_category_avg", 0)
            print(f"  {i}. {product}: {stock:,.2f} kg ({ratio:.2f}x category average)")
    else:
        print("  No understock items found or error occurred")
    
    print("\n" + "="*80)
    print(" " * 30 + "ANALYSIS COMPLETE ")
    print("="*80)
