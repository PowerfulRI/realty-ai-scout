"""
Perplexity API client for real estate market research
Provides AI-powered market insights and property research
"""

import os
import requests
import json
import logging
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerplexityClient:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Perplexity API client"""
        self.api_key = api_key or os.getenv('PERPLEXITY_API_KEY')
        self.base_url = "https://api.perplexity.ai"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def research_property(self, address: str) -> Dict:
        """Research property and neighborhood information"""
        query = f"""
        Research the property at {address} and provide:
        1. Current estimated market value and recent comparable sales
        2. Neighborhood characteristics (schools, amenities, walkability)
        3. Recent market trends in the area
        4. Property tax information and HOA fees if applicable
        5. Any recent renovations or notable features
        
        Focus on factual data from reliable real estate sources.
        """
        
        return self._make_request(query)
    
    def find_comparables(self, address: str, property_details: Dict) -> Dict:
        """Find and analyze comparable properties"""
        beds = property_details.get('beds', 'unknown')
        baths = property_details.get('baths', 'unknown')
        sqft = property_details.get('sqft', 'unknown')
        
        query = f"""
        Find recent comparable home sales near {address} with these criteria:
        - {beds} bedrooms, {baths} bathrooms
        - Approximately {sqft} square feet
        - Sold within the last 6 months
        - Within 1 mile radius
        
        For each comparable, provide:
        - Address and sale price
        - Days on market
        - Property features and condition
        - Date of sale
        
        Rank by similarity and reliability as comparables.
        """
        
        return self._make_request(query)
    
    def analyze_market_trends(self, zip_code: str) -> Dict:
        """Analyze market trends for a specific area"""
        query = f"""
        Analyze the real estate market trends in ZIP code {zip_code}:
        1. Average home prices and recent changes (6-12 months)
        2. Days on market trends
        3. Inventory levels (buyer's vs seller's market)
        4. Seasonal patterns and market velocity
        5. Price per square foot trends
        6. Future market outlook and factors affecting prices
        
        Provide specific data points and percentages where available.
        """
        
        return self._make_request(query)
    
    def research_neighborhood(self, address: str) -> Dict:
        """Research neighborhood amenities and characteristics"""
        query = f"""
        Research the neighborhood around {address}:
        1. School ratings and district information
        2. Walk Score and public transportation
        3. Nearby amenities (shopping, restaurants, parks)
        4. Crime statistics and safety ratings
        5. Demographics and community characteristics
        6. Future development plans affecting property values
        
        Provide specific ratings and scores where available.
        """
        
        return self._make_request(query)
    
    def _make_request(self, query: str) -> Dict:
        """Make API request to Perplexity"""
        if not self.api_key:
            logger.error("Perplexity API key not found")
            return {"error": "API key not configured"}
        
        try:
            payload = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a real estate research assistant. Provide accurate, factual information from reliable sources. Include specific data points, prices, and dates when available."
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                "temperature": 0.2,
                "max_tokens": 2000
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "content": result["choices"][0]["message"]["content"],
                    "usage": result.get("usage", {})
                }
            else:
                logger.error(f"Perplexity API error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"Exception in Perplexity API call: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Example usage
if __name__ == "__main__":
    client = PerplexityClient()
    
    # Test property research
    test_address = "123 Main St, San Francisco, CA"
    result = client.research_property(test_address)
    
    if result.get("success"):
        print("Property Research Results:")
        print(result["content"])
    else:
        print(f"Error: {result.get('error')}")