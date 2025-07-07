"""
Nessus Service

Business logic layer for Nessus operations.
"""

import json
import os
from typing import Dict, List, Optional
from api.nessus_client import NessusClient
from utils.helpers import create_output_data, save_to_json
from utils.html_reporter import HTMLReporter
from tqdm import tqdm


class NessusService:
    """Service layer for Nessus operations"""
    
    def __init__(self, client: NessusClient):
        """
        Initialize Nessus service
        
        Args:
            client: Nessus API client instance
        """
        self.client = client
        self.html_reporter = HTMLReporter()
    
    def test_connection(self) -> bool:
        """Test connection to Nessus"""
        return self.client.test_connection()
    
    def fetch_all_agents(self, include_details: bool = True) -> List[Dict]:
        """
        Fetch all agents with optional detailed information
        
        Args:
            include_details: Whether to fetch detailed info for each agent
            
        Returns:
            List of agent dictionaries
        """
        print("Fetching agents from Nessus...")
        agents = self.client.get_agents()
        
        if not agents:
            print("No agents found")
            return []
        
        print(f"Found {len(agents)} agents")
        
        # Otomatik kaydet
        output_data = create_output_data(agents, "nessus_agents")
        save_to_json(output_data, "output/nessus_agents.json")
        
        # Generate HTML report
        html_file = self.html_reporter.generate_fetch_report(output_data, "agents")
        print(f"✓ HTML report saved to {html_file}")
        
        if include_details:
            detailed_agents = []
            for agent in tqdm(agents, desc="Fetching agent details"):
                agent_id = agent.get('id')
                if agent_id:
                    details = self.client.get_agent_details(agent_id)
                    if details:
                        detailed_agents.append(details)
                    else:
                        detailed_agents.append(agent)  # Use basic info if details failed
                else:
                    detailed_agents.append(agent)
            # Detaylı veriyi de kaydet
            self.save_agents_to_file(detailed_agents, "output/nessus_agents.json")
            return detailed_agents
        
        return agents
    
    def fetch_agents_by_status(self, status: str) -> List[Dict]:
        """
        Fetch agents filtered by status
        
        Args:
            status: Agent status (online, offline, etc.)
            
        Returns:
            List of filtered agent dictionaries
        """
        agents = self.fetch_all_agents(include_details=False)
        return [agent for agent in agents if agent.get('status') == status]
    
    def fetch_agents_by_platform(self, platform: str) -> List[Dict]:
        """
        Fetch agents filtered by platform
        
        Args:
            platform: Agent platform (Windows, Linux, etc.)
            
        Returns:
            List of filtered agent dictionaries
        """
        agents = self.fetch_all_agents(include_details=True)
        return [agent for agent in agents if agent.get('platform') == platform]
    
    def save_agents_to_file(self, agents: List[Dict], filename: str) -> bool:
        """
        Save agents data to file
        
        Args:
            agents: List of agent dictionaries
            filename: Output filename
            
        Returns:
            True if successful, False otherwise
        """
        output_data = create_output_data(agents, "agents")
        return save_to_json(output_data, filename)
    
    def get_agent_statistics(self, agents: List[Dict]) -> Dict:
        """
        Generate statistics from agents data
        
        Args:
            agents: List of agent dictionaries
            
        Returns:
            Statistics dictionary
        """
        if not agents:
            return {}
        
        stats = {
            'total_agents': len(agents),
            'by_status': {},
            'by_platform': {},
            'by_version': {}
        }
        
        for agent in agents:
            # Status statistics
            status = agent.get('status', 'unknown')
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
            
            # Platform statistics
            platform = agent.get('platform', 'unknown')
            stats['by_platform'][platform] = stats['by_platform'].get(platform, 0) + 1
            
            # Version statistics
            version = agent.get('version', 'unknown')
            stats['by_version'][version] = stats['by_version'].get(version, 0) + 1
        
        return stats
    
    def fetch_all_scans(self) -> List[Dict]:
        """
        Fetch all scans from Nessus
        
        Returns:
            List of scan dictionaries
        """
        print("Fetching scans from Nessus...")
        scans = self.client.get_scans()
        print(f"Found {len(scans)} scans")
        return scans
    
    def fetch_scan_results(self, scan_id: int) -> Optional[Dict]:
        """
        Fetch results for a specific scan
        
        Args:
            scan_id: Scan ID
            
        Returns:
            Scan results dictionary or None if error
        """
        print(f"Fetching results for scan {scan_id}...")
        return self.client.get_scan_results(scan_id)
    
    def search_agents_by_ip(self, ip_address: str) -> List[Dict]:
        """
        Search agents by IP address
        
        Args:
            ip_address: IP address to search for
            
        Returns:
            List of matching agent dictionaries
        """
        print(f"Searching for agents with IP: {ip_address}")
        agents = self.client.get_agents_by_ip(ip_address)
        print(f"Found {len(agents)} agents with IP {ip_address}")
        return agents 