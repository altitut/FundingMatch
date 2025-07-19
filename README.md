# FundingMatch

An AI-powered funding opportunity matching system that connects researchers with relevant grants and funding opportunities using semantic search and advanced embeddings.

## Overview

FundingMatch uses Google's Gemini AI (2.0 Flash) and ChromaDB vector database to analyze researcher profiles and match them with funding opportunities from government sources and custom CSV files. The system provides intelligent matching with confidence scores ranging from 20% to 95%, along with AI-generated explanations for each match.

## Features

- **Smart Document Analysis**: Processes research papers, CVs, proposals, and web content to build comprehensive researcher profiles
- **Multi-Source Funding Data**: Integrates with SAM.gov, SBIR.gov, NSF, and custom CSV sources
- **Semantic Matching**: Uses 768-dimensional Gemini embeddings for accurate similarity search
- **AI Explanations**: Provides detailed match explanations and proposal retrofitting suggestions
- **Real-time Progress**: Shows live updates during CSV processing with opportunity-by-opportunity progress
- **Deadline Management**: Automatically extracts and tracks funding deadlines using multiple methods
- **Rate Limiting**: Handles API quotas gracefully with exponential backoff
- **Data Isolation**: Separate vector databases for users, opportunities, and proposals to prevent corruption
- **High-Confidence Tracking**: Highlights matches above 80% confidence with detailed statistics

## Architecture

```
Frontend (React/TypeScript)
    ↓
Backend API (Flask/Python)
    ↓
Vector Database (ChromaDB)
    ↓
AI Services (Gemini 2.0)
```

### Backend Components (Python/Flask)
- `app.py`: Main Flask application server with SSE support
- `backend/embeddings_manager.py`: Gemini text-embedding-004 integration
- `backend/isolated_vector_database.py`: Isolated ChromaDB instances for data safety
- `backend/funding_opportunities_manager.py`: CSV processing with deadline extraction
- `backend/user_profile_manager.py`: Profile creation and document processing
- `backend/url_content_fetcher.py`: Web scraping for profile enrichment
- `backend/pdf_extractor.py`: PDF text extraction using pypdf
- `backend/rate_limiter.py`: API rate limiting with exponential backoff
- `backend/matching_results_manager.py`: User-specific match storage

### Frontend Components (React/TypeScript)
- `frontend/src/components/DataIngestion.tsx`: CSV upload with real-time progress
- `frontend/src/components/UserProfile.tsx`: Profile management with drag-and-drop
- `frontend/src/components/Matching.tsx`: Opportunity matching with AI explanations
- `frontend/src/components/OpportunityDetail.tsx`: Detailed opportunity view

## Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- Google Cloud account with Gemini API access
- (Optional) SAM.gov API key for government opportunities

### Backend Setup

1. Clone the repository:
```bash
git clone https://github.com/altitut/FundingMatch.git
cd FundingMatch
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r backend/requirements.txt
```

4. Create `.env` file:
```env
GEMINI_API_KEY=your_gemini_api_key
SAM_GOV_API_KEY=your_sam_gov_key  # Optional
GRANTS_GOV_API_KEY=your_grants_gov_key  # Optional
```

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Build the frontend:
```bash
npm run build
```

### Quick Start

Run the complete application:
```bash
./start_app.sh
```

This will:
- Kill any existing processes on ports 8787 and 3000
- Activate the Python virtual environment
- Start the Flask backend on port 8787
- Start the React frontend on port 3000
- Open the application in your browser

## Usage

### 1. Upload Funding Opportunities

Navigate to the **Data Ingestion** tab:
1. Click "Select CSV File" or drag and drop
2. Required columns: `title`, `description`, `url`, `agency`, `keywords`
3. Optional: `close_date`, `Next due date (Y-m-d)`
4. Watch real-time progress as opportunities are processed
5. View statistics including high-confidence matches

The system will:
- Show progress for each opportunity (e.g., "Processing opportunity 23 of 478")
- Extract deadlines from CSV, URLs, or using AI
- Skip duplicates and expired opportunities
- Generate 768-dimensional embeddings for each opportunity

### 2. Create User Profile

Go to the **User Profile** tab:
1. Enter researcher name and expertise areas
2. Upload PDFs (papers, CV, proposals) - drag and drop supported
3. Add URLs to online profiles (faculty pages, Google Scholar, etc.)
4. Click "Create Profile" to generate embeddings

Advanced option - JSON bulk upload:
```json
{
  "person": {
    "name": "Dr. Jane Smith",
    "summary": "AI researcher focusing on machine learning applications",
    "links": [
      {"url": "https://faculty.university.edu/jsmith", "type": "faculty_profile"},
      {"url": "https://scholar.google.com/citations?user=ABC123", "type": "academic_profile"},
      {"url": "https://orcid.org/0000-0000-0000-0000", "type": "orcid"}
    ],
    "biographical_information": {
      "research_interests": ["Artificial Intelligence", "Machine Learning", "Computer Vision"],
      "education": [
        {"degree": "PhD", "field": "Computer Science", "institution": "MIT", "year": 2018}
      ],
      "awards": [
        {"name": "NSF CAREER Award", "year": 2023}
      ]
    }
  }
}
```

