#!/usr/bin/env python3
"""
Comprehensive Portfolio Analysis System
======================================

This script performs comprehensive AI-powered analysis of research portfolios using real APIs.
It processes documents, URLs, and creates semantic profiles for funding opportunity matching.

Features:
- Real Gemini API integration for document analysis
- Incremental processing with cache management
- Comprehensive semantic profile generation
- Support for multiple document types (PDFs, URLs)
- Timestamped output for organized results

Usage:
    python comprehensive_portfolio_analysis.py              # Incremental processing
    python comprehensive_portfolio_analysis.py --force      # Force reprocess all files

Output:
    - Semantic profiles saved to semantic_profiles_<timestamp>/ folder
    - Processing summaries and cache files for efficiency
    - Comprehensive analysis reports

Date: 2025
"""

import os
import sys
import json
import glob
from pathlib import Path
from datetime import datetime
import time
import hashlib
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.append('backend')

from backend.document_processor import DocumentProcessor
from backend.data_models.semantic_profile_schema import save_semantic_profile

def get_timestamped_output_dir():
    """Get the semantic profiles output directory (no timestamp in folder name)"""
    # Always use the same directory name
    output_dir = "semantic_profiles"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def classify_document_by_path(file_path):
    """
    Classify document type based on directory structure and filename
    
    Args:
        file_path (str): Path to the document file
        
    Returns:
        str: Document type classification
    """
    
    path_lower = file_path.lower()
    filename = Path(file_path).name.lower()
    
    # CV Classification
    if 'cv' in filename or 'curriculum' in filename:
        return "Curriculum Vitae"
    
    # Dissertation
    if 'dissertation' in filename:
        return "Technical Report"
    
    # Research Papers
    if 'researchpapers' in path_lower:
        if 'first author' in path_lower:
            return "First Author Journal Article"
        elif 'co-author' in path_lower:
            if 'journals' in path_lower:
                return "Co-author Journal Article"
            elif 'conferences' in path_lower:
                return "Conference Paper"
        elif 'rice' in path_lower:
            return "Conference Paper"  # Rice papers are typically conference papers
    
    # Proposals - Fixed logic to check actual folder structure
    if 'proposals' in path_lower:
        if '/successful/' in path_lower:
            return "Successful Proposal"
        elif '/notsuccessful/' in path_lower:
            return "Unsuccessful Proposal"
        elif '/pending/' in path_lower:
            return "Unsuccessful Proposal"  # Treat pending as unsuccessful for analysis
        else:
            # Fallback based on filename patterns
            if any(word in filename for word in ['declined', 'rejected', 'not funded', 'unsuccessful']):
                return "Unsuccessful Proposal"
            elif any(word in filename for word in ['funded', 'awarded', 'successful']):
                return "Successful Proposal"
            else:
                return "Unsuccessful Proposal"  # Default to unsuccessful if unclear
    
    # Patent applications
    if 'patent' in filename:
        return "Patent Application"
    
    # Business plans
    if 'business' in filename or 'bp_' in filename:
        return "Technical Report"
    
    # Default fallback
    return "Technical Report"

def get_all_documents():
    """
    Get all documents from the input_documents directory by scanning recursively
    
    Returns:
        list: List of document dictionaries with path and type
    """
    
    documents = []
    input_dir = "input_documents"
    
    if not os.path.exists(input_dir):
        print(f"❌ Input directory '{input_dir}' not found!")
        return documents
    
    # Supported file extensions
    supported_extensions = {'.pdf', '.doc', '.docx', '.txt'}
    
    print(f"📂 Scanning {input_dir} directory for documents...")
    
    # Recursively scan the input_documents directory
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            file_path = os.path.join(root, file)
            file_ext = os.path.splitext(file)[1].lower()
            
            if file_ext in supported_extensions:
                doc_type = classify_document_by_path(file_path)
                documents.append({
                    "path": file_path,
                    "type": doc_type
                })
                print(f"   📄 Found: {file_path} (Type: {doc_type})")
    
    print(f"📊 Total documents found: {len(documents)}")
    return documents

