#!/usr/bin/env python3
"""
FundingMatch API Server
Provides REST endpoints for the React frontend
"""

import os
import sys
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from funding_opportunities_manager import FundingOpportunitiesManager
from user_profile_manager import UserProfileManager
from rag_explainer import RAGExplainer
from vector_database import VectorDatabaseManager

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})  # Enable CORS for all origins on API routes

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'pdf', 'json'}

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('FundingOpportunities/temp', exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize managers
funding_manager = FundingOpportunitiesManager()
user_manager = UserProfileManager()
vector_db = VectorDatabaseManager()


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    try:
        stats = vector_db.get_collection_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ingest/csv', methods=['POST'])
def ingest_csv():
    """Ingest CSV file with funding opportunities"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename) or not file.filename.endswith('.csv'):
        return jsonify({'success': False, 'error': 'Only CSV files are allowed'}), 400
    
    try:
        # Save file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join('FundingOpportunities/temp', filename)
        file.save(temp_path)
        
        # Move to main folder for processing
        final_path = os.path.join('FundingOpportunities', filename)
        os.rename(temp_path, final_path)
        
        # Process the file
        processed_count = funding_manager.process_csv_files()
        
        return jsonify({
            'success': True,
            'message': f'Successfully processed {processed_count} files',
            'filename': filename
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/profile/upload', methods=['POST'])
def upload_profile_document():
    """Upload PDF or JSON for user profile"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'Invalid file type'}), 400
    
    try:
        # Save file
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'path': save_path
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/profile/create', methods=['POST'])
def create_profile():
    """Create user profile from uploaded documents"""
    try:
        data = request.json
        uploaded_files = data.get('files', [])
        urls = data.get('urls', [])
        
        # Find JSON and PDF files
        json_file = None
        pdf_files = []
        
        for file_info in uploaded_files:
            filepath = file_info['path']
            if filepath.endswith('.json'):
                json_file = filepath
            elif filepath.endswith('.pdf'):
                pdf_files.append(filepath)
        
        if not json_file:
            # Create a basic JSON profile
            profile_data = {
                "person": {
                    "name": data.get('name', 'User'),
                    "biographical_information": {
                        "research_interests": data.get('interests', []),
                        "education": [],
                        "awards": []
                    },
                    "links": [{"url": url, "type": "web"} for url in urls]
                }
            }
            json_file = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_profile.json')
            with open(json_file, 'w') as f:
                json.dump(profile_data, f)
        
        # Create profile
        profile = user_manager.create_user_profile(json_file, pdf_files)
        
        # Store profile
        success = user_manager.store_user_profile(profile)
        
        if success:
            # Save profile summary
            profile_summary = {
                'name': profile['name'],
                'research_interests': profile['research_interests'],
                'documents_processed': len(profile['extracted_pdfs']),
                'created_at': datetime.now().isoformat()
            }
            
            return jsonify({
                'success': True,
                'profile': profile_summary
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to store profile'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/match', methods=['POST'])
def match_opportunities():
    """Match user profile with funding opportunities"""
    try:
        # Get the stored profile
        upload_dir = app.config['UPLOAD_FOLDER']
        json_files = [f for f in os.listdir(upload_dir) if f.endswith('.json')]
        
        if not json_files:
            return jsonify({
                'success': False,
                'error': 'No user profile found. Please create a profile first.'
            }), 400
        
        # Use the first JSON file
        json_path = os.path.join(upload_dir, json_files[0])
        
        # Get PDFs
        pdf_files = [os.path.join(upload_dir, f) for f in os.listdir(upload_dir) 
                    if f.endswith('.pdf')]
        
        # Recreate profile
        profile = user_manager.create_user_profile(json_path, pdf_files)
        
        # Get matches
        n_results = request.json.get('n_results', 20)
        matches = user_manager.match_user_to_opportunities(profile, n_results=n_results)
        
        return jsonify({
            'success': True,
            'matches': matches,
            'total': len(matches)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/opportunity/<int:index>/explain', methods=['POST'])
def explain_opportunity(index):
    """Get detailed explanation for a specific opportunity"""
    try:
        data = request.json
        opportunity = data.get('opportunity')
        
        if not opportunity:
            return jsonify({
                'success': False,
                'error': 'No opportunity data provided'
            }), 400
        
        # Get user profile
        upload_dir = app.config['UPLOAD_FOLDER']
        json_files = [f for f in os.listdir(upload_dir) if f.endswith('.json')]
        
        if not json_files:
            return jsonify({
                'success': False,
                'error': 'No user profile found'
            }), 400
        
        json_path = os.path.join(upload_dir, json_files[0])
        pdf_files = [os.path.join(upload_dir, f) for f in os.listdir(upload_dir) 
                    if f.endswith('.pdf')]
        
        # Create profile
        profile = user_manager.create_user_profile(json_path, pdf_files)
        
        # Generate explanation
        rag_explainer = RAGExplainer()
        explanation = rag_explainer.explain_match(
            profile,
            opportunity,
            profile['extracted_pdfs']
        )
        
        return jsonify({
            'success': True,
            'explanation': explanation
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Serve React app in production
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    if path != "" and os.path.exists(os.path.join('frontend/build', path)):
        return send_from_directory('frontend/build', path)
    else:
        return send_from_directory('frontend/build', 'index.html')


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=True, port=port)