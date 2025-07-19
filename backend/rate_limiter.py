"""
Rate limiter for API calls
"""

import time
from typing import Optional, Callable, Any
import threading
from datetime import datetime, timedelta


class RateLimiter:
    """Thread-safe rate limiter with exponential backoff"""
    
    def __init__(self, calls_per_minute: int = 10):
        """
        Initialize rate limiter
        
        Args:
            calls_per_minute: Maximum calls allowed per minute
        """
        self.calls_per_minute = calls_per_minute
        self.min_interval = 60.0 / calls_per_minute  # seconds between calls
        self.last_call_time = 0
        self.lock = threading.Lock()
        self.backoff_until = 0
        self.backoff_seconds = 1  # Start with 1 second backoff
        
    def wait_if_needed(self) -> None:
        """Wait if necessary to respect rate limit"""
        with self.lock:
            current_time = time.time()
            
            # Check if we're in backoff period
            if current_time < self.backoff_until:
                wait_time = self.backoff_until - current_time
                print(f"  ⏱️  Rate limit backoff: waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)
                current_time = time.time()
            
            # Check normal rate limit
            time_since_last_call = current_time - self.last_call_time
            if time_since_last_call < self.min_interval:
                wait_time = self.min_interval - time_since_last_call
                time.sleep(wait_time)
                current_time = time.time()
            
            self.last_call_time = current_time
    
    def handle_rate_limit_error(self, retry_after: Optional[float] = None) -> None:
        """
        Handle rate limit error with exponential backoff
        
        Args:
            retry_after: Seconds to wait (from API response)
        """
        with self.lock:
            if retry_after:
                self.backoff_until = time.time() + retry_after
                print(f"  ⚠️  Rate limit hit. Backing off for {retry_after} seconds")
            else:
                # Exponential backoff
                self.backoff_until = time.time() + self.backoff_seconds
                print(f"  ⚠️  Rate limit hit. Backing off for {self.backoff_seconds} seconds")
                self.backoff_seconds = min(self.backoff_seconds * 2, 60)  # Max 60 seconds
    
    def reset_backoff(self) -> None:
        """Reset backoff after successful call"""
        with self.lock:
            self.backoff_seconds = 1
    
    def execute_with_retry(self, func: Callable, max_retries: int = 3, *args, **kwargs) -> Any:
        """
        Execute function with rate limiting and retry logic
        
        Args:
            func: Function to execute
            max_retries: Maximum number of retries
            *args, **kwargs: Arguments to pass to function
            
        Returns:
            Function result or None if all retries failed
        """
        for attempt in range(max_retries):
            try:
                # Wait if needed before making call
                self.wait_if_needed()
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Reset backoff on success
                self.reset_backoff()
                
                return result
                
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    # Extract retry delay if provided
                    retry_after = None
                    if "retryDelay" in error_str:
                        try:
                            # Extract seconds from error message
                            import re
                            match = re.search(r"'retryDelay':\s*'(\d+)s'", error_str)
                            if match:
                                retry_after = int(match.group(1))
                        except:
                            pass
                    
                    self.handle_rate_limit_error(retry_after)
                    
                    if attempt < max_retries - 1:
                        continue
                    else:
                        print(f"  ❌ Max retries exceeded for {func.__name__}")
                        return None
                else:
                    # Non-rate-limit error, raise it
                    raise
        
        return None


# Global rate limiter for Gemini API
gemini_rate_limiter = RateLimiter(calls_per_minute=10)