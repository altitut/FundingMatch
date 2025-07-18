# FundingMatch - AI-Powered Funding Opportunity Matching System

## Overview

FundingMatch is an intelligent system that matches researchers with relevant funding opportunities using advanced embeddings and AI-powered explanations. It processes funding opportunity data from CSV files, creates semantic embeddings, matches them with user profiles extracted from PDFs and structured data, and provides detailed explanations using Google's Gemini AI.

## Features

- **Semantic Matching**: Uses Google Gemini embeddings to match researchers with funding opportunities based on semantic similarity
- **Multi-source Profile Creation**: Extracts user information from PDFs, JSON files, and URLs
- **RAG-Powered Explanations**: Provides detailed explanations for why opportunities match, identifies reusable content, and suggests next steps
- **Automated Processing**: Tracks processed opportunities, removes expired ones, and enriches data with URL content
- **Comprehensive Reporting**: Generates detailed matching reports with confidence scores

## System Requirements

- Python 3.8+
- Google Gemini API key
- ChromaDB for vector storage
- Internet connection for URL content fetching

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd FundingMatch
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables in `.env`:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

## Project Structure

```
FundingMatch/
├── backend/                      # Core functionality modules
│   ├── embeddings_manager.py     # Gemini embeddings generation
│   ├── vector_database.py        # ChromaDB vector storage
│   ├── funding_opportunities_manager.py  # CSV processing & tracking
│   ├── user_profile_manager.py   # User profile creation
│   ├── pdf_extractor.py          # PDF text extraction
│   ├── url_content_fetcher.py    # URL content extraction
│   └── rag_explainer.py          # RAG explanation generation
├── FundingOpportunities/         # Input CSV files
│   └── Ingested/                 # Processed CSV files
├── input_documents/              # User documents
│   ├── *.pdf                     # User PDFs (CV, papers, etc.)
│   └── *.json                    # User profile JSON
├── output_results/               # Generated reports
├── chroma_db/                    # Vector database storage
└── release_notes/                # Documentation archive
```

## How It Works

### Step 1: Process Funding Opportunities

```bash
python process_csv_to_embeddings.py
```

This script:
- Scans `FundingOpportunities/` folder for CSV files
- Extracts funding opportunity data
- Fetches additional content from URLs in the CSV
- Generates embeddings using Gemini API
- Stores in ChromaDB vector database
- Moves processed files to `Ingested/` folder
- Tracks processed opportunities to avoid duplicates

**Input**: CSV files in `FundingOpportunities/` with columns:
- `title`: Opportunity title
- `description`: Detailed description
- `url`: Link to full details
- `agency`: Funding agency
- `keywords`: Relevant keywords
- `close_date`, `due_date`, or `deadline`: Expiration date

**Output**: Embeddings stored in ChromaDB

### Step 2: Create User Profile

```bash
python create_user_profile.py
```

This script:
- Reads user JSON file from `input_documents/`
- Extracts text from PDF documents (CV, papers, proposals)
- Fetches content from URLs in user profile
- Combines all information into a comprehensive profile
- Generates and stores profile embeddings

**Input**:
- JSON file: `input_documents/<username>.json` with structure:
```json
{
  "person": {
    "name": "User Name",
    "biographical_information": {
      "research_interests": ["AI", "ML", ...],
      "education": [...],
      "awards": [...]
    },
    "links": [
      {"url": "https://...", "type": "faculty_profile"}
    ]
  }
}
```
- PDF files in `input_documents/`

**Output**: User profile embeddings in ChromaDB

### Step 3: Match User with Opportunities

```bash
python match_opportunities.py
```

This script:
- Retrieves user profile embeddings
- Searches for similar funding opportunities
- Calculates confidence scores
- Ranks opportunities by relevance

**Output**: `output_results/user_funding_matches.json`

### Step 4: Generate RAG Explanations

```bash
python generate_rag_explanations.py
```

This script:
- Takes top matched opportunities
- Generates personalized explanations using Gemini
- Identifies reusable proposals/papers
- Provides specific next steps

**Output**: `output_results/user_funding_matches_explained.json`

### Step 5: Run Complete Pipeline

```bash
python main.py
```

Runs the entire pipeline:
1. Process any new CSV files
2. Create/update user profile
3. Match with opportunities
4. Generate explanations for top matches
5. Save comprehensive report

## Output Files

### user_funding_matches.json
```json
{
  "user": {
    "name": "User Name",
    "research_interests": [...]
  },
  "matches": [
    {
      "title": "Opportunity Title",
      "confidence_score": 85.5,
      "agency": "NSF",
      "deadline": "2025-12-31",
      "url": "https://..."
    }
  ]
}
```

### user_funding_matches_explained.json
```json
{
  "explained_opportunities": [
    {
      "title": "Opportunity Title",
      "confidence_score": 85.5,
      "rag_explanation": {
        "match_explanation": "This opportunity aligns with your expertise in...",
        "reusable_content": [
          {
            "document": "previous_proposal.pdf",
            "how_to_reuse": "Adapt the methodology section..."
          }
        ],
        "next_steps": [
          "Review the full solicitation",
          "Contact program officer",
          "Prepare 2-page concept paper"
        ]
      }
    }
  ]
}
```

## Configuration

### Embeddings Configuration
- Model: `models/text-embedding-004`
- Dimensions: 768
- Task types: RETRIEVAL_DOCUMENT, RETRIEVAL_QUERY

### RAG Configuration
- Model: `gemini-2.0-flash-exp`
- Temperature: 0.7
- Max tokens: 1000

### Rate Limiting
- Embeddings: 140 requests/minute
- URL fetching: 10 second timeout

## Troubleshooting

### Common Issues

1. **API Key Error**
   - Ensure `GEMINI_API_KEY` is set in `.env`
   - Check API key validity

2. **PDF Extraction Failed**
   - Ensure PDFs are text-based, not scanned images
   - Check file permissions

3. **Low Confidence Scores**
   - Normal range is 15-30% for cosine similarity
   - Focus on relative ranking, not absolute scores

4. **ChromaDB Errors**
   - Delete `chroma_db/` folder to reset database
   - Check disk space

## Development

### Adding New Features

1. **New Data Sources**: Extend `funding_opportunities_manager.py`
2. **Custom Embeddings**: Modify `embeddings_manager.py`
3. **Matching Algorithm**: Update `user_profile_manager.py`
4. **Explanation Format**: Customize `rag_explainer.py`

### Testing

Run comprehensive tests:
```bash
python run_tests.py
```

## License

This project is proprietary. All rights reserved.

## Support

For issues or questions, please contact the development team or check the release notes in `release_notes/` directory.