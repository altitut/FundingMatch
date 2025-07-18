# RAG-Enhanced Funding Match System Documentation

## Overview

The FundingMatch system now includes a sophisticated Retrieval Augmented Generation (RAG) component that provides personalized explanations for why specific funding opportunities match a user's profile. This system uses Google's Gemini 2.0 Flash to generate detailed insights, identify reusable content, and provide actionable next steps.

## Key Features

### 1. Intelligent Match Explanations
- Analyzes user's research interests, experience, and publications
- Provides 2-3 sentence explanations of why each opportunity is relevant
- Uses semantic understanding to connect user expertise with opportunity requirements

### 2. Reusable Content Identification
- Automatically identifies which previous proposals, papers, or documents can be adapted
- Provides specific guidance on how to reuse each document
- Helps users leverage their existing work efficiently

### 3. Actionable Next Steps
- Generates concrete, numbered steps for each opportunity
- Includes guidance on reviewing solicitations, contacting program officers, and preparing applications
- Tailored to the specific requirements of each funding agency

## System Architecture

### Components

1. **User Profile Manager** (`backend/user_profile_manager.py`)
   - Extracts text from PDFs using PyMuPDF
   - Fetches content from user's profile URLs
   - Combines all information into comprehensive embeddings

2. **RAG Explainer** (`backend/rag_explainer.py`)
   - Uses Google's Gemini 2.0 Flash API
   - Generates contextual explanations
   - Parses responses into structured format

3. **Vector Database** (`backend/vector_database.py`)
   - Stores user and opportunity embeddings
   - Performs similarity searches using ChromaDB
   - Manages persistent storage of profiles

## Usage Example

```python
# Create user profile
user_manager = UserProfileManager()
profile = user_manager.create_user_profile(
    user_json_path="input_documents/user.json",
    pdf_paths=["CV.pdf", "dissertation.pdf", "proposals/*.pdf"]
)

# Store profile with embeddings
user_manager.store_user_profile(profile)

# Match with opportunities
matches = user_manager.match_user_to_opportunities(profile, n_results=20)

# Generate explanations for top matches
rag_explainer = RAGExplainer()
for opportunity in matches[:5]:
    explanation = rag_explainer.explain_match(
        profile, 
        opportunity,
        profile['extracted_pdfs']
    )
    print(f"Match: {opportunity['title']}")
    print(f"Explanation: {explanation['match_explanation']}")
    print(f"Reusable Content: {explanation['reusable_content']}")
    print(f"Next Steps: {explanation['next_steps']}")
```

## Test Results

The system was tested with Dr. Alfredo Costilla-Reyes' profile and successfully:

1. **Processed 7 documents** including CV, dissertation, and proposals
2. **Matched with 111 funding opportunities** from NSF, NIH, DOD, and other agencies
3. **Generated explanations for top 5 opportunities** with:
   - Personalized match explanations
   - Identified 5 unique reusable documents
   - Provided specific next steps for each opportunity

### Example Output

**Opportunity**: NSF EPSCoR E-RISE Program
**Confidence Score**: 21.8%
**Explanation**: "The NSF EPSCoR E-RISE program aims to bolster research infrastructure, aligning with Alfredo's experience in developing and commercializing technologies related to wearable sensors, remote asset monitoring, and AI-powered solutions."

**Reusable Content**:
- `NSF22_PFI_OutlierDetection_RemoteAssetMonitoring.pdf`: Can be adapted to highlight relevance to E-RISE program's focus on strengthening research infrastructure
- `CV PI Alfredo Costilla Reyes 04-2025.pdf`: Showcases qualifications and leadership abilities
- `COSTILLAREYES-DISSERTATION-2020.pdf`: Contains relevant theoretical background and methodologies

**Next Steps**:
1. Review the E-RISE program solicitation thoroughly
2. Identify relevant EPSCoR jurisdiction and potential collaborators
3. Develop compelling project proposal aligned with program goals

## Configuration

### Environment Variables
```bash
# Required in .env file
GEMINI_API_KEY=your_gemini_api_key_here
```

### Installation
```bash
# Install required packages
pip install google-genai PyMuPDF chromadb python-dotenv
```

## Performance Metrics

- **PDF Processing**: ~2-5 seconds per document
- **Embedding Generation**: ~1 second per profile
- **Match Search**: <1 second for 20 results
- **RAG Explanation**: ~3-5 seconds per opportunity
- **Total Processing Time**: ~30 seconds for complete user analysis

## Best Practices

1. **Document Preparation**
   - Include CV, research statements, and previous proposals
   - Ensure PDFs are text-searchable (not scanned images)
   - Include both successful and unsuccessful proposals for better context

2. **Profile Enrichment**
   - Add comprehensive research interests in JSON profile
   - Include relevant URLs (faculty pages, Google Scholar, etc.)
   - Update profile regularly with new publications and awards

3. **Match Optimization**
   - Review top 10-15 matches for best results
   - Use confidence scores as relative indicators
   - Consider both high and medium confidence matches

## Future Enhancements

1. **Multi-user Support**: Batch processing for research groups
2. **Deadline Tracking**: Automated reminders for upcoming deadlines
3. **Proposal Templates**: Generate draft proposals based on matches
4. **Success Prediction**: ML model to predict proposal success rates
5. **Collaborative Features**: Team formation suggestions based on opportunity requirements

## Troubleshooting

### Common Issues

1. **"GEMINI_API_KEY not found"**
   - Ensure `.env` file exists with valid API key
   - Run `load_dotenv()` before initializing components

2. **Low Confidence Scores**
   - Normal for cosine similarity (0.2-0.3 is good)
   - Focus on relative ranking rather than absolute scores

3. **PDF Extraction Errors**
   - Ensure PDFs are not password-protected
   - Check for corrupted files
   - Use text-based PDFs, not scanned images

## API Reference

### UserProfileManager

```python
create_user_profile(user_json_path: str, pdf_paths: List[str]) -> Dict[str, Any]
store_user_profile(profile: Dict[str, Any]) -> bool
match_user_to_opportunities(user_profile: Dict[str, Any], n_results: int) -> List[Dict[str, Any]]
```

### RAGExplainer

```python
explain_match(user_profile: Dict, opportunity: Dict, user_documents: Dict) -> Dict[str, Any]
generate_batch_explanations(user_profile: Dict, opportunities: List, user_documents: Dict, top_n: int) -> List[Dict]
```

## License and Credits

This system uses:
- Google Gemini 2.0 Flash for natural language generation
- ChromaDB for vector storage
- PyMuPDF for PDF text extraction
- BeautifulSoup for web content extraction

Developed as part of the FundingMatch project to help researchers find and apply for relevant funding opportunities.