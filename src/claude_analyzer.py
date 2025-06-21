"""
Claude AI analyzer for property insights and recommendations
Processes property data and generates analysis, descriptions, and pricing strategies
"""

import os
import json
import logging
from typing import Dict, List, Optional
from anthropic import Anthropic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClaudeAnalyzer:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Claude AI client"""
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.client = Anthropic(api_key=self.api_key) if self.api_key else None
    
    def analyze_property_value(self, property_data: Dict, comparables: List[Dict], market_data: Dict) -> Dict:
        """Analyze property value using comparable sales and market data"""
        if not self.client:
            return {"error": "Claude API key not configured"}
        
        prompt = f"""
        As a professional real estate appraiser, analyze this property and provide a comprehensive valuation:

        SUBJECT PROPERTY:
        {json.dumps(property_data, indent=2)}

        COMPARABLE SALES:
        {json.dumps(comparables, indent=2)}

        MARKET DATA:
        {json.dumps(market_data, indent=2)}

        Please provide:
        1. ESTIMATED MARKET VALUE with confidence range
        2. COMPARABLE ANALYSIS - which comps are most/least reliable and why
        3. MARKET ADJUSTMENTS - time, condition, location, size adjustments
        4. PRICING STRATEGY - suggested list price and reasoning
        5. MARKET TIMING - best time to sell based on current conditions
        6. POTENTIAL ISSUES - any red flags or concerns

        Format your response as structured JSON with clear sections.
        """
        
        return self._make_request(prompt)
    
    def generate_listing_description(self, property_data: Dict, analysis: Dict) -> Dict:
        """Generate compelling listing description"""
        if not self.client:
            return {"error": "Claude API key not configured"}
        
        prompt = f"""
        Create a compelling real estate listing description for this property:

        PROPERTY DATA:
        {json.dumps(property_data, indent=2)}

        ANALYSIS DATA:
        {json.dumps(analysis, indent=2)}

        Generate:
        1. HEADLINE - catchy 1-line summary
        2. DESCRIPTION - 2-3 paragraph compelling description highlighting key features
        3. KEY FEATURES - bullet points of main selling points
        4. NEIGHBORHOOD HIGHLIGHTS - local amenities and attractions
        5. CALL TO ACTION - motivating closing statement

        Style: Professional but engaging, emphasize unique selling points, avoid superlatives without substance.
        """
        
        return self._make_request(prompt)
    
    def assess_property_condition(self, photos: List[str], property_data: Dict) -> Dict:
        """Assess property condition from photos (when available)"""
        if not self.client:
            return {"error": "Claude API key not configured"}
        
        # Note: This would require Claude's vision capabilities
        # For now, implement text-based condition assessment
        
        prompt = f"""
        Assess property condition based on available data:

        PROPERTY INFORMATION:
        {json.dumps(property_data, indent=2)}

        Based on year built, price relative to area, and any description text, assess:
        1. OVERALL CONDITION - Excellent/Good/Fair/Poor
        2. LIKELY UPDATES NEEDED - kitchen, bathrooms, systems, etc.
        3. CONDITION ADJUSTMENTS - how condition affects value vs comparables
        4. RENOVATION RECOMMENDATIONS - priority improvements for value
        5. INVESTMENT POTENTIAL - fix-up costs vs value increase

        Provide reasoning for each assessment.
        """
        
        return self._make_request(prompt)
    
    def create_market_report(self, address: str, analysis_data: Dict) -> Dict:
        """Create comprehensive market report"""
        if not self.client:
            return {"error": "Claude API key not configured"}
        
        prompt = f"""
        Create a comprehensive market report for {address}:

        ANALYSIS DATA:
        {json.dumps(analysis_data, indent=2)}

        Generate a professional market report including:
        1. EXECUTIVE SUMMARY
        2. PROPERTY VALUATION SUMMARY
        3. COMPARABLE SALES ANALYSIS
        4. MARKET CONDITIONS OVERVIEW
        5. PRICING RECOMMENDATIONS
        6. MARKETING STRATEGY
        7. RISK FACTORS AND CONSIDERATIONS

        Format as a professional report suitable for real estate professionals.
        """
        
        return self._make_request(prompt)
    
    def analyze_investment_potential(self, property_data: Dict, market_data: Dict) -> Dict:
        """Analyze property as an investment opportunity"""
        if not self.client:
            return {"error": "Claude API key not configured"}
        
        prompt = f"""
        Analyze this property's investment potential:

        PROPERTY DATA:
        {json.dumps(property_data, indent=2)}

        MARKET DATA:
        {json.dumps(market_data, indent=2)}

        Provide investment analysis:
        1. CASH FLOW ANALYSIS - estimated rental income vs expenses
        2. APPRECIATION POTENTIAL - market trends and growth factors
        3. RISK ASSESSMENT - market volatility, location factors
        4. INVESTMENT SCORE - rate 1-10 with reasoning
        5. COMPARABLE INVESTMENTS - how this compares to alternatives
        6. EXIT STRATEGY - resale potential and timeline

        Include specific numbers and calculations where possible.
        """
        
        return self._make_request(prompt)
    
    def _make_request(self, prompt: str) -> Dict:
        """Make request to Claude API"""
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return {
                "success": True,
                "content": response.content[0].text,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Example usage
if __name__ == "__main__":
    analyzer = ClaudeAnalyzer()
    
    # Test property analysis
    sample_property = {
        "address": "123 Main St, Anytown, CA",
        "price": 750000,
        "sqft": 2100,
        "beds": 3,
        "baths": 2,
        "year_built": 1995
    }
    
    sample_comps = [
        {"address": "125 Main St", "price": 725000, "sqft": 2000, "beds": 3, "baths": 2},
        {"address": "127 Oak Ave", "price": 780000, "sqft": 2200, "beds": 3, "baths": 2}
    ]
    
    sample_market = {"trend": "rising", "avg_dom": 25, "inventory": "low"}
    
    result = analyzer.analyze_property_value(sample_property, sample_comps, sample_market)
    
    if result.get("success"):
        print("Property Analysis:")
        print(result["content"])
    else:
        print(f"Error: {result.get('error')}")