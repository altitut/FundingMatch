# FundingMatch

An AI-powered funding opportunity matching system that helps researchers find relevant grants and funding opportunities based on their research profiles.

## Overview

FundingMatch uses Google's Gemini AI and vector embeddings to match researcher profiles with funding opportunities from various government sources including NSF, SBIR, SAM.gov, and Grants.gov. The system analyzes research papers, CVs, and online profiles to create comprehensive researcher profiles and matches them with relevant funding opportunities.

## Features

- **AI-Powered Matching**: Uses Gemini embeddings and vector similarity search for accurate matching
- **Multi-Source Data Ingestion**: 
  - PDF documents (CVs, research papers, proposals)
  - JSON profiles with bulk URL processing
  - Web content from faculty pages, Google Scholar, etc.
- **Real-Time Progress Tracking**: Server-sent events for live updates during processing
- **Duplicate Detection**: Smart deduplication of funding opportunities
- **RAG-Enhanced Explanations**: AI-generated explanations for why opportunities match
- **Modern Web Interface**: React-based frontend with Tailwind CSS

## Architecture

### Backend (Python/Flask)
- `app.py`: Main Flask application server
- `backend/embeddings_manager.py`: Gemini embeddings API integration
- `backend/vector_database.py`: ChromaDB vector storage
- `backend/funding_opportunities_manager.py`: CSV processing and opportunity management
- `backend/user_profile_manager.py`: User profile creation and management
- `backend/url_content_fetcher.py`: Web scraping for profile enrichment
- `backend/pdf_extractor.py`: PDF text extraction and analysis

### Frontend (React/TypeScript)
- `frontend/src/components/DataIngestion.tsx`: CSV upload and opportunity management
- `frontend/src/components/UserProfile.tsx`: User profile creation and editing
- `frontend/src/components/Matching.tsx`: Funding opportunity matching interface

## Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- Google Gemini API key
- (Optional) SAM.gov and Grants.gov API keys

### Installation

1. Clone the repository:
```bash
git clone https://github.com/altitut/FundingMatch.git
cd FundingMatch
```

2. Create a `.env` file with your API keys:
```env
GEMINI_API_KEY=your_gemini_api_key
SAM_GOV_API_KEY=your_sam_gov_api_key
GRANTS_GOV_API_KEY=your_grants_gov_api_key
```

3. Install dependencies and start the application:
```bash
./start_app.sh
```

This will:
- Create a Python virtual environment
- Install Python dependencies
- Install frontend dependencies
- Start both backend (port 5001) and frontend (port 3000)

## Usage

### 1. Data Ingestion
Navigate to the Data Ingestion tab to upload CSV files containing funding opportunities. The system will:
- Process opportunities and generate embeddings
- Detect and skip duplicates
- Extract deadlines and enrich with URL content
- Display processed and unprocessed opportunities

### 2. User Profile Creation
In the User Profile tab:
- Enter your name and research interests
- Upload PDF documents (CV, papers, proposals)
- Add URLs to your online profiles
- Or upload a JSON file for bulk URL processing

Example JSON format:
```json
{
  "person": {
    "name": "Your Name",
    "summary": "Brief bio",
    "links": [
      {
        "url": "https://faculty.university.edu/profile",
        "type": "faculty_profile"
      },
      {
        "url": "https://scholar.google.com/citations?user=ID",
        "type": "academic_profile"
      }
    ],
    "biographical_information": {
      "research_interests": ["AI", "Machine Learning"],
      "education": [],
      "awards": []
    }
  }
}
```

### 3. Matching
Go to the Matching tab to:
- Select a user profile
- View matched funding opportunities
- See AI-generated explanations for each match
- Export results

## Data Sources

The system can process funding opportunities from:
- NSF (National Science Foundation)
- SBIR/STTR programs
- SAM.gov federal opportunities
- Grants.gov
- Custom CSV files

## API Endpoints

- `POST /api/ingest/csv` - Upload funding opportunity CSV
- `POST /api/profile/create` - Create user profile
- `POST /api/profile/update` - Update existing profile
- `GET /api/users` - List all users
- `POST /api/match` - Match user with opportunities
- `GET /api/opportunities` - List all opportunities

## Performance

- Gemini API: 60 requests per minute rate limit
- Embedding generation: ~0.1s per document
- Vector search: Sub-second for 10k+ opportunities
- Batch processing: 5-20 opportunities at a time

## Troubleshooting

### Port Already in Use
The start script automatically kills processes on ports 5001 and 3000. If issues persist:
```bash
./stop_app.sh
./start_app.sh
```

### ChromaDB Corruption
If you see "no such column" errors, the vector database is corrupted:
```bash
rm -rf chroma_db
./start_app.sh
```

### Missing Dependencies
```bash
# Python
pip install -r requirements.txt

# Frontend
cd frontend && npm install
```

## Development

### Running Tests
```bash
# No automated tests currently
# Use --quick and --test flags on processing scripts for testing
```

### Adding New Funding Sources
1. Create a CSV processor in `backend/funding_opportunities_manager.py`
2. Add field mappings for the new format
3. Update the frontend if needed

## License

This project is licensed under the MIT License.

## Contributors

- Alfredo Costilla-Reyes (alfredocostilla)

## Acknowledgments

- Google Gemini for embeddings and AI capabilities
- ChromaDB for vector storage
- NSF, SBIR, SAM.gov for funding data