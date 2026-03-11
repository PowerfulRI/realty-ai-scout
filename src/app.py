"""
Realty AI Scout - Main Flask Application
AI-powered real estate analysis tool for property valuation and market insights
"""

from flask import Flask, render_template, request, jsonify
import os
import sys
import json
import time
from dotenv import load_dotenv

# Ensure src/ is on the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')


def try_scrape(address):
    """Attempt to scrape property data. Returns scraped data or empty structure."""
    try:
        from selenium_scraper import PropertyScraper
        scraper = PropertyScraper(headless=True)
        if scraper.start_driver():
            print(f"Scraping data for: {address}")
            scraped_data = scraper.scrape_property_and_comps(address)
            scraper.close_driver()
            print(f"Scraping done. Property: {bool(scraped_data.get('property'))}, "
                  f"Comps: {len(scraped_data.get('comparables', []))}")
            return scraped_data
    except Exception as e:
        print(f"Scraping failed: {e}")
    return {'property': {'address': address}, 'comparables': []}


def build_property_data(req_json, scraped_property=None):
    """Merge manual input with scraped data. Manual input takes priority."""
    base = scraped_property or {}

    # Manual fields override scraped data when provided
    manual_fields = {
        'price': req_json.get('price'),
        'beds': req_json.get('beds'),
        'baths': req_json.get('baths'),
        'sqft': req_json.get('sqft'),
        'year_built': req_json.get('year_built'),
        'lot_size': req_json.get('lot_size'),
        'basement': req_json.get('basement'),
        'sqft_finished_basement': req_json.get('sqft_finished_basement'),
        'property_type': req_json.get('property_type'),
        'condition': req_json.get('condition'),
    }

    for key, val in manual_fields.items():
        if val is not None and val != '' and val != 'Unknown':
            base[key] = val

    # Calculate total living sqft if we have both
    if base.get('sqft') and base.get('sqft_finished_basement'):
        try:
            above = int(str(base['sqft']).replace(',', ''))
            below = int(str(base['sqft_finished_basement']).replace(',', ''))
            base['sqft_above_grade'] = above
            base['total_living_sqft'] = above + below
        except (ValueError, TypeError):
            pass

    base['address'] = req_json.get('address', base.get('address', 'Unknown'))
    base['data_source'] = 'manual' if any(v for v in manual_fields.values()) else 'scraped'
    return base


def parse_claude_json(content):
    """Extract JSON from Claude's response text."""
    start_idx = content.find('{')
    end_idx = content.rfind('}') + 1
    if start_idx >= 0 and end_idx > start_idx:
        try:
            return json.loads(content[start_idx:end_idx])
        except json.JSONDecodeError:
            pass
    return {"raw_analysis": content}


@app.route('/')
def index():
    """Main page with property analysis form"""
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze_property():
    """Analyze property and return insights"""
    try:
        data = request.json
        address = data.get('address')
        if not address:
            return jsonify({'error': 'Address is required'}), 400

        from claude_analyzer import ClaudeAnalyzer
        analyzer = ClaudeAnalyzer()

        # Try scraping, fall back to Claude-only analysis
        scraped_data = try_scrape(address)

        # Merge manual input with scraped data
        property_data = build_property_data(data, scraped_data.get('property'))
        scraped_data['property'] = property_data

        print(f"Analysis with data source: {property_data.get('data_source')}")
        print(f"Property: price={property_data.get('price')}, sqft={property_data.get('sqft')}, "
              f"beds={property_data.get('beds')}, basement={property_data.get('basement')}")

        analysis_result = analyzer.comprehensive_property_analysis(scraped_data)

        if analysis_result.get('success'):
            analysis_json = parse_claude_json(analysis_result.get('content', ''))
            return jsonify({
                'address': address,
                'status': 'success',
                'property_data': property_data,
                'comparables': scraped_data.get('comparables', []),
                'analysis': analysis_json,
                'timestamp': time.time()
            })
        else:
            return jsonify({
                'error': f'Claude analysis failed: {analysis_result.get("error", "Unknown error")}',
                'address': address,
            }), 500

    except Exception as e:
        print(f"Pipeline error: {e}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


@app.route('/flip-analysis', methods=['POST'])
def flip_analysis():
    """Analyze property for flip/investment potential"""
    try:
        data = request.json
        address = data.get('address')
        if not address:
            return jsonify({'error': 'Address is required'}), 400

        from claude_analyzer import ClaudeAnalyzer
        analyzer = ClaudeAnalyzer()

        # Try scraping, fall back to Claude-only analysis
        scraped_data = try_scrape(address)

        # Merge manual input with scraped data
        property_data = build_property_data(data, scraped_data.get('property'))
        comparables = scraped_data.get('comparables', [])

        print(f"Flip analysis with data source: {property_data.get('data_source')}")
        print(f"Property: price={property_data.get('price')}, sqft={property_data.get('sqft')}, "
              f"beds={property_data.get('beds')}, basement={property_data.get('basement')}")

        flip_result = analyzer.analyze_flip_potential(property_data, comparables)

        if flip_result.get('success'):
            analysis_json = parse_claude_json(flip_result.get('content', ''))
            return jsonify({
                'address': address,
                'status': 'success',
                'property_data': property_data,
                'comparables': comparables,
                'flip_analysis': analysis_json,
                'flip_metrics': flip_result.get('flip_metrics', {}),
                'timestamp': time.time()
            })
        else:
            return jsonify({
                'error': f'Flip analysis failed: {flip_result.get("error", "Unknown")}',
                'flip_metrics': flip_result.get('flip_metrics', {}),
                'property_data': property_data,
            }), 500

    except Exception as e:
        return jsonify({'error': f'Flip analysis failed: {str(e)}'}), 500


if __name__ == '__main__':
    print("Starting Realty AI Scout on http://localhost:8000")
    print("Access at: http://localhost:8000")
    app.run(debug=True, host='localhost', port=8000)
