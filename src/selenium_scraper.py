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
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

    # Keywords that indicate distressed/non-arm's-length sales
DISTRESSED_KEYWORDS = [
    'foreclosure', 'foreclosed', 'pre-foreclosure', 'pre foreclosure',
    'bank owned', 'bank-owned', 'reo', 'real estate owned',
    'probate', 'estate sale', 'estate',
    'short sale', 'short-sale',
    'auction', 'auctioned',
    'hud', 'government owned',
    'as-is', 'as is',
    'fixer', 'fixer-upper', 'fixer upper',
    'handyman special', 'investor special',
    'needs work', 'needs rehab', 'needs renovation',
    'distressed', 'motivated seller',
    'sheriff sale', "sheriff's sale",
    'tax lien', 'tax sale',
    'wholesale', 'off market',
]


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
        """Start Chrome WebDriver with automatic driver management"""
        try:
            # Try webdriver-manager first
            driver_path = ChromeDriverManager().install()
            # Fix: webdriver-manager sometimes returns wrong file path
            import os
            if not os.access(driver_path, os.X_OK) or 'THIRD_PARTY' in driver_path or 'LICENSE' in driver_path:
                # Look for actual binary in same directory
                driver_dir = os.path.dirname(driver_path)
                candidate = os.path.join(driver_dir, 'chromedriver')
                if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                    driver_path = candidate
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=self.options)
            return True
        except Exception as e:
            logger.error(f"Failed to start Chrome driver via webdriver-manager: {e}")
            # Fallback: try system chromedriver
            try:
                self.driver = webdriver.Chrome(options=self.options)
                return True
            except Exception as e2:
                logger.error(f"Failed to start Chrome driver: {e2}")
                logger.error("Make sure Chrome/Chromium is installed on your system")
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
                'sqft_above_grade': None,
                'sqft_below_grade': None,
                'sqft_finished_basement': None,
                'total_living_sqft': None,
                'beds': None,
                'baths': None,
                'lot_size': None,
                'year_built': None,
                'basement': None,
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
            
            # Try to get property details via CSS selectors first
            try:
                details_selectors = [
                    '[data-testid="bed-bath-item"]',
                    '.ds-bed-bath-living-area-container span',
                    '.summary-table tbody tr',
                    '.StyledPropertyCardDataArea-c11n span',
                ]

                detail_text = ""
                for selector in details_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            text = element.text.strip()
                            if any(keyword in text.lower() for keyword in ['bed', 'bath', 'sqft', 'sq ft', 'bd', 'ba']):
                                detail_text += text + " "
                    except:
                        continue

                # Parse details from collected text
                if 'bed' in detail_text.lower() or ' bd' in detail_text.lower():
                    bed_match = re.search(r'(\d+)\s*(?:bed|bd)', detail_text.lower())
                    if bed_match:
                        property_data['beds'] = int(bed_match.group(1))

                if 'bath' in detail_text.lower() or ' ba' in detail_text.lower():
                    bath_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:bath|ba)', detail_text.lower())
                    if bath_match:
                        property_data['baths'] = float(bath_match.group(1))

                if any(sq in detail_text.lower() for sq in ['sqft', 'sq ft']):
                    sqft_match = re.search(r'([\d,]+)\s*(?:sqft|sq ft)', detail_text.lower())
                    if sqft_match:
                        property_data['sqft'] = int(sqft_match.group(1).replace(',', ''))

            except Exception as e:
                logger.warning(f"Could not extract property details via selectors: {e}")

            # Fallback: parse full page text for beds/baths/sqft/year if selectors missed them
            try:
                if not property_data['beds'] or not property_data['baths'] or not property_data['sqft']:
                    page_text = self.driver.find_element(By.TAG_NAME, 'body').text
                    page_lower = page_text.lower()
                    logger.info(f"Falling back to full page text parsing (length: {len(page_text)})")

                    if not property_data['beds']:
                        # Patterns: "3 bd", "3 beds", "3 Beds", "Bedrooms: 3", "Bedrooms 3"
                        for pattern in [r'(\d+)\s*(?:bd|beds?)\b', r'bedrooms?\s*:?\s*(\d+)']:
                            m = re.search(pattern, page_lower)
                            if m:
                                property_data['beds'] = int(m.group(1))
                                logger.info(f"Page text: found beds = {property_data['beds']}")
                                break

                    if not property_data['baths']:
                        for pattern in [r'(\d+(?:\.\d+)?)\s*(?:ba|baths?)\b', r'bathrooms?\s*:?\s*(\d+(?:\.\d+)?)']:
                            m = re.search(pattern, page_lower)
                            if m:
                                property_data['baths'] = float(m.group(1))
                                logger.info(f"Page text: found baths = {property_data['baths']}")
                                break

                    if not property_data['sqft']:
                        for pattern in [r'([\d,]+)\s*(?:sqft|sq\.?\s*ft)', r'living\s*area\s*:?\s*([\d,]+)', r'([\d,]+)\s*square\s*feet']:
                            m = re.search(pattern, page_lower)
                            if m:
                                val = int(m.group(1).replace(',', ''))
                                if 200 < val < 50000:  # Sanity check
                                    property_data['sqft'] = val
                                    logger.info(f"Page text: found sqft = {property_data['sqft']}")
                                    break

                    if not property_data['year_built']:
                        for pattern in [r'(?:year\s*built|built\s*in)\s*:?\s*(\d{4})', r'built\s*:?\s*(\d{4})']:
                            m = re.search(pattern, page_lower)
                            if m:
                                yr = int(m.group(1))
                                if 1800 < yr < 2027:
                                    property_data['year_built'] = yr
                                    logger.info(f"Page text: found year_built = {yr}")
                                    break

                    if not property_data['lot_size']:
                        m = re.search(r'lot\s*:?\s*([\d,.]+)\s*(acres?|sqft|sq\s*ft)', page_lower)
                        if m:
                            property_data['lot_size'] = f"{m.group(1)} {m.group(2)}"
                            logger.info(f"Page text: found lot_size = {property_data['lot_size']}")

                    if not property_data['price']:
                        m = re.search(r'\$\s*([\d,]+)', page_text)
                        if m:
                            val = int(m.group(1).replace(',', ''))
                            if val > 20000:
                                property_data['price'] = str(val)
                                logger.info(f"Page text: found price = ${val}")

            except Exception as e:
                logger.warning(f"Could not extract details from page text: {e}")

            # Try to extract basement/below-grade info from page text
            try:
                page_text = self.driver.find_element(By.TAG_NAME, 'body').text.lower()

                # Look for basement mentions
                basement_patterns = [
                    r'finished\s+basement',
                    r'basement[:\s]+finished',
                    r'full\s+basement',
                    r'partial\s+basement',
                    r'walkout\s+basement',
                    r'walk-out\s+basement',
                    r'below\s+grade[:\s]+(\d[\d,]*)\s*(?:sqft|sq\s*ft)',
                    r'basement[:\s]+(\d[\d,]*)\s*(?:sqft|sq\s*ft)',
                    r'finished\s+lower\s+level',
                    r'lower\s+level[:\s]+finished',
                    r'(\d[\d,]*)\s*(?:sqft|sq\s*ft)\s+(?:finished\s+)?basement',
                ]

                basement_info = []
                for pattern in basement_patterns:
                    matches = re.findall(pattern, page_text)
                    if matches:
                        basement_info.append(f"matched: '{pattern}' -> {matches}")
                        # Try to extract basement sqft
                        for m in matches:
                            if m and m.replace(',', '').isdigit():
                                property_data['sqft_below_grade'] = int(m.replace(',', ''))
                                property_data['sqft_finished_basement'] = int(m.replace(',', ''))

                if basement_info:
                    property_data['basement'] = 'detected'
                    logger.info(f"Basement info found: {basement_info}")
                else:
                    # Check for any basement mention at all
                    if 'basement' in page_text or 'below grade' in page_text:
                        property_data['basement'] = 'mentioned'
                        logger.info("Basement mentioned but no specific details found")

                # Calculate total living sqft if we have both
                if property_data.get('sqft') and property_data.get('sqft_finished_basement'):
                    property_data['sqft_above_grade'] = property_data['sqft']
                    property_data['total_living_sqft'] = property_data['sqft'] + property_data['sqft_finished_basement']
                    logger.info(f"Total living sqft: {property_data['total_living_sqft']} "
                                f"(above: {property_data['sqft']}, basement: {property_data['sqft_finished_basement']})")

            except Exception as e:
                logger.warning(f"Could not extract basement info: {e}")

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
    
    def scrape_redfin(self, address):
        """Scrape property data from Redfin (less aggressive blocking than Zillow)"""
        if not self.driver:
            return None

        try:
            clean_address = address.replace(',', '').replace(' ', '-')
            search_url = f"https://www.redfin.com/search#query={address.replace(' ', '%20')}"

            logger.info(f"Searching Redfin for: {address}")
            self.driver.get(search_url)
            time.sleep(4)

            property_data = {
                'source': 'redfin',
                'address': address,
                'price': None, 'sqft': None, 'beds': None, 'baths': None,
                'lot_size': None, 'year_built': None, 'basement': None,
                'sqft_above_grade': None, 'sqft_below_grade': None,
                'sqft_finished_basement': None, 'total_living_sqft': None,
                'description': None, 'photos': [], 'property_type': None,
                'scraped_at': time.time()
            }

            # Redfin often redirects to the property page directly
            # Or shows search results — try to click through to the property
            current_url = self.driver.current_url
            logger.info(f"Redfin landed on: {current_url}")

            # If we're on a search results page, try clicking the first result
            if '/search' in current_url or 'query=' in current_url:
                try:
                    result_links = self.driver.find_elements(By.CSS_SELECTOR,
                        'a.slider-item, a[href*="/home/"], .HomeCardContainer a, .HomeViews a')
                    if result_links:
                        result_links[0].click()
                        time.sleep(3)
                        current_url = self.driver.current_url
                        logger.info(f"Clicked through to: {current_url}")
                except Exception as e:
                    logger.warning(f"Could not click Redfin search result: {e}")

            # Parse the full page text
            page_text = self.driver.find_element(By.TAG_NAME, 'body').text
            page_lower = page_text.lower()
            logger.info(f"Redfin page text length: {len(page_text)}")

            # Price
            price_match = re.search(r'\$\s*([\d,]+)', page_text)
            if price_match:
                val = int(price_match.group(1).replace(',', ''))
                if val > 20000:
                    property_data['price'] = str(val)

            # Beds
            for pattern in [r'(\d+)\s*(?:bd|beds?)\b', r'bedrooms?\s*:?\s*(\d+)']:
                m = re.search(pattern, page_lower)
                if m:
                    property_data['beds'] = int(m.group(1))
                    break

            # Baths
            for pattern in [r'(\d+(?:\.\d+)?)\s*(?:ba|baths?)\b', r'bathrooms?\s*:?\s*(\d+(?:\.\d+)?)']:
                m = re.search(pattern, page_lower)
                if m:
                    property_data['baths'] = float(m.group(1))
                    break

            # Sqft
            for pattern in [r'([\d,]+)\s*(?:sq\.?\s*ft|sqft)', r'living\s*area\s*:?\s*([\d,]+)', r'([\d,]+)\s*square\s*feet']:
                m = re.search(pattern, page_lower)
                if m:
                    val = int(m.group(1).replace(',', ''))
                    if 200 < val < 50000:
                        property_data['sqft'] = val
                        break

            # Year built
            for pattern in [r'(?:year\s*built|built)\s*:?\s*(\d{4})', r'built\s+in\s+(\d{4})']:
                m = re.search(pattern, page_lower)
                if m:
                    yr = int(m.group(1))
                    if 1800 < yr < 2027:
                        property_data['year_built'] = yr
                        break

            # Lot size
            m = re.search(r'lot\s*(?:size)?\s*:?\s*([\d,.]+)\s*(acres?|sqft|sq\s*ft)', page_lower)
            if m:
                property_data['lot_size'] = f"{m.group(1)} {m.group(2)}"

            # Basement
            basement_patterns = [
                r'finished\s+basement', r'full\s+basement', r'partial\s+basement',
                r'walkout\s+basement', r'walk-out\s+basement',
            ]
            for pattern in basement_patterns:
                if re.search(pattern, page_lower):
                    property_data['basement'] = 'detected'
                    break
            if not property_data['basement'] and 'basement' in page_lower:
                property_data['basement'] = 'mentioned'

            # Property type
            for ptype in ['single family', 'condo', 'townhouse', 'multi-family', 'duplex', 'triplex']:
                if ptype in page_lower:
                    property_data['property_type'] = ptype.title()
                    break

            found_fields = sum(1 for k in ['price', 'beds', 'baths', 'sqft'] if property_data.get(k))
            logger.info(f"Redfin scraped {found_fields}/4 key fields for {address}")
            return property_data

        except Exception as e:
            logger.error(f"Error scraping Redfin for {address}: {e}")
            return None
    
    @staticmethod
    def _is_distressed_sale(card_text):
        """Check if a listing is a distressed sale (foreclosure, probate, short sale, etc.)"""
        text_lower = card_text.lower()
        for keyword in DISTRESSED_KEYWORDS:
            if keyword in text_lower:
                return True, keyword
        return False, None

    @staticmethod
    def _is_valid_comp(comp_data, subject_data=None):
        """Validate that a comp is a legitimate arm's-length sale worth using"""
        # Must have a sale price
        if not comp_data.get('sale_price'):
            return False, "no price"

        try:
            price = int(str(comp_data['sale_price']).replace(',', ''))
        except (ValueError, TypeError):
            return False, "invalid price"

        # Minimum price threshold - likely not a real market sale
        if price < 50000:
            return False, f"price too low (${price:,}) - likely distressed or partial interest"

        # If we have subject property data, check similarity
        if subject_data:
            subject_price = None
            if subject_data.get('price'):
                try:
                    subject_price = int(str(subject_data['price']).replace(',', ''))
                except (ValueError, TypeError):
                    pass

            # Price should be within 50% of subject (very wide net)
            if subject_price and subject_price > 0:
                ratio = price / subject_price
                if ratio < 0.35 or ratio > 2.5:
                    return False, f"price ratio {ratio:.1f}x outside range - likely different market segment"

            # Sqft should be within 50% if available
            if subject_data.get('sqft') and comp_data.get('sqft'):
                try:
                    subj_sqft = int(str(subject_data['sqft']).replace(',', ''))
                    comp_sqft = int(str(comp_data['sqft']).replace(',', ''))
                    if subj_sqft > 0:
                        sqft_ratio = comp_sqft / subj_sqft
                        if sqft_ratio < 0.5 or sqft_ratio > 2.0:
                            return False, f"sqft ratio {sqft_ratio:.1f}x - not comparable size"
                except (ValueError, TypeError):
                    pass

            # Beds should be within +-2 if available
            if subject_data.get('beds') and comp_data.get('beds'):
                try:
                    bed_diff = abs(int(comp_data['beds']) - int(subject_data['beds']))
                    if bed_diff > 2:
                        return False, f"{bed_diff} bed difference - not comparable"
                except (ValueError, TypeError):
                    pass

        return True, "valid"

    @staticmethod
    def _extract_zip_and_city(address):
        """Extract zip code and city from address for broader comp search"""
        # Try to find zip code
        zip_match = re.search(r'(\d{5})', address)
        zip_code = zip_match.group(1) if zip_match else None

        # Try to find city/state
        parts = address.replace(',', ' ').split()
        city = None
        # Common pattern: "5 Charles St Willimantic CT"
        # Find the state abbreviation and take the word(s) before it
        state_abbrevs = ['ct', 'ma', 'ri', 'ny', 'nj', 'pa', 'nh', 'vt', 'me']
        for i, part in enumerate(parts):
            if part.lower() in state_abbrevs and i > 0:
                # City is likely the word before state
                city = parts[i - 1]
                break

        return zip_code, city

    def find_comparables(self, address, subject_data=None, max_comps=8):
        """Find comparable properties, filtering out distressed sales"""
        if not self.driver:
            return []

        try:
            clean_address = address.replace(' ', '-').replace(',', '')
            zip_code, city = self._extract_zip_and_city(address)

            # Build search URLs - try specific address first, then broaden to zip/city
            sold_urls = [
                f"https://www.zillow.com/homes/recently_sold/{clean_address}_rb/",
            ]
            # Add zip code search for broader comp pool
            if zip_code:
                sold_urls.append(f"https://www.zillow.com/homes/recently_sold/{zip_code}_rb/")
            # Add city+state search as fallback
            if city:
                city_clean = city.replace(' ', '-')
                sold_urls.append(f"https://www.zillow.com/homes/recently_sold/{city_clean}-CT_rb/")
            # Generic fallback
            sold_urls.append(f"https://www.zillow.com/{clean_address}_rb/sold_rb/")

            raw_comps = []
            filtered_out = []

            for url in sold_urls:
                try:
                    logger.info(f"Searching for comparables at: {url}")
                    self.driver.get(url)
                    time.sleep(3)

                    # Look for property cards
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
                                # Grab more than we need so we can filter
                                property_elements = elements[:max_comps * 3]
                                break
                        except:
                            continue

                    if not property_elements:
                        continue

                    for i, prop in enumerate(property_elements):
                        try:
                            full_card_text = prop.text

                            # --- DISTRESSED SALE FILTER ---
                            is_distressed, keyword = self._is_distressed_sale(full_card_text)
                            if is_distressed:
                                logger.info(f"FILTERED OUT comp {i}: distressed sale detected ('{keyword}')")
                                filtered_out.append({
                                    'reason': f'distressed: {keyword}',
                                    'text_preview': full_card_text[:100]
                                })
                                continue

                            comp_data = {
                                'address': 'Unknown Address',
                                'sale_price': None,
                                'sale_date': None,
                                'sqft': None,
                                'beds': None,
                                'baths': None,
                                'distance_miles': None,
                                'sale_type': 'standard',
                                'source': 'zillow_comps',
                                'scraped_at': time.time()
                            }

                            # Extract address
                            for addr_sel in ['[data-testid="property-card-addr"]', '.list-card-addr', '.property-card-addr', 'address']:
                                try:
                                    addr_elem = prop.find_element(By.CSS_SELECTOR, addr_sel)
                                    comp_data['address'] = addr_elem.text.strip()
                                    break
                                except:
                                    continue

                            # Extract price
                            for price_sel in ['[data-testid="property-card-price"]', '.list-card-price', '.property-card-price', '.price']:
                                try:
                                    price_elem = prop.find_element(By.CSS_SELECTOR, price_sel)
                                    price_text = price_elem.text.strip()
                                    if '$' in price_text:
                                        price_match = re.search(r'\$([0-9,]+)', price_text)
                                        if price_match:
                                            comp_data['sale_price'] = price_match.group(1).replace(',', '')
                                    break
                                except:
                                    continue

                            # Extract beds/baths/sqft
                            detail_text = full_card_text.lower()
                            bed_match = re.search(r'(\d+)\s*bed', detail_text)
                            if bed_match:
                                comp_data['beds'] = int(bed_match.group(1))
                            bath_match = re.search(r'(\d+(?:\.\d+)?)\s*bath', detail_text)
                            if bath_match:
                                comp_data['baths'] = float(bath_match.group(1))
                            sqft_match = re.search(r'([\d,]+)\s*(?:sqft|sq ft)', detail_text)
                            if sqft_match:
                                comp_data['sqft'] = int(sqft_match.group(1).replace(',', ''))

                            # --- COMP QUALITY FILTER ---
                            is_valid, reason = self._is_valid_comp(comp_data, subject_data)
                            if not is_valid:
                                logger.info(f"FILTERED OUT comp '{comp_data['address']}': {reason}")
                                filtered_out.append({
                                    'address': comp_data['address'],
                                    'reason': reason,
                                    'sale_price': comp_data.get('sale_price')
                                })
                                continue

                            raw_comps.append(comp_data)
                            logger.info(f"VALID comp: {comp_data['address']} - ${comp_data.get('sale_price', 'N/A')}")

                        except Exception as e:
                            logger.warning(f"Error processing comp {i}: {e}")
                            continue

                    if raw_comps:
                        break

                except Exception as e:
                    logger.warning(f"Error with URL {url}: {e}")
                    continue

            if filtered_out:
                logger.info(f"Filtered out {len(filtered_out)} distressed/non-comparable sales")
            if not raw_comps:
                logger.warning("No valid comparable properties found after filtering")
            else:
                logger.info(f"Found {len(raw_comps)} valid comparable properties (filtered {len(filtered_out)})")

            return raw_comps[:max_comps]

        except Exception as e:
            logger.error(f"Error finding comparables near {address}: {e}")
            return []

    def _merge_scraped_data(self, primary, secondary):
        """Merge two scraped data dicts — primary wins, secondary fills gaps"""
        if not secondary:
            return primary
        if not primary:
            return secondary
        merged = dict(primary)
        for key, val in secondary.items():
            if key in ('source', 'scraped_at'):
                continue
            if val and (not merged.get(key) or merged.get(key) in (None, 'Unknown', '', 'mentioned')):
                merged[key] = val
                logger.info(f"Filled '{key}' from {secondary.get('source', 'backup')}: {val}")
        if primary.get('source') and secondary.get('source'):
            merged['source'] = f"{primary['source']}+{secondary['source']}"
        return merged

    def scrape_property_and_comps(self, address):
        """Scrape property data from multiple sources, then find filtered comparables"""
        # Try Zillow first
        property_data = self.scrape_zillow(address)

        # Check if we're missing key fields — try Redfin as backup
        key_fields = ['beds', 'baths', 'sqft']
        missing = [f for f in key_fields if not (property_data or {}).get(f)]
        if missing:
            logger.info(f"Zillow missing {missing} — trying Redfin backup")
            redfin_data = self.scrape_redfin(address)
            property_data = self._merge_scraped_data(property_data, redfin_data)

        # Pass subject property data so comps can be filtered by similarity
        comparables = self.find_comparables(address, subject_data=property_data)

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