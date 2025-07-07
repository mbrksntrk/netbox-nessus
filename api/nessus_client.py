"""
Nessus API Client

Client for interacting with the Nessus vulnerability scanner API.
"""

from typing import Dict, List, Optional
from .base_client import BaseAPIClient


class NessusClient(BaseAPIClient):
    """Nessus API client for fetching agent data"""
    
    def __init__(self, base_url: str, access_key: str, secret_key: str, verify_ssl: bool = False):
        """
        Initialize Nessus API client
        
        Args:
            base_url: Nessus server URL (e.g., https://nessus-server:8834)
            access_key: API access key
            secret_key: API secret key
            verify_ssl: Whether to verify SSL certificates
        """
        super().__init__(base_url, verify_ssl)
        
        # Set Nessus-specific headers
        self.session.headers.update({
            'X-ApiKeys': f'accessKey={access_key}; secretKey={secret_key}'
        })
    
    def test_connection(self) -> bool:
        """Test connection to Nessus API"""
        try:
            response = self.get('/server/properties')
            return response is not None
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    def get_agents(self) -> List[Dict]:
        """
        Fetch all agents from Nessus
        
        Returns:
            List of agent dictionaries
        """
        response = self.get('/agents')
        if response:
            return response.get('agents', [])
        return []
    
    def get_agent_details(self, agent_id: int) -> Optional[Dict]:
        """
        Fetch detailed information for a specific agent
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent details dictionary or None if error
        """
        return self.get(f'/agents/{agent_id}')
    
    def get_scans(self) -> List[Dict]:
        """
        Fetch all scans from Nessus
        
        Returns:
            List of scan dictionaries
        """
        response = self.get('/scans')
        if response:
            return response.get('scans', [])
        return []
    
    def get_scan_details(self, scan_id: int) -> Optional[Dict]:
        """
        Fetch detailed information for a specific scan
        
        Args:
            scan_id: Scan ID
            
        Returns:
            Scan details dictionary or None if error
        """
        return self.get(f'/scans/{scan_id}')
    
    def get_scan_results(self, scan_id: int) -> Optional[Dict]:
        """
        Fetch results for a specific scan
        
        Args:
            scan_id: Scan ID
            
        Returns:
            Scan results dictionary or None if error
        """
        return self.get(f'/scans/{scan_id}/results')
    
    def get_agents_by_ip(self, ip_address: str) -> List[Dict]:
        """
        Fetch agents by IP address
        
        Args:
            ip_address: IP address to search for
            
        Returns:
            List of agent dictionaries with matching IP
        """
        # Get all agents first
        all_agents = self.get_agents()
        matching_agents = []
        
        for agent in all_agents:
            # Check if agent has IP information
            agent_ip = agent.get('distro', '')  # Some agents store IP in distro field
            if ip_address in agent_ip:
                matching_agents.append(agent)
                continue
            
            # Check other possible IP fields
            if 'ip' in agent and ip_address in str(agent['ip']):
                matching_agents.append(agent)
                continue
            
            # Check in agent details if available
            agent_id = agent.get('id')
            if agent_id:
                details = self.get_agent_details(agent_id)
                if details:
                    # Check various IP fields in details
                    detail_ip = details.get('distro', '') or details.get('ip', '') or details.get('primary_ip', '')
                    if ip_address in str(detail_ip):
                        matching_agents.append(details)
                    else:
                        matching_agents.append(agent)
        
        return matching_agents 