"""
Configuration Settings

Load and manage configuration from config.json and environment variables.
"""

import os
import json
from typing import Dict, Any


class Settings:
    """Configuration settings manager"""
    
    def __init__(self, config_file: str = 'config/config.json'):
        """
        Initialize settings
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file and environment variables"""
        # Default configuration
        config = {
            'nessus': {
                'base_url': 'https://localhost:8834',
                'access_key': '',
                'secret_key': '',
                'verify_ssl': False
            },
            'netbox': {
                'base_url': 'https://localhost',
                'token': '',
                'verify_ssl': False
            },
            'output': {
                'file': 'nessus_agents.json',
                'format': 'json'
            },
            'logging': {
                'level': 'INFO',
                'file': 'app.log'
            }
        }
        
        # Load from config file if exists
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    config.update(file_config)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load {self.config_file}: {e}")
        
        # Override with environment variables
        config = self._override_with_env(config)
        
        return config
    
    def _override_with_env(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Override configuration with environment variables"""
        # Nessus settings
        if os.getenv('NESSUS_URL'):
            config['nessus']['base_url'] = os.getenv('NESSUS_URL')
        if os.getenv('NESSUS_ACCESS_KEY'):
            config['nessus']['access_key'] = os.getenv('NESSUS_ACCESS_KEY')
        if os.getenv('NESSUS_SECRET_KEY'):
            config['nessus']['secret_key'] = os.getenv('NESSUS_SECRET_KEY')
        if os.getenv('NESSUS_VERIFY_SSL'):
            config['nessus']['verify_ssl'] = os.getenv('NESSUS_VERIFY_SSL').lower() == 'true'
        
        # Netbox settings
        if os.getenv('NETBOX_URL'):
            config['netbox']['base_url'] = os.getenv('NETBOX_URL')
        if os.getenv('NETBOX_TOKEN'):
            config['netbox']['token'] = os.getenv('NETBOX_TOKEN')
        if os.getenv('NETBOX_VERIFY_SSL'):
            config['netbox']['verify_ssl'] = os.getenv('NETBOX_VERIFY_SSL').lower() == 'true'
        
        # Output settings
        if os.getenv('OUTPUT_FILE'):
            config['output']['file'] = os.getenv('OUTPUT_FILE')
        
        return config
    
    def get_nessus_config(self) -> Dict[str, Any]:
        """Get Nessus configuration"""
        return self.config.get('nessus', {})
    
    def get_netbox_config(self) -> Dict[str, Any]:
        """Get Netbox configuration"""
        return self.config.get('netbox', {})
    
    def get_output_config(self) -> Dict[str, Any]:
        """Get output configuration"""
        return self.config.get('output', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return self.config.get('logging', {})
    
    def validate_nessus_config(self) -> bool:
        """Validate Nessus configuration"""
        nessus_config = self.get_nessus_config()
        return bool(
            nessus_config.get('base_url') and
            nessus_config.get('access_key') and
            nessus_config.get('secret_key')
        )
    
    def validate_netbox_config(self) -> bool:
        """Validate Netbox configuration"""
        netbox_config = self.get_netbox_config()
        return bool(
            netbox_config.get('base_url') and
            netbox_config.get('token')
        )
    
    def save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Error saving configuration: {e}")
            return False


# Global settings instance
settings = Settings() 