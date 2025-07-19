#!/usr/bin/env python3
"""
FundingMatch API Server
Provides REST endpoints for the React frontend
"""

import os
import sys
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import queue
import threading
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
from matching_results_manager import MatchingResultsManager

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
matching_results = MatchingResultsManager()


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/test-ingest', methods=['POST'])
def test_ingest():
    """Simple test endpoint for ingestion"""
    try:
        return jsonify({
            'success': True,
            'message': 'Test endpoint working',
            'request_method': request.method,
            'files_present': 'file' in request.files,
            'file_count': len(request.files) if request.files else 0
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    try:
        # Get stats from vector DB
        db_stats = vector_db.get_collection_stats()
        
        # Also get tracked opportunities count
        tracked_count = len(funding_manager.processed_ids.get("opportunities", {}))
        
        # If there's a mismatch, use the vector DB as source of truth
        if db_stats['opportunities'] == 0 and tracked_count > 0:
            print(f"Warning: Mismatch - Tracked: {tracked_count}, In DB: {db_stats['opportunities']}")
            # Clear the tracked IDs since they're not in the database
            funding_manager.processed_ids["opportunities"] = {}
            funding_manager._save_processed_ids()
        
        # Also check for researchers in the database if count is 0
        if db_stats['researchers'] == 0:
            # Check files to get user count
            upload_dir = app.config['UPLOAD_FOLDER']
            user_count = 0
            
            if os.path.exists(upload_dir):
                # Count unique users from JSON files
                seen_users = set()
                json_files = [f for f in os.listdir(upload_dir) if f.endswith('.json')]
                for json_file in json_files:
                    try:
                        with open(os.path.join(upload_dir, json_file), 'r') as f:
                            data = json.load(f)
                            person = data.get('person', {})
                            name = person.get('name', '')
                            if name:
                                # Generate same ID as user_profile_manager
                                import hashlib
                                user_id = hashlib.md5(name.encode()).hexdigest()
                                seen_users.add(user_id)
                    except:
                        pass
                
                user_count = len(seen_users)
            
            # Update stats with file-based count if higher
            if user_count > db_stats['researchers']:
                db_stats['researchers'] = user_count
        
        # Get high-confidence matches count
        high_confidence_count = matching_results.get_high_confidence_matches_count(80.0)
        high_confidence_details = matching_results.get_high_confidence_matches_details(80.0, 5)
        
        # Add high-confidence matches to stats
        db_stats['high_confidence_matches'] = high_confidence_count
        db_stats['top_matches'] = high_confidence_details
        
        return jsonify({
            'success': True,
            'stats': db_stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/opportunities', methods=['GET'])
def get_opportunities():
    """Get all funding opportunities"""
    try:
        # Get all opportunities from the database
        opportunities = vector_db.get_all_opportunities()
        return jsonify({
            'success': True,
            'opportunities': opportunities
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/cleanup-expired', methods=['POST'])
def cleanup_expired_opportunities():
    """Remove expired funding opportunities from the database"""
    try:
        # Get force parameter from request
        force = request.json.get('force', False) if request.is_json else False
        
        # Run cleanup
        removed_count = funding_manager.remove_expired_opportunities(force=force)
        
        # Get updated statistics
        stats = funding_manager.get_statistics()
        
        return jsonify({
            'success': True,
            'removed_count': removed_count,
            'message': f'Removed {removed_count} expired opportunities',
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/sync-database', methods=['POST'])
def sync_database():
    """Sync tracked opportunities with vector database"""
    try:
        # Get tracked IDs
        tracked_ids = funding_manager.processed_ids.get("opportunities", {})
        
        # Get IDs actually in database
        db_opportunities = vector_db.get_all_opportunities()
        db_ids = {opp['id'] for opp in db_opportunities}
        
        # Find tracked IDs not in database
        missing_ids = set(tracked_ids.keys()) - db_ids
        
        # Remove missing IDs from tracking
        for missing_id in missing_ids:
            del funding_manager.processed_ids["opportunities"][missing_id]
        
        funding_manager._save_processed_ids()
        
        return jsonify({
            'success': True,
            'message': f'Synced database. Removed {len(missing_ids)} orphaned tracking entries.',
            'tracked_count': len(funding_manager.processed_ids.get("opportunities", {})),
            'db_count': len(db_opportunities)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users with their documents"""
    try:
        # Get all users from the database
        users = vector_db.get_all_researchers()
        
        # If no users in vector DB but files exist, create temporary users from files
        if not users:
            upload_dir = app.config['UPLOAD_FOLDER']
            if os.path.exists(upload_dir):
                # Look for JSON files to extract user names
                json_files = [f for f in os.listdir(upload_dir) if f.endswith('.json')]
                for json_file in json_files:
                    try:
                        with open(os.path.join(upload_dir, json_file), 'r') as f:
                            data = json.load(f)
                            person = data.get('person', {})
                            name = person.get('name', '')
                            if name:
                                # Generate same ID as user_profile_manager
                                import hashlib
                                user_id = hashlib.md5(name.encode()).hexdigest()
                                users.append({
                                    'id': user_id,
                                    'name': name,
                                    'research_interests': person.get('biographical_information', {}).get('research_interests', [])
                                })
                    except:
                        pass
        
        # Get processed documents for each user
        users_with_docs = []
        for user in users:
            user_data = {
                'id': user.get('id'),
                'name': user.get('name'),
                'documents': [],
                'urls': []
            }
            
            # Get documents from uploads folder
            upload_dir = app.config['UPLOAD_FOLDER']
            if os.path.exists(upload_dir):
                for file in os.listdir(upload_dir):
                    if file.endswith('.pdf'):
                        user_data['documents'].append({
                            'name': file,
                            'status': 'processed'
                        })
                    elif file.endswith('.json'):
                        # Parse JSON to check if it belongs to this user
                        try:
                            with open(os.path.join(upload_dir, file), 'r') as f:
                                data = json.load(f)
                                person = data.get('person', {})
                                json_name = person.get('name', '')
                                
                                # Generate ID to match user
                                import hashlib
                                json_user_id = hashlib.md5(json_name.encode()).hexdigest() if json_name else ''
                                
                                if json_user_id == user.get('id'):
                                    # This JSON belongs to this user - get URLs
                                    links = person.get('links', [])
                                    for link in links:
                                        user_data['urls'].append({
                                            'url': link.get('url', ''),
                                            'type': link.get('type', 'web'),
                                            'status': link.get('status', 'processed')
                                        })
                        except:
                            pass
            
            users_with_docs.append(user_data)
        
        return jsonify({
            'success': True,
            'users': users_with_docs
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/profile/remove-document', methods=['POST'])
def remove_document():
    """Remove a document from user profile"""
    try:
        data = request.json
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'success': False, 'error': 'No filename provided'}), 400
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user and all their associated data"""
    try:
        # Remove user from vector database
        vector_db.remove_researcher(user_id)
        
        # Remove all files associated with the user
        upload_dir = app.config['UPLOAD_FOLDER']
        if os.path.exists(upload_dir):
            for file in os.listdir(upload_dir):
                filepath = os.path.join(upload_dir, file)
                # Remove files that might be associated with this user
                try:
                    os.remove(filepath)
                except:
                    pass
        
        return jsonify({
            'success': True,
            'message': 'User and associated data removed successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/profile/remove-document', methods=['POST'])
def remove_document_from_profile():
    """Remove a document from user profile and update embeddings"""
    try:
        data = request.json
        user_id = data.get('user_id')
        filename = data.get('filename')
        
        if not user_id or not filename:
            return jsonify({'success': False, 'error': 'Missing user_id or filename'}), 400
        
        # Get existing user profile
        user_data = vector_db.researchers.get(ids=[user_id], include=['metadatas', 'documents'])
        if not user_data or not user_data.get('metadatas'):
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Find the user's JSON file
        json_file = None
        upload_dir = app.config['UPLOAD_FOLDER']
        
        # Try to find matching JSON file by checking content
        json_files = [f for f in os.listdir(upload_dir) if f.endswith('.json')]
        for jf in json_files:
            try:
                with open(os.path.join(upload_dir, jf), 'r') as f:
                    json_data = json.load(f)
                    person = json_data.get('person', {})
                    name = person.get('name', '')
                    # Generate ID same way as user_profile_manager
                    import hashlib
                    file_user_id = hashlib.md5(name.encode()).hexdigest()
                    if file_user_id == user_id:
                        json_file = os.path.join(upload_dir, jf)
                        break
            except:
                pass
        
        if not json_file:
            return jsonify({'success': False, 'error': 'User profile JSON not found'}), 404
        
        # Remove the physical file
        file_path = os.path.join(upload_dir, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Get remaining PDF files
        pdf_files = [os.path.join(upload_dir, f) 
                    for f in os.listdir(upload_dir) 
                    if f.endswith('.pdf') and f != filename]
        
        # Recreate profile with remaining documents
        profile = user_manager.create_user_profile(json_file, pdf_files)
        
        # Store updated profile (this will update embeddings)
        success = user_manager.store_user_profile(profile)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Document removed and profile updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to update profile after document removal'
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/profile/remove-url', methods=['POST'])
def remove_url_from_profile():
    """Remove a URL from user profile and update embeddings"""
    try:
        data = request.json
        user_id = data.get('user_id')
        url_to_remove = data.get('url')
        
        if not user_id or not url_to_remove:
            return jsonify({'success': False, 'error': 'Missing user_id or url'}), 400
        
        # Get existing user profile
        user_data = vector_db.researchers.get(ids=[user_id], include=['metadatas', 'documents'])
        if not user_data or not user_data.get('metadatas'):
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Find the user's JSON file
        json_file = None
        upload_dir = app.config['UPLOAD_FOLDER']
        
        # Try to find matching JSON file by checking content
        json_files = [f for f in os.listdir(upload_dir) if f.endswith('.json')]
        for jf in json_files:
            try:
                json_path = os.path.join(upload_dir, jf)
                with open(json_path, 'r') as f:
                    json_data = json.load(f)
                    person = json_data.get('person', {})
                    name = person.get('name', '')
                    # Generate ID same way as user_profile_manager
                    import hashlib
                    file_user_id = hashlib.md5(name.encode()).hexdigest()
                    if file_user_id == user_id:
                        json_file = json_path
                        
                        # Remove the URL from the JSON
                        links = person.get('links', [])
                        updated_links = [link for link in links if link.get('url') != url_to_remove]
                        
                        if len(updated_links) < len(links):
                            # URL was found and removed
                            person['links'] = updated_links
                            
                            # Save updated JSON
                            with open(json_path, 'w') as f_write:
                                json.dump(json_data, f_write, indent=2)
                            
                            break
            except:
                pass
        
        if not json_file:
            return jsonify({'success': False, 'error': 'User profile JSON not found'}), 404
        
        # Get remaining PDF files
        pdf_files = [os.path.join(upload_dir, f) 
                    for f in os.listdir(upload_dir) 
                    if f.endswith('.pdf')]
        
        # Recreate profile with updated URLs
        profile = user_manager.create_user_profile(json_file, pdf_files)
        
        # Store updated profile (this will update embeddings)
        success = user_manager.store_user_profile(profile)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'URL removed and profile updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to update profile after URL removal'
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/profile/process', methods=['POST'])
def process_profile_updates():
    """Process new documents for embeddings"""
    try:
        data = request.json
        user_id = data.get('user_id')
        new_files = data.get('new_files', [])
        
        # Find the correct JSON file for this user
        json_file = None
        upload_dir = app.config['UPLOAD_FOLDER']
        
        if user_id:
            # Try to find matching JSON file by checking content
            json_files = [f for f in os.listdir(upload_dir) if f.endswith('.json')]
            for jf in json_files:
                try:
                    json_path = os.path.join(upload_dir, jf)
                    with open(json_path, 'r') as f:
                        json_data = json.load(f)
                        person = json_data.get('person', {})
                        name = person.get('name', '')
                        # Generate ID same way as user_profile_manager
                        import hashlib
                        file_user_id = hashlib.md5(name.encode()).hexdigest()
                        if file_user_id == user_id:
                            json_file = json_path
                            break
                except:
                    pass
        
        if not json_file:
            # Fallback to first JSON file if user_id not found
            json_files = [f for f in os.listdir(upload_dir) if f.endswith('.json')]
            if not json_files:
                return jsonify({'success': False, 'error': 'No user profile found'}), 400
            json_file = os.path.join(upload_dir, json_files[0])
        
        # Get all PDF files
        pdf_files = [os.path.join(upload_dir, f) 
                    for f in os.listdir(upload_dir) if f.endswith('.pdf')]
        
        print(f"Reprocessing profile with {len(pdf_files)} PDFs")
        
        # Create updated profile
        profile = user_manager.create_user_profile(json_file, pdf_files)
        
        # Count documents and URLs
        documents_processed = len(profile.get('extracted_pdfs', {}))
        urls_processed = len([url for url in profile.get('urls', []) if url.get('status') == 'processed'])
        
        # Store updated profile
        success = user_manager.store_user_profile(profile)
        
        if success:
            return jsonify({
                'success': True,
                'documents_processed': documents_processed,
                'urls_processed': urls_processed,
                'message': f'Profile reprocessed successfully with {documents_processed} documents and {urls_processed} URLs'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to store updated profile'}), 500
            
    except Exception as e:
        print(f"Error in process_profile_updates: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/profile/update', methods=['POST'])
def update_profile():
    """Update existing user profile with new documents"""
    try:
        data = request.json
        user_id = data.get('user_id')
        files = data.get('files', [])
        urls = data.get('urls', [])
        add_only = data.get('add_only', True)
        
        if not user_id:
            return jsonify({'success': False, 'error': 'No user_id provided'}), 400
        
        # Get existing user data
        user_data = vector_db.researchers.get(ids=[user_id], include=['metadatas'])
        if not user_data or not user_data.get('metadatas'):
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Find the user's JSON file
        json_file = None
        upload_dir = app.config['UPLOAD_FOLDER']
        
        # Try to find matching JSON file by checking content
        json_files = [f for f in os.listdir(upload_dir) if f.endswith('.json')]
        for jf in json_files:
            try:
                with open(os.path.join(upload_dir, jf), 'r') as f:
                    json_data = json.load(f)
                    person = json_data.get('person', {})
                    name = person.get('name', '')
                    # Generate ID same way as user_profile_manager
                    import hashlib
                    file_user_id = hashlib.md5(name.encode()).hexdigest()
                    if file_user_id == user_id:
                        json_file = os.path.join(upload_dir, jf)
                        break
            except:
                pass
        
        if not json_file:
            # Create a basic JSON file from existing metadata
            metadata = user_data['metadatas'][0]
            profile_data = {
                "person": {
                    "name": metadata.get('name', 'User'),
                    "biographical_information": {
                        "research_interests": metadata.get('research_interests', []),
                        "education": [],
                        "awards": []
                    },
                    "links": [{"url": url, "type": "web"} for url in urls if url]
                }
            }
            json_file = os.path.join(upload_dir, f"{user_id}_profile.json")
            with open(json_file, 'w') as f:
                json.dump(profile_data, f)
        
        # Update the JSON file with new URLs BEFORE creating profile
        if urls:
            try:
                with open(json_file, 'r') as f:
                    json_data = json.load(f)
                
                # Get existing links
                existing_links = json_data.get('person', {}).get('links', [])
                existing_urls = [link['url'] for link in existing_links]
                
                # Add new URLs
                for url in urls:
                    if url and url not in existing_urls:
                        existing_links.append({"url": url, "type": "web"})
                
                # Update JSON data
                json_data.setdefault('person', {})['links'] = existing_links
                
                # Save updated JSON
                with open(json_file, 'w') as f:
                    json.dump(json_data, f, indent=2)
            except Exception as e:
                print(f"Warning: Could not update JSON file with URLs: {e}")
        
        # Get all PDF files to process
        pdf_files = []
        
        # First, collect all existing PDFs from uploads directory
        existing_pdfs = []
        if os.path.exists(upload_dir):
            for file in os.listdir(upload_dir):
                if file.endswith('.pdf'):
                    existing_pdfs.append(os.path.join(upload_dir, file))
        
        # Add existing PDFs first
        pdf_files.extend(existing_pdfs)
        
        # Then add any new PDFs from the request
        for file_info in files:
            if file_info.get('type') == 'pdf':
                filepath = file_info.get('path', '')
                # Handle both absolute and relative paths
                if not os.path.isabs(filepath):
                    filepath = os.path.join(os.path.dirname(__file__), filepath)
                if os.path.exists(filepath) and filepath not in pdf_files:
                    pdf_files.append(filepath)
        
        print(f"Processing {len(pdf_files)} total PDFs for profile update")
        
        # Create updated profile with all documents (URLs will be processed from JSON)
        profile = user_manager.create_user_profile(json_file, pdf_files)
        
        # Store updated profile
        success = user_manager.store_user_profile(profile)
        
        if success:
            # Count new items added
            new_pdf_count = len([f for f in files if f.get('type') == 'pdf' and 'uploads/' not in f.get('path', '')])
            # Count URLs that were actually new (not already in existing_urls)
            new_url_count = len([u for u in urls if u.strip()])
            total_new_items = new_pdf_count + new_url_count
            
            return jsonify({
                'success': True,
                'message': 'Profile updated successfully',
                'documents_processed': new_pdf_count,
                'urls_processed': new_url_count,
                'total_processed': total_new_items
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to update profile'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Global progress queue for SSE
progress_queues = {}

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
        
        # Generate a unique session ID for progress tracking
        session_id = datetime.now().strftime('%Y%m%d%H%M%S') + '_' + filename
        
        # Create a progress queue for this session
        progress_queue = queue.Queue()
        progress_queues[session_id] = progress_queue
        
        # Process in background thread
        def process_with_progress():
            def progress_callback(progress_data):
                progress_queue.put(json.dumps(progress_data))
            
            try:
                summary = funding_manager.process_single_csv_file(filename, 
                                                                progress_callback=progress_callback)
                # Send final summary
                progress_queue.put(json.dumps({
                    'status': 'complete',
                    'summary': summary
                }))
            except Exception as e:
                progress_queue.put(json.dumps({
                    'status': 'error',
                    'error': str(e)
                }))
            finally:
                # Clean up after 5 minutes
                threading.Timer(300, lambda: progress_queues.pop(session_id, None)).start()
        
        # Start processing in background
        thread = threading.Thread(target=process_with_progress)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'filename': filename,
            'message': 'Processing started. Use session_id to track progress.'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ingest/progress/<session_id>')
def ingest_progress(session_id):
    """Server-Sent Events endpoint for progress updates"""
    def generate():
        if session_id not in progress_queues:
            yield f"data: {json.dumps({'error': 'Invalid session ID'})}\n\n"
            return
        
        progress_queue = progress_queues[session_id]
        
        # Send initial connection message
        yield f"data: {json.dumps({'status': 'connected'})}\n\n"
        
        # Send progress updates
        while True:
            try:
                # Wait for progress update with timeout
                progress_data = progress_queue.get(timeout=30)
                yield f"data: {progress_data}\n\n"
                
                # Check if processing is complete
                data = json.loads(progress_data)
                if data.get('status') in ['complete', 'error']:
                    break
                    
            except queue.Empty:
                # Send keepalive
                yield f"data: {json.dumps({'keepalive': True})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                break
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )


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
            # Update the JSON file to include all URLs (from both JSON and manual input)
            try:
                with open(json_file, 'r') as f:
                    json_data = json.load(f)
                
                # Update links in JSON data
                existing_urls = [link['url'] for link in json_data.get('person', {}).get('links', [])]
                for url in urls:
                    if url and url not in existing_urls:
                        json_data.setdefault('person', {}).setdefault('links', []).append({
                            'url': url,
                            'type': 'web',
                            'status': 'processed'
                        })
                
                # Save updated JSON
                with open(json_file, 'w') as f:
                    json.dump(json_data, f, indent=2)
            except Exception as e:
                print(f"Warning: Could not update JSON file with URLs: {e}")
            
            # Save profile summary
            profile_summary = {
                'id': profile['id'],
                'name': profile['name'],
                'research_interests': profile['research_interests'],
                'documents_processed': len(profile['extracted_pdfs']),
                'created_at': datetime.now().isoformat()
            }
            
            return jsonify({
                'success': True,
                'profile': profile_summary,
                'user_id': profile['id']
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


@app.route('/api/match/saved/<user_id>', methods=['GET'])
def get_saved_matches(user_id):
    """Get saved matches for a user"""
    try:
        limit = request.args.get('limit', type=int)
        matches = matching_results.get_matches(user_id, limit)
        
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

@app.route('/api/match', methods=['POST'])
def match_opportunities():
    """Match user profile with funding opportunities"""
    try:
        # Get user_id from request
        user_id = request.json.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'No user_id provided'
            }), 400
        
        # Search for matching opportunities directly using user's ID
        n_results = request.json.get('n_results', 20)
        
        # Get user embeddings from the database
        try:
            result = vector_db.researchers.get(ids=[user_id], include=['embeddings', 'metadatas', 'documents'])
        except Exception as e:
            print(f"Error getting user from vector DB: {e}")
            result = None
        
        # Check if we have valid embeddings
        has_embeddings = False
        if result and 'embeddings' in result and result['embeddings'] is not None:
            # Check if embeddings list is not empty and first embedding exists
            if len(result['embeddings']) > 0 and result['embeddings'][0] is not None:
                has_embeddings = True
        
        if not has_embeddings:
            # Try to find user in files and recreate profile
            upload_dir = app.config['UPLOAD_FOLDER']
            user_found = False
            
            if os.path.exists(upload_dir):
                # Look for JSON files with matching user
                json_files = [f for f in os.listdir(upload_dir) if f.endswith('.json')]
                for json_file in json_files:
                    try:
                        json_path = os.path.join(upload_dir, json_file)
                        with open(json_path, 'r') as f:
                            data = json.load(f)
                            person = data.get('person', {})
                            name = person.get('name', '')
                            if name:
                                # Generate same ID as user_profile_manager
                                import hashlib
                                file_user_id = hashlib.md5(name.encode()).hexdigest()
                                
                                if file_user_id == user_id:
                                    # Found the user - recreate profile
                                    pdf_files = [os.path.join(upload_dir, f) 
                                               for f in os.listdir(upload_dir) if f.endswith('.pdf')]
                                    
                                    # Recreate and store profile
                                    profile = user_manager.create_user_profile(json_path, pdf_files)
                                    success = user_manager.store_user_profile(profile)
                                    
                                    if success:
                                        # Try again to get embeddings
                                        result = vector_db.researchers.get(ids=[user_id], include=['embeddings', 'metadatas', 'documents'])
                                        user_found = True
                                    break
                    except Exception as e:
                        print(f"Error processing file {json_file}: {e}")
                        pass
            
            # Re-check embeddings after profile creation
            has_embeddings = False
            if result and 'embeddings' in result and result['embeddings'] is not None:
                if len(result['embeddings']) > 0 and result['embeddings'][0] is not None:
                    has_embeddings = True
            
            if not user_found or not has_embeddings:
                return jsonify({
                    'success': False,
                    'error': 'User not found. Please create a profile first.'
                }), 400
        
        # Use the stored embedding to search for opportunities
        user_embedding = result['embeddings'][0]
        matches = vector_db.search_opportunities_for_profile(
            user_embedding,
            n_results=n_results
        )
        
        # Format matches for frontend
        formatted_matches = []
        
        # Get min and max scores for normalization
        scores = [match.get('similarity_score', 0) for match in matches]
        min_score = min(scores) if scores else 0
        max_score = max(scores) if scores else 1
        score_range = max_score - min_score if max_score > min_score else 1
        
        for match in matches:
            # Calculate confidence scores with better distribution
            similarity = match.get('similarity_score', 0)
            
            # Normalize score to 0-1 range based on actual min/max
            if score_range > 0:
                normalized_score = (similarity - min_score) / score_range
            else:
                normalized_score = similarity
            
            # Apply non-linear transformation for better spread
            # This maps [0,1] to approximately [20,95] with most values in [40,85]
            confidence = 20 + (75 * (normalized_score ** 0.7))
            confidence = min(95, max(20, confidence))
            
            # Handle keywords - ensure it's always a list
            keywords = match.get('keywords', [])
            if isinstance(keywords, str):
                try:
                    # Try to parse as JSON if it's a string
                    import json as json_module
                    keywords = json_module.loads(keywords)
                except:
                    # If parsing fails, treat as comma-separated string
                    keywords = [k.strip() for k in keywords.split(',') if k.strip()]
            elif not isinstance(keywords, list):
                keywords = []
            
            formatted_matches.append({
                'title': match.get('title', 'Unknown'),
                'agency': match.get('agency', 'Unknown'),
                'description': match.get('description', '')[:200] + '...' if match.get('description') else '',
                'keywords': keywords[:5] if keywords else [],
                'deadline': match.get('close_date', 'Not specified'),
                'url': match.get('url', ''),
                'confidence_score': round(confidence, 1),
                'similarity_score': round(similarity, 4),
                'raw_distance': round(match.get('raw_distance', 0), 4) if 'raw_distance' in match else None
            })
        
        # Sort by confidence score
        formatted_matches.sort(key=lambda x: x['confidence_score'], reverse=True)
        
        # Save matches to user database
        try:
            matching_results.save_matches(user_id, formatted_matches)
        except Exception as e:
            print(f"Warning: Failed to save matches to database: {e}")
        
        return jsonify({
            'success': True,
            'matches': formatted_matches,
            'total': len(formatted_matches)
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


@app.route('/api/opportunities/unprocessed', methods=['GET'])
def get_unprocessed_opportunities():
    """Get tracking data for unprocessed opportunities"""
    try:
        tracking_file = os.path.join('FundingOpportunities', 'unprocessed_tracking.json')
        
        if os.path.exists(tracking_file):
            with open(tracking_file, 'r') as f:
                tracking_data = json.load(f)
        else:
            # Return empty structure if file doesn't exist
            tracking_data = {
                "no_deadline": [],
                "duplicates": [],
                "errors": [],
                "expired": [],
                "statistics": {
                    "total_no_deadline": 0,
                    "total_duplicates": 0,
                    "total_errors": 0,
                    "total_expired": 0
                }
            }
        
        return jsonify({
            'success': True,
            'data': tracking_data
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
    port = int(os.getenv('PORT', 5001))
    app.run(debug=True, port=port)