"""
Base API Client

Common functionality for all API clients including HTTP operations,
error handling, and session management.
"""

import requests
import json
import urllib3
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class BaseAPIClient(ABC):
    """Base class for API clients with common functionality"""
    
    def __init__(self, base_url: str, verify_ssl: bool = False, timeout: int = 30):
        """
        Initialize base API client
        
        Args:
            base_url: API server URL
            verify_ssl: Whether to verify SSL certificates
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """
        Make HTTP request to API
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            **kwargs: Additional request parameters
            
        Returns:
            Response data as dictionary or None if error
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                verify=self.verify_ssl,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            
            # Handle empty responses
            if response.status_code == 204:  # No Content
                return None
                
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self._handle_request_error(e, method, endpoint)
            return None
        except json.JSONDecodeError as e:
            self._handle_json_error(e, method, endpoint)
            return None
    
    def get(self, endpoint: str, **kwargs) -> Optional[Dict]:
        """Make GET request"""
        return self._make_request('GET', endpoint, **kwargs)
    
    def post(self, endpoint: str, data: Optional[Dict] = None, **kwargs) -> Optional[Dict]:
        """Make POST request"""
        if data:
            kwargs['json'] = data
        return self._make_request('POST', endpoint, **kwargs)
    
    def put(self, endpoint: str, data: Optional[Dict] = None, **kwargs) -> Optional[Dict]:
        """Make PUT request"""
        if data:
            kwargs['json'] = data
        return self._make_request('PUT', endpoint, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> Optional[Dict]:
        """Make DELETE request"""
        return self._make_request('DELETE', endpoint, **kwargs)
    
    def _handle_request_error(self, error: Exception, method: str, endpoint: str):
        """Handle HTTP request errors"""
        print(f"Request error ({method} {endpoint}): {error}")
    
    def _handle_json_error(self, error: Exception, method: str, endpoint: str):
        """Handle JSON parsing errors"""
        print(f"JSON parsing error ({method} {endpoint}): {error}")
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test connection to API - must be implemented by subclasses"""
        pass
    
    def close(self):
        """Close the session"""
        if self.session:
            self.session.close() 