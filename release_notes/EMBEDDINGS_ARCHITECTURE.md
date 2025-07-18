# Embeddings-Based FundingMatch Architecture

## Overview
This document outlines the upgrade from keyword-based matching to embedding-based semantic matching using Google's Gemini embeddings API.

## Architecture Components

### 1. Embeddings Generation
- **API**: Gemini-embedding-001 (768-dimensional embeddings)
- **Content to Embed**:
  - Researcher semantic profiles (expertise, research domains, publications)
  - Funding opportunity descriptions (title, abstract, requirements)
  - Proposal abstracts (successful and unsuccessful)

### 2. Vector Database
- **Options**: ChromaDB (lightweight), Qdrant (performance), or Pinecone (cloud)
- **Structure**:
  - Collections: researchers, opportunities, proposals
  - Metadata: timestamps, scores, categories, success status
  - Indexing: HNSW for efficient similarity search

### 3. Matching Pipeline
```
Researcher Profile → Embeddings → Vector DB
                                      ↓
                              Similarity Search
                                      ↓
Funding Opportunities ← Ranked Results ← Score Calculation
```

### 4. RAG Enhancement
- Retrieve top-k similar opportunities
- Generate context from metadata and full documents
- Use Gemini 2.5 Pro for explanation generation
- Include proposal retrofitting suggestions

## Implementation Steps

### Phase 1: Core Infrastructure
1. Gemini embeddings wrapper
2. Vector database setup
3. Data migration utilities

### Phase 2: Embedding Pipeline
1. Profile embedding generation
2. Opportunity embedding generation
3. Batch processing optimization

### Phase 3: Matching System
1. Similarity search implementation
2. Hybrid scoring (embeddings + metadata)
3. Ranking algorithm

### Phase 4: RAG System
1. Context retrieval
2. Prompt engineering for explanations
3. Proposal retrofitting logic

## Benefits
- **Semantic Understanding**: Beyond keyword matching
- **Scalability**: Efficient vector search
- **Flexibility**: Easy to add new opportunities
- **Explainability**: RAG-powered explanations