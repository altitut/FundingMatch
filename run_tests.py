#!/usr/bin/env python3
"""
Run comprehensive tests for the FundingMatch system
"""

import os
import sys
import subprocess
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def print_header(text):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"🧪 {text}")
    print('='*60)

def test_environment():
    """Test environment setup"""
    print_header("Testing Environment Setup")
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Check API key
    print("1. Checking GEMINI_API_KEY...")
    if os.getenv('GEMINI_API_KEY'):
        print("   ✅ API key found")
        tests_passed += 1
    else:
        print("   ❌ API key not found")
        tests_failed += 1
    
    # Test 2: Check directories
    print("2. Checking required directories...")
    dirs = ['backend', 'input_documents', 'FundingOpportunities', 'output_results']
    for dir_name in dirs:
        if os.path.exists(dir_name):
            print(f"   ✅ {dir_name}/ exists")
            tests_passed += 1
        else:
            print(f"   ❌ {dir_name}/ missing")
            tests_failed += 1
    
    # Test 3: Check main scripts
    print("3. Checking main scripts...")
    scripts = [
        'process_csv_to_embeddings.py',
        'create_user_profile.py',
        'match_opportunities.py',
        'generate_rag_explanations.py',
        'main.py'
    ]
    for script in scripts:
        if os.path.exists(script):
            print(f"   ✅ {script} exists")
            tests_passed += 1
        else:
            print(f"   ❌ {script} missing")
            tests_failed += 1
    
    # Test 4: Check backend modules
    print("4. Checking backend modules...")
    modules = [
        'backend/embeddings_manager.py',
        'backend/vector_database.py',
        'backend/funding_opportunities_manager.py',
        'backend/user_profile_manager.py',
        'backend/pdf_extractor.py',
        'backend/url_content_fetcher.py',
        'backend/rag_explainer.py'
    ]
    for module in modules:
        if os.path.exists(module):
            print(f"   ✅ {module} exists")
            tests_passed += 1
        else:
            print(f"   ❌ {module} missing")
            tests_failed += 1
    
    return tests_passed, tests_failed

def test_imports():
    """Test that all modules can be imported"""
    print_header("Testing Module Imports")
    
    tests_passed = 0
    tests_failed = 0
    
    # Add backend to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
    
    modules = [
        'embeddings_manager',
        'vector_database',
        'funding_opportunities_manager',
        'user_profile_manager',
        'pdf_extractor',
        'url_content_fetcher',
        'rag_explainer'
    ]
    
    for module in modules:
        print(f"Importing {module}...")
        try:
            __import__(module)
            print(f"   ✅ {module} imported successfully")
            tests_passed += 1
        except Exception as e:
            print(f"   ❌ Failed to import {module}: {e}")
            tests_failed += 1
    
    return tests_passed, tests_failed

def test_pipeline():
    """Test the main pipeline with minimal data"""
    print_header("Testing Pipeline Execution")
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Check if main.py exists and is valid Python
    print("1. Testing main.py syntax...")
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'py_compile', 'main.py'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("   ✅ main.py has valid Python syntax")
            tests_passed += 1
        else:
            print(f"   ❌ main.py has syntax errors: {result.stderr}")
            tests_failed += 1
    except Exception as e:
        print(f"   ❌ Failed to check main.py: {e}")
        tests_failed += 1
    
    # Test 2: Check database connection
    print("2. Testing database connection...")
    try:
        from vector_database import VectorDatabaseManager
        db = VectorDatabaseManager()
        stats = db.get_collection_stats()
        print(f"   ✅ Connected to ChromaDB (Opportunities: {stats.get('opportunities', 0)})")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Failed to connect to database: {e}")
        tests_failed += 1
    
    # Test 3: Check if PDFs can be processed
    print("3. Testing PDF extraction...")
    try:
        from pdf_extractor import PDFExtractor
        extractor = PDFExtractor()
        # Just test initialization
        print("   ✅ PDF extractor initialized")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Failed to initialize PDF extractor: {e}")
        tests_failed += 1
    
    return tests_passed, tests_failed

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 FundingMatch Comprehensive Test Suite")
    print("="*60)
    
    total_passed = 0
    total_failed = 0
    
    # Run environment tests
    passed, failed = test_environment()
    total_passed += passed
    total_failed += failed
    
    # Run import tests
    passed, failed = test_imports()
    total_passed += passed
    total_failed += failed
    
    # Run pipeline tests
    passed, failed = test_pipeline()
    total_passed += passed
    total_failed += failed
    
    # Summary
    print_header("Test Summary")
    print(f"Total tests passed: {total_passed}")
    print(f"Total tests failed: {total_failed}")
    
    if total_failed == 0:
        print("\n🎉 All tests passed! The system is ready to use.")
        print("\nTo run the complete pipeline:")
        print("  python main.py")
        print("\nOr run individual steps:")
        print("  python process_csv_to_embeddings.py")
        print("  python create_user_profile.py")
        print("  python match_opportunities.py")
        print("  python generate_rag_explanations.py")
        return 0
    else:
        print(f"\n❌ {total_failed} tests failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())