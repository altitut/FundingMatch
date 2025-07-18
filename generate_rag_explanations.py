#!/usr/bin/env python3
"""
Generate RAG-based explanations for funding matches
"""

import os
import sys
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from user_profile_manager import UserProfileManager
from rag_explainer import RAGExplainer


def main():
    """Generate explanations for top funding matches"""
    
    print("=== Generating RAG Explanations for Funding Matches ===\n")
    
    # Check if matches exist
    matches_file = "output_results/user_funding_matches.json"
    if not os.path.exists(matches_file):
        print("❌ No funding matches found. Please run match_opportunities.py first")
        return
    
    # Load matches
    with open(matches_file, 'r') as f:
        match_results = json.load(f)
    
    print(f"Generating explanations for {match_results['user']['name']}")
    print(f"Total matches to explain: {min(5, len(match_results['matches']))}")
    
    # Initialize components
    try:
        rag_explainer = RAGExplainer()
        user_manager = UserProfileManager()
    except Exception as e:
        print(f"❌ Error initializing components: {e}")
        return
    
    # Recreate user profile
    print("\nLoading user profile...")
    
    # Find user JSON
    json_files = [f for f in os.listdir("input_documents") if f.endswith('.json')]
    if not json_files:
        print("❌ User JSON file not found")
        return
    
    user_json_path = os.path.join("input_documents", json_files[0])
    
    # Find PDFs
    pdf_paths = []
    for root, dirs, files in os.walk("input_documents"):
        for file in files:
            if file.endswith('.pdf'):
                pdf_paths.append(os.path.join(root, file))
    
    # Create profile
    profile = user_manager.create_user_profile(user_json_path, pdf_paths)
    
    # Generate explanations for top matches
    print("\nGenerating explanations...")
    explained_opportunities = []
    
    top_matches = match_results['matches'][:5]
    
    for i, opp in enumerate(top_matches, 1):
        print(f"\nExplaining match {i}/5: {opp['title'][:60]}...")
        
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
            explained_opportunities.append(opp_with_explanation)
            
            print("✓ Explanation generated")
            
            # Display summary
            if explanation.get('match_explanation'):
                print(f"  Why it matches: {explanation['match_explanation'][:100]}...")
            if explanation.get('reusable_content'):
                print(f"  Reusable documents: {len(explanation['reusable_content'])}")
            if explanation.get('next_steps'):
                print(f"  Next steps provided: {len(explanation['next_steps'])}")
                
        except Exception as e:
            print(f"❌ Error generating explanation: {e}")
    
    # Save enhanced results
    print("\nSaving results...")
    
    enhanced_results = {
        'user': match_results['user'],
        'total_matches': len(match_results['matches']),
        'explained_opportunities': explained_opportunities,
        'documents_analyzed': list(profile['extracted_pdfs'].keys()),
        'generated_at': datetime.now().isoformat()
    }
    
    output_file = "output_results/user_funding_matches_explained.json"
    with open(output_file, 'w') as f:
        json.dump(enhanced_results, f, indent=2)
    
    print(f"\n✓ Enhanced results saved to {output_file}")
    
    # Generate readable report
    print("\nGenerating readable report...")
    
    report_file = "output_results/funding_match_report.md"
    with open(report_file, 'w') as f:
        f.write(f"# Funding Match Report for {match_results['user']['name']}\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"- Total matches found: {len(match_results['matches'])}\n")
        f.write(f"- Top matches explained: {len(explained_opportunities)}\n")
        f.write(f"- Documents analyzed: {len(profile['extracted_pdfs'])}\n\n")
        
        f.write("## Top Funding Opportunities\n\n")
        
        for i, opp in enumerate(explained_opportunities, 1):
            f.write(f"### {i}. {opp['title']}\n\n")
            f.write(f"**Confidence Score:** {opp['confidence_score']}%\n")
            f.write(f"**Agency:** {opp['agency']}\n")
            f.write(f"**Deadline:** {opp['deadline']}\n")
            if opp.get('url'):
                f.write(f"**URL:** {opp['url']}\n")
            f.write("\n")
            
            if 'rag_explanation' in opp:
                exp = opp['rag_explanation']
                
                f.write("**Why This Matches:**\n")
                f.write(f"{exp.get('match_explanation', 'No explanation available')}\n\n")
                
                if exp.get('reusable_content'):
                    f.write("**Reusable Content:**\n")
                    for content in exp['reusable_content']:
                        f.write(f"- **{content['document']}**: {content['how_to_reuse']}\n")
                    f.write("\n")
                
                if exp.get('next_steps'):
                    f.write("**Next Steps:**\n")
                    for j, step in enumerate(exp['next_steps'], 1):
                        f.write(f"{j}. {step}\n")
                    f.write("\n")
            
            f.write("---\n\n")
    
    print(f"✓ Readable report saved to {report_file}")
    
    # Summary statistics
    print("\n=== Summary ===")
    print(f"Total opportunities analyzed: {len(explained_opportunities)}")
    
    # Count reusable documents
    all_reusable = []
    for opp in explained_opportunities:
        if 'rag_explanation' in opp:
            for content in opp['rag_explanation'].get('reusable_content', []):
                all_reusable.append(content['document'])
    
    if all_reusable:
        unique_reusable = list(set(all_reusable))
        print(f"Unique documents identified as reusable: {len(unique_reusable)}")
        
        # Most frequently reusable
        from collections import Counter
        doc_counts = Counter(all_reusable)
        print("\nMost frequently reusable documents:")
        for doc, count in doc_counts.most_common(3):
            print(f"  - {doc}: {count} opportunities")


if __name__ == "__main__":
    main()