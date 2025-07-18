#!/usr/bin/env python3
"""
FundingMatch - Main Pipeline Execution
Complete workflow for funding opportunity matching using embeddings
"""

import os
import sys
import subprocess
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def print_banner():
    """Print the FundingMatch banner"""
    banner = """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                           FundingMatch                                        ║
║           AI-Powered Funding Opportunity Matching with Embeddings            ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)

def check_environment():
    """Check if the environment is properly configured"""
    print("🔍 Checking environment configuration...")
    
    # Check for API key
    if not os.getenv('GEMINI_API_KEY'):
        print("❌ GEMINI_API_KEY not found in .env file")
        return False
    
    # Check input documents
    if not os.path.exists("input_documents"):
        print("❌ input_documents/ directory not found")
        return False
    
    # Check for user JSON
    json_files = [f for f in os.listdir("input_documents") if f.endswith('.json')]
    if not json_files:
        print("❌ No user JSON file found in input_documents/")
        return False
    
    # Check for PDFs
    pdf_count = sum(1 for root, dirs, files in os.walk("input_documents") 
                    for file in files if file.endswith('.pdf'))
    if pdf_count == 0:
        print("⚠️  Warning: No PDF files found in input_documents/")
    
    print("✅ Environment check passed")
    return True

def run_step(script_name, step_name):
    """Run a pipeline step"""
    print(f"\n{'='*60}")
    print(f"🔄 {step_name}")
    print('='*60)
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=False, text=True)
        
        if result.returncode == 0:
            print(f"✅ {step_name} completed successfully")
            return True
        else:
            print(f"❌ {step_name} failed with return code {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ Error running {step_name}: {e}")
        return False

def main():
    """Main execution function"""
    print_banner()
    
    # Check environment
    if not check_environment():
        print("\n❌ Please fix environment issues and try again")
        sys.exit(1)
    
    # Record start time
    start_time = time.time()
    
    # Pipeline steps
    steps = [
        ("process_csv_to_embeddings.py", "Step 1: Process Funding Opportunities"),
        ("create_user_profile.py", "Step 2: Create User Profile"),
        ("match_opportunities.py", "Step 3: Match Opportunities"),
        ("generate_rag_explanations.py", "Step 4: Generate Explanations")
    ]
    
    results = {}
    
    # Execute pipeline
    for script, name in steps:
        success = run_step(script, name)
        results[name] = success
        
        # Continue even if a step fails (except for critical ones)
        if not success and "Process Funding" in name:
            print("⚠️  No new opportunities to process, continuing...")
        elif not success and script != "generate_rag_explanations.py":
            print(f"❌ Critical step failed: {name}")
            break
    
    # Calculate execution time
    execution_time = time.time() - start_time
    
    # Print summary
    print(f"\n{'='*60}")
    print("📋 EXECUTION SUMMARY")
    print('='*60)
    
    for name, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{name}: {status}")
    
    print(f"\n⏱️  Total execution time: {execution_time:.2f} seconds")
    
    # Check output
    if os.path.exists("output_results"):
        print("\n📁 Output files generated:")
        for file in os.listdir("output_results"):
            print(f"   • {file}")
    
    # Final status
    all_success = all(results.values())
    critical_success = results.get("Step 2: Create User Profile", False) and \
                      results.get("Step 3: Match Opportunities", False)
    
    if all_success:
        print("\n🎉 All steps completed successfully!")
        print("📊 Check output_results/ for your personalized funding matches")
    elif critical_success:
        print("\n⚠️  Pipeline completed with warnings")
        print("📊 Basic matching completed - check output_results/")
    else:
        print("\n❌ Pipeline failed - please check errors above")
    
    # Exit code
    sys.exit(0 if all_success else 1)

if __name__ == "__main__":
    main()