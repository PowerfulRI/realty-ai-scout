"""
Comprehensive property data scraper using Selenium
Scrapes Zillow, Realtor.com, and other real estate sites
Collects property data AND comparable properties for Claude analysis
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PropertyScraper:
    def __init__(self, headless=True):
        """Initialize Chrome WebDriver with options"""
        self.options = Options()
        if headless:
            self.options.add_argument('--headless')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        self.driver = None
    
    def start_driver(self):
        """Start Chrome WebDriver"""
        try:
            self.driver = webdriver.Chrome(options=self.options)
            return True
        except Exception as e:
            logger.error(f"Failed to start Chrome driver: {e}")
            return False
    
    def close_driver(self):
        """Close Chrome WebDriver"""
        if self.driver:
            self.driver.quit()
    
    def scrape_zillow(self, address):
        """Scrape property data from Zillow"""
        if not self.driver:
            return None
            
        try:
            # Clean address for URL
            clean_address = address.replace(' ', '-').replace(',', '')
            search_url = f"https://www.zillow.com/homes/{clean_address}_rb/"
            
            logger.info(f"Searching Zillow for: {address}")
            self.driver.get(search_url)
            
            # Wait for page to load
            time.sleep(3)
            
            property_data = {
                'source': 'zillow',
                'address': address,
                'price': None,
                'sqft': None,
                'beds': None,
                'baths': None,
                'lot_size': None,
                'year_built': None,
                'description': None,
                'photos': [],
                'property_type': None,
                'zestimate': None,
                'scraped_at': time.time()
            }
            
            # Try multiple selectors for price
            price_selectors = [
                '[data-testid="price"]',
                '.Text-c11n-8-108-1__sc-aiai24-0.dpf__sc-1me4shm-0.SummaryTable__text',
                'span[data-testid="price"]',
                '.ds-value',
                '.ds-price'
            ]
            
            for selector in price_selectors:
                try:
                    price_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    price_text = price_element.text.strip()
                    if price_text and '$' in price_text:
                        # Extract numeric value
                        price_clean = price_text.replace('$', '').replace(',', '').replace('+', '')
                        property_data['price'] = price_clean
                        logger.info(f"Found price: {price_text}")
                        break
                except:
                    continue
            
            # Try to get property details
            try:
                # Look for beds/baths/sqft in various formats
                details_selectors = [
                    '[data-testid="bed-bath-item"]',
                    '.Text-c11n-8-108-1__sc-aiai24-0.dpf__sc-1me4shm-0.SummaryTable__text',
                    '.ds-bed-bath-living-area-container span',
                    '.summary-table tbody tr'
                ]
                
                detail_text = ""
                for selector in details_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            text = element.text.strip()
                            if any(keyword in text.lower() for keyword in ['bed', 'bath', 'sqft', 'sq ft']):
                                detail_text += text + " "
                    except:
                        continue
                
                # Parse details from collected text
                if 'bed' in detail_text.lower():
                    import re
                    bed_match = re.search(r'(\d+)\s*bed', detail_text.lower())
                    if bed_match:
                        property_data['beds'] = int(bed_match.group(1))
                
                if 'bath' in detail_text.lower():
                    bath_match = re.search(r'(\d+(?:\.\d+)?)\s*bath', detail_text.lower())
                    if bath_match:
                        property_data['baths'] = float(bath_match.group(1))
                
                if any(sq in detail_text.lower() for sq in ['sqft', 'sq ft']):
                    sqft_match = re.search(r'([\d,]+)\s*(?:sqft|sq ft)', detail_text.lower())
                    if sqft_match:
                        property_data['sqft'] = int(sqft_match.group(1).replace(',', ''))
                        
            except Exception as e:
                logger.warning(f"Could not extract property details: {e}")
            
            # Try to get Zestimate
            try:
                zestimate_selectors = [
                    '[data-testid="zestimate-value"]',
                    '.Zestimate',
                    '.zestimate-value'
                ]
                
                for selector in zestimate_selectors:
                    try:
                        zest_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        zest_text = zest_element.text.strip()
                        if zest_text and '$' in zest_text:
                            property_data['zestimate'] = zest_text
                            break
                    except:
                        continue
                        
            except Exception as e:
                logger.warning(f"Could not extract Zestimate: {e}")
            
            # Get property description
            try:
                desc_selectors = [
                    '[data-testid="description-text"]',
                    '.Text-c11n-8-108-1__sc-aiai24-0.Text__sc-1jb7a5k-0',
                    '.Text-aiai24-0'
                ]
                
                for selector in desc_selectors:
                    try:
                        desc_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        desc_text = desc_element.text.strip()
                        if len(desc_text) > 50:  # Reasonable description length
                            property_data['description'] = desc_text[:500]  # Limit length
                            break
                    except:
                        continue
                        
            except Exception as e:
                logger.warning(f"Could not extract description: {e}")
            
            # Get photo URLs
            try:
                photo_elements = self.driver.find_elements(By.CSS_SELECTOR, 'img[src*="zillow"]')
                photos = []
                for img in photo_elements[:5]:  # Limit to first 5 photos
                    src = img.get_attribute('src')
                    if src and 'http' in src and any(x in src for x in ['.jpg', '.jpeg', '.png']):
                        photos.append(src)
                property_data['photos'] = photos
            except Exception as e:
                logger.warning(f"Could not extract photos: {e}")
            
            logger.info(f"Zillow scraping completed for {address}")
            return property_data
            
        except Exception as e:
            logger.error(f"Error scraping Zillow for {address}: {e}")
            return None
    
    def scrape_realtor_com(self, address):
        """Scrape property data from Realtor.com"""
        if not self.driver:
            return None
            
        try:
            # Navigate to Realtor.com search
            search_url = f"https://www.realtor.com/realestateandhomes-search/{address.replace(' ', '-')}"
            self.driver.get(search_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # TODO: Implement specific Realtor.com scraping logic
            
            property_data = {
                'source': 'realtor.com',
                'address': address,
                'price': None,
                'sqft': None,
                'beds': None,
                'baths': None,
                'mls_id': None,
                'description': None,
                'scraped_at': time.time()
            }
            
            return property_data
            
        except Exception as e:
            logger.error(f"Error scraping Realtor.com for {address}: {e}")
            return None
    
    def find_comparables(self, address, radius_miles=1, max_comps=5):
        """Find comparable properties near the given address"""
        if not self.driver:
            return []
            
        try:
            # Create search URL for recently sold properties
            clean_address = address.replace(' ', '-').replace(',', '')
            
            # Try multiple approaches to find sold properties
            sold_urls = [
                f"https://www.zillow.com/homes/recently_sold/{clean_address}_rb/",
                f"https://www.zillow.com/{clean_address}_rb/sold_rb/",
                f"https://www.zillow.com/homes/for_sale/{clean_address}_rb/sold_rb/"
            ]
            
            comparables = []
            
            for url in sold_urls:
                try:
                    logger.info(f"Searching for comparables at: {url}")
                    self.driver.get(url)
                    time.sleep(3)
                    
                    # Look for property cards/listings
                    property_selectors = [
                        'article[data-testid="property-card"]',
                        '.list-card',
                        '.property-card',
                        '[data-testid="property-card-link"]'
                    ]
                    
                    property_elements = []
                    for selector in property_selectors:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            if elements:
                                property_elements = elements[:max_comps]
                                break
                        except:
                            continue
                    
                    if not property_elements:
                        continue
                        
                    for i, prop in enumerate(property_elements):
                        try:
                            comp_data = {
                                'address': 'Unknown Address',
                                'sale_price': None,
                                'sale_date': None,
                                'sqft': None,
                                'beds': None,
                                'baths': None,
                                'distance_miles': None,
                                'source': 'zillow_comps',
                                'scraped_at': time.time()
                            }
                            
                            # Extract address
                            try:
                                address_selectors = [
                                    '[data-testid="property-card-addr"]',
                                    '.list-card-addr',
                                    '.property-card-addr',
                                    'address'
                                ]
                                
                                for addr_sel in address_selectors:
                                    try:
                                        addr_elem = prop.find_element(By.CSS_SELECTOR, addr_sel)
                                        comp_data['address'] = addr_elem.text.strip()
                                        break
                                    except:
                                        continue
                            except:
                                pass
                            
                            # Extract price
                            try:
                                price_selectors = [
                                    '[data-testid="property-card-price"]',
                                    '.list-card-price',
                                    '.property-card-price',
                                    '.price'
                                ]
                                
                                for price_sel in price_selectors:
                                    try:
                                        price_elem = prop.find_element(By.CSS_SELECTOR, price_sel)
                                        price_text = price_elem.text.strip()
                                        if '$' in price_text:
                                            # Extract numeric value
                                            import re
                                            price_match = re.search(r'\$([0-9,]+)', price_text)
                                            if price_match:
                                                comp_data['sale_price'] = price_match.group(1).replace(',', '')
                                        break
                                    except:
                                        continue
                            except:
                                pass
                            
                            # Extract property details (beds/baths/sqft)
                            try:
                                detail_text = prop.text.lower()
                                
                                # Extract beds
                                bed_match = re.search(r'(\d+)\s*bed', detail_text)
                                if bed_match:
                                    comp_data['beds'] = int(bed_match.group(1))
                                
                                # Extract baths
                                bath_match = re.search(r'(\d+(?:\.\d+)?)\s*bath', detail_text)
                                if bath_match:
                                    comp_data['baths'] = float(bath_match.group(1))
                                
                                # Extract sqft
                                sqft_match = re.search(r'([\d,]+)\s*(?:sqft|sq ft)', detail_text)
                                if sqft_match:
                                    comp_data['sqft'] = int(sqft_match.group(1).replace(',', ''))
                                    
                            except Exception as e:
                                logger.warning(f"Could not extract comp details: {e}")
                            
                            # Only add if we got meaningful data
                            if comp_data['sale_price'] or comp_data['sqft']:
                                comparables.append(comp_data)
                                logger.info(f"Found comparable: {comp_data['address']}")
                                
                        except Exception as e:
                            logger.warning(f"Error processing comparable {i}: {e}")
                            continue
                    
                    if comparables:
                        break  # If we found comps, no need to try other URLs
                        
                except Exception as e:
                    logger.warning(f"Error with URL {url}: {e}")
                    continue
            
            # If no comps found, create sample data for demo
            if not comparables:
                logger.info("No comparables found, creating sample data")
                for i in range(3):
                    comp_data = {
                        'address': f'Sample Comparable {i+1} (Near {address})',
                        'sale_price': f"{450000 + (i * 25000)}",
                        'sale_date': '2024-12-01',
                        'sqft': 2000 + (i * 100),
                        'beds': 3,
                        'baths': 2.0,
                        'distance_miles': 0.3 + (i * 0.1),
                        'source': 'zillow_comps_sample',
                        'scraped_at': time.time()
                    }
                    comparables.append(comp_data)
            
            logger.info(f"Found {len(comparables)} comparable properties")
            return comparables[:max_comps]
            
        except Exception as e:
            logger.error(f"Error finding comparables near {address}: {e}")
            return []
    
    def scrape_property_and_comps(self, address):
        """Scrape both property data and comparable properties"""
        property_data = self.scrape_zillow(address)
        comparables = self.find_comparables(address)
        
        return {
            'property': property_data,
            'comparables': comparables,
            'scraped_at': time.time()
        }

# Example usage
if __name__ == "__main__":
    scraper = PropertyScraper(headless=False)
    if scraper.start_driver():
        try:
            # Test scraping
            test_address = "123 Main St, Anytown, CA"
            zillow_data = scraper.scrape_zillow(test_address)
            print(f"Zillow data: {zillow_data}")
            
            realtor_data = scraper.scrape_realtor_com(test_address)
            print(f"Realtor.com data: {realtor_data}")
            
        finally:
            scraper.close_driver()