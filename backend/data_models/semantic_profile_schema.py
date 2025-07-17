"""
Semantic Profile Schema Definition and Validation
FundingMatch v2.0 - Phase 1: Schema Foundation
"""

import json
import jsonschema
from typing import Dict, List, Any, Optional
from datetime import datetime
import os

# Schema version for compatibility management
SCHEMA_VERSION = "2.0"

# Complete semantic profile JSON schema
SEMANTIC_PROFILE_SCHEMA = {
    "type": "object",
    "properties": {
        "profile_metadata": {
            "type": "object",
            "properties": {
                "generated_date": {"type": "string", "format": "date-time"},
                "total_documents": {"type": "integer", "minimum": 0},
                "processing_version": {"type": "string", "enum": ["2.0"]},
                "primary_researcher": {"type": "string", "minLength": 1}
            },
            "required": ["generated_date", "total_documents", "processing_version", "primary_researcher"]
        },
        "portfolio_summary": {
            "type": "object",
            "properties": {
                "research_domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1
                },
                "career_stage": {"type": "string"},
                "funding_track_record": {
                    "type": "object",
                    "properties": {
                        "total_secured": {"type": "number", "minimum": 0},
                        "successful_proposals": {"type": "integer", "minimum": 0},
                        "agencies_worked_with": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["total_secured", "successful_proposals", "agencies_worked_with"]
                },
                "publication_metrics": {
                    "type": "object",
                    "properties": {
                        "first_author_papers": {"type": "integer", "minimum": 0},
                        "total_publications": {"type": "integer", "minimum": 0},
                        "h_index": {"type": "integer", "minimum": 0}
                    },
                    "required": ["first_author_papers", "total_publications", "h_index"]
                }
            },
            "required": ["research_domains", "career_stage", "funding_track_record", "publication_metrics"]
        },
        "documents": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "source_file": {"type": "string", "minLength": 1},
                    "document_type": {
                        "type": "string",
                        "enum": [
                            "Curriculum Vitae",
                            "Successful Proposal",
                            "Unsuccessful Proposal",
                            "First Author Journal Article",
                            "Co-author Journal Article",
                            "Conference Paper",
                            "Technical Report",
                            "Patent Application",
                            "Book Chapter",
                            "Workshop Paper"
                        ]
                    },
                    "processed_date": {"type": "string", "format": "date-time"},
                    "analysis": {"type": "object"}  # Flexible structure for different document types
                },
                "required": ["source_file", "document_type", "processed_date", "analysis"]
            },
            "minItems": 1
        },
        "synthesis": {
            "type": "object",
            "properties": {
                "core_competencies": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "domain": {"type": "string", "minLength": 1},
                            "evidence_strength": {
                                "type": "string",
                                "enum": ["Very Strong", "Strong", "Moderate", "Emerging"]
                            },
                            "supporting_documents": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 1
                            },
                            "key_innovations": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["domain", "evidence_strength", "supporting_documents", "key_innovations"]
                    },
                    "minItems": 1
                },
                "funding_readiness": {
                    "type": "object",
                    "properties": {
                        "sbir_sttr": {"type": "string"},
                        "academic_grants": {"type": "string"},
                        "commercial_contracts": {"type": "string"}
                    },
                    "required": ["sbir_sttr", "academic_grants", "commercial_contracts"]
                },
                "strategic_advantages": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1
                }
            },
            "required": ["core_competencies", "funding_readiness", "strategic_advantages"]
        }
    },
    "required": ["profile_metadata", "portfolio_summary", "documents", "synthesis"]
}

