#!/usr/bin/env python3
"""
FundingMatch v2.0 - Main Execution Script
Complete AI-Powered Funding Opportunity Matching Workflow

This script executes the complete FundingMatch workflow:
1. Comprehensive portfolio analysis (document processing + semantic profiling)
2. Real-time opportunity matching using government APIs

Features:
- Uses Gemini 2.5 Pro for advanced PDF processing
- Processes multiple document types (CV, proposals, publications)
- Fetches real opportunities from SAM.gov and SBIR.gov APIs
- Generates timestamped output folders
- Comprehensive match scoring and analysis

Author: AI Assistant
Date: 2025-01-10
"""

import sys
import os
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_banner():
    """Print the FundingMatch banner"""
    banner = """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                           FundingMatch v2.0                                  ║
║                   AI-Powered Funding Opportunity Matching                    ║
║                          Complete Workflow Execution                         ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║  Phase 1: Comprehensive Portfolio Analysis (Gemini 2.5 Pro)                  ║
║  Phase 2: Real-Time Opportunity Matching (SAM.gov + SBIR.gov)               ║
║  Output: Organized folders with timestamped semantic profiles and reports    ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)

def check_environment():
    """Check if the environment is properly configured"""
    print("🔍 Checking environment configuration...")
    
    # Check if required files exist
    required_files = [
        "comprehensive_portfolio_analysis.py",
        "run_real_opportunity_matching.py", 
        "backend/document_processor.py",
        "backend/enhanced_matcher.py",
        "backend/sam_api.py",
        "backend/sbir_api.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False
    
    # Check if input directory exists
    input_dir = "/Users/alfredocostilla/Documents/FundingMatch/input_documents"
    if not os.path.exists(input_dir):
        print(f"❌ Input directory not found: {input_dir}")
        return False
    
    # Check for API keys
    if not os.getenv('GEMINI_API_KEY'):
        print("❌ GEMINI_API_KEY environment variable not set")
        return False
    
    if not os.getenv('SAM_GOV_API_KEY'):
        print("❌ SAM_GOV_API_KEY environment variable not set")
        return False
    
    print("✅ Environment check passed")
    return True

def run_phase_1():
    """Execute Phase 1: Comprehensive Portfolio Analysis"""
    print("\n" + "="*80)
    print("🔬 PHASE 1: COMPREHENSIVE PORTFOLIO ANALYSIS")
    print("="*80)
    
    try:
        # Execute comprehensive_portfolio_analysis.py with real-time output
        print("🔄 Starting comprehensive portfolio analysis...")
        print("📊 Real-time progress will be shown below:")
        print("-" * 80)
        
        result = subprocess.run([
            sys.executable, 
            "comprehensive_portfolio_analysis.py"
        ], cwd=os.getcwd())
        
        print("-" * 80)
        if result.returncode != 0:
            print(f"❌ Phase 1 failed with return code {result.returncode}")
            return False, None
        
        print("✅ Phase 1 completed successfully")
        
        # Find the generated semantic profile
        semantic_profiles_dir = "semantic_profiles"
        if not os.path.exists(semantic_profiles_dir):
            print("❌ Could not find generated semantic profiles directory")
            return False, None
        
        # Find the latest semantic profile JSON file
        profile_files = []
        for file in os.listdir(semantic_profiles_dir):
            if file.endswith('.json'):
                profile_files.append(os.path.join(semantic_profiles_dir, file))
        
        if not profile_files:
            print("❌ No semantic profile JSON files found")
            return False, None
        
        # Use the most recent profile
        latest_profile = max(profile_files, key=os.path.getctime)
        print(f"📄 Generated semantic profile: {latest_profile}")
        
        return True, latest_profile
        
    except Exception as e:
        print(f"❌ Phase 1 failed with exception: {e}")
        return False, None

def run_phase_2(semantic_profile_path):
    """Execute Phase 2: Real-Time Opportunity Matching"""
    print("\n" + "="*80)
    print("🎯 PHASE 2: REAL-TIME OPPORTUNITY MATCHING")
    print("="*80)
    
    try:
        # Execute run_real_opportunity_matching.py with real-time output
        print("🔄 Starting real-time opportunity matching...")
        print("🎯 Real-time progress will be shown below:")
        print("-" * 80)
        
        result = subprocess.run([
            sys.executable, 
            "run_real_opportunity_matching.py"
        ], cwd=os.getcwd())
        
        print("-" * 80)
        if result.returncode != 0:
            print(f"❌ Phase 2 failed with return code {result.returncode}")
            return False
        
        print("✅ Phase 2 completed successfully")
        
        # Find the generated opportunity matches directory
        opportunity_matches_dir = "opportunity_matches"
        if os.path.exists(opportunity_matches_dir):
            print(f"📊 Generated opportunity matches: {opportunity_matches_dir}")
        
        return True
        
    except Exception as e:
        print(f"❌ Phase 2 failed with exception: {e}")
        return False

def print_summary(phase1_success, phase2_success):
    """Print execution summary"""
    print("\n" + "="*80)
    print("📋 EXECUTION SUMMARY")
    print("="*80)
    
    if phase1_success:
        print("✅ Phase 1: Comprehensive Portfolio Analysis - SUCCESS")
    else:
        print("❌ Phase 1: Comprehensive Portfolio Analysis - FAILED")
    
    if phase2_success:
        print("✅ Phase 2: Real-Time Opportunity Matching - SUCCESS")
    else:
        print("❌ Phase 2: Real-Time Opportunity Matching - FAILED")
    
    print()
    
    if phase1_success and phase2_success:
        print("🎉 FundingMatch v2.0 workflow completed successfully!")
        print("📁 Check the timestamped directories for your results:")
        
        # List generated directories
        for item in os.listdir('.'):
            if item.startswith('semantic_profiles_') and os.path.isdir(item):
                print(f"   • Semantic Profile: {item}")
            elif item.startswith('opportunity_matches_') and os.path.isdir(item):
                print(f"   • Opportunity Matches: {item}")
        
        print()
        print("🚀 You can now review your funding opportunities and match reports!")
        
    elif phase1_success:
        print("⚠️  Phase 1 completed but Phase 2 failed")
        print("   Your semantic profile was generated successfully")
        print("   Check the semantic_profiles_* directory for results")
        
    else:
        print("❌ Workflow failed in Phase 1")
        print("   Please check your environment configuration and try again")
    
    print("="*80)

def main():
    """Main execution function"""
    print_banner()
    
    # Check environment
    if not check_environment():
        print("❌ Environment check failed. Please fix the issues and try again.")
        sys.exit(1)
    
    # Record start time
    start_time = time.time()
    
    # Execute Phase 1
    phase1_success, semantic_profile_path = run_phase_1()
    
    # Execute Phase 2 (regardless of Phase 1 success, but with latest profile)
    phase2_success = False
    if phase1_success:
        phase2_success = run_phase_2(semantic_profile_path)
    else:
        print("⚠️  Skipping Phase 2 due to Phase 1 failure")
    
    # Calculate execution time
    execution_time = time.time() - start_time
    
    # Print summary
    print_summary(phase1_success, phase2_success)
    print(f"⏱️  Total execution time: {execution_time:.2f} seconds")
    
    # Exit with appropriate code
    if phase1_success and phase2_success:
        sys.exit(0)
    elif phase1_success:
        sys.exit(1)  # Partial success
    else:
        sys.exit(2)  # Complete failure

if __name__ == "__main__":
    main() 