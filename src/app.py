"""
Realty AI Scout - Main Flask Application
AI-powered real estate analysis tool for property valuation and market insights
"""

from flask import Flask, render_template, request, jsonify
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')

@app.route('/')
def index():
    """Main page with property analysis form"""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_property():
    """Analyze property and return insights"""
    try:
        address = request.json.get('address')
        if not address:
            return jsonify({'error': 'Address is required'}), 400
        
        # Simplified property analysis pipeline
        from .selenium_scraper import PropertyScraper
        from .claude_analyzer import ClaudeAnalyzer
        
        # Initialize components
        scraper = PropertyScraper(headless=True)
        analyzer = ClaudeAnalyzer()
        
        try:
            # 1. Scrape property data and comparables
            if scraper.start_driver():
                scraped_data = scraper.scrape_property_and_comps(address)
                scraper.close_driver()
                
                # 2. Analyze with Claude AI
                analysis = analyzer.comprehensive_property_analysis(scraped_data)
                
                # 3. Return comprehensive results
                return jsonify({
                    'address': address,
                    'status': 'success',
                    'scraped_data': scraped_data,
                    'analysis': analysis,
                    'timestamp': time.time()
                })
            else:
                return jsonify({'error': 'Failed to initialize web scraper'}), 500
                
        except Exception as e:
            return jsonify({
                'error': f'Analysis failed: {str(e)}',
                'address': address,
                'status': 'error'
            }), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)