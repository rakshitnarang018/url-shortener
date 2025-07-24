# TODO: Implement your data models here
# Consider what data structures you'll need for:
# - Storing URL mappings
# - Tracking click counts
# - Managing URL metadata

"""
URL Shortener Models using Python built-in data structures
Thread-safe in-memory storage implementation
"""
import threading
import time
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class URLData:
    """Data class representing a shortened URL record"""
    original_url: str
    short_code: str
    created_at: float
    click_count: int = 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'original_url': self.original_url,
            'short_code': self.short_code,
            'created_at': self.created_at,
            'click_count': self.click_count
        }


class URLStore:
    """Thread-safe in-memory storage for URL mappings"""
    
    def __init__(self):
        # Primary storage: short_code -> URLData
        self._urls: Dict[str, URLData] = {}
        # Reverse lookup: original_url -> short_code (for duplicate detection)
        self._reverse_lookup: Dict[str, str] = {}
        # Thread safety lock
        self._lock = threading.RLock()
    
    def store_url(self, original_url: str, short_code: str) -> URLData:
        """Store a new URL mapping"""
        with self._lock:
            url_data = URLData(
                original_url=original_url,
                short_code=short_code,
                created_at=time.time()
            )
            self._urls[short_code] = url_data
            self._reverse_lookup[original_url] = short_code
            return url_data
    
    def get_by_short_code(self, short_code: str) -> Optional[URLData]:
        """Retrieve URL data by short code"""
        with self._lock:
            return self._urls.get(short_code)
    
    def get_by_original_url(self, original_url: str) -> Optional[str]:
        """Get existing short code for original URL (duplicate detection)"""
        with self._lock:
            return self._reverse_lookup.get(original_url)
    
    def increment_clicks(self, short_code: str) -> bool:
        """Increment click count for a short code"""
        with self._lock:
            if short_code in self._urls:
                self._urls[short_code].click_count += 1
                return True
            return False
    
    def exists(self, short_code: str) -> bool:
        """Check if short code exists"""
        with self._lock:
            return short_code in self._urls
    
    def get_stats(self) -> dict:
        """Get basic statistics"""
        with self._lock:
            return {
                'total_urls': len(self._urls),
                'total_clicks': sum(url_data.click_count for url_data in self._urls.values())
            }


# Global instance - thread-safe singleton
url_store = URLStore()