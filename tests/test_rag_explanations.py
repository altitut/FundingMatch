#!/usr/bin/env python3
"""
Test RAG explanations for funding opportunity matches
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from backend.user_profile_manager import UserProfileManager
from backend.rag_explainer import RAGExplainer


def main():
    """Test RAG explanation generation"""
    
    print("=== RAG Explanation Test for Funding Matches ===\n")
    
    # 1. Load previous matching results
    print("1. Loading previous matching results...")
    try:
        with open('user_funding_matches.json', 'r') as f:
            match_results = json.load(f)
        print(f"   ✓ Loaded {len(match_results['matches'])} matched opportunities")
    except Exception as e:
        print(f"   ✗ Error loading matches: {e}")
        return
    
    # 2. Initialize components
    print("\n2. Initializing components...")
    try:
        user_manager = UserProfileManager()
        rag_explainer = RAGExplainer()
        print("   ✓ Components initialized")
    except Exception as e:
        print(f"   ✗ Error initializing: {e}")
        return
    
    # 3. Recreate user profile
    print("\n3. Loading user profile...")
    user_json_path = "input_documents/alfredo_costilla_reyes.json"
    pdf_paths = [
        "input_documents/CV PI Alfredo Costilla Reyes 04-2025.pdf",
        "input_documents/COSTILLAREYES-DISSERTATION-2020.pdf"
    ]
    
    # Add more documents for richer context
    additional_docs = [
        "input_documents/Proposals/Successful/NSF_SBIR/NSF21_SBIR_AutoML_OnDeviceAI.pdf",
        "input_documents/Proposals/Successful/NSF_SBIR/NSF22_SBIR_ph2_AutoML_OnDeviceAI.pdf",
        "input_documents/ResearchPapers/First author journals/A Time-Interleave-Based Power Management System with Maximum Power Extraction and Health Protection Algorithm for Multip.pdf",
        "input_documents/ResearchPapers/Rice/AutoVideo.pdf",
        "input_documents/Proposals/NotSuccessful/NSF22_PFI_OutlierDetection_RemoteAssetMonitoring.pdf"
    ]
    
    all_pdfs = pdf_paths + additional_docs
    existing_pdfs = [pdf for pdf in all_pdfs if os.path.exists(pdf)]
    
    try:
        profile = user_manager.create_user_profile(user_json_path, existing_pdfs)
        print(f"   ✓ Profile loaded with {len(profile['extracted_pdfs'])} documents")
        
        # Show document names for reference
        print("   Documents available for reuse:")
        for doc_name in profile['extracted_pdfs'].keys():
            print(f"     - {doc_name}")
            
    except Exception as e:
        print(f"   ✗ Error creating profile: {e}")
        return
    
    # 4. Generate explanations for top opportunities
    print("\n4. Generating RAG explanations for top 5 opportunities...")
    
    top_opportunities = match_results['matches'][:5]
    explained_opps = []
    
    for i, opp in enumerate(top_opportunities):
        print(f"\n   Processing opportunity {i+1}/5: {opp['title'][:60]}...")
        
        try:
            # Generate explanation
            explanation = rag_explainer.explain_match(
                profile, 
                opp,
                profile['extracted_pdfs']
            )
            
            # Add to opportunity
            opp_with_explanation = opp.copy()
            opp_with_explanation['rag_explanation'] = explanation
            explained_opps.append(opp_with_explanation)
            
            # Display results
            print(f"   ✓ Explanation generated")
            print(f"\n   MATCH EXPLANATION:")
            print(f"   {explanation['match_explanation']}")
            
            if explanation['reusable_content']:
                print(f"\n   REUSABLE CONTENT:")
                for content in explanation['reusable_content']:
                    print(f"   - {content['document']}")
                    print(f"     → {content['how_to_reuse']}")
            
            if explanation['next_steps']:
                print(f"\n   NEXT STEPS:")
                for j, step in enumerate(explanation['next_steps'], 1):
                    print(f"   {j}. {step}")
            
        except Exception as e:
            print(f"   ✗ Error generating explanation: {e}")
            import traceback
            traceback.print_exc()
    
    # 5. Save enhanced results
    print("\n5. Saving enhanced results...")
    
    enhanced_results = {
        'user': match_results['user'],
        'original_matches': len(match_results['matches']),
        'explained_opportunities': explained_opps,
        'generated_at': datetime.now().isoformat(),
        'documents_analyzed': list(profile['extracted_pdfs'].keys())
    }
    
    output_file = 'user_funding_matches_explained.json'
    try:
        with open(output_file, 'w') as f:
            json.dump(enhanced_results, f, indent=2)
        print(f"   ✓ Results saved to {output_file}")
    except Exception as e:
        print(f"   ✗ Error saving results: {e}")
    
    # 6. Generate summary report
    print("\n6. Summary Report:")
    print(f"   Total opportunities analyzed: {len(explained_opps)}")
    print(f"   Documents available for reuse: {len(profile['extracted_pdfs'])}")
    
    # Count reusable documents
    all_reusable = []
    for opp in explained_opps:
        if 'rag_explanation' in opp:
            for content in opp['rag_explanation'].get('reusable_content', []):
                all_reusable.append(content['document'])
    
    unique_reusable = list(set(all_reusable))
    print(f"   Unique documents identified as reusable: {len(unique_reusable)}")
    
    if unique_reusable:
        print("   Most frequently reusable documents:")
        doc_counts = {}
        for doc in all_reusable:
            doc_counts[doc] = doc_counts.get(doc, 0) + 1
        
        sorted_docs = sorted(doc_counts.items(), key=lambda x: x[1], reverse=True)
        for doc, count in sorted_docs[:3]:
            print(f"     - {doc}: {count} opportunities")
    
    print("\n✓ RAG Explanation test completed successfully!")


if __name__ == "__main__":
    main()