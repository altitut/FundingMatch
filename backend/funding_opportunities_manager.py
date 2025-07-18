"""
Funding Opportunities Manager
Handles CSV processing, embeddings generation, and ChromaDB storage with expiration management
"""

import os
import csv
import json
import shutil
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import hashlib

try:
    from .embeddings_manager import GeminiEmbeddingsManager
    from .vector_database import VectorDatabaseManager
    from .url_content_fetcher import URLContentFetcher
except ImportError:
    from embeddings_manager import GeminiEmbeddingsManager
    from vector_database import VectorDatabaseManager
    from url_content_fetcher import URLContentFetcher


class FundingOpportunitiesManager:
    """Manages funding opportunities lifecycle including processing, storage, and expiration"""
    
    def __init__(self, funding_dir: str = "FundingOpportunities", 
                 ingested_dir: str = "FundingOpportunities/Ingested"):
        """
        Initialize the funding opportunities manager
        
        Args:
            funding_dir: Directory containing CSV files to process
            ingested_dir: Directory to move processed CSV files
        """
        self.funding_dir = Path(funding_dir)
        self.ingested_dir = Path(ingested_dir)
        
        # Create directories if they don't exist
        self.funding_dir.mkdir(exist_ok=True)
        self.ingested_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.embeddings_manager = GeminiEmbeddingsManager()
        self.vector_db = VectorDatabaseManager()
        self.url_fetcher = URLContentFetcher()
        
        # Track processed opportunities
        self.processed_ids_file = self.funding_dir / "processed_opportunities.json"
        self.processed_ids = self._load_processed_ids()
        print(f"Loaded {len(self.processed_ids.get('opportunities', {}))} previously processed opportunities")
        
    def _load_processed_ids(self) -> Dict[str, Any]:
        """Load set of processed opportunity IDs"""
        if self.processed_ids_file.exists():
            with open(self.processed_ids_file, 'r') as f:
                return json.load(f)
        return {"opportunities": {}, "last_cleanup": None}
    
    def _save_processed_ids(self):
        """Save processed opportunity IDs"""
        with open(self.processed_ids_file, 'w') as f:
            json.dump(self.processed_ids, f, indent=2)
    
    def _generate_opportunity_id(self, opportunity: Dict[str, Any]) -> str:
        """Generate unique ID for an opportunity based on its content"""
        # Use core stable identifiers only - remove description which can vary
        # Normalize title by lowercasing and stripping whitespace
        title = opportunity.get('title', '').lower().strip()
        agency = opportunity.get('agency', '').strip()
        
        # For SBIR, topic number is the key differentiator
        topic_number = (opportunity.get('topic_number', '') or 
                       opportunity.get('Topic Number', '')).strip()
        
        # Core ID components
        id_string = f"{title}"
        id_string += f"|{agency}"
        
        # If we have a topic number, that's usually unique enough with title+agency
        if topic_number:
            id_string += f"|{topic_number}"
        else:
            # For non-SBIR, use program_id and branch as additional differentiators
            id_string += f"|{opportunity.get('program_id', '').strip()}"
            id_string += f"|{opportunity.get('branch', '').strip()}"
            
        # Only add phase/year if they exist to avoid false duplicates
        phase = opportunity.get('phase', '').strip()
        if phase:
            id_string += f"|{phase}"
            
        # Year is important for differentiating annual solicitations
        year = (opportunity.get('year', '') or 
                opportunity.get('Solicitation Year', '')).strip()
        if year:
            id_string += f"|{year}"
        
        # For opportunities with the same title/agency/topic, use dates to differentiate
        # This handles cases where HHS has multiple solicitations with same topic number
        close_date = (opportunity.get('close_date', '') or 
                     opportunity.get('Close Date', '') or
                     opportunity.get('deadline', '') or
                     opportunity.get('Deadline', '')).strip()
        if close_date:
            id_string += f"|{close_date}"
        
        # Also include release date if available as additional differentiator
        release_date = (opportunity.get('release_date', '') or 
                       opportunity.get('Release Date', '')).strip()
        if release_date:
            id_string += f"|{release_date}"
        
        # If still no unique identifiers, add URL as last resort
        if not close_date and not release_date:
            url = (opportunity.get('url', '') or 
                   opportunity.get('URL', '') or
                   opportunity.get('solicitation_url', '') or
                   opportunity.get('Solicitation URL', '')).strip()
            if url:
                # Use just the last part of URL to avoid full URL in hash
                id_string += f"|{url.split('/')[-1]}"
        
        # Generate hash
        return hashlib.md5(id_string.encode()).hexdigest()
    
    def _enrich_opportunity_with_url(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich opportunity with content from URL"""
        # Try different URL fields
        url_fields = ['url', 'URL', 'solicitation_url', 'Solicitation URL', 
                      'link', 'Link', 'website', 'sbir_topic_link', 'SBIRTopicLink']
        
        url = None
        for field in url_fields:
            if field in opportunity and opportunity[field]:
                url = opportunity[field]
                break
        
        if url:
            print(f"  🌐 Fetching content from: {url[:60]}...")
            # Add small delay to avoid rate limiting
            import time
            time.sleep(0.5)
            url_content = self.url_fetcher.fetch_url_content(url)
            
            if url_content:
                # Add URL content to opportunity
                opportunity['url_content'] = url_content
                
                # Enhance description with URL content
                if url_content.get('description'):
                    current_desc = opportunity.get('description', '')
                    opportunity['description'] = f"{current_desc}\n\nFrom URL: {url_content['description']}"
                
                # Add keywords from URL
                if url_content.get('keywords'):
                    current_keywords = opportunity.get('keywords', [])
                    if isinstance(current_keywords, list):
                        opportunity['keywords'] = list(set(current_keywords + url_content['keywords']))
                
                # Try to extract deadline from URL if not present
                if not opportunity.get('close_date') and url_content.get('deadline_info'):
                    deadline_date = self._parse_date(url_content['deadline_info'])
                    if deadline_date:
                        opportunity['close_date'] = deadline_date.strftime("%Y-%m-%d")
                        print(f"  📅 Found deadline from URL: {opportunity['close_date']}")
                
                # Add other enrichments
                if url_content.get('eligibility_info'):
                    opportunity['eligibility_enriched'] = url_content['eligibility_info']
                if url_content.get('award_info'):
                    opportunity['award_info_enriched'] = url_content['award_info']
                if url_content.get('contact_info'):
                    opportunity['contact_enriched'] = url_content['contact_info']
        
        return opportunity
    
    def _parse_date(self, date_string: str) -> Optional[datetime]:
        """Parse various date formats"""
        if not date_string or date_string.strip() == "":
            return None
            
        # Clean the date string
        date_string = date_string.strip()
        
        # Try different date formats
        date_formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%B %d, %Y",
            "%d-%m-%Y",
            "%Y/%m/%d",
            "%b %d, %Y",  # Jan 1, 2025
            "%B %d %Y",   # January 1 2025
            "%b %d %Y",   # Jan 1 2025
            "%d %B %Y",   # 1 January 2025
            "%d %b %Y",   # 1 Jan 2025
            "%m-%d-%Y",
            "%d/%m/%Y",
            "%Y.%m.%d",
            "%d.%m.%Y"
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_string, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        
        # Try to extract date from text like "August 20, 2025"
        import re
        date_pattern = re.compile(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})')
        match = date_pattern.search(date_string)
        if match:
            try:
                return datetime.strptime(match.group(0), "%B %d, %Y").replace(tzinfo=timezone.utc)
            except:
                pass
                
        return None
    
    def _extract_deadline_with_gemini(self, opportunity: Dict[str, Any]) -> Optional[str]:
        """Use Gemini to extract deadline from opportunity description"""
        try:
            # Combine all text fields
            text = f"""
            Title: {opportunity.get('title', '')}
            Description: {opportunity.get('description', '')}
            URL Content: {opportunity.get('url_content', {}).get('text', '')[:1000]}
            """
            
            prompt = """Extract the deadline or close date from this funding opportunity. 
            Return ONLY the date in format YYYY-MM-DD. 
            If no deadline is found, return 'NO_DEADLINE'.
            If the deadline is expressed as 'anytime' or 'continuous', return 'ANYTIME'.
            
            Text: {text}
            """
            
            # Use Gemini to extract deadline
            from google import genai
            import os
            client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
            response = client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=[prompt.format(text=text)]
            )
            
            result = response.text.strip()
            if result not in ['NO_DEADLINE', 'ANYTIME']:
                # Try to parse the date
                parsed_date = self._parse_date(result)
                if parsed_date:
                    return result
                    
        except Exception as e:
            print(f"  ⚠️ Error extracting deadline with Gemini: {e}")
            
        return None
    
    def _is_expired(self, opportunity: Dict[str, Any]) -> Tuple[bool, Optional[datetime]]:
        """
        Check if an opportunity is expired
        
        Returns:
            Tuple of (is_expired, expiration_date)
        """
        # Get current date
        now = datetime.now(timezone.utc)
        
        # Check various date fields
        date_fields = ['close_date', 'Close Date', 'deadline', 'Deadline', 'Next due date (Y-m-d)']
        
        for field in date_fields:
            if field in opportunity and opportunity[field]:
                exp_date = self._parse_date(opportunity[field])
                if exp_date:
                    return exp_date < now, exp_date
                    
        # If no date found in standard fields, try Gemini extraction (disable for now to save API calls)
        # Uncomment the following lines to enable Gemini deadline extraction
        # gemini_deadline = self._extract_deadline_with_gemini(opportunity)
        # if gemini_deadline and gemini_deadline not in ['NO_DEADLINE', 'ANYTIME']:
        #     # Add the extracted deadline to the opportunity
        #     opportunity['close_date'] = gemini_deadline
        #     exp_date = self._parse_date(gemini_deadline)
        #     if exp_date:
        #         return exp_date < now, exp_date
        # elif gemini_deadline == 'ANYTIME':
        #     # Set far future date for continuous opportunities
        #     opportunity['close_date'] = 'Continuous'
        #     far_future = datetime(2030, 12, 31, tzinfo=timezone.utc)
        #     return False, far_future
            
        # If no date found at all, consider not expired but flag it
        opportunity['close_date'] = 'Not specified'
        return False, None
    
    def process_csv_files(self, batch_size: int = 20) -> Dict[str, Any]:
        """
        Process all CSV files in the funding directory
        
        Args:
            batch_size: Number of opportunities to process in batch
            
        Returns:
            Processing summary
        """
        summary = {
            "processed_files": [],
            "new_opportunities": 0,
            "expired_skipped": 0,
            "duplicate_skipped": 0,
            "errors": []
        }
        
        # Find all CSV files
        csv_files = list(self.funding_dir.glob("*.csv"))
        
        for csv_file in csv_files:
            # Skip if already in ingested folder
            if csv_file.parent.name == "Ingested":
                continue
                
            print(f"\nProcessing: {csv_file.name}")
            
            try:
                # Process based on file type
                if "nsf" in csv_file.name.lower():
                    opportunities = self._process_nsf_csv(csv_file)
                elif "sbir" in csv_file.name.lower() or "topics" in csv_file.name.lower():
                    opportunities = self._process_sbir_csv(csv_file)
                else:
                    # Generic CSV processing
                    opportunities = self._process_generic_csv(csv_file)
                
                # Process opportunities
                file_summary = self._process_opportunities(opportunities, batch_size)
                
                summary["new_opportunities"] += file_summary["new"]
                summary["expired_skipped"] += file_summary["expired"]
                summary["duplicate_skipped"] += file_summary["duplicates"]
                
                # Move file to ingested folder
                ingested_path = self.ingested_dir / csv_file.name
                shutil.move(str(csv_file), str(ingested_path))
                print(f"Moved {csv_file.name} to Ingested folder")
                
                summary["processed_files"].append(csv_file.name)
                
            except Exception as e:
                error_msg = f"Error processing {csv_file.name}: {str(e)}"
                print(f"❌ {error_msg}")
                summary["errors"].append(error_msg)
        
        # Clean up expired opportunities
        removed = self.remove_expired_opportunities()
        summary["expired_removed"] = removed
        
        # Save processed IDs
        self._save_processed_ids()
        
        return summary
    
    def process_single_csv_file(self, filename: str, progress_callback=None) -> Dict[str, Any]:
        """
        Process a single CSV file with progress tracking
        
        Args:
            filename: Name of CSV file to process
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Processing summary
        """
        csv_path = self.funding_dir / filename
        
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {filename}")
        
        summary = {
            "filename": filename,
            "new_opportunities": 0,
            "expired_skipped": 0,
            "duplicate_skipped": 0,
            "errors": [],
            "unprocessed": []  # Track unprocessed opportunities with reasons
        }
        
        # Send initial progress
        if progress_callback:
            progress_callback({
                "status": "processing",
                "stage": "reading",
                "message": f"Reading {filename}..."
            })
        
        try:
            # Process based on file type
            if "nsf" in filename.lower():
                opportunities = self._process_nsf_csv(csv_path)
                if progress_callback:
                    progress_callback({
                        "status": "processing",
                        "stage": "debug",
                        "message": f"Processing as NSF file"
                    })
            elif "sbir" in filename.lower() or "topics" in filename.lower():
                opportunities = self._process_sbir_csv(csv_path)
                if progress_callback:
                    progress_callback({
                        "status": "processing",
                        "stage": "debug",
                        "message": f"Processing as SBIR/Topics file"
                    })
            else:
                opportunities = self._process_generic_csv(csv_path)
                if progress_callback:
                    progress_callback({
                        "status": "processing",
                        "stage": "debug",
                        "message": f"Processing as generic CSV file"
                    })
            
            total_opportunities = len(opportunities)
            
            # Send progress for parsing complete
            if progress_callback:
                progress_callback({
                    "status": "processing",
                    "stage": "parsing_complete",
                    "message": f"Found {total_opportunities} opportunities",
                    "total": total_opportunities
                })
            
            # Debug: log if no opportunities found
            if total_opportunities == 0:
                if progress_callback:
                    progress_callback({
                        "status": "processing",
                        "stage": "warning",
                        "message": "No opportunities found in CSV file"
                    })
                return summary
            
            # Process opportunities with progress tracking
            processed = 0
            batch_data = []
            batch_size = 5  # Smaller batch size for better progress tracking and rate limiting
            
            # Debug first opportunity
            if opportunities and progress_callback:
                first_opp = opportunities[0]
                progress_callback({
                    "status": "processing",
                    "stage": "debug",
                    "message": f"First opportunity: {first_opp.get('title', 'No title')[:50]}"
                })
                progress_callback({
                    "status": "processing",
                    "stage": "debug", 
                    "message": f"Close date: {first_opp.get('close_date', 'No date')}"
                })
            
            for i, opp in enumerate(opportunities):
                # Check if expired
                is_expired, exp_date = self._is_expired(opp)
                
                if is_expired:
                    summary["expired_skipped"] += 1
                    processed += 1
                    summary["unprocessed"].append({
                        "title": opp.get('title', 'Unknown'),
                        "agency": opp.get('agency', 'Unknown'),
                        "reason": f"Expired on {exp_date.strftime('%Y-%m-%d') if exp_date else 'unknown date'}"
                    })
                    if progress_callback and i < 5:  # Log first 5 for debugging
                        progress_callback({
                            "status": "processing",
                            "stage": "debug",
                            "message": f"Skipped expired: {opp.get('title', 'Unknown')[:50]}..."
                        })
                    continue
                
                # Generate unique ID
                opp_id = self._generate_opportunity_id(opp)
                
                # Check if already processed
                if opp_id in self.processed_ids["opportunities"]:
                    existing = self.processed_ids["opportunities"][opp_id]
                    
                    # Log duplicate info for debugging
                    summary["duplicate_skipped"] += 1
                    processed += 1
                    
                    # Build detailed reason with existing opportunity info
                    reason = f"Already processed (duplicate of '{existing.get('title', 'Unknown')[:50]}...' from {existing.get('file', 'unknown file')})"
                    if existing.get('topic_number'):
                        reason += f" [Topic: {existing.get('topic_number')}]"
                    
                    summary["unprocessed"].append({
                        "title": opp.get('title', 'Unknown'),
                        "agency": opp.get('agency', 'Unknown'),
                        "reason": reason
                    })
                    
                    if progress_callback and i < 5:  # Log first 5 for debugging
                        progress_callback({
                            "status": "processing", 
                            "stage": "debug",
                            "message": f"Skipped duplicate: {opp.get('title', 'Unknown')[:50]}... (matches existing: {existing.get('title', 'Unknown')[:50]}...)"
                        })
                    continue
                
                # Enrich with URL content if available
                enriched_opp = self._enrich_opportunity_with_url(opp)
                
                # Add to batch
                batch_data.append({
                    "id": opp_id,
                    "opportunity": enriched_opp,
                    "expiration_date": exp_date
                })
                
                # Process batch when full or at end
                if len(batch_data) >= batch_size or (i == len(opportunities) - 1 and batch_data):
                    if progress_callback:
                        progress_callback({
                            "status": "processing",
                            "stage": "embeddings",
                            "message": f"Generating embeddings ({processed}/{total_opportunities})",
                            "current": processed,
                            "total": total_opportunities
                        })
                    
                    # Generate embeddings and store
                    try:
                        # Extract text for embeddings
                        texts = []
                        for item in batch_data:
                            opp = item["opportunity"]
                            text = f"{opp.get('title', '')} {opp.get('description', '')} {opp.get('agency', '')}"
                            if 'keywords' in opp:
                                text += f" {opp.get('keywords', '')}"
                            texts.append(text)
                        
                        if progress_callback:
                            progress_callback({
                                "status": "processing",
                                "stage": "debug",
                                "message": f"Batch has {len(batch_data)} items, generating embeddings..."
                            })
                        
                        # Get embeddings
                        embeddings = self.embeddings_manager.generate_embeddings_batch(texts)
                        
                        # Add to vector database
                        ids = []
                        metadatas = []
                        documents = []
                        
                        for i, item in enumerate(batch_data):
                            opp = item["opportunity"]
                            ids.append(item["id"])
                            
                            # Prepare metadata (ChromaDB has restrictions on metadata)
                            metadata = {
                                "title": str(opp.get("title", ""))[:100],  # Limit length
                                "agency": str(opp.get("agency", "")),
                                "deadline": str(opp.get("close_date", "")),
                                "url": str(opp.get("url", "")),
                                "program": str(opp.get("program", "")),
                                "timestamp": datetime.now().isoformat()
                            }
                            metadatas.append(metadata)
                            
                            # Store full opportunity as JSON document
                            documents.append(json.dumps(opp))
                        
                        # Batch upsert to ChromaDB
                        self.vector_db.opportunities.upsert(
                            ids=ids,
                            embeddings=embeddings,
                            metadatas=metadatas,
                            documents=documents
                        )
                        
                        # Track processed opportunities
                        for item in batch_data:
                            self.processed_ids["opportunities"][item["id"]] = {
                                "file": filename,
                                "title": item["opportunity"].get("title", "Unknown"),
                                "agency": item["opportunity"].get("agency", "Unknown"),
                                "topic_number": item["opportunity"].get("topic_number", "") or item["opportunity"].get("Topic Number", ""),
                                "processed_at": datetime.now(timezone.utc).isoformat(),
                                "expiration_date": item["expiration_date"].isoformat() if item["expiration_date"] else None
                            }
                            summary["new_opportunities"] += 1
                        
                        processed += len(batch_data)
                        batch_data = []
                        
                        # Send progress update
                        if progress_callback:
                            progress_callback({
                                "status": "processing",
                                "stage": "storing",
                                "message": f"Stored {processed}/{total_opportunities} opportunities",
                                "current": processed,
                                "total": total_opportunities
                            })
                        
                    except Exception as e:
                        import traceback
                        error_detail = f"Batch processing error: {str(e)}\n{traceback.format_exc()}"
                        summary["errors"].append(error_detail)
                        print(f"ERROR in batch processing: {error_detail}")
                        
                        # Track unprocessed opportunities from this batch
                        for item in batch_data:
                            summary["unprocessed"].append({
                                "title": item["opportunity"].get('title', 'Unknown'),
                                "agency": item["opportunity"].get('agency', 'Unknown'),
                                "reason": f"Processing error: {str(e)[:100]}"
                            })
                        
                        if progress_callback:
                            progress_callback({
                                "status": "processing",
                                "stage": "error",
                                "message": f"Error processing batch: {str(e)}",
                                "current": processed,
                                "total": total_opportunities
                            })
                        # Clear batch data on error
                        processed += len(batch_data)
                        batch_data = []
            
            # Save processed IDs
            self._save_processed_ids()
            
            # Move file to ingested folder
            ingested_path = self.ingested_dir / filename
            csv_path.rename(ingested_path)
            
            # Send completion
            if progress_callback:
                progress_callback({
                    "status": "processing",
                    "stage": "complete",
                    "message": f"Successfully processed {filename}",
                    "summary": summary
                })
            
        except Exception as e:
            summary["errors"].append(str(e))
            if progress_callback:
                progress_callback({
                    "status": "error",
                    "error": str(e),
                    "message": f"Failed to process {filename}"
                })
        
        return summary
    
    def _process_nsf_csv(self, csv_path: Path) -> List[Dict[str, Any]]:
        """Process NSF CSV file"""
        opportunities = []
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                opportunity = {
                    "title": row.get("Title", ""),
                    "description": row.get("Synopsis", ""),
                    "agency": "NSF",
                    "program_id": row.get("Program ID", ""),
                    "award_type": row.get("Award Type", ""),
                    "close_date": row.get("Next due date (Y-m-d)", ""),
                    "posted_date": row.get("Posted date (Y-m-d)", ""),
                    "url": row.get("URL", ""),
                    "solicitation_url": row.get("Solicitation URL", ""),
                    "status": row.get("Status", ""),
                    "accepts_anytime": row.get("Proposals accepted anytime", "False") == "True",
                }
                
                opportunities.append(opportunity)
                
        return opportunities
    
    def _process_sbir_csv(self, csv_path: Path) -> List[Dict[str, Any]]:
        """Process SBIR CSV file"""
        opportunities = []
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                opportunity = {
                    "title": row.get("Topic Title", ""),
                    "description": row.get("Topic Description", ""),
                    "agency": row.get("Agency", ""),
                    "branch": row.get("Branch", ""),
                    "program": row.get("Program", "SBIR"),
                    "phase": row.get("Phase", ""),
                    "topic_number": row.get("Topic Number", ""),
                    "close_date": row.get("Close Date", ""),
                    "release_date": row.get("Release Date", ""),
                    "open_date": row.get("Open Date", ""),
                    "url": row.get("Solicitation Agency URL", ""),
                    "sbir_topic_link": row.get("SBIRTopicLink", ""),
                    "status": row.get("Solicitation Status", ""),
                    "year": row.get("Solicitation Year", ""),
                }
                
                opportunities.append(opportunity)
                
        return opportunities
    
    def _process_generic_csv(self, csv_path: Path) -> List[Dict[str, Any]]:
        """Process generic CSV file"""
        opportunities = []
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Map common fields
                opportunity = dict(row)  # Keep all fields
                
                # Ensure key fields exist
                if 'title' not in opportunity:
                    opportunity['title'] = row.get('Title', row.get('Name', ''))
                if 'description' not in opportunity:
                    opportunity['description'] = row.get('Description', row.get('Synopsis', ''))
                if 'agency' not in opportunity:
                    opportunity['agency'] = row.get('Agency', row.get('Organization', ''))
                    
                opportunities.append(opportunity)
                
        return opportunities
    
    def _process_opportunities(self, opportunities: List[Dict[str, Any]], 
                             batch_size: int = 20) -> Dict[str, int]:
        """
        Process opportunities and add to vector database
        
        Returns:
            Summary of processing results
        """
        import time
        
        summary = {"new": 0, "expired": 0, "duplicates": 0}
        batch_data = []
        requests_this_minute = 0
        minute_start = time.time()
        
        for opp in opportunities:
            # Generate unique ID
            opp_id = self._generate_opportunity_id(opp)
            
            # Check if already processed
            if opp_id in self.processed_ids["opportunities"]:
                summary["duplicates"] += 1
                continue
            
            # Enrich opportunity with URL content
            opp = self._enrich_opportunity_with_url(opp)
            
            # Check if expired
            is_expired, exp_date = self._is_expired(opp)
            if is_expired:
                print(f"  ⏰ Skipping expired: {opp['title'][:50]}... (expired: {exp_date})")
                summary["expired"] += 1
                continue
            
            # Generate embedding
            try:
                # Rate limiting: 150 requests per minute
                requests_this_minute += 1
                if requests_this_minute >= 140:  # Leave some buffer
                    elapsed = time.time() - minute_start
                    if elapsed < 60:
                        sleep_time = 60 - elapsed + 1
                        print(f"  ⏸  Rate limit approaching, sleeping for {sleep_time:.1f} seconds...")
                        time.sleep(sleep_time)
                    requests_this_minute = 0
                    minute_start = time.time()
                
                opp_with_embedding = self.embeddings_manager.embed_funding_opportunity(opp)
                
                # Add to batch
                batch_data.append((opp_id, opp, opp_with_embedding['embedding']))
                
                # Track as processed
                self.processed_ids["opportunities"][opp_id] = {
                    "title": opp.get('title', 'Unknown'),
                    "agency": opp.get('agency', 'Unknown'),
                    "topic_number": opp.get('topic_number', '') or opp.get('Topic Number', ''),
                    "processed_date": datetime.now().isoformat(),
                    "expiration_date": exp_date.isoformat() if exp_date else None
                }
                
                summary["new"] += 1
                
                # Process batch if full
                if len(batch_data) >= batch_size:
                    self.vector_db.batch_add_opportunities(batch_data)
                    print(f"  ✓ Added batch of {len(batch_data)} opportunities")
                    batch_data = []
                    
            except Exception as e:
                print(f"  ❌ Error processing opportunity: {e}")
                # If rate limit error, wait and retry
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    print("  ⏸  Rate limit hit, waiting 60 seconds...")
                    time.sleep(60)
                    requests_this_minute = 0
                    minute_start = time.time()
        
        # Process remaining batch
        if batch_data:
            self.vector_db.batch_add_opportunities(batch_data)
            print(f"  ✓ Added final batch of {len(batch_data)} opportunities")
        
        return summary
    
    def remove_expired_opportunities(self) -> int:
        """
        Remove expired opportunities from the database
        
        Returns:
            Number of opportunities removed
        """
        removed_count = 0
        now = datetime.now(timezone.utc)
        
        # Check if we should run cleanup (once per day)
        last_cleanup = self.processed_ids.get("last_cleanup")
        if last_cleanup:
            last_cleanup_date = datetime.fromisoformat(last_cleanup)
            if (now - last_cleanup_date).days < 1:
                return 0
        
        print("\nChecking for expired opportunities...")
        
        # Get all opportunities from database
        # Note: ChromaDB doesn't have a direct way to iterate all items
        # So we'll check our tracked opportunities
        expired_ids = []
        
        for opp_id, opp_info in self.processed_ids["opportunities"].items():
            if opp_info.get("expiration_date"):
                exp_date = datetime.fromisoformat(opp_info["expiration_date"])
                if exp_date < now:
                    expired_ids.append(opp_id)
        
        # Remove expired opportunities
        for opp_id in expired_ids:
            try:
                # ChromaDB doesn't have a direct delete by ID for the current version
                # We'll mark as removed in our tracking
                del self.processed_ids["opportunities"][opp_id]
                removed_count += 1
            except Exception as e:
                print(f"  ❌ Error removing {opp_id}: {e}")
        
        if removed_count > 0:
            print(f"  ✓ Removed {removed_count} expired opportunities")
        
        # Update last cleanup time
        self.processed_ids["last_cleanup"] = now.isoformat()
        
        return removed_count
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the funding opportunities"""
        stats = {
            "total_tracked": len(self.processed_ids["opportunities"]),
            "vector_db_stats": self.vector_db.get_collection_stats(),
            "last_cleanup": self.processed_ids.get("last_cleanup"),
            "csv_files_pending": len(list(self.funding_dir.glob("*.csv"))),
            "csv_files_ingested": len(list(self.ingested_dir.glob("*.csv")))
        }
        
        # Count opportunities by expiration status
        now = datetime.now(timezone.utc)
        active = 0
        expired = 0
        no_date = 0
        
        for opp_info in self.processed_ids["opportunities"].values():
            if opp_info.get("expiration_date"):
                exp_date = datetime.fromisoformat(opp_info["expiration_date"])
                if exp_date >= now:
                    active += 1
                else:
                    expired += 1
            else:
                no_date += 1
        
        stats["opportunities_active"] = active
        stats["opportunities_expired"] = expired
        stats["opportunities_no_date"] = no_date
        
        return stats


if __name__ == "__main__":
    # Test the manager
    manager = FundingOpportunitiesManager()
    stats = manager.get_statistics()
    print(f"Current statistics: {json.dumps(stats, indent=2)}")