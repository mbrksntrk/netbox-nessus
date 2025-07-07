"""
Helper Functions

Common utility functions used across the application.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any


def save_to_json(data: Dict[str, Any], filename: str) -> bool:
    """
    Save data to JSON file
    
    Args:
        data: Data to save
        filename: Output filename
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully saved data to {filename}")
        return True
        
    except IOError as e:
        print(f"Error saving to {filename}: {e}")
        return False


def load_from_json(filename: str) -> Dict[str, Any]:
    """
    Load data from JSON file
    
    Args:
        filename: Input filename
        
    Returns:
        Loaded data dictionary or empty dict if error
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading from {filename}: {e}")
        return {}


def format_timestamp(timestamp: datetime = None) -> str:
    """
    Format timestamp for output
    
    Args:
        timestamp: Datetime object (defaults to current time)
        
    Returns:
        Formatted timestamp string
    """
    if timestamp is None:
        timestamp = datetime.now()
    return timestamp.isoformat()


def create_output_data(data: List[Dict], data_type: str = "data") -> Dict[str, Any]:
    """
    Create standardized output data structure
    
    Args:
        data: List of data items
        data_type: Type of data (e.g., "agents", "devices")
        
    Returns:
        Standardized output dictionary
    """
    return {
        'timestamp': format_timestamp(),
        'data_type': data_type,
        'total_count': len(data),
        'data': data
    }


def create_output_data_dict(data: Dict[str, Any], data_type: str = "data") -> Dict[str, Any]:
    """
    Create standardized output data structure for dictionary data
    
    Args:
        data: Dictionary data
        data_type: Type of data (e.g., "sync_results", "comparison_results")
        
    Returns:
        Standardized output dictionary
    """
    return {
        'timestamp': format_timestamp(),
        'data_type': data_type,
        'data': data
    }


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file system usage
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    
    # Ensure filename is not empty
    if not filename:
        filename = 'output'
    
    return filename


def ensure_file_extension(filename: str, extension: str = '.json') -> str:
    """
    Ensure filename has the specified extension
    
    Args:
        filename: Original filename
        extension: Desired extension (with or without dot)
        
    Returns:
        Filename with proper extension
    """
    if not extension.startswith('.'):
        extension = '.' + extension
    
    if not filename.endswith(extension):
        filename += extension
    
    return filename


def merge_data_sources(*data_sources: List[Dict]) -> List[Dict]:
    """
    Merge multiple data sources into a single list
    
    Args:
        *data_sources: Variable number of data source lists
        
    Returns:
        Merged data list
    """
    merged = []
    for data_source in data_sources:
        if data_source:
            merged.extend(data_source)
    return merged


def filter_data(data: List[Dict], filters: Dict[str, Any]) -> List[Dict]:
    """
    Filter data based on criteria
    
    Args:
        data: List of data dictionaries
        filters: Dictionary of field: value pairs to filter by
        
    Returns:
        Filtered data list
    """
    if not filters:
        return data
    
    filtered = []
    for item in data:
        match = True
        for field, value in filters.items():
            if field not in item or item[field] != value:
                match = False
                break
        if match:
            filtered.append(item)
    
    return filtered 