def get_urls_from_json():
    """
    Get URLs from alfredo_costilla_reyes.json for analysis
    
    Returns:
        list: List of URL dictionaries with path, type, and metadata
    """
    
    urls = []
    json_file = 'input_documents/alfredo_costilla_reyes.json'
    
    if os.path.exists(json_file):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            links = data.get('person', {}).get('links', [])
            for link in links:
                url_type = link.get('type', 'webpage')
                # Map URL types to document types for analysis
                if url_type == 'faculty_profile':
                    doc_type = "Curriculum Vitae"  # Faculty profiles are like CVs
                elif url_type == 'nsf_award':
                    doc_type = "Successful Proposal"  # NSF awards represent successful proposals
                elif url_type == 'news_article':
                    doc_type = "Technical Report"  # News articles are informational
                elif url_type == 'academic_profile':
                    doc_type = "First Author Journal Article"  # Academic profiles show publications
                else:
                    doc_type = "Technical Report"  # Default for other types
                
                urls.append({
                    "path": link['url'],
                    "type": doc_type,
                    "summary": link.get('summary', ''),
                    "url_type": url_type
                })
        except Exception as e:
            print(f"Warning: Could not process JSON file {json_file}: {e}")
    
    return urls

def get_file_hash(file_path):
    """
    Get hash of file content for change detection
    
    Args:
        file_path (str): Path to file or URL
        
    Returns:
        str: Hash string for change detection
    """
    try:
        if file_path.startswith('http'):
            # For URLs, use the URL itself as hash
            return hashlib.md5(file_path.encode()).hexdigest()
        else:
            # For files, use file size and modification time
            stat = os.stat(file_path)
            return hashlib.md5(f"{stat.st_size}_{stat.st_mtime}".encode()).hexdigest()
    except Exception:
        return "unknown"

def load_processed_cache():
    """
    Load previously processed documents cache
    
    Returns:
        dict: Cache dictionary with processed file hashes
    """
    cache_file = ".portfolio_cache.json"
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_processed_cache(cache):
    """
    Save processed documents cache
    
    Args:
        cache (dict): Cache dictionary to save
    """
    cache_file = ".portfolio_cache.json"
    try:
        with open(cache_file, 'w') as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save cache: {e}")

def load_processed_documents():
    """
    Load previously processed documents from the most recent semantic profile
    
    Returns:
        list: List of processed document entries
    """
    try:
        # Find the most recent semantic profile
        profile_files = [f for f in os.listdir('.') if f.startswith('alfredo_costilla_reyes_COMPREHENSIVE_semantic_profile_')]
        if profile_files:
            latest_profile = max(profile_files, key=lambda x: os.path.getctime(x))
            with open(latest_profile, 'r') as f:
                semantic_profile = json.load(f)
            return semantic_profile.get('documents', [])
        else:
            return []
    except Exception as e:
        print(f"Warning: Could not load processed documents: {e}")
        return []

def filter_items_for_processing(all_items, force=False):
    """
    Filter items to only process new ones and CV files with changes
    
    Args:
        all_items (list): List of all items to potentially process
        force (bool): Whether to force reprocessing of all items
        
    Returns:
        list: Filtered list of items that need processing
    """
    if force:
        # Force reprocess all items
        return all_items
    
    cache = load_processed_cache()
    items_to_process = []
    
    for item in all_items:
        item_path = item["path"]
        item_type = item["type"]
        current_hash = get_file_hash(item_path)
        
        # Check if item was processed before
        cached_hash = cache.get(item_path)
        
        if cached_hash != current_hash:
            # New or changed item
            items_to_process.append(item)
            # Update cache
            cache[item_path] = current_hash
        else:
            # Always reprocess CV files to ensure fresh data
            if item_type == "Curriculum Vitae":
                items_to_process.append(item)
    
    # Save updated cache
    save_processed_cache(cache)
    
    return items_to_process

