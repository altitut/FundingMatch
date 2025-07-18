#!/usr/bin/env python3
"""
Check available methods in google-genai library
"""

import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Initialize client
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("Error: GEMINI_API_KEY not found")
    exit(1)

client = genai.Client(api_key=api_key)

# Check available attributes
print("=== Client attributes ===")
print(dir(client))

print("\n=== Models attributes ===")
print(dir(client.models))

# Try to list available models
print("\n=== Available models ===")
try:
    models = client.models.list()
    for model in models:
        print(f"- {model.name}")
        if 'embedding' in model.name.lower():
            print(f"  Embedding model found: {model}")
except Exception as e:
    print(f"Error listing models: {e}")

# Check if we can access specific embedding model
print("\n=== Checking embedding model ===")
try:
    # Try different approaches
    model_name = 'models/text-embedding-004'
    
    # Check if we can get the model
    print(f"Trying to access model: {model_name}")
    
except Exception as e:
    print(f"Error: {e}")