# Document type specific schemas
DOCUMENT_TYPE_SCHEMAS = {
    "Curriculum Vitae": {
        "type": "object",
        "properties": {
            "personal_info": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "minLength": 1},
                    "title": {"type": "string"},
                    "education": {"type": "string"},
                    "contact": {"type": "string"}
                },
                "required": ["name"]
            },
            "experience": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string"},
                        "organization": {"type": "string"},
                        "duration": {"type": "string"},
                        "key_activities": {"type": "array", "items": {"type": "string"}}
                    }
                }
            },
            "expertise": {"type": "array", "items": {"type": "string"}},
            "entrepreneurship": {"type": "object"}
        },
        "required": ["personal_info", "experience", "expertise"]
    },
    "Successful Proposal": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "minLength": 1},
            "summary": {"type": "string", "minLength": 1},
            "agency": {"type": "string", "minLength": 1},
            "program": {"type": "string", "minLength": 1},
            "award_amount": {"type": "number", "minimum": 0},
            "project_period": {"type": "string"},
            "key_objectives": {"type": "array", "items": {"type": "string"}},
            "proposed_methods": {"type": "array", "items": {"type": "string"}},
            "innovation_claims": {"type": "array", "items": {"type": "string"}},
            "commercialization_plan": {"type": "object"}
        },
        "required": ["title", "summary", "agency", "program", "award_amount", "key_objectives", "proposed_methods"]
    },
    "Unsuccessful Proposal": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "minLength": 1},
            "summary": {"type": "string", "minLength": 1},
            "agency": {"type": "string", "minLength": 1},
            "program": {"type": "string", "minLength": 1},
            "requested_amount": {"type": "number", "minimum": 0},
            "rejection_feedback": {"type": "string"},
            "reusable_sections": {"type": "array", "items": {"type": "string"}},
            "improvement_areas": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["title", "summary", "agency", "program", "requested_amount", "reusable_sections", "improvement_areas"]
    },
    "First Author Journal Article": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "minLength": 1},
            "journal": {"type": "string", "minLength": 1},
            "year": {"type": "integer", "minimum": 1900, "maximum": 2030},
            "authors": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "abstract_summary": {"type": "string", "minLength": 1},
            "key_contributions": {"type": "array", "items": {"type": "string"}},
            "impact_metrics": {"type": "object"},
            "relevant_domains": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["title", "journal", "year", "authors", "abstract_summary", "key_contributions", "relevant_domains"]
    },
    "Co-author Journal Article": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "minLength": 1},
            "journal": {"type": "string", "minLength": 1},
            "year": {"type": "integer", "minimum": 1900, "maximum": 2030},
            "authors": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "author_position": {"type": "integer", "minimum": 2},
            "abstract_summary": {"type": "string", "minLength": 1},
            "contribution_description": {"type": "string", "minLength": 1},
            "relevant_domains": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["title", "journal", "year", "authors", "author_position", "abstract_summary", "contribution_description", "relevant_domains"]
    },
    "Conference Paper": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "minLength": 1},
            "conference": {"type": "string", "minLength": 1},
            "year": {"type": "integer", "minimum": 1900, "maximum": 2030},
            "authors": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "abstract_summary": {"type": "string", "minLength": 1},
            "key_contributions": {"type": "array", "items": {"type": "string"}},
            "conference_tier": {"type": "string", "enum": ["Tier 1", "Tier 2", "Tier 3", "Workshop"]},
            "relevant_domains": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["title", "conference", "year", "authors", "abstract_summary", "key_contributions", "relevant_domains"]
    },
    "Technical Report": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "minLength": 1},
            "organization": {"type": "string", "minLength": 1},
            "year": {"type": "integer", "minimum": 1900, "maximum": 2030},
            "authors": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "report_number": {"type": "string"},
            "summary": {"type": "string", "minLength": 1},
            "key_findings": {"type": "array", "items": {"type": "string"}},
            "relevant_domains": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["title", "organization", "year", "authors", "summary", "key_findings", "relevant_domains"]
    },
    "Patent Application": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "minLength": 1},
            "application_number": {"type": "string", "minLength": 1},
            "filing_date": {"type": "string"},
            "inventors": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "assignee": {"type": "string"},
            "abstract_summary": {"type": "string", "minLength": 1},
            "technical_field": {"type": "string"},
            "commercial_potential": {"type": "string"},
            "relevant_domains": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["title", "application_number", "inventors", "abstract_summary", "technical_field", "relevant_domains"]
    },
    "Book Chapter": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "minLength": 1},
            "book_title": {"type": "string", "minLength": 1},
            "publisher": {"type": "string", "minLength": 1},
            "year": {"type": "integer", "minimum": 1900, "maximum": 2030},
            "authors": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "editors": {"type": "array", "items": {"type": "string"}},
            "chapter_summary": {"type": "string", "minLength": 1},
            "key_contributions": {"type": "array", "items": {"type": "string"}},
            "relevant_domains": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["title", "book_title", "publisher", "year", "authors", "chapter_summary", "key_contributions", "relevant_domains"]
    },
    "Workshop Paper": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "minLength": 1},
            "workshop_name": {"type": "string", "minLength": 1},
            "year": {"type": "integer", "minimum": 1900, "maximum": 2030},
            "authors": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "abstract_summary": {"type": "string", "minLength": 1},
            "key_contributions": {"type": "array", "items": {"type": "string"}},
            "workshop_type": {"type": "string"},
            "relevant_domains": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["title", "workshop_name", "year", "authors", "abstract_summary", "key_contributions", "relevant_domains"]
    }
}

