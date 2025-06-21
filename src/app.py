"""
Realty AI Scout - Main Flask Application
AI-powered real estate analysis tool for property valuation and market insights
"""

from flask import Flask, render_template, request, jsonify
import os
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
        
        # TODO: Implement property analysis pipeline
        # 1. Scrape property data using Selenium
        # 2. Research market with Perplexity API
        # 3. Analyze with Claude AI
        # 4. Return structured results
        
        return jsonify({
            'address': address,
            'status': 'Analysis coming soon!',
            'message': 'Property analysis pipeline will be implemented here'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)