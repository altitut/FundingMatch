#!/usr/bin/env python3
"""
Check embed_content signature
"""

import os
from google import genai
from dotenv import load_dotenv
import inspect

load_dotenv()

# Initialize client
api_key = os.getenv('GEMINI_API_KEY')
client = genai.Client(api_key=api_key)

# Check embed_content signature
print("=== embed_content signature ===")
print(inspect.signature(client.models.embed_content))

# Try different ways to call it
print("\n=== Testing embed_content ===")

# Test 1: Try with positional arguments
try:
    response = client.models.embed_content(
        "models/text-embedding-004",
        "Test text for embedding"
    )
    print("✓ Success with positional args")
    print(f"  Response type: {type(response)}")
    print(f"  Response attributes: {dir(response)}")
    if hasattr(response, 'embedding'):
        print(f"  Embedding length: {len(response.embedding)}")
except Exception as e:
    print(f"✗ Failed with positional args: {e}")

# Test 2: Try with different parameters
try:
    response = client.models.embed_content(
        model="models/text-embedding-004",
        contents=["Test text for embedding"]
    )
    print("\n✓ Success with model and contents")
    print(f"  Response type: {type(response)}")
except Exception as e:
    print(f"\n✗ Failed with model and contents: {e}")