#!/usr/bin/env python3
"""
Test script for FundingMatch frontend
Tests all API endpoints and frontend functionality
"""

import os
import sys
import requests
import json
import time
from datetime import datetime

# Configuration
API_BASE = 'http://localhost:5000/api'
FRONTEND_URL = 'http://localhost:3000'

def print_header(text):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"🧪 {text}")
    print('='*60)

def test_api_health():
    """Test if API is running"""
    print_header("Testing API Health")
    
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API is healthy")
            print(f"   Status: {data.get('status')}")
            print(f"   Timestamp: {data.get('timestamp')}")
            return True
        else:
            print(f"❌ API returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Please ensure the Flask server is running:")
        print("   python app.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_stats_endpoint():
    """Test database statistics endpoint"""
    print_header("Testing Stats Endpoint")
    
    try:
        response = requests.get(f"{API_BASE}/stats")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                stats = data.get('stats', {})
                print("✅ Stats retrieved successfully")
                print(f"   Opportunities: {stats.get('opportunities', 0)}")
                print(f"   Researchers: {stats.get('researchers', 0)}")
                print(f"   Proposals: {stats.get('proposals', 0)}")
                return True
            else:
                print(f"❌ Stats request failed: {data.get('error')}")
                return False
        else:
            print(f"❌ Stats endpoint returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_csv_upload():
    """Test CSV upload functionality"""
    print_header("Testing CSV Upload")
    
    # Create a test CSV file
    test_csv = """title,description,url,agency,keywords,close_date
Test Opportunity,This is a test funding opportunity for testing purposes,https://example.com/test,TEST,"testing,demo,example",2025-12-31
"""
    
    test_file = "test_opportunity.csv"
    with open(test_file, 'w') as f:
        f.write(test_csv)
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': ('test_opportunity.csv', f, 'text/csv')}
            response = requests.post(f"{API_BASE}/ingest/csv", files=files)
        
        os.remove(test_file)  # Clean up
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ CSV upload successful")
                print(f"   Message: {data.get('message')}")
                return True
            else:
                print(f"❌ CSV upload failed: {data.get('error')}")
                return False
        else:
            print(f"❌ CSV upload returned status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        if os.path.exists(test_file):
            os.remove(test_file)
        return False

def test_profile_upload():
    """Test profile document upload"""
    print_header("Testing Profile Upload")
    
    # Create a test JSON profile
    test_profile = {
        "person": {
            "name": "Test User",
            "biographical_information": {
                "research_interests": ["AI", "Machine Learning", "Data Science"],
                "education": [{"degree": "PhD", "field": "Computer Science"}],
                "awards": []
            },
            "links": []
        }
    }
    
    test_file = "test_profile.json"
    with open(test_file, 'w') as f:
        json.dump(test_profile, f)
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': ('test_profile.json', f, 'application/json')}
            response = requests.post(f"{API_BASE}/profile/upload", files=files)
        
        os.remove(test_file)  # Clean up
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Profile upload successful")
                print(f"   Filename: {data.get('filename')}")
                return True
            else:
                print(f"❌ Profile upload failed: {data.get('error')}")
                return False
        else:
            print(f"❌ Profile upload returned status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        if os.path.exists(test_file):
            os.remove(test_file)
        return False

def test_frontend_build():
    """Check if frontend is built and ready"""
    print_header("Checking Frontend Build")
    
    frontend_build = "frontend/build"
    if os.path.exists(frontend_build):
        print("✅ Frontend build directory exists")
        return True
    else:
        print("❌ Frontend not built. Please run:")
        print("   cd frontend && npm run build")
        return False

def print_summary(tests_passed, tests_failed):
    """Print test summary"""
    print_header("Test Summary")
    
    total = tests_passed + tests_failed
    print(f"Total tests: {total}")
    print(f"Passed: {tests_passed}")
    print(f"Failed: {tests_failed}")
    
    if tests_failed == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ {tests_failed} tests failed")

def print_instructions():
    """Print setup instructions"""
    print("\n" + "="*60)
    print("📚 Setup Instructions")
    print("="*60)
    
    print("\n1. Start the Flask backend:")
    print("   python app.py")
    
    print("\n2. Start the React frontend (development mode):")
    print("   cd frontend && npm start")
    
    print("\n3. Or build and serve the frontend (production mode):")
    print("   cd frontend && npm run build")
    print("   Then access the app at http://localhost:5000")
    
    print("\n4. Access the application:")
    print("   - Development: http://localhost:3000")
    print("   - Production: http://localhost:5000")

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 FundingMatch Frontend Test Suite")
    print("="*60)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test API endpoints
    if test_api_health():
        tests_passed += 1
    else:
        tests_failed += 1
        print("\n⚠️  API is not running. Skipping remaining API tests.")
        print_instructions()
        return
    
    # Continue with other tests
    if test_stats_endpoint():
        tests_passed += 1
    else:
        tests_failed += 1
    
    if test_csv_upload():
        tests_passed += 1
    else:
        tests_failed += 1
    
    if test_profile_upload():
        tests_passed += 1
    else:
        tests_failed += 1
    
    if test_frontend_build():
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Summary
    print_summary(tests_passed, tests_failed)
    
    if tests_passed == 5:
        print("\n🎉 System is ready to use!")
        print_instructions()

if __name__ == "__main__":
    main()