class SemanticProfileValidator:
    """Validates semantic profiles against schema and provides detailed feedback"""
    
    def __init__(self):
        self.schema = SEMANTIC_PROFILE_SCHEMA
        self.document_schemas = DOCUMENT_TYPE_SCHEMAS
        
    def validate_semantic_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a complete semantic profile
        
        Args:
            profile: The semantic profile dictionary to validate
            
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "schema_version": SCHEMA_VERSION
        }
        
        try:
            # Validate against main schema
            jsonschema.validate(profile, self.schema)
            
            # Validate individual documents
            for i, document in enumerate(profile.get("documents", [])):
                doc_type = document.get("document_type")
                if doc_type in self.document_schemas:
                    try:
                        jsonschema.validate(document.get("analysis", {}), self.document_schemas[doc_type])
                    except jsonschema.ValidationError as e:
                        validation_result["warnings"].append(f"Document {i+1} ({doc_type}): {e.message}")
                        
            # Check for data quality issues
            self._check_data_quality(profile, validation_result)
            
        except jsonschema.ValidationError as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Schema validation error: {e.message}")
            
        return validation_result
    
    def _check_data_quality(self, profile: Dict[str, Any], validation_result: Dict[str, Any]):
        """Check for data quality issues beyond schema validation"""
        
        # Check if documents support the claimed competencies
        competencies = profile.get("synthesis", {}).get("core_competencies", [])
        available_docs = [doc["source_file"] for doc in profile.get("documents", [])]
        
        for competency in competencies:
            supporting_docs = competency.get("supporting_documents", [])
            for doc in supporting_docs:
                if doc not in available_docs:
                    validation_result["warnings"].append(
                        f"Competency '{competency['domain']}' references missing document: {doc}"
                    )
        
        # Check funding track record consistency
        funding_record = profile.get("portfolio_summary", {}).get("funding_track_record", {})
        successful_proposals = [doc for doc in profile.get("documents", []) 
                              if doc["document_type"] == "Successful Proposal"]
        
        if funding_record.get("successful_proposals", 0) != len(successful_proposals):
            validation_result["warnings"].append(
                "Funding track record count doesn't match successful proposal documents"
            )

