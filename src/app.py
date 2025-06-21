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
        from selenium_scraper import PropertyScraper
        from claude_analyzer import ClaudeAnalyzer
        
        # Initialize components
        scraper = PropertyScraper(headless=True)
        analyzer = ClaudeAnalyzer()
        
        try:
            # 1. Scrape property data and comparables
            if scraper.start_driver():
                print(f"Started scraping for: {address}")
                scraped_data = scraper.scrape_property_and_comps(address)
                scraper.close_driver()
                
                print(f"Scraping completed. Found property: {bool(scraped_data.get('property'))}")
                print(f"Found {len(scraped_data.get('comparables', []))} comparables")
                
                # 2. Analyze with Claude AI
                print("Starting Claude analysis...")
                analysis_result = analyzer.comprehensive_property_analysis(scraped_data)
                
                if analysis_result.get('success'):
                    # Try to parse the JSON response from Claude
                    try:
                        analysis_content = analysis_result.get('content', '')
                        # Look for JSON in the response
                        import json as json_module
                        start_idx = analysis_content.find('{')
                        end_idx = analysis_content.rfind('}') + 1
                        
                        if start_idx >= 0 and end_idx > start_idx:
                            json_str = analysis_content[start_idx:end_idx]
                            analysis_json = json_module.loads(json_str)
                        else:
                            # If no JSON found, structure the text response
                            analysis_json = {
                                "executive_summary": "Analysis completed successfully",
                                "raw_analysis": analysis_content,
                                "status": "text_response"
                            }
                    except Exception as parse_error:
                        print(f"JSON parsing error: {parse_error}")
                        analysis_json = {
                            "executive_summary": "Analysis completed but needs manual review",
                            "raw_analysis": analysis_result.get('content', 'No content'),
                            "parsing_error": str(parse_error)
                        }
                    
                    # 3. Return comprehensive results
                    return jsonify({
                        'address': address,
                        'status': 'success',
                        'property_data': scraped_data.get('property', {}),
                        'comparables': scraped_data.get('comparables', []),
                        'analysis': analysis_json,
                        'timestamp': time.time()
                    })
                else:
                    return jsonify({
                        'error': f'Claude analysis failed: {analysis_result.get("error", "Unknown error")}',
                        'address': address,
                        'status': 'analysis_error',
                        'scraped_data': scraped_data
                    }), 500
                    
            else:
                return jsonify({'error': 'Failed to initialize web scraper'}), 500
                
        except Exception as e:
            print(f"Pipeline error: {e}")
            return jsonify({
                'error': f'Analysis failed: {str(e)}',
                'address': address,
                'status': 'error'
            }), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting Realty AI Scout on http://localhost:8000")
    app.run(debug=True, host='localhost', port=8000)