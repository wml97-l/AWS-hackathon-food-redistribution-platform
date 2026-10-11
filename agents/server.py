from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import json
import uuid
import csv
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Path to distribution data CSV
DISTRIBUTION_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'distribution_data.csv')

# Cache for distribution stats
_distribution_stats_cache = None

# Cache for stock alerts
_stock_alerts_cache = None

from agent import agent
from category_based_risk import (
    agent as risk_agent,
    get_overstock_items,
    get_understock_items,
    get_category_stock_levels,
    calculate_stock_levels_by_category
)

app = Flask(__name__)
CORS(app)

# Session storage for conversation history
sessions = {}


@app.route('/api/ask', methods=['POST'])
def ask_agent():
    data = request.json
    if not data or 'query' not in data:
        return jsonify({'error': 'No query provided'}), 400

    query = data['query']
    session_id = data.get('session_id') or str(uuid.uuid4())
    action = data.get('action', 'query')  # 'query', 'refine', or 'clarify'

    print(f"[Session {session_id[:8]}] Action: {action}, Query: {query}")

    # Get or create conversation history
    if session_id not in sessions:
        sessions[session_id] = []

    history = sessions[session_id]

    try:
        # Call agent with history and action
        response = agent(query, session_id=session_id, history=history, action=action)

        # Store this exchange in history
        history.append({
            "role": "user",
            "content": query,
            "action": action
        })
        history.append({
            "role": "assistant",
            "content": response
        })

        # Keep history bounded (last 10 exchanges)
        if len(history) > 20:
            sessions[session_id] = history[-20:]

        # Build response based on status
        result = {
            'session_id': session_id,
            'status': response.get('status', 'complete')
        }

        if response.get('status') == 'needs_clarification':
            result['question'] = response.get('question', '')
            result['options'] = response.get('options', [])
            result['context'] = response.get('context', '')
        elif response.get('recommended_charities'):
            result['recommended_charities'] = response['recommended_charities']
            result['summary'] = response.get('summary', '')
        elif response.get('text_response'):
            result['text_response'] = response['text_response']
        elif response.get('error'):
            result['error'] = response['error']
            result['status'] = 'error'
        else:
            result['text_response'] = str(response)

        return jsonify(result)

    except Exception as e:
        print(f"Error processing query: {e}")
        return jsonify({
            'session_id': session_id,
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/session/<session_id>', methods=['DELETE'])
def clear_session(session_id):
    """Clear a conversation session."""
    if session_id in sessions:
        del sessions[session_id]
        return jsonify({'message': 'Session cleared'})
    return jsonify({'message': 'Session not found'}), 404


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})


