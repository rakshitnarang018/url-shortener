"""
Utility functions for URL shortener
Using Python built-in modules only
"""
import random
import string
import re
from urllib.parse import urlparse
from typing import Optional


# Base62 character set for short codes
BASE62_CHARS = string.ascii_letters + string.digits  # a-z, A-Z, 0-9


def validate_url(url: str) -> bool:
    """
    Validate if the provided string is a valid URL
    Uses built-in urllib.parse for validation
    """
    if not url or not isinstance(url, str):
        return False
    
    # Basic URL format check
    url = url.strip()
    if not url:
        return False
    
    # Add scheme if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        parsed = urlparse(url)
        # Check if scheme and netloc are present and valid
        if not (parsed.scheme and parsed.netloc):
            return False
        
        # Additional validation: netloc should contain at least one dot for domain
        if '.' not in parsed.netloc:
            return False
            
        # Check for valid characters in netloc
        if not re.match(r'^[a-zA-Z0-9.-]+$', parsed.netloc):
            return False
            
        return True
    except Exception:
        return False


def normalize_url(url: str) -> str:
    """
    Normalize URL by adding scheme if missing
    """
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        return 'https://' + url
    return url


def generate_short_code(length: int = 6) -> str:
    """
    Generate a random short code using Base62 characters
    Uses Python's built-in random module
    """
    return ''.join(random.choices(BASE62_CHARS, k=length))


def generate_unique_short_code(existing_codes: set, length: int = 6, max_attempts: int = 100) -> Optional[str]:
    """
    Generate a unique short code that doesn't exist in the provided set
    Uses collision detection with retry mechanism
    """
    for _ in range(max_attempts):
        code = generate_short_code(length)
        if code not in existing_codes:
            return code
    
    # If we can't find a unique code with current length, try with longer length
    return generate_short_code(length + 1)


class URLValidator:
    """URL validation utility class"""
    
    # Common URL patterns to reject
    BLOCKED_PATTERNS = [
        r'localhost',
        r'127\.0\.0\.1',
        r'0\.0\.0\.0',
        r'file://',
        r'javascript:',
        r'data:',
    ]
    
    @classmethod
    def is_valid_url(cls, url: str) -> tuple[bool, str]:
        """
        Comprehensive URL validation
        Returns (is_valid, error_message)
        """
        if not url or not isinstance(url, str):
            return False, "URL cannot be empty"
        
        url = url.strip()
        if not url:
            return False, "URL cannot be empty"
        
        # Check length
        if len(url) > 2048:  # Reasonable URL length limit
            return False, "URL too long (max 2048 characters)"
        
        # Check for blocked patterns
        for pattern in cls.BLOCKED_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                return False, f"URL contains blocked pattern: {pattern}"
        
        # Validate URL format
        if not validate_url(url):
            return False, "Invalid URL format"
        
        return True, ""


class ShortCodeGenerator:
    """Short code generation utility class"""
    
    def __init__(self, default_length: int = 6):
        self.default_length = default_length
        self._used_codes: set = set()
    
    def generate(self, existing_codes: set = None) -> str:
        """Generate a unique short code"""
        if existing_codes is None:
            existing_codes = self._used_codes
        
        code = generate_unique_short_code(existing_codes, self.default_length)
        if code:
            self._used_codes.add(code)
        return code
    
    def mark_used(self, code: str):
        """Mark a code as used"""
        self._used_codes.add(code)


# Global generator instance
short_code_generator = ShortCodeGenerator()