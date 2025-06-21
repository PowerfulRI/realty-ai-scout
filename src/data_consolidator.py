"""
Data consolidation and validation module
Merges data from multiple sources and handles conflicts/validation
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import statistics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataConsolidator:
    def __init__(self):
        """Initialize data consolidator"""
        self.confidence_weights = {
            'zillow': 0.8,
            'realtor.com': 0.9,
            'perplexity': 0.7,
            'county_records': 1.0
        }
    
    def merge_property_data(self, sources: List[Dict]) -> Dict:
        """Merge property data from multiple sources"""
        if not sources:
            return {}
        
        merged = {
            'address': None,
            'price': None,
            'sqft': None,
            'beds': None,
            'baths': None,
            'lot_size': None,
            'year_built': None,
            'property_type': None,
            'description': None,
            'photos': [],
            'source_data': sources,
            'confidence_scores': {},
            'conflicts': [],
            'last_updated': datetime.now().isoformat()
        }
        
        # Extract and validate each field
        merged['address'] = self._consolidate_address(sources)
        merged['price'] = self._consolidate_price(sources)
        merged['sqft'] = self._consolidate_numeric_field(sources, 'sqft')
        merged['beds'] = self._consolidate_numeric_field(sources, 'beds')
        merged['baths'] = self._consolidate_numeric_field(sources, 'baths')
        merged['lot_size'] = self._consolidate_numeric_field(sources, 'lot_size')
        merged['year_built'] = self._consolidate_numeric_field(sources, 'year_built')
        merged['property_type'] = self._consolidate_text_field(sources, 'property_type')
        merged['description'] = self._consolidate_descriptions(sources)
        merged['photos'] = self._consolidate_photos(sources)
        
        # Calculate overall confidence score
        merged['overall_confidence'] = self._calculate_confidence(sources)
        
        return merged
    
    def validate_comparables(self, subject_property: Dict, comparables: List[Dict]) -> List[Dict]:
        """Validate and score comparable properties"""
        if not comparables:
            return []
        
        validated_comps = []
        
        for comp in comparables:
            score = self._score_comparable(subject_property, comp)
            if score >= 0.5:  # Minimum threshold for valid comparable
                comp['comparable_score'] = score
                comp['grade'] = self._grade_comparable(score)
                validated_comps.append(comp)
        
        # Sort by score (best first)
        validated_comps.sort(key=lambda x: x.get('comparable_score', 0), reverse=True)
        
        return validated_comps[:10]  # Return top 10 comparables
    
    def detect_outliers(self, values: List[float], threshold: float = 2.0) -> List[int]:
        """Detect outlier values using standard deviation"""
        if len(values) < 3:
            return []
        
        mean = statistics.mean(values)
        stdev = statistics.stdev(values)
        
        outliers = []
        for i, value in enumerate(values):
            if abs(value - mean) > threshold * stdev:
                outliers.append(i)
        
        return outliers
    
    def _consolidate_address(self, sources: List[Dict]) -> Optional[str]:
        """Consolidate address from multiple sources"""
        addresses = [s.get('address') for s in sources if s.get('address')]
        if not addresses:
            return None
        
        # Use the most common address or first valid one
        return max(set(addresses), key=addresses.count)
    
    def _consolidate_price(self, sources: List[Dict]) -> Optional[Dict]:
        """Consolidate price information"""
        prices = []
        price_sources = []
        
        for source in sources:
            if source.get('price') and isinstance(source['price'], (int, float)):
                prices.append(float(source['price']))
                price_sources.append(source.get('source', 'unknown'))
        
        if not prices:
            return None
        
        # Detect price outliers
        outliers = self.detect_outliers(prices)
        
        return {
            'values': prices,
            'sources': price_sources,
            'median': statistics.median(prices),
            'mean': statistics.mean(prices),
            'outliers': outliers,
            'confidence': len(prices) / len(sources)
        }
    
    def _consolidate_numeric_field(self, sources: List[Dict], field: str) -> Optional[Dict]:
        """Consolidate numeric field from multiple sources"""
        values = []
        value_sources = []
        
        for source in sources:
            value = source.get(field)
            if value is not None and isinstance(value, (int, float)):
                values.append(float(value))
                value_sources.append(source.get('source', 'unknown'))
        
        if not values:
            return None
        
        # Use most common value or median if all different
        try:
            most_common = max(set(values), key=values.count)
            if values.count(most_common) > 1:
                consensus_value = most_common
            else:
                consensus_value = statistics.median(values)
        except:
            consensus_value = values[0]
        
        return {
            'value': consensus_value,
            'all_values': values,
            'sources': value_sources,
            'confidence': len(values) / len(sources)
        }
    
    def _consolidate_text_field(self, sources: List[Dict], field: str) -> Optional[str]:
        """Consolidate text field from multiple sources"""
        values = [s.get(field) for s in sources if s.get(field)]
        if not values:
            return None
        
        # Return most common value
        return max(set(values), key=values.count)
    
    def _consolidate_descriptions(self, sources: List[Dict]) -> List[str]:
        """Consolidate property descriptions"""
        descriptions = []
        for source in sources:
            desc = source.get('description')
            if desc and isinstance(desc, str) and len(desc.strip()) > 10:
                descriptions.append({
                    'text': desc.strip(),
                    'source': source.get('source', 'unknown')
                })
        
        return descriptions
    
    def _consolidate_photos(self, sources: List[Dict]) -> List[str]:
        """Consolidate photo URLs from multiple sources"""
        photos = []
        for source in sources:
            source_photos = source.get('photos', [])
            if isinstance(source_photos, list):
                photos.extend(source_photos)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_photos = []
        for photo in photos:
            if photo not in seen:
                seen.add(photo)
                unique_photos.append(photo)
        
        return unique_photos
    
    def _score_comparable(self, subject: Dict, comp: Dict) -> float:
        """Score how good a comparable is (0.0 to 1.0)"""
        score = 0.0
        factors = 0
        
        # Size similarity (25% weight)
        if subject.get('sqft') and comp.get('sqft'):
            size_diff = abs(subject['sqft'] - comp['sqft']) / subject['sqft']
            score += max(0, 1 - size_diff) * 0.25
            factors += 0.25
        
        # Bedroom similarity (15% weight)
        if subject.get('beds') and comp.get('beds'):
            bed_match = 1.0 if subject['beds'] == comp['beds'] else 0.5
            score += bed_match * 0.15
            factors += 0.15
        
        # Bathroom similarity (15% weight)
        if subject.get('baths') and comp.get('baths'):
            bath_diff = abs(subject['baths'] - comp['baths'])
            bath_score = max(0, 1 - bath_diff * 0.3)
            score += bath_score * 0.15
            factors += 0.15
        
        # Age similarity (10% weight)
        if subject.get('year_built') and comp.get('year_built'):
            age_diff = abs(subject['year_built'] - comp['year_built'])
            age_score = max(0, 1 - age_diff / 50)  # 50 year max difference
            score += age_score * 0.10
            factors += 0.10
        
        # Distance (would need coordinates - placeholder)
        # Recency of sale (would need sale date - placeholder)
        
        return score / factors if factors > 0 else 0.0
    
    def _grade_comparable(self, score: float) -> str:
        """Grade comparable quality"""
        if score >= 0.8:
            return 'A'
        elif score >= 0.7:
            return 'B'
        elif score >= 0.5:
            return 'C'
        else:
            return 'D'
    
    def _calculate_confidence(self, sources: List[Dict]) -> float:
        """Calculate overall confidence in merged data"""
        if not sources:
            return 0.0
        
        # Weight by source reliability
        weighted_confidence = 0.0
        total_weight = 0.0
        
        for source in sources:
            source_name = source.get('source', 'unknown')
            weight = self.confidence_weights.get(source_name, 0.5)
            weighted_confidence += weight
            total_weight += 1.0
        
        return min(1.0, weighted_confidence / total_weight)

# Example usage
if __name__ == "__main__":
    consolidator = DataConsolidator()
    
    # Test data consolidation
    sample_sources = [
        {
            'source': 'zillow',
            'address': '123 Main St, Anytown, CA',
            'price': 750000,
            'sqft': 2100,
            'beds': 3,
            'baths': 2
        },
        {
            'source': 'realtor.com',
            'address': '123 Main Street, Anytown, CA',
            'price': 745000,
            'sqft': 2150,
            'beds': 3,
            'baths': 2
        }
    ]
    
    merged = consolidator.merge_property_data(sample_sources)
    print("Merged Property Data:")
    print(json.dumps(merged, indent=2, default=str))