#!/usr/bin/env python3
"""
Add missing documents from input_documents to Alfredo's profile
"""

import os
import shutil
import json
from pathlib import Path

def get_missing_documents():
    """Get list of PDFs in input_documents but not in uploads"""
    input_docs_dir = Path("input_documents")
    uploads_dir = Path("uploads")
    
    # Get all PDFs from input_documents
    input_pdfs = set()
    for pdf_path in input_docs_dir.rglob("*.pdf"):
        input_pdfs.add(pdf_path.name)
    
    # Get all PDFs from uploads
    upload_pdfs = set()
    for pdf_path in uploads_dir.glob("*.pdf"):
        upload_pdfs.add(pdf_path.name)
    
    # Find missing PDFs
    missing_pdfs = []
    for pdf_path in input_docs_dir.rglob("*.pdf"):
        if pdf_path.name not in upload_pdfs:
            missing_pdfs.append(pdf_path)
    
    return missing_pdfs

def add_documents_to_profile():
    """Add missing documents to Alfredo's profile"""
    missing_pdfs = get_missing_documents()
    
    if not missing_pdfs:
        print("✅ All documents from input_documents are already in uploads")
        return
    
    print(f"\n📄 Found {len(missing_pdfs)} missing documents:")
    for pdf in missing_pdfs:
        print(f"  - {pdf.name}")
    
    # Copy missing PDFs to uploads
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)
    
    copied = 0
    for pdf_path in missing_pdfs:
        try:
            dest_path = uploads_dir / pdf_path.name
            if not dest_path.exists():
                shutil.copy2(pdf_path, dest_path)
                print(f"  ✅ Copied: {pdf_path.name}")
                copied += 1
            else:
                print(f"  ⚠️  Already exists: {pdf_path.name}")
        except Exception as e:
            print(f"  ❌ Error copying {pdf_path.name}: {e}")
    
    print(f"\n✅ Copied {copied} new documents to uploads folder")
    
    # Now trigger profile reprocessing
    if copied > 0:
        print("\n🔄 To update Alfredo's embeddings with these new documents:")
        print("   1. Go to the User Profile page")
        print("   2. Click 'Reprocess' for Alfredo Costilla-Reyes")
        print("   This will regenerate embeddings including all documents")

if __name__ == "__main__":
    print("Adding missing documents to Alfredo's profile...")
    add_documents_to_profile()