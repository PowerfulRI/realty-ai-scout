# 🏠 Realty AI Scout

AI-powered real estate analysis tool for property valuation, comparable analysis, and market insights using multi-source data aggregation and Claude AI.

## 🚀 Features

- **Multi-Source Data Collection**: Scrapes property data from Zillow, Realtor.com, and other sources using Selenium
- **AI-Powered Market Research**: Uses Perplexity API for comprehensive market intelligence
- **Smart Comparable Analysis**: Finds and analyzes comparable properties with advanced scoring algorithms
- **Claude AI Analysis**: Generates property valuations, listing descriptions, and investment insights
- **Data Consolidation**: Merges and validates data from multiple sources with conflict resolution
- **Professional Reports**: Creates comprehensive market reports and analysis

## 🛠️ Tech Stack

- **Backend**: Python Flask
- **Web Scraping**: Selenium WebDriver
- **AI APIs**: Claude (Anthropic), Perplexity
- **Database**: SQLite (development), PostgreSQL (production ready)
- **Frontend**: HTML/CSS/JavaScript (simple UI)

## 📦 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/PowerfulRI/realty-ai-scout.git
   cd realty-ai-scout
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Chrome WebDriver**
   ```bash
   # macOS
   brew install chromedriver
   
   # Or download from https://chromedriver.chromium.org/
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

## 🔧 Configuration

Create a `.env` file with your API keys:

```env
# AI API Keys
ANTHROPIC_API_KEY=your_claude_api_key_here
PERPLEXITY_API_KEY=your_perplexity_api_key_here

# Flask Configuration
FLASK_SECRET_KEY=your_secret_key_here
FLASK_ENV=development

# Database (optional)
DATABASE_URL=sqlite:///realty_scout.db
```

## 🚀 Quick Start

1. **Start the application**
   ```bash
   python src/app.py
   ```

2. **Open your browser**
   ```
   http://localhost:5000
   ```

3. **Enter a property address**
   - The tool will scrape data from multiple sources
   - Generate AI-powered analysis and insights
   - Provide comparable properties and market trends

## 📊 How It Works

### Data Collection Pipeline
1. **Address Input** → Standardized address format
2. **Selenium Scraping** → Extract property data from multiple real estate sites
3. **Perplexity Research** → AI-powered market research and verification
4. **Data Consolidation** → Merge and validate data with conflict resolution
5. **Claude Analysis** → Generate insights, valuations, and recommendations

### Comparable Analysis
- Finds properties within 1-mile radius
- Filters by similar size, bedrooms, bathrooms
- Recent sales within 3-6 months
- Scores comparables using weighted algorithm:
  - Proximity: 40%
  - Recency: 25% 
  - Size similarity: 15%
  - Condition similarity: 10%
  - Features similarity: 10%

## 🏗️ Project Structure

```
realty-ai-scout/
├── src/
│   ├── app.py                 # Flask web application
│   ├── selenium_scraper.py    # Multi-source data scraping
│   ├── perplexity_client.py   # Market research API client
│   ├── claude_analyzer.py     # AI analysis and insights
│   ├── data_consolidator.py   # Data merging and validation
│   └── __init__.py
├── templates/
│   └── index.html            # Web interface
├── static/
│   └── style.css            # Styling
├── tests/
│   └── test_*.py            # Unit tests
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore file
└── README.md               # This file
```

## 🔍 API Usage

### Property Analysis
```python
from src.selenium_scraper import PropertyScraper
from src.perplexity_client import PerplexityClient
from src.claude_analyzer import ClaudeAnalyzer

# Initialize components
scraper = PropertyScraper()
perplexity = PerplexityClient()
analyzer = ClaudeAnalyzer()

# Analyze property
address = "123 Main St, Anytown, CA"
property_data = scraper.scrape_zillow(address)
market_data = perplexity.research_property(address)
analysis = analyzer.analyze_property_value(property_data, [], market_data)
```

## 🧪 Testing

Run the test suite:
```bash
python -m pytest tests/
```

## 📈 Weekend Development Timeline

### Saturday (8-10 hours)
- ✅ Project setup and Flask app
- ✅ Selenium scraping implementation
- ✅ Property data extraction
- ✅ Basic comparable search
- ✅ Claude API integration

### Sunday (8-10 hours)
- 🔄 Web interface development
- 🔄 Property analysis pipeline
- 🔄 AI-generated insights
- 🔄 Styling and error handling
- 🔄 Testing and debugging

## 🚧 Development Status

- [x] Project structure and setup
- [x] Core modules created
- [x] Multi-source scraping framework
- [x] AI integration architecture
- [ ] Selenium scraping implementation
- [ ] Perplexity API integration
- [ ] Claude analysis pipeline
- [ ] Web interface
- [ ] Data validation and testing

## 🔮 Future Enhancements

- **Image Analysis**: Property condition assessment from photos
- **Advanced UI**: React frontend with interactive charts
- **Database**: PostgreSQL for data persistence
- **Caching**: Redis for performance optimization
- **Authentication**: User accounts and saved searches
- **Mobile App**: React Native mobile application
- **API**: RESTful API for third-party integrations

## 🛡️ Legal & Compliance

- Respects robots.txt and rate limiting
- Focuses on publicly available data
- Implements proper error handling and fallbacks
- No unauthorized access to protected content

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

- Create an [Issue](https://github.com/PowerfulRI/realty-ai-scout/issues) for bug reports
- Start a [Discussion](https://github.com/PowerfulRI/realty-ai-scout/discussions) for questions
- Check the [Wiki](https://github.com/PowerfulRI/realty-ai-scout/wiki) for documentation

## ⚠️ Disclaimer

This tool is for informational purposes only. Property valuations and market analysis should not be considered as professional appraisals or investment advice. Always consult with qualified real estate professionals for important decisions.

---

**Built with ❤️ using Claude Code and AI-powered development**