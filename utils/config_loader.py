import os
import json

def get_config_value(key, env_key=None, config_path='config.json', section=None):
    """
    Get configuration value from environment variable or config.json (supports nested section).
    Args:
        key: The key to look for (e.g. 'base_url')
        env_key: The environment variable name (defaults to key.upper())
        config_path: Path to config.json
        section: Optional section (e.g. 'netbox')
    Returns:
        The value if found, else None
    """
    if env_key is None:
        env_key = key.upper()
    value = os.environ.get(env_key)
    if value:
        return value
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
            if section and section in config and key in config[section]:
                return config[section][key]
            if key in config:
                return config[key]
    return None 