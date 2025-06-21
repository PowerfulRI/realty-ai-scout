# Claude Code Instructions for Realty AI Scout

## Project Overview
This is an AI-powered real estate analysis tool that scrapes property data from multiple sources and uses Claude AI to provide comprehensive property analysis, valuations, and market insights.

## Development Commands

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the application
python src/app.py
```

### Testing
```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_app.py

# Run with coverage
python -m pytest --cov=src tests/
```

### Code Quality
```bash
# Format code with black
black src/ tests/

# Lint with flake8
flake8 src/ tests/

# Type checking (if implemented)
mypy src/
```

## Project Structure
- `src/` - Main application code
- `templates/` - HTML templates for web interface
- `static/` - CSS and JavaScript files
- `tests/` - Unit tests
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variables template

## Key Components

### Data Pipeline
1. **Selenium Scraper** (`src/selenium_scraper.py`) - Multi-source property data collection
2. **Perplexity Client** (`src/perplexity_client.py`) - AI-powered market research
3. **Data Consolidator** (`src/data_consolidator.py`) - Merge and validate data from sources
4. **Claude Analyzer** (`src/claude_analyzer.py`) - Generate insights and recommendations

### Web Interface
- **Flask App** (`src/app.py`) - Main web application
- **HTML Template** (`templates/index.html`) - Single-page interface
- **CSS Styles** (`static/style.css`) - Custom styling

## API Keys Required
- `ANTHROPIC_API_KEY` - For Claude AI analysis
- `PERPLEXITY_API_KEY` - For market research
- Chrome WebDriver - For property data scraping

## Common Development Tasks

### Adding New Data Sources
1. Create scraper method in `src/selenium_scraper.py`
2. Add data consolidation logic in `src/data_consolidator.py`
3. Update confidence weights and validation rules

### Enhancing AI Analysis
1. Add new analysis methods to `src/claude_analyzer.py`
2. Create structured prompts for specific insights
3. Update web interface to display new analysis results

### Testing New Features
1. Write unit tests in `tests/` directory
2. Test with real addresses (use test data)
3. Validate API rate limits and error handling

## Deployment Notes
- Requires Chrome/Chromium for Selenium
- Set `SELENIUM_HEADLESS=True` for production
- Consider rate limiting for API calls
- Use environment variables for all secrets

## Weekend Development Priorities
1. Implement Selenium scraping for Zillow/Realtor.com
2. Set up Perplexity API integration
3. Build Claude AI analysis pipeline
4. Test end-to-end property analysis workflow
5. Polish web interface and error handling