def compute_distribution_stats():
    """Compute statistics from the distribution CSV file."""
    global _distribution_stats_cache
    if _distribution_stats_cache:
        return _distribution_stats_cache

    location_stats = defaultdict(lambda: {'records': 0, 'kg_in': 0, 'kg_out': 0})
    category_stats = defaultdict(lambda: {'records': 0, 'kg_in': 0, 'kg_out': 0})
    source_stats = defaultdict(lambda: {'records': 0, 'kg_out': 0})
    monthly_stats = defaultdict(lambda: {'kg_in': 0, 'kg_out': 0})

    total_records = 0
    total_kg_in = 0
    total_kg_out = 0

    valid_locations = {'DUBLIN', 'CORK', 'GALWAY'}

    try:
        with open(DISTRIBUTION_CSV, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 23:
                    continue

                total_records += 1

                category = row[1] if row[1] else 'Unknown'
                location = row[4] if row[4] in valid_locations else None

                try:
                    kg_in = float(row[6]) if row[6] and row[6] != 'nan' else 0
                    kg_out = float(row[8]) if row[8] and row[8] != 'nan' else 0
                except ValueError:
                    kg_in = 0
                    kg_out = 0

                total_kg_in += kg_in
                total_kg_out += kg_out

                # Location stats
                if location:
                    location_stats[location]['records'] += 1
                    location_stats[location]['kg_in'] += kg_in
                    location_stats[location]['kg_out'] += kg_out

                # Category stats
                category_stats[category]['records'] += 1
                category_stats[category]['kg_in'] += kg_in
                category_stats[category]['kg_out'] += kg_out

                # Source stats
                source = row[20].strip() if len(row) > 20 and row[20] else 'Unknown'
                if source and source != 'nan':
                    source_stats[source]['records'] += 1
                    source_stats[source]['kg_out'] += kg_out

                # Monthly stats (from column 22 - transaction date)
                try:
                    date_str = row[21] if len(row) > 21 else ''
                    if date_str and '2024' in date_str:
                        month = date_str[:7]  # Extract YYYY-MM
                        monthly_stats[month]['kg_in'] += kg_in
                        monthly_stats[month]['kg_out'] += kg_out
                except:
                    pass

        # Sort and limit results
        top_categories = sorted(
            [{'name': k, **v} for k, v in category_stats.items()],
            key=lambda x: x['records'],
            reverse=True
        )[:10]

        top_sources = sorted(
            [{'name': k, **v} for k, v in source_stats.items()],
            key=lambda x: x['records'],
            reverse=True
        )[:6]

        location_data = [{'name': k, **v} for k, v in location_stats.items()]

        monthly_data = sorted([
            {'month': k, **v} for k, v in monthly_stats.items()
        ], key=lambda x: x['month'])

        _distribution_stats_cache = {
            'summary': {
                'total_records': total_records,
                'total_kg_in': round(total_kg_in, 2),
                'total_kg_out': round(total_kg_out, 2),
                'distribution_rate': round((total_kg_out / total_kg_in * 100) if total_kg_in > 0 else 0, 1)
            },
            'by_location': location_data,
            'by_category': top_categories,
            'by_source': top_sources,
            'by_month': monthly_data
        }

        return _distribution_stats_cache

    except FileNotFoundError:
        return {'error': 'Distribution data file not found'}
    except Exception as e:
        return {'error': str(e)}


@app.route('/api/distribution-stats', methods=['GET'])
def get_distribution_stats():
    """Get distribution statistics for dashboard visualizations."""
    stats = compute_distribution_stats()
    return jsonify(stats)


def compute_stock_alerts():
    """
    Compute stock alerts directly from distribution_data.csv.
    Identifies overstock (high remaining stock) and understock (low remaining stock) items.
    """
    global _stock_alerts_cache
    if _stock_alerts_cache:
        return _stock_alerts_cache

    # Column indices for distribution_data.csv (no headers)
    COL_CATEGORY = 1
    COL_SUBCATEGORY = 2
    COL_PRODUCT = 3
    COL_FINAL_STOCK = 9

    product_stock = defaultdict(lambda: {'total_stock': 0, 'count': 0, 'category': '', 'subcategory': ''})

    try:
        with open(DISTRIBUTION_CSV, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 10:
                    continue

                product = row[COL_PRODUCT]
                category = row[COL_CATEGORY]
                subcategory = row[COL_SUBCATEGORY]

                try:
                    final_stock = float(row[COL_FINAL_STOCK]) if row[COL_FINAL_STOCK] else 0
                except ValueError:
                    final_stock = 0

                # Aggregate by product - take max stock seen (most recent state)
                if final_stock > product_stock[product]['total_stock']:
                    product_stock[product]['total_stock'] = final_stock
                    product_stock[product]['category'] = category
                    product_stock[product]['subcategory'] = subcategory
                product_stock[product]['count'] += 1

        # Convert to list and sort
        all_products = [
            {
                'product_name': name,
                'category': data['category'],
                'subcategory': data['subcategory'],
                'final_stock_kg': round(data['total_stock'], 2),
                'transaction_count': data['count']
            }
            for name, data in product_stock.items()
            if data['total_stock'] > 0  # Only include items with stock
        ]

        # Calculate category averages for ratio
        category_totals = defaultdict(lambda: {'total': 0, 'count': 0})
        for p in all_products:
            category_totals[p['category']]['total'] += p['final_stock_kg']
            category_totals[p['category']]['count'] += 1

        category_avg = {
            cat: data['total'] / data['count'] if data['count'] > 0 else 0
            for cat, data in category_totals.items()
        }

        # Add ratio to category average
        for p in all_products:
            avg = category_avg.get(p['category'], 1)
            p['ratio_to_category_avg'] = round(p['final_stock_kg'] / avg, 2) if avg > 0 else 0

        # Overstock: highest absolute stock AND high ratio
        overstock = sorted(
            [p for p in all_products if p['ratio_to_category_avg'] > 2],
            key=lambda x: x['final_stock_kg'],
            reverse=True
        )[:10]

        # Understock: low stock items that have transaction history (were distributed)
        understock = sorted(
            [p for p in all_products if p['final_stock_kg'] < 5 and p['transaction_count'] > 1],
            key=lambda x: x['final_stock_kg']
        )[:10]

        _stock_alerts_cache = {
            'overstock': {
                'overstock_items': overstock[:3],
                'total_count': len(overstock)
            },
            'understock': {
                'understock_items': understock[:3],
                'total_count': len(understock)
            }
        }

        return _stock_alerts_cache

    except FileNotFoundError:
        return {'error': 'Distribution data file not found'}
    except Exception as e:
        return {'error': str(e)}


@app.route('/api/stock-alerts', methods=['GET'])
def get_stock_alerts():
    """Get pre-computed stock alerts for dashboard."""
    alerts = compute_stock_alerts()
    return jsonify(alerts)


# ============== RISK AGENT ENDPOINTS ==============

@app.route('/api/risk-analysis', methods=['POST'])
def analyze_risk():
    """
    Query the waste prevention risk agent.
    Analyzes charity fit, expiry risks, and stock levels.
    """
    data = request.json
    if not data or 'query' not in data:
        return jsonify({'error': 'No query provided'}), 400

    query = data['query']
    print(f"[Risk Agent] Query: {query}")

    try:
        response = risk_agent(query)
        response_text = str(response) if response else ""

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
            return jsonify({
                'status': 'complete',
                'analysis': parsed
            })
        except json.JSONDecodeError:
            return jsonify({
                'status': 'complete',
                'text_response': response_text
            })

    except Exception as e:
        print(f"Error in risk analysis: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/stock-levels', methods=['GET'])
def get_stock_levels():
    """
    Get current overstock and understock items.
    Query params:
        - overstock_threshold: multiplier for category average (default: 4.0)
        - understock_threshold: ratio to category average (default: 0.25)
        - limit: max items to return per category (default: 10)
    """
    try:
        overstock_threshold = float(request.args.get('overstock_threshold', 4.0))
        understock_threshold = float(request.args.get('understock_threshold', 0.25))
        limit = int(request.args.get('limit', 10))

        overstock = get_overstock_items(threshold_multiplier=overstock_threshold, limit=limit)
        understock = get_understock_items(threshold_ratio=understock_threshold, limit=limit)

        return jsonify({
            'overstock': overstock,
            'understock': understock
        })

    except Exception as e:
        print(f"Error getting stock levels: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/category-stock/<category>', methods=['GET'])
def get_category_stock(category):
    """Get detailed stock analysis for a specific category."""
    try:
        result = get_category_stock_levels(category)
        return jsonify(result)
    except Exception as e:
        print(f"Error getting category stock: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stock-summary', methods=['GET'])
def get_stock_summary():
    """Get a summary of stock levels across all categories."""
    try:
        result = calculate_stock_levels_by_category()
        return jsonify(result)
    except Exception as e:
        print(f"Error getting stock summary: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("Starting Flask server on port 5001...")
    app.run(host='0.0.0.0', port=5001, debug=True)