def create_sample_semantic_profile() -> Dict[str, Any]:
    """Create a sample semantic profile for testing"""
    
    sample_profile = {
        "profile_metadata": {
            "generated_date": datetime.now().isoformat(),
            "total_documents": 2,
            "processing_version": "2.0",
            "primary_researcher": "Dr. Test Researcher"
        },
        "portfolio_summary": {
            "research_domains": ["Computer Vision", "Machine Learning"],
            "career_stage": "Mid-Career Academic",
            "funding_track_record": {
                "total_secured": 500000,
                "successful_proposals": 1,
                "agencies_worked_with": ["NSF"]
            },
            "publication_metrics": {
                "first_author_papers": 5,
                "total_publications": 8,
                "h_index": 10
            }
        },
        "documents": [
            {
                "source_file": "sample_cv.pdf",
                "document_type": "Curriculum Vitae",
                "processed_date": datetime.now().isoformat(),
                "analysis": {
                    "personal_info": {
                        "name": "Dr. Test Researcher",
                        "title": "Associate Professor",
                        "education": "PhD Computer Science",
                        "contact": "test@example.edu"
                    },
                    "experience": [
                        {
                            "role": "Associate Professor",
                            "organization": "Test University",
                            "duration": "2020-present",
                            "key_activities": ["Teaching", "Research", "Service"]
                        }
                    ],
                    "expertise": ["Computer Vision", "Machine Learning"]
                }
            },
            {
                "source_file": "sample_proposal.pdf",
                "document_type": "Successful Proposal",
                "processed_date": datetime.now().isoformat(),
                "analysis": {
                    "title": "AI for Test Applications",
                    "summary": "A test proposal for AI applications",
                    "agency": "National Science Foundation",
                    "program": "Test Program",
                    "award_amount": 500000,
                    "project_period": "3 years",
                    "key_objectives": ["Develop AI system", "Validate approach"],
                    "proposed_methods": ["Machine Learning", "Computer Vision"],
                    "innovation_claims": ["Novel approach", "Improved accuracy"]
                }
            }
        ],
        "synthesis": {
            "core_competencies": [
                {
                    "domain": "Computer Vision",
                    "evidence_strength": "Strong",
                    "supporting_documents": ["sample_cv.pdf", "sample_proposal.pdf"],
                    "key_innovations": ["Novel CV algorithms", "Real-time processing"]
                }
            ],
            "funding_readiness": {
                "sbir_sttr": "Good - Some experience",
                "academic_grants": "Excellent - Proven track record",
                "commercial_contracts": "Moderate - Limited experience"
            },
            "strategic_advantages": [
                "Proven academic track record",
                "Strong technical expertise",
                "Established research network"
            ]
        }
    }
    
    return sample_profile

def load_sample_semantic_profile() -> Dict[str, Any]:
    """Load sample semantic profile for testing"""
    return create_sample_semantic_profile()

def validate_semantic_profile(profile: Dict[str, Any]) -> bool:
    """Simple validation function that returns True/False"""
    validator = SemanticProfileValidator()
    result = validator.validate_semantic_profile(profile)
    return result["valid"]

def save_semantic_profile(profile: Dict[str, Any], filepath: str) -> bool:
    """Save semantic profile to file with validation"""
    validator = SemanticProfileValidator()
    result = validator.validate_semantic_profile(profile)
    
    if not result["valid"]:
        print(f"Validation errors: {result['errors']}")
        return False
    
    if result["warnings"]:
        print(f"Validation warnings: {result['warnings']}")
    
    try:
        with open(filepath, 'w') as f:
            json.dump(profile, f, indent=2)
        print(f"Semantic profile saved to {filepath}")
        return True
    except Exception as e:
        print(f"Error saving profile: {e}")
        return False

def load_semantic_profile(filepath: str) -> Optional[Dict[str, Any]]:
    """Load and validate semantic profile from file"""
    try:
        with open(filepath, 'r') as f:
            profile = json.load(f)
        
        validator = SemanticProfileValidator()
        result = validator.validate_semantic_profile(profile)
        
        if not result["valid"]:
            print(f"Loaded profile is invalid: {result['errors']}")
            return None
            
        if result["warnings"]:
            print(f"Profile warnings: {result['warnings']}")
            
        return profile
        
    except Exception as e:
        print(f"Error loading profile: {e}")
        return None

# Export for testing
__all__ = [
    'SEMANTIC_PROFILE_SCHEMA',
    'DOCUMENT_TYPE_SCHEMAS', 
    'SemanticProfileValidator',
    'create_sample_semantic_profile',
    'load_sample_semantic_profile',
    'validate_semantic_profile',
    'save_semantic_profile',
    'load_semantic_profile'
] 