### 3. Run Matching

Go to the **Matching** tab:
1. Select a user profile from the dropdown
2. View funding opportunities sorted by confidence score (95% to 20%)
3. Click "Show AI Explanation" for detailed match reasoning
4. Top 10 matches shown as detailed cards
5. Additional matches in a compact list view

Match scores indicate:
- **90-95%**: Excellent match - strongly aligned with research
- **80-89%**: High match - good alignment, worth pursuing
- **70-79%**: Moderate match - some alignment, review carefully
- **Below 70%**: Low match - limited alignment

### CSV Format Example

```csv
title,description,url,agency,keywords,close_date
"AI Research Grant","Funding for artificial intelligence research in healthcare","https://example.gov/ai-grant","NSF","AI,machine learning,healthcare,research","2025-12-31"
"Quantum Computing Initiative","Support for quantum computing hardware development","https://example.gov/quantum","DOE","quantum,computing,hardware","2025-11-15"
```

## API Endpoints

### Profile Management
- `GET /api/profile/users` - List all user profiles
- `POST /api/profile/create` - Create new user profile
- `POST /api/profile/update` - Update existing profile
- `POST /api/profile/process?userId={id}` - Reprocess user embeddings
- `DELETE /api/profile/delete` - Delete user profile

### Funding Opportunities
- `POST /api/ingest/csv` - Upload CSV file with progress tracking
- `GET /api/ingest/progress/<session_id>` - SSE endpoint for progress
- `GET /api/opportunities` - List all opportunities
- `GET /api/opportunities/unprocessed` - Get unprocessed tracking data
- `POST /api/cleanup-expired` - Remove expired opportunities

### Matching
- `POST /api/match` - Run opportunity matching for a user
- `GET /api/matches` - Get saved match results
- `POST /api/opportunity/<index>/explain` - Get AI explanation for match

### Statistics
- `GET /api/stats` - Get system statistics and high-confidence matches

## Performance & Limits

- **Gemini API**: 10 requests/minute (with automatic rate limiting)
- **Embedding generation**: ~0.1s per document
- **Vector search**: <100ms for 10k+ opportunities
- **Batch processing**: 5 opportunities per batch
- **CSV processing**: ~2-3 opportunities/second
- **Max embeddings dimension**: 768 (Gemini text-embedding-004)

## Troubleshooting

### Common Issues

1. **"Documents: 0, URLs: 0" on reprocessing**:
   - This has been fixed in the latest version
   - The system now properly counts all PDFs in the uploads folder

2. **Low matching scores (all below 40%)**:
   - Fixed in latest version with proper L2 distance normalization
   - Scores now properly range from 20% to 95%

3. **Gemini API quota errors (429 RESOURCE_EXHAUSTED)**:
   - Automatic rate limiting with exponential backoff implemented
   - System will retry failed requests automatically

4. **ChromaDB "no such column" errors**:
   - Delete the corrupted database folders:
   ```bash
   rm -rf chroma_db_users chroma_db_opportunities chroma_db_proposals
   ```
   - Restart the application

5. **Progress not showing during CSV upload**:
   - Ensure your browser supports Server-Sent Events
   - Check browser console for SSE connection errors

### Debug Mode

Enable detailed logging:
```bash
export FLASK_DEBUG=1
python app.py
```

### Port Conflicts

If ports are already in use:
```bash
# Kill processes on specific ports
lsof -i :8787 | grep LISTEN | awk '{print $2}' | xargs kill -9
lsof -i :3000 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

## Advanced Features

### Deadline Extraction

The system uses a multi-stage approach for deadline extraction:
1. **CSV fields**: Checks `close_date`, `Next due date (Y-m-d)` columns
2. **URL scraping**: Extracts deadlines from opportunity websites
3. **AI extraction**: Uses Gemini to find deadlines in descriptions
4. **Date parsing**: Handles multiple formats including duplicated dates

### Similarity Scoring Algorithm

```python
# L2 distance to similarity conversion
distance = min(2.0, max(0.0, distance))  # Clamp to [0, 2]
similarity = 1 - (distance / 2.0)  # Convert to [0, 1]

# Exponential transformation for better spread
normalized = (similarity - min_sim) / (max_sim - min_sim)
transformed = 1 - exp(-3 * normalized)
confidence = 20 + (transformed * 75)  # Final range: [20%, 95%]
```

### Data Isolation

The system uses three separate ChromaDB instances:
- `chroma_db_users`: User profiles and embeddings
- `chroma_db_opportunities`: Funding opportunities
- `chroma_db_proposals`: Historical proposals (future feature)

This prevents cross-contamination of data during corruption events.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style
- Python: Follow PEP 8
- TypeScript: Use ESLint configuration
- Commits: Use conventional commit messages

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

**Alfredo Costilla-Reyes** (altitut)
- Email: alfredo@altitut.ai
- GitHub: [@altitut](https://github.com/altitut)

## Acknowledgments

- Google Gemini team for excellent embeddings API
- ChromaDB for reliable vector storage
- Flask and React communities for great frameworks
- Government agencies (NSF, SBIR, SAM.gov) for public funding data