# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FundingMatch is a Python-based AI-powered system for matching researchers with funding opportunities using government APIs and Google Gemini 2.5 Pro for document analysis.

## Key Commands

### Running the Main Workflow
```bash
# Complete workflow (portfolio analysis + opportunity matching)
python main.py

# Enhanced embeddings-based matching (NEW)
python run_embeddings_matching.py  # Uses vector search and RAG
python migrate_to_embeddings.py   # Migrate existing data to vector DB

# NSF-specific comprehensive matcher
python nsf_comprehensive_matcher.py --quick  # 100 opportunities
python nsf_comprehensive_matcher.py         # All 478 opportunities

# Individual components
python comprehensive_portfolio_analysis.py [--force]  # Analyze research documents
python comprehensive_funding_analysis.py [--quick|--test|--force]  # Process funding CSVs
python run_real_opportunity_matching.py  # Match opportunities
```

### Development Commands
```bash
# Install dependencies
pip install -r backend/requirements.txt

# No automated tests currently exist
# Manual testing uses --quick and --test flags on scripts
```

## Architecture

### Core Components
- **Document Processing**: Uses Gemini 2.5 Pro to analyze PDFs and generate semantic profiles
- **API Integrations**: SAM.gov, SBIR.gov, NSF, and Grants.gov (optional)
- **Matching Engine**: AI-powered matching with confidence scoring (0-100%)
- **Report Generation**: Markdown reports with evidence and recommendations
- **Embeddings System** (NEW): Vector-based semantic search using Gemini embeddings
- **RAG Enhancement** (NEW): AI-generated explanations for matches and proposal retrofitting

### Key Modules
- `backend/document_processor.py`: Document analysis with Gemini AI
- `backend/enhanced_matcher.py`: AI matching algorithm
- `backend/embeddings_manager.py` (NEW): Gemini embeddings API integration
- `backend/vector_database.py` (NEW): ChromaDB vector storage
- `backend/embeddings_matcher.py` (NEW): Enhanced matching with RAG
- `backend/sam_api.py`, `backend/sbir_api.py`: Government API integrations
- `backend/data_models/semantic_profile_schema.py`: Data schemas

### Data Flow
1. Documents in `/input_documents/` → Semantic profiles in `/semantic_profiles_*/`
2. Funding CSVs in `/FundingOpportunities/` → Processed to JSON
3. APIs fetch real-time opportunities → Match with profiles
4. Results saved to `/opportunity_matches_*/` with markdown reports

### Enhanced Embeddings Flow (NEW)
1. Semantic profiles → Gemini embeddings → ChromaDB vector storage
2. Funding opportunities → Gemini embeddings → ChromaDB vector storage
3. Vector similarity search → Top-k matches → RAG explanations
4. Proposal retrofitting analysis using historical proposals

### Environment Configuration
Required `.env` file:
```
GEMINI_API_KEY=your_key
SAM_GOV_API_KEY=your_key
GRANTS_GOV_API_KEY=your_key  # optional
```

### Performance Considerations
- Gemini API: 60 RPM rate limit, 1-2 seconds per document
- NSF matcher: Batch processing (50 opportunities, 3 parallel workers)
- Incremental processing: Caches results to avoid redundant work
- Use `--force` flag to reprocess all files
- Embeddings: 768-dimensional vectors, ~0.1s per embedding
- Vector search: Sub-second for 10k+ opportunities using HNSW index

### Key Files to Know
- `all_documents.txt`: List of documents to process
- `FundingOpportunities/COMPLETE_funding_semantic.json`: All processed opportunities
- `FundingOpportunitiesManual/nsf_funding_semantic.json`: NSF semantic dataset (478 opportunities)
- Latest semantic profile: Found by timestamp in `/semantic_profiles_*/`