#!/usr/bin/env python3
"""
PDF text extraction functionality for user documents
"""

import os
import fitz  # PyMuPDF
from typing import Dict, List, Optional
import re


class PDFExtractor:
    """Extract text from PDF documents"""
    
    def __init__(self):
        pass
    
    def extract_text_from_pdf(self, pdf_path: str) -> Optional[str]:
        """
        Extract text from a PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text or None if error
        """
        try:
            if not os.path.exists(pdf_path):
                print(f"PDF file not found: {pdf_path}")
                return None
                
            # Open PDF
            doc = fitz.open(pdf_path)
            
            # Extract text from all pages
            text_content = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    text_content.append(text)
            
            doc.close()
            
            # Join all text
            full_text = "\n".join(text_content)
            
            # Clean up text
            full_text = self._clean_text(full_text)
            
            return full_text
            
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might interfere
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # Trim
        text = text.strip()
        
        return text
    
    def extract_key_sections(self, text: str) -> Dict[str, str]:
        """
        Extract key sections from academic/CV text
        
        Args:
            text: Full text content
            
        Returns:
            Dictionary of key sections
        """
        sections = {
            'education': '',
            'experience': '',
            'publications': '',
            'skills': '',
            'awards': '',
            'research': ''
        }
        
        # Common section headers
        section_patterns = {
            'education': r'(?i)(education|academic\s+background|degrees?)',
            'experience': r'(?i)(experience|employment|work\s+history|positions?)',
            'publications': r'(?i)(publications?|papers?|articles?)',
            'skills': r'(?i)(skills?|expertise|competenc)',
            'awards': r'(?i)(awards?|honors?|achievements?)',
            'research': r'(?i)(research\s+interests?|research\s+areas?|research\s+experience)'
        }
        
        # Try to extract sections
        text_lower = text.lower()
        
        for section_name, pattern in section_patterns.items():
            matches = list(re.finditer(pattern, text_lower))
            if matches:
                # Find the start of this section
                start_idx = matches[0].start()
                
                # Find the next section start
                next_section_start = len(text)
                for other_section, other_pattern in section_patterns.items():
                    if other_section != section_name:
                        other_matches = list(re.finditer(other_pattern, text_lower[start_idx + 100:]))
                        if other_matches:
                            potential_end = start_idx + 100 + other_matches[0].start()
                            if potential_end < next_section_start:
                                next_section_start = potential_end
                
                # Extract section text
                section_text = text[start_idx:next_section_start].strip()
                sections[section_name] = section_text[:2000]  # Limit section length
        
        return sections
    
    def extract_from_multiple_pdfs(self, pdf_paths: List[str]) -> Dict[str, str]:
        """
        Extract and combine text from multiple PDFs
        
        Args:
            pdf_paths: List of PDF file paths
            
        Returns:
            Dictionary with filename as key and extracted text as value
        """
        results = {}
        
        for pdf_path in pdf_paths:
            if os.path.exists(pdf_path):
                text = self.extract_text_from_pdf(pdf_path)
                if text:
                    filename = os.path.basename(pdf_path)
                    results[filename] = text
                    print(f"✓ Extracted text from {filename} ({len(text)} characters)")
                else:
                    print(f"✗ Failed to extract text from {pdf_path}")
        
        return results