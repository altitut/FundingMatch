import requests
from datetime import datetime, timedelta
from urllib.parse import urlparse

def validate_url(url):
    """
    Validate if a URL is accessible and returns valid content
    """
    if not url:
        return False
    
    try:
        # Parse URL to check if it's properly formatted
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
        
        # Make a HEAD request to check if URL is accessible
        response = requests.head(url, timeout=5, allow_redirects=True)
        return response.status_code == 200
    except:
        return False

def is_opportunity_current(opportunity):
    """
    Check if an opportunity is currently active (deadline hasn't passed)
    """
    deadline = opportunity.get('deadline') or opportunity.get('closing_date')
    if not deadline:
        return True  # If no deadline specified, assume it's current
    
    try:
        # Try different date formats
        date_formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%B %d, %Y",
            "%d %B %Y"
        ]
        
        deadline_date = None
        for fmt in date_formats:
            try:
                deadline_date = datetime.strptime(deadline, fmt)
                break
            except ValueError:
                continue
        
        if not deadline_date:
            return True  # If can't parse date, assume it's current
        
        # Check if deadline is in the future
        return deadline_date > datetime.now()
    except:
        return True  # If any error, assume it's current

def filter_current_opportunities(opportunities):
    """
    Filter opportunities to only include those that are currently active
    """
    current_opportunities = []
    for opp in opportunities:
        if is_opportunity_current(opp):
            current_opportunities.append(opp)
    return current_opportunities

def get_deadline_status(opportunity):
    """
    Get the status of an opportunity's deadline
    """
    deadline = opportunity.get('deadline') or opportunity.get('closing_date')
    if not deadline:
        return "Rolling deadline"
    
    try:
        date_formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%B %d, %Y",
            "%d %B %Y"
        ]
        
        deadline_date = None
        for fmt in date_formats:
            try:
                deadline_date = datetime.strptime(deadline, fmt)
                break
            except ValueError:
                continue
        
        if not deadline_date:
            return deadline
        
        days_remaining = (deadline_date - datetime.now()).days
        
        if days_remaining < 0:
            return "❌ CLOSED"
        elif days_remaining <= 7:
            return f"⚠️ Due in {days_remaining} days"
        elif days_remaining <= 30:
            return f"🟡 Due in {days_remaining} days"
        else:
            return f"🟢 Due in {days_remaining} days"
    except:
        return deadline

def clean_opportunity_urls(opportunity):
    """
    Clean and validate URLs in an opportunity
    """
    url_fields = ['url', 'link', 'website']
    
    for field in url_fields:
        if field in opportunity:
            url = opportunity[field]
            if not validate_url(url):
                # Remove invalid URL
                opportunity[field] = None
    
    return opportunity 