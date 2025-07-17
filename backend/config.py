import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Gemini API configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # Grants.gov API configuration
    GRANTS_GOV_API_KEY = os.getenv('GRANTS_GOV_API_KEY')
    GRANTS_GOV_BASE_URL = "https://www.grants.gov/grantsws/rest/opportunities/search/"
    
    # Sam.gov API configuration
    SAM_GOV_API_KEY = os.getenv('SAM_GOV_API_KEY')
    SAM_GOV_BASE_URL = "https://api.sam.gov/opportunities/v2/search"
    
    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # File paths
    CV_FILE_PATH = "../input_documents/CV PI Alfredo Costilla Reyes 04-2025.pdf" 