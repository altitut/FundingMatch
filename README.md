# FundingMatch v2.0 - Comprehensive Funding Opportunity Matching System

![FundingMatch Logo](https://img.shields.io/badge/FundingMatch-v2.0-blue) ![AI Powered](https://img.shields.io/badge/AI-Powered-green) ![Real APIs](https://img.shields.io/badge/APIs-Real%20Data-orange)

A comprehensive AI-powered system for matching researchers with funding opportunities using real government APIs and advanced machine learning analysis.

## 🚀 Overview

FundingMatch v2.0 is an end-to-end solution that:
- **Analyzes research portfolios** using Gemini 2.5 Pro AI
- **Fetches real opportunities** from SAM.gov and SBIR.gov APIs
- **Matches opportunities** with AI-powered analysis
- **Generates comprehensive reports** with evidence and recommendations

## 📋 Table of Contents

- [Features](#-features)
- [System Requirements](#-system-requirements)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage Guide](#-usage-guide)
- [API Documentation](#-api-documentation)
- [Output Structure](#-output-structure)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)

## ✨ Features

### 🔬 **Real AI Analysis**
- **Gemini 2.5 Pro** integration for advanced PDF and document analysis
- Comprehensive semantic profile generation
- Evidence-based matching with confidence scores

### 🌐 **Live API Integration**
- **SAM.gov** - Federal contracting opportunities
- **SBIR.gov** - Small Business Innovation Research solicitations
- Real-time data with current/future deadlines

### 📊 **Intelligent Matching**
- AI-powered opportunity scoring (0-100%)
- Supporting evidence extraction
- Competitive advantage identification
- Strategic recommendation generation

### 📁 **Organized Output**
- Timestamped folders for results
- Comprehensive markdown reports
- Clickable opportunity links
- Processing summaries and caching

## 🔬 NSF Comprehensive Matcher (NEW)

### **Advanced NSF Funding Analysis**
The NSF Comprehensive Matcher (`nsf_comprehensive_matcher.py`) provides specialized analysis for National Science Foundation funding opportunities using pre-processed semantic data.

#### **Key Features**
- **Semantic Data Processing**: Utilizes comprehensive NSF funding semantic dataset (478+ opportunities)
- **Batch Processing**: Processes opportunities in batches of 50 with parallel workers (3 per batch)
- **Gemini 2.5 Pro Integration**: Advanced AI analysis with 60 RPM rate limiting
- **Detailed Results Table**: Comprehensive ranking with scores, analysis time, and URLs
- **Proposal Matching**: Analyzes successful/unsuccessful proposals for strategic recommendations
- **Selected Opportunities Export**: Saves high-scoring opportunities (≥70%) to dedicated file

#### **Usage**
```bash
# Quick mode - analyze 100 opportunities
python nsf_comprehensive_matcher.py --quick

# Full analysis - process all 478 opportunities
python nsf_comprehensive_matcher.py
```

#### **Data Sources**
- **NSF Semantic Data**: `FundingOpportunitiesManual/nsf_funding_semantic.json`
- **Researcher Profile**: Latest comprehensive semantic profile
- **Proposal Archive**: Analyzes both successful and unsuccessful proposals

#### **Output Files**
- **Detailed Report**: `opportunity_matches/NSF_Semantic_Matching_Report_<timestamp>.md`
- **Selected Opportunities**: `FundingOpportunitiesManual/nsf_funding_semantic_SELECTED.json`
- **Results Table**: Rank | Score | Program ID | Title | Summary | Analysis Time | URLs

#### **Performance Metrics**
- **Processing Speed**: ~4-6 opportunities per minute
- **Success Rate**: 27% high-scoring matches (≥70%) from test dataset
- **Batch Processing**: 50 opportunities per batch with 3 parallel workers
- **Rate Limiting**: 60 RPM for Gemini 2.5 Pro API compliance

#### **Recent Enhancements (V6)**
- Removed token management restrictions for comprehensive analysis
- Enhanced report formatting with proper markdown structure
- Improved JSON response parsing and error handling
- Added detailed results table at report top
- Implemented selected opportunities saving functionality

## 🛠 System Requirements

### **Environment**
- Python 3.8+
- macOS, Linux, or Windows
- Internet connection for API access

### **API Keys Required**
- **GEMINI_API_KEY** - For AI analysis (required)
- **SAM_GOV_API_KEY** - For SAM.gov data (required)
- **GRANTS_GOV_API_KEY** - For Grants.gov data (optional)

### **Python Dependencies**
```
google-genai==1.25.0
requests==2.31.0
python-dotenv==1.0.0
flask==3.0.0
flask-cors==4.0.0
```

## 📦 Installation

### 1. **Clone Repository**
```bash
git clone https://github.com/your-org/fundingmatch.git
cd fundingmatch
```

### 2. **Install Dependencies**
```bash
pip install -r backend/requirements.txt
```

### 3. **Setup Environment Variables**
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
SAM_GOV_API_KEY=your_sam_gov_api_key_here
GRANTS_GOV_API_KEY=your_grants_gov_api_key_here
```

### 4. **Prepare Input Documents**
Place your research documents in the `input_documents/` folder:
```
input_documents/
├── CV PI Your Name.pdf
├── Proposals/
│   ├── Successful/
│   │   └── NSF_SBIR_Phase1.pdf
│   └── NotSuccessful/
│       └── NIH_R01.pdf
└── ResearchPapers/
    ├── First_author_journals/
    └── Co-author/
```

### 5. **Create Document List**
Update `all_documents.txt` with paths to your documents:
```
input_documents/CV PI Your Name.pdf
input_documents/Proposals/Successful/NSF_SBIR_Phase1.pdf
input_documents/ResearchPapers/First_author_journals/paper1.pdf
```

## 🚀 Quick Start

### **Option 1: Complete Workflow (Recommended)**
```bash
python main.py
```
This executes the complete workflow:
1. **Phase 1**: Comprehensive portfolio analysis using Gemini 2.5 Pro
2. **Phase 2**: Real-time opportunity matching with government APIs
3. **Output**: Timestamped folders with results and comprehensive reports

### **Option 2: NSF Comprehensive Matcher (NEW)**
```bash
# Quick analysis of 100 NSF opportunities
python nsf_comprehensive_matcher.py --quick

# Full analysis of all 478 NSF opportunities
python nsf_comprehensive_matcher.py
```
This specialized tool:
1. **Semantic Analysis**: Uses pre-processed NSF funding semantic data
2. **Batch Processing**: Processes opportunities in optimized batches
3. **Detailed Reports**: Generates comprehensive analysis with results table
4. **Selected Opportunities**: Saves high-scoring matches for follow-up

### **Option 3: Step-by-Step Execution**

### **Step 1: Generate Semantic Profile**
```bash
python comprehensive_portfolio_analysis.py
```
This will:
- Analyze all documents using Gemini 2.5 Pro AI
- Create semantic profile in `semantic_profiles_<timestamp>/`
- Generate processing summary

### **Step 2: Find Opportunities**
```bash
python run_real_opportunity_matching.py
```
This will:
- Load the latest semantic profile
- Fetch real opportunities from APIs
- Generate matches and save to `opportunity_matches_<timestamp>/`

### **Step 3: Review Results**
Check the generated reports in the timestamped folders:
- **Semantic Profile**: `semantic_profiles_*/alfredo_*_semantic_profile_*.json`
- **Match Report**: `opportunity_matches_*/COMPREHENSIVE_OPPORTUNITIES_match_report_*.md`

## 📖 Usage Guide

### **Complete Workflow Execution**

```bash
# Execute the complete FundingMatch workflow
python main.py
```

**Features:**
- **Environment Check**: Validates API keys and required files
- **Phase 1**: Comprehensive portfolio analysis
- **Phase 2**: Real-time opportunity matching
- **Summary Report**: Detailed execution summary with timings
- **Error Handling**: Graceful failure handling with clear error messages

### **Comprehensive Portfolio Analysis**

```bash
# Standard incremental analysis
python comprehensive_portfolio_analysis.py

# Force reprocess all documents
python comprehensive_portfolio_analysis.py --force
```

**Features:**
- **Incremental Processing**: Only analyzes new/changed documents
- **Document Classification**: Automatically categorizes documents by type
- **URL Analysis**: Processes web links from JSON metadata
- **Real AI Analysis**: Uses Gemini 2.5 Pro for advanced PDF and document understanding

### **Comprehensive Funding Analysis**

```bash
# Process new CSV files only (incremental)
python comprehensive_funding_analysis.py

# Quick mode - process first 5 opportunities
python comprehensive_funding_analysis.py --quick

# Test mode - process 82 opportunities from each file
python comprehensive_funding_analysis.py --test

# Force reprocess all opportunities
python comprehensive_funding_analysis.py --force
```

**Features:**
- **Incremental Processing**: Only processes new CSV files, skips duplicates
- **Standardized Data Structure**: Consistent format across all opportunities
- **URL Content Processing**: Fetches and analyzes program/solicitation pages
- **Real AI Analysis**: Uses Gemini 2.5 Pro for comprehensive opportunity analysis
- **Append Mode**: Adds new opportunities to existing `COMPLETE_funding_semantic.json`

### **Real Opportunity Matching**

```bash
python run_real_opportunity_matching.py
```

**Process:**
1. **Profile Loading**: Automatically finds latest semantic profile
2. **API Integration**: Fetches from SAM.gov and SBIR.gov
3. **AI Matching**: Analyzes opportunities against profile
4. **Report Generation**: Creates comprehensive markdown reports

### **Advanced Usage**

#### **Custom Document Types**
Modify `classify_document_by_path()` in `comprehensive_portfolio_analysis.py`:
```python
def classify_document_by_path(file_path):
    if 'your_custom_type' in file_path.lower():
        return "Your Custom Type"
    return "Technical Report"
```

#### **API Configuration**
Modify search parameters in `run_real_opportunity_matching.py`:
```python
sam_opportunities = sam_api.search_opportunities(
    keywords=["your", "custom", "keywords"],
    limit=50
)
```

## 🔌 API Documentation

### **SAM.gov API**
- **Endpoint**: `https://api.sam.gov/opportunities/v2/search`
- **Authentication**: API Key required
- **Rate Limits**: 1000 requests/hour
- **Documentation**: [SAM.gov API Guide](https://open.gsa.gov/api/opportunities-api/)

### **SBIR.gov API**
- **Endpoint**: `https://api.www.sbir.gov/public/api/solicitations`
- **Authentication**: No key required
- **Rate Limits**: 50 rows per request
- **Documentation**: [SBIR.gov API Guide](https://www.sbir.gov/api/solicitation)

### **Gemini API**
- **Model**: `gemini-2.5-pro`
- **Authentication**: API Key required
- **Rate Limits**: 1000 requests/minute
- **Documentation**: [Gemini API Guide](https://ai.google.dev/docs)

## 📁 Output Structure

```
FundingMatch/
├── semantic_profiles_20250710_083216/
│   ├── alfredo_costilla_reyes_COMPREHENSIVE_semantic_profile_20250710_083245.json
│   └── processing_summary_20250710_083245.json
├── opportunity_matches_20250710_083216/
│   └── COMPREHENSIVE_OPPORTUNITIES_match_report_20250710_085123.md
├── FundingOpportunities/
│   ├── COMPLETE_funding_semantic.json        # Complete funding opportunities dataset
│   ├── ProcessedOpportunities.md             # List of processed opportunities
│   ├── Ingested/                             # Processed CSV files
│   └── *.csv                                 # New CSV files to process
├── FundingOpportunitiesManual/
│   ├── nsf_funding_semantic.json        # NSF semantic dataset (478 opportunities)
│   └── nsf_funding_semantic_SELECTED.json  # High-scoring opportunities (≥70%)
├── opportunity_matches/
│   └── COMPLETE_Funding_Semantic_Matching_Report_<timestamp>.md  # Complete analysis report
├── backend/
│   ├── tests/           # Test files (removed after session)
│   ├── sam_api.py      # SAM.gov API integration
│   ├── sbir_api.py     # SBIR.gov API integration
│   └── enhanced_matcher.py  # AI matching engine
├── input_documents/    # Your research documents
├── comprehensive_portfolio_analysis.py  # Main analysis script
├── comprehensive_funding_analysis.py   # Funding opportunities analysis script
├── run_real_opportunity_matching.py     # Main matching script
├── nsf_comprehensive_matcher.py        # NSF specialized matcher
└── README.md          # This file
```

### **Semantic Profile Structure**
```json
{
  "profile_metadata": {
    "primary_researcher": "Researcher Name",
    "total_documents": 47,
    "processing_date": "2025-07-10"
  },
  "portfolio_summary": {
    "research_domains": ["AI", "Machine Learning"],
    "funding_track_record": {
      "total_secured": 1275000,
      "successful_proposals": 7
    }
  },
  "synthesis": {
    "core_competencies": [...],
    "strategic_advantages": [...],
    "funding_readiness": {...}
  }
}
```

### **Match Report Features**
- **Executive Summary** with key statistics
- **Top Matches** with 75%+ confidence scores
- **Supporting Evidence** from researcher's portfolio
- **Competitive Advantages** identified by AI
- **Strategic Recommendations** for proposal development
- **Clickable Links** to opportunity details

## 🔧 Troubleshooting

### **Common Issues**

#### **API Key Errors**
```
❌ GEMINI_API_KEY not found in environment variables
```
**Solution**: Ensure `.env` file exists with valid API keys

#### **No Opportunities Found**
```
❌ No opportunities found from APIs
```
**Solutions**:
- Check internet connectivity
- Verify API keys are valid
- Try different search keywords

#### **Profile Loading Errors**
```
❌ Error: No semantic profile found
```
**Solution**: Run `comprehensive_portfolio_analysis.py` first

#### **Document Processing Errors**
```
❌ Error processing document: Permission denied
```
**Solutions**:
- Check file permissions
- Ensure PDFs are not encrypted
- Verify file paths in `all_documents.txt`

### **Performance Optimization**

#### **Incremental Processing**
The system automatically skips unchanged documents. To force reprocessing:
```bash
python comprehensive_portfolio_analysis.py --force
```

#### **API Rate Limiting**
- SAM.gov: Built-in delays between requests
- SBIR.gov: Automatic fallback methods
- Gemini: 1-second delays between document analyses

## 🧪 Testing

### **Run Test Suite**
```bash
cd backend/tests
python -m pytest test_*.py -v
```

### **Test Individual Components**
```bash
# Test SAM.gov API
python backend/tests/test_sam_api.py

# Test SBIR.gov API
python backend/tests/test_sbir_api.py

# Test Document Processing
python backend/tests/test_document_processor.py
```

## 🤝 Contributing

### **Development Setup**
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request

### **Code Style**
- Follow PEP 8 guidelines
- Add docstrings to all functions
- Include type hints where appropriate
- Write comprehensive tests

## 📊 System Statistics

- **Document Types Supported**: 10+ (CV, Proposals, Papers, etc.)
- **API Sources**: 2 live + 1 optional
- **AI Model**: Gemini 2.5 Pro (2M context)
- **Output Formats**: JSON, Markdown
- **Success Rate**: 30%+ high-quality matches (27% for NSF matcher)
- **Processing Speed**: ~1-2 seconds per document, ~4-6 NSF opportunities per minute
- **NSF Dataset**: 478+ opportunities with comprehensive semantic analysis
- **Batch Processing**: 50 opportunities per batch with 3 parallel workers

## 🔮 Future Enhancements

- **NIH Reporter Integration** for funding history
- **NSF Awards Database** for trend analysis
- **Automated Proposal Generation** based on matches
- **Team Collaboration Features** for multi-PI proposals
- **Dashboard Web Interface** for visualization

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google Gemini AI** for advanced document analysis
- **SAM.gov** for federal opportunity data
- **SBIR.gov** for small business research opportunities
---

**Built with ❤️**