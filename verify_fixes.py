#!/usr/bin/env python3
"""
Verify that all fixes are working correctly
"""

import requests
import json
from pathlib import Path
import time

BASE_URL = "http://localhost:8787/api"

def test_reprocessing():
    """Test that reprocessing returns correct document counts"""
    print("\n1. Testing Profile Reprocessing...")
    
    # Get existing users
    response = requests.get(f"{BASE_URL}/profile/users")
    users = response.json()
    print(f"   Found {len(users)} users")
    
    # Find Alfredo's user ID
    alfredo_id = None
    for user in users:
        if "Alfredo" in user['name'] or "Costilla" in user['name']:
            alfredo_id = user['id']
            break
    
    if not alfredo_id:
        print("   ❌ Could not find Alfredo's profile")
        return False
    
    # Reprocess profile
    print(f"   Reprocessing profile for user ID: {alfredo_id}")
    response = requests.post(f"{BASE_URL}/profile/process?userId={alfredo_id}")
    result = response.json()
    
    print(f"   Response: {result}")
    
    # Check results
    if result.get('documents_processed', 0) > 0:
        print(f"   ✅ Documents processed: {result.get('documents_processed')}")
        print(f"   ✅ URLs processed: {result.get('urls_processed', 0)}")
        return True
    else:
        print("   ❌ No documents reported as processed")
        return False

def test_matching_scores():
    """Test that matching scores show proper variation"""
    print("\n2. Testing Matching Score Variation...")
    
    # Get matching results
    response = requests.get(f"{BASE_URL}/matches")
    if response.status_code != 200:
        print("   ❌ Could not retrieve matches")
        return False
    
    matches = response.json()
    
    if not matches:
        print("   ⚠️  No matches found. Running matching first...")
        # Trigger matching
        match_response = requests.post(f"{BASE_URL}/match/run")
        if match_response.status_code == 200:
            print("   Matching completed, checking results...")
            time.sleep(2)
            response = requests.get(f"{BASE_URL}/matches")
            matches = response.json()
    
    if not matches:
        print("   ❌ No matches available")
        return False
    
    # Analyze score distribution
    scores = []
    for match in matches[:20]:  # Check top 20 matches
        score = match.get('confidence_score', 0)
        scores.append(score)
    
    if scores:
        min_score = min(scores)
        max_score = max(scores)
        score_range = max_score - min_score
        avg_score = sum(scores) / len(scores)
        
        print(f"   Score Statistics (top 20 matches):")
        print(f"   - Min: {min_score:.1f}%")
        print(f"   - Max: {max_score:.1f}%")
        print(f"   - Range: {score_range:.1f}%")
        print(f"   - Average: {avg_score:.1f}%")
        
        # Check for good variation
        if score_range > 20:  # At least 20% range
            print(f"   ✅ Good score variation detected ({score_range:.1f}% range)")
            return True
        else:
            print(f"   ❌ Poor score variation ({score_range:.1f}% range)")
            return False
    else:
        print("   ❌ No scores found")
        return False

def check_uploads_folder():
    """Verify uploads folder has all documents"""
    print("\n3. Checking Uploads Folder...")
    
    uploads_dir = Path("uploads")
    if not uploads_dir.exists():
        print("   ❌ Uploads folder not found")
        return False
    
    pdf_files = list(uploads_dir.glob("*.pdf"))
    print(f"   ✅ Found {len(pdf_files)} PDF files in uploads folder")
    
    # Show first few files
    print("   Sample files:")
    for pdf in pdf_files[:5]:
        print(f"     - {pdf.name}")
    if len(pdf_files) > 5:
        print(f"     ... and {len(pdf_files) - 5} more")
    
    return len(pdf_files) > 40  # Should have at least 40 files

def main():
    print("🔍 Verifying FundingMatch Fixes")
    print("=" * 50)
    
    # Check uploads folder first
    uploads_ok = check_uploads_folder()
    
    # Test reprocessing
    reprocess_ok = test_reprocessing()
    
    # Test matching scores
    scores_ok = test_matching_scores()
    
    print("\n" + "=" * 50)
    print("📊 Summary:")
    print(f"   Uploads folder: {'✅ OK' if uploads_ok else '❌ FAILED'}")
    print(f"   Reprocessing: {'✅ OK' if reprocess_ok else '❌ FAILED'}")
    print(f"   Score variation: {'✅ OK' if scores_ok else '❌ FAILED'}")
    
    if all([uploads_ok, reprocess_ok, scores_ok]):
        print("\n✅ All systems working correctly!")
    else:
        print("\n❌ Some issues remain. Please check the output above.")

if __name__ == "__main__":
    main()