def main():
    """
    Main function to process Alfredo's complete portfolio with real AI analysis
    """
    
    print("🚀 COMPREHENSIVE PORTFOLIO ANALYSIS SYSTEM")
    print("=" * 80)
    print("📊 Real AI-Powered Document Analysis & Semantic Profile Generation")
    print("🔬 Using Gemini 2.5 Pro API for Deep Analysis")
    print("📁 Organized Output with Timestamped Folders")
    print()
    
    # Check for quick flag (only process 2 files) or force full analysis by default
    quick_mode = "--quick" in sys.argv
    force_reprocess = "--force" in sys.argv or not quick_mode  # Full analysis by default
    
    if force_reprocess and not quick_mode:
        # Clear cache when forcing reprocessing (unless in quick mode)
        cache_file = ".portfolio_cache.json"
        if os.path.exists(cache_file):
            os.remove(cache_file)
            print("🔄 Cache cleared for full portfolio analysis")
    
    # Check for Gemini API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment variables")
        print("💡 Make sure .env file contains GEMINI_API_KEY")
        return
    
    print(f"✅ Gemini API key loaded: {api_key[:10]}...")
    print("🔬 Using REAL AI analysis - NOT mock data")
    print()
    
    # Get output directory
    output_dir = get_timestamped_output_dir()
    print(f"📁 Output directory: {output_dir}")
    print()
    
    # Initialize processor with real API
    try:
        processor = DocumentProcessor(api_key)
        print("✅ DocumentProcessor initialized with Gemini API")
        
    except Exception as e:
        print(f"❌ Error initializing DocumentProcessor: {e}")
        return
    
    # Get all documents and URLs
    portfolio_documents = get_all_documents()
    portfolio_urls = get_urls_from_json()
    
    # Combine all items for processing
    all_items = portfolio_documents + portfolio_urls
    
    print(f"\n📄 COMPREHENSIVE DOCUMENT ANALYSIS")
    print(f"📊 Total PDF documents found: {len(portfolio_documents)}")
    print(f"🔗 Total URLs found: {len(portfolio_urls)}")
    print(f"📊 Total items to process: {len(all_items)}")
    print("-" * 50)
    
    # Filter items for incremental processing
    items_to_process = filter_items_for_processing(all_items, force=force_reprocess)
    
    if len(items_to_process) == 0:
        print("✅ No new items to process. All documents are up to date.")
        print("💡 To force reprocessing, run with --force flag")
        print("💡 To run quick analysis (2 files only), run with --quick flag")
        print("🔄 Loading previously processed documents for analysis...")
        
        # Load most recent semantic profile
        try:
            # Find the most recent semantic profile in the semantic_profiles directory
            profile_dir = "semantic_profiles"
            if os.path.exists(profile_dir):
                profile_files = [f for f in os.listdir(profile_dir) if f.startswith('alfredo_costilla_reyes_COMPREHENSIVE_semantic_profile_')]
                if profile_files:
                    latest_profile = max(profile_files, key=lambda x: os.path.getctime(os.path.join(profile_dir, x)))
                    print(f"📁 Found existing analysis: {os.path.join(profile_dir, latest_profile)}")
                    return
            
            print("❌ No previous analysis found. Will process all files.")
            # Continue with processing instead of returning
        except Exception as e:
            print(f"❌ Error loading previous analysis: {e}")
            # Continue with processing instead of returning
    
    if quick_mode:
        print(f"🔄 Quick mode: processing {len(items_to_process)} items")
    else:
        print(f"🔄 Full portfolio analysis: processing {len(items_to_process)} items")
    print("-" * 50)
    
    # Process filtered items with real AI analysis
    processed_documents = []
    total_items = len(items_to_process)
    
    print("🧠 Starting REAL AI Analysis...")
    print("-" * 50)
    
    for i, item_info in enumerate(items_to_process, 1):
        item_path = item_info["path"]
        item_type = item_info["type"]
        
        # Determine source type and display name
        if item_path.startswith('http'):
            source_type = "URL"
            item_name = item_info.get('url_type', 'URL')
            display_name = f"{item_name} ({item_info.get('summary', '')[:30]}...)"
        else:
            source_type = "PDF"
            item_name = Path(item_path).name
            display_name = item_name
        
        print(f"{i:2d}/{total_items}. Processing: {display_name[:60]}...")
        print(f"        Type: {item_type}")
        print(f"        Source: {source_type}")
        print(f"        Path: {item_path}")
        
        # Check if PDF exists or if it's a URL
        if source_type == "URL" or os.path.exists(item_path):
            try:
                # Real AI processing
                start_time = time.time()
                document_entry = processor.process_document(item_path, item_type)
                processing_time = time.time() - start_time
                
                # Add source information to the document entry
                document_entry['source_type'] = source_type
                if source_type == "URL":
                    document_entry['url_summary'] = item_info.get('summary', '')
                    document_entry['url_type'] = item_info.get('url_type', '')
                
                processed_documents.append(document_entry)
                print(f"        ✅ SUCCESS ({processing_time:.1f}s)")
                
                # Brief analysis summary
                analysis = document_entry.get('analysis', {})
                if 'title' in analysis:
                    print(f"        📝 Title: {analysis['title'][:50]}...")
                elif 'name' in analysis.get('personal_info', {}):
                    print(f"        👤 Name: {analysis['personal_info']['name']}")
                
                # Small delay to respect API rate limits
                time.sleep(1)
                
            except Exception as e:
                print(f"        ❌ ERROR: {str(e)[:60]}...")
                # Continue processing other items
                
        else:
            print(f"        ⚠️  FILE NOT FOUND")
        
        print()
    
    print(f"📊 PROCESSING COMPLETE: {len(processed_documents)}/{total_items} items analyzed")
    
    if len(processed_documents) == 0:
        print("❌ No documents were successfully processed")
        return
    
    # Generate comprehensive semantic profile
    print("\n🧠 GENERATING COMPREHENSIVE SEMANTIC PROFILE...")
    print("-" * 50)
    
    try:
        start_time = time.time()
        semantic_profile = processor._synthesize_portfolio(processed_documents)
        synthesis_time = time.time() - start_time
        
        print(f"✅ Semantic profile generated successfully ({synthesis_time:.1f}s)")
        
        # Display comprehensive summary
        print("\n📋 COMPREHENSIVE PORTFOLIO ANALYSIS:")
        print("-" * 50)
        
        metadata = semantic_profile['profile_metadata']
        portfolio = semantic_profile['portfolio_summary']
        synthesis = semantic_profile['synthesis']
        
        print(f"👤 Researcher: {metadata['primary_researcher']}")
        print(f"📄 Documents Analyzed: {metadata['total_documents']}")
        print(f"🎯 Research Domains: {len(portfolio['research_domains'])}")
        print(f"💪 Core Competencies: {len(synthesis['core_competencies'])}")
        print(f"🏆 Strategic Advantages: {len(synthesis['strategic_advantages'])}")
        print(f"💰 Funding Secured: ${portfolio['funding_track_record']['total_secured']:,}")
        print(f"✅ Successful Proposals: {portfolio['funding_track_record']['successful_proposals']}")
        print(f"📚 Publications: {portfolio['publication_metrics']['total_publications']}")
        print(f"📈 Career Stage: {portfolio['career_stage']}")
        
        print(f"\n🎯 Research Domains:")
        for domain in portfolio['research_domains'][:10]:  # Top 10
            print(f"   • {domain}")
        
        print(f"\n💪 Core Competencies:")
        for comp in synthesis['core_competencies']:
            print(f"   • {comp['domain']} ({comp['evidence_strength']})")
            print(f"     Evidence: {len(comp['supporting_documents'])} documents")
        
        print(f"\n🚀 Funding Readiness:")
        for funding_type, readiness in synthesis['funding_readiness'].items():
            print(f"   • {funding_type.replace('_', '/')}: {readiness}")
        
        print(f"\n🏆 Top Strategic Advantages:")
        for i, advantage in enumerate(synthesis['strategic_advantages'][:5], 1):
            print(f"   {i}. {advantage}")
        
    except Exception as e:
        print(f"❌ Error generating semantic profile: {e}")
        return
    
    # Save comprehensive results to timestamped folder
    print(f"\n💾 SAVING COMPREHENSIVE RESULTS...")
    print("-" * 50)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"alfredo_costilla_reyes_COMPREHENSIVE_semantic_profile_{timestamp}.json")
    
    try:
        success = save_semantic_profile(semantic_profile, output_file)
        if success:
            file_size = os.path.getsize(output_file)
            print(f"✅ Comprehensive semantic profile saved to: {output_file}")
            print(f"📁 File size: {file_size:,} bytes")
            
            # Also save processing summary
            summary_file = os.path.join(output_dir, f"processing_summary_{timestamp}.json")
            processing_summary = {
                "processing_date": datetime.now().isoformat(),
                "output_directory": output_dir,
                "total_documents_found": len(portfolio_documents),
                "total_urls_found": len(portfolio_urls),
                "total_items_found": len(all_items),
                "items_to_process": len(items_to_process),
                "successfully_processed": len(processed_documents),
                "processing_rate": f"{len(processed_documents)}/{len(items_to_process)}",
                "incremental_processing": True,
                "api_used": "Gemini 2.5 Pro",
                "processing_mode": "REAL_AI_ANALYSIS",
                "semantic_profile_file": output_file
            }
            
            with open(summary_file, 'w') as f:
                json.dump(processing_summary, f, indent=2)
            
            print(f"📊 Processing summary saved to: {summary_file}")
            
        else:
            print(f"❌ Failed to save semantic profile")
            
    except Exception as e:
        print(f"❌ Error saving files: {e}")
        return
    
    print(f"\n🎉 COMPREHENSIVE PORTFOLIO ANALYSIS COMPLETE!")
    print("=" * 80)
    print(f"📊 FINAL STATISTICS:")
    print(f"   • Total PDFs: {len(portfolio_documents)}")
    print(f"   • Total URLs: {len(portfolio_urls)}")
    print(f"   • Total Items: {len(all_items)}")
    print(f"   • Items Processed: {len(items_to_process)}")
    print(f"   • Successfully Processed: {len(processed_documents)}")
    print(f"   • Success Rate: {len(processed_documents)/len(items_to_process)*100:.1f}%")
    print(f"   • Analysis Mode: {'Quick Mode' if quick_mode else 'Full Portfolio Analysis'} (Gemini 2.5 Pro)")
    print(f"   • Output Directory: {output_dir}")
    print(f"   • Semantic Profile: {output_file}")
    print("=" * 80)

if __name__ == "__main__":
    main() 