"""
Comparison Service

Service for comparing Nessus agents with Netbox devices and virtual machines.
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from services.nessus_service import NessusService
from services.netbox_service import NetboxService
from utils.helpers import save_to_json, create_output_data, create_output_data_dict
from utils.html_reporter import HTMLReporter
from tqdm import tqdm


class ComparisonService:
    """Service for comparing data between Nessus and Netbox"""
    
    def __init__(self, nessus_service: NessusService, netbox_service: NetboxService):
        """
        Initialize comparison service
        
        Args:
            nessus_service: Nessus service instance
            netbox_service: Netbox service instance
        """
        self.nessus_service = nessus_service
        self.netbox_service = netbox_service
        self.html_reporter = HTMLReporter()
    
    def _extract_hostname(self, name: str) -> str:
        """
        Extract hostname from name (everything before the first dot)
        
        Args:
            name: Full name that might contain domain
            
        Returns:
            Hostname part (lowercase)
        """
        if not name:
            return ""
        # Split by dot and take the first part, then lowercase
        return name.split('.')[0].lower()
    
    def _get_primary_ip(self, item: Dict) -> Optional[str]:
        """
        Extract primary IP from Netbox item
        
        Args:
            item: Netbox device or VM dictionary
            
        Returns:
            Primary IP address or None
        """
        # Try different possible IP fields
        primary_ip = item.get('primary_ip')
        if primary_ip and isinstance(primary_ip, dict):
            return primary_ip.get('address', '').split('/')[0]  # Remove CIDR notation
        
        primary_ip4 = item.get('primary_ip4')
        if primary_ip4 and isinstance(primary_ip4, dict):
            return primary_ip4.get('address', '').split('/')[0]
        
        return None
    
    def test_connection(self) -> bool:
        """Test connections to both services"""
        try:
            # Test both underlying services
            nessus_ok = self.nessus_service.test_connection()
            netbox_ok = self.netbox_service.test_connection()
            return nessus_ok and netbox_ok
        except Exception as e:
            print(f"Comparison service connection test failed: {e}")
            return False
    
    def _load_cached_data(self, filename: str) -> Optional[List[Dict]]:
        """
        Load cached data from JSON file
        
        Args:
            filename: Path to JSON file
            
        Returns:
            List of data items or None if file doesn't exist
        """
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Extract the actual data from the wrapper structure
                    if isinstance(data, dict) and 'data' in data:
                        raw_data = data['data']
                        if isinstance(raw_data, list):
                            # Filtrele: sadece dict olan ve None olmayan elemanları al
                            filtered_data = [x for x in raw_data if x is not None and isinstance(x, dict)]
                            return filtered_data
                        else:
                            return None
                    elif isinstance(data, list):
                        # Filtrele: sadece dict olan ve None olmayan elemanları al
                        filtered_data = [x for x in data if x is not None and isinstance(x, dict)]
                        return filtered_data
                    else:
                        return None
            return None
        except Exception as e:
            print(f"Warning: Could not load cached data from {filename}: {e}")
            return None
    
    def _get_agents_data(self) -> List[Dict]:
        """
        Get agents data, preferring cached data if available
        
        Returns:
            List of agent data
        """
        # Try to load from cache first - sadece nessus_agents.json'u dene
        cached_agents = self._load_cached_data("output/nessus_agents.json")
        if cached_agents:
            print("✓ Using cached Nessus agents data from output/nessus_agents.json")
            return cached_agents
        
        # Fall back to fresh API call
        print("No cached agents data found, fetching from Nessus...")
        agents = self.nessus_service.fetch_all_agents(include_details=True)
        return [x for x in agents if isinstance(x, dict)]
    
    def _get_devices_data(self) -> List[Dict]:
        """
        Get devices data, preferring cached data if available
        
        Returns:
            List of device data
        """
        # Try to load from cache first
        cached_devices = self._load_cached_data("output/netbox_devices.json")
        if cached_devices:
            print("✓ Using cached Netbox devices data")
            return cached_devices
        
        # Fall back to fresh API call
        print("No cached devices data found, fetching from Netbox...")
        devices = self.netbox_service.fetch_all_devices()
        return [x for x in devices if isinstance(x, dict)]
    
    def _get_vms_data(self) -> List[Dict]:
        """
        Get VMs data, preferring cached data if available
        
        Returns:
            List of VM data
        """
        # Try to load from cache first
        cached_vms = self._load_cached_data("output/netbox_vms.json")
        if cached_vms:
            print("✓ Using cached Netbox VMs data")
            return cached_vms
        
        # Fall back to fresh API call
        print("No cached VMs data found, fetching from Netbox...")
        vms = self.netbox_service.fetch_all_virtual_machines()
        return [x for x in vms if isinstance(x, dict)]
    
    def compare_agents_with_devices(self) -> Dict:
        """
        Compare Nessus agents with Netbox devices
        
        Returns:
            Comparison results dictionary
        """
        print("=== Comparing Nessus Agents with Netbox Devices ===")
        
        # Get data from cache or API
        agents = self._get_agents_data()
        devices = self._get_devices_data()
        
        comparison = {
            'summary': {
                'total_agents': len(agents),
                'total_devices': len(devices),
                'matched': 0,
                'unmatched_agents': 0,
                'unmatched_devices': 0
            },
            'matched_items': [],
            'unmatched_agents': [],
            'unmatched_devices': [],
            'details': {}
        }
        
        # Create lookup dictionaries by hostname
        agent_names = {self._extract_hostname(agent.get('name', '')): agent for agent in agents if agent and isinstance(agent, dict) and agent.get('name')}
        device_names = {self._extract_hostname(device.get('name', '')): device for device in devices if device and isinstance(device, dict) and device.get('name')}
        
        # Create IP-based lookup for devices
        device_ips = {}
        for device in devices:
            if device and isinstance(device, dict):
                ip = self._get_primary_ip(device)
                if ip:
                    device_ips[ip] = device
        
        # Find matches by hostname first
        matched_names = set(agent_names.keys()) & set(device_names.keys())
        matched_agents = set()
        matched_devices = set()
        
        for name in tqdm(matched_names, desc="Matching agents/devices by hostname"):
            agent = agent_names[name]
            device = device_names[name]
            
            match_details = {
                'name': name,
                'match_type': 'hostname',
                'nessus_agent': {
                    'id': agent.get('id'),
                    'status': agent.get('status'),
                    'platform': agent.get('platform'),
                    'version': agent.get('version'),
                    'last_connect': agent.get('last_connect'),
                    'ip': agent.get('ip')
                },
                'netbox_device': {
                    'id': device.get('id'),
                    'status': device.get('status', {}).get('value') if device.get('status') else None,
                    'site': device.get('site', {}).get('name') if device.get('site') else None,
                    'platform': device.get('platform', {}).get('name') if device.get('platform') else None,
                    'device_type': device.get('device_type', {}).get('model') if device.get('device_type') else None,
                    'primary_ip': self._get_primary_ip(device),
                    'all_ips': self._get_all_ips(device)
                },
                'status_match': agent.get('status') == 'online' and device.get('status', {}).get('value') == 'active',
                'platform_match': agent.get('platform') == device.get('platform', {}).get('name') if device.get('platform') else False
            }
            
            comparison['matched_items'].append(match_details)
            comparison['summary']['matched'] += 1
            matched_agents.add(agent.get('id'))
            matched_devices.add(device.get('id'))
        
        # Find IP-based matches for remaining agents
        for agent in agents:
            if agent and isinstance(agent, dict) and agent.get('id') not in matched_agents:
                agent_ip = agent.get('ip')  # Nessus agent IP field
                if agent_ip and agent_ip in device_ips:
                    device = device_ips[agent_ip]
                    if device.get('id') not in matched_devices:  # Device not already matched
                        name = self._extract_hostname(agent.get('name', ''))
                        
                        match_details = {
                            'name': name,
                            'match_type': 'ip',
                            'nessus_agent': {
                                'id': agent.get('id'),
                                'status': agent.get('status'),
                                'platform': agent.get('platform'),
                                'version': agent.get('version'),
                                'last_connect': agent.get('last_connect'),
                                'ip': agent.get('ip')
                            },
                            'netbox_device': {
                                'id': device.get('id'),
                                'status': device.get('status', {}).get('value') if device.get('status') else None,
                                'site': device.get('site', {}).get('name') if device.get('site') else None,
                                'platform': device.get('platform', {}).get('name') if device.get('platform') else None,
                                'device_type': device.get('device_type', {}).get('model') if device.get('device_type') else None,
                                'primary_ip': self._get_primary_ip(device),
                                'all_ips': self._get_all_ips(device)
                            },
                            'status_match': agent.get('status') == 'online' and device.get('status', {}).get('value') == 'active',
                            'platform_match': agent.get('platform') == device.get('platform', {}).get('name') if device.get('platform') else False
                        }
                        
                        comparison['matched_items'].append(match_details)
                        comparison['summary']['matched'] += 1
                        matched_agents.add(agent.get('id'))
                        matched_devices.add(device.get('id'))
        
        # Find unmatched agents (not matched by hostname or IP)
        for agent in agents:
            if agent and isinstance(agent, dict) and agent.get('id') not in matched_agents:
                name = self._extract_hostname(agent.get('name', ''))
                comparison['unmatched_agents'].append({
                    'name': name,
                    'id': agent.get('id'),
                    'status': agent.get('status'),
                    'platform': agent.get('platform'),
                    'version': agent.get('version'),
                    'ip': agent.get('ip')
                })
                comparison['summary']['unmatched_agents'] += 1
        
        # Find unmatched devices (not matched by hostname or IP)
        for device in devices:
            if device and isinstance(device, dict) and device.get('id') not in matched_devices:
                name = self._extract_hostname(device.get('name', ''))
                comparison['unmatched_devices'].append({
                    'name': name,
                    'id': device.get('id'),
                    'status': device.get('status', {}).get('value') if device.get('status') else None,
                    'site': device.get('site', {}).get('name') if device.get('site') else None,
                    'platform': device.get('platform', {}).get('name') if device.get('platform') else None,
                    'primary_ip': self._get_primary_ip(device)
                })
                comparison['summary']['unmatched_devices'] += 1
        
        # Generate detailed statistics
        comparison['details'] = self._generate_comparison_details(comparison)
        
        # Otomatik kaydet
        self.save_comparison_results(comparison, "output/comparison_devices_results.json")
        
        # Generate HTML report
        html_file = self.html_reporter.generate_comparison_report(comparison, "devices")
        print(f"✓ HTML report saved to {html_file}")
        
        return comparison
    
    def compare_agents_with_vms(self) -> Dict:
        """
        Compare Nessus agents with Netbox virtual machines
        
        Returns:
            Comparison results dictionary
        """
        print("=== Comparing Nessus Agents with Netbox Virtual Machines ===")
        
        # Get data from cache or API
        agents = self._get_agents_data()
        vms = self._get_vms_data()
        
        comparison = {
            'summary': {
                'total_agents': len(agents),
                'total_vms': len(vms),
                'matched': 0,
                'unmatched_agents': 0,
                'unmatched_vms': 0
            },
            'matched_items': [],
            'unmatched_agents': [],
            'unmatched_vms': [],
            'details': {}
        }
        
        # Create lookup dictionaries by hostname
        agent_names = {self._extract_hostname(agent.get('name', '')): agent for agent in agents if agent and isinstance(agent, dict) and agent.get('name')}
        vm_names = {self._extract_hostname(vm.get('name', '')): vm for vm in vms if vm and isinstance(vm, dict) and vm.get('name')}
        
        # Create IP-based lookup for VMs
        vm_ips = {}
        for vm in vms:
            if vm and isinstance(vm, dict):
                ip = self._get_primary_ip(vm)
                if ip:
                    vm_ips[ip] = vm
        
        # Find matches by hostname first
        matched_names = set(agent_names.keys()) & set(vm_names.keys())
        matched_agents = set()
        matched_vms = set()
        
        for name in tqdm(matched_names, desc="Matching agents/VMs by hostname"):
            agent = agent_names[name]
            vm = vm_names[name]
            
            match_details = {
                'name': name,
                'match_type': 'hostname',
                'nessus_agent': {
                    'id': agent.get('id'),
                    'status': agent.get('status'),
                    'platform': agent.get('platform'),
                    'version': agent.get('version'),
                    'last_connect': agent.get('last_connect'),
                    'ip': agent.get('ip')
                },
                'netbox_vm': {
                    'id': vm.get('id'),
                    'status': vm.get('status', {}).get('value') if vm.get('status') else None,
                    'cluster': vm.get('cluster', {}).get('name') if vm.get('cluster') else None,
                    'platform': vm.get('platform', {}).get('name') if vm.get('platform') else None,
                    'site': vm.get('site', {}).get('name') if vm.get('site') else None,
                    'vcpus': vm.get('vcpus'),
                    'memory': vm.get('memory'),
                    'disk': vm.get('disk'),
                    'primary_ip': self._get_primary_ip(vm),
                    'all_ips': self._get_all_ips(vm)
                },
                'status_match': agent.get('status') == 'online' and vm.get('status', {}).get('value') == 'active',
                'platform_match': agent.get('platform') == vm.get('platform', {}).get('name') if vm.get('platform') else False
            }
            
            comparison['matched_items'].append(match_details)
            comparison['summary']['matched'] += 1
            matched_agents.add(agent.get('id'))
            matched_vms.add(vm.get('id'))
        
        # Find IP-based matches for remaining agents
        for agent in agents:
            if agent and isinstance(agent, dict) and agent.get('id') not in matched_agents:
                agent_ip = agent.get('ip')  # Nessus agent IP field
                if agent_ip and agent_ip in vm_ips:
                    vm = vm_ips[agent_ip]
                    if vm.get('id') not in matched_vms:  # VM not already matched
                        name = self._extract_hostname(agent.get('name', ''))
                        
                        match_details = {
                            'name': name,
                            'match_type': 'ip',
                            'nessus_agent': {
                                'id': agent.get('id'),
                                'status': agent.get('status'),
                                'platform': agent.get('platform'),
                                'version': agent.get('version'),
                                'last_connect': agent.get('last_connect'),
                                'ip': agent.get('ip')
                            },
                            'netbox_vm': {
                                'id': vm.get('id'),
                                'status': vm.get('status', {}).get('value') if vm.get('status') else None,
                                'cluster': vm.get('cluster', {}).get('name') if vm.get('cluster') else None,
                                'platform': vm.get('platform', {}).get('name') if vm.get('platform') else None,
                                'site': vm.get('site', {}).get('name') if vm.get('site') else None,
                                'vcpus': vm.get('vcpus'),
                                'memory': vm.get('memory'),
                                'disk': vm.get('disk'),
                                'primary_ip': self._get_primary_ip(vm),
                                'all_ips': self._get_all_ips(vm)
                            },
                            'status_match': agent.get('status') == 'online' and vm.get('status', {}).get('value') == 'active',
                            'platform_match': agent.get('platform') == vm.get('platform', {}).get('name') if vm.get('platform') else False
                        }
                        
                        comparison['matched_items'].append(match_details)
                        comparison['summary']['matched'] += 1
                        matched_agents.add(agent.get('id'))
                        matched_vms.add(vm.get('id'))
        
        # Find unmatched agents (not matched by hostname or IP)
        for agent in agents:
            if agent and isinstance(agent, dict) and agent.get('id') not in matched_agents:
                name = self._extract_hostname(agent.get('name', ''))
                comparison['unmatched_agents'].append({
                    'name': name,
                    'id': agent.get('id'),
                    'status': agent.get('status'),
                    'platform': agent.get('platform'),
                    'version': agent.get('version'),
                    'ip': agent.get('ip')
                })
                comparison['summary']['unmatched_agents'] += 1
        
        # Find unmatched VMs (not matched by hostname or IP)
        for vm in vms:
            if vm and isinstance(vm, dict) and vm.get('id') not in matched_vms:
                name = self._extract_hostname(vm.get('name', ''))
                comparison['unmatched_vms'].append({
                    'name': name,
                    'id': vm.get('id'),
                    'status': vm.get('status', {}).get('value') if vm.get('status') else None,
                    'cluster': vm.get('cluster', {}).get('name') if vm.get('cluster') else None,
                    'platform': vm.get('platform', {}).get('name') if vm.get('platform') else None,
                    'site': vm.get('site', {}).get('name') if vm.get('site') else None,
                    'primary_ip': self._get_primary_ip(vm)
                })
                comparison['summary']['unmatched_vms'] += 1
        
        # Generate detailed statistics
        comparison['details'] = self._generate_comparison_details(comparison)
        
        # Otomatik kaydet
        self.save_comparison_results(comparison, "output/comparison_vms_results.json")
        
        # Generate HTML report
        html_file = self.html_reporter.generate_comparison_report(comparison, "vms")
        print(f"✓ HTML report saved to {html_file}")
        
        return comparison
    
    def _generate_comparison_details(self, comparison: Dict) -> Dict:
        """
        Generate detailed statistics for comparison
        
        Args:
            comparison: Comparison results dictionary
            
        Returns:
            Detailed statistics dictionary
        """
        details = {
            'status_analysis': {
                'status_matches': 0,
                'status_mismatches': 0
            },
            'platform_analysis': {
                'platform_matches': 0,
                'platform_mismatches': 0
            },
            'coverage_analysis': {
                'nessus_coverage': 0.0,
                'netbox_coverage': 0.0
            }
        }
        
        # Analyze matched items
        for item in comparison['matched_items']:
            if item.get('status_match'):
                details['status_analysis']['status_matches'] += 1
            else:
                details['status_analysis']['status_mismatches'] += 1
            
            if item.get('platform_match'):
                details['platform_analysis']['platform_matches'] += 1
            else:
                details['platform_analysis']['platform_mismatches'] += 1
        
        # Calculate coverage percentages
        total_agents = comparison['summary']['total_agents']
        total_netbox_items = comparison['summary'].get('total_devices', comparison['summary'].get('total_vms', 0))
        
        if total_agents > 0:
            details['coverage_analysis']['nessus_coverage'] = (
                comparison['summary']['matched'] / total_agents * 100
            )
        
        if total_netbox_items > 0:
            details['coverage_analysis']['netbox_coverage'] = (
                comparison['summary']['matched'] / total_netbox_items * 100
            )
        
        return details
    
    def save_comparison_results(self, comparison: Dict, filename: str) -> bool:
        """
        Save comparison results to file
        
        Args:
            comparison: Comparison results dictionary
            filename: Output filename
            
        Returns:
            True if successful, False otherwise
        """
        output_data = create_output_data_dict(comparison, "comparison_results")
        return save_to_json(output_data, filename)
    
    def print_comparison_summary(self, comparison: Dict, comparison_type: str):
        """
        Print comparison summary to console
        
        Args:
            comparison: Comparison results dictionary
            comparison_type: Type of comparison (devices/vms)
        """
        summary = comparison['summary']
        details = comparison['details']
        
        print(f"\n=== {comparison_type.upper()} Comparison Summary ===")
        print(f"Total Nessus Agents: {summary['total_agents']}")
        print(f"Total Netbox {comparison_type.title()}: {summary.get('total_devices', summary.get('total_vms', 0))}")
        print(f"Matched Items: {summary['matched']}")
        print(f"Unmatched Agents: {summary['unmatched_agents']}")
        print(f"Unmatched {comparison_type.title()}: {summary.get('unmatched_devices', summary.get('unmatched_vms', 0))}")
        
        print(f"\nCoverage Analysis:")
        print(f"  Nessus Coverage: {details['coverage_analysis']['nessus_coverage']:.1f}%")
        print(f"  Netbox Coverage: {details['coverage_analysis']['netbox_coverage']:.1f}%")
        
        if summary['matched'] > 0:
            print(f"\nStatus Analysis:")
            print(f"  Status Matches: {details['status_analysis']['status_matches']}")
            print(f"  Status Mismatches: {details['status_analysis']['status_mismatches']}")
            
            print(f"\nPlatform Analysis:")
            print(f"  Platform Matches: {details['platform_analysis']['platform_matches']}")
            print(f"  Platform Mismatches: {details['platform_analysis']['platform_mismatches']}")

    def comprehensive_comparison(self) -> Dict:
        """
        Comprehensive comparison of Nessus agents with both Netbox devices and VMs
        
        Returns:
            Comprehensive comparison results
        """
        print("=== Comprehensive Comparison ===")
        
        # Get data from cache or API
        agents = self._get_agents_data()
        devices = self._get_devices_data()
        vms = self._get_vms_data()
        
        comprehensive = {
            'summary': {
                'total_agents': len(agents),
                'total_devices': len(devices),
                'total_vms': len(vms),
                'matched_with_devices': 0,
                'matched_with_vms': 0,
                'unmatched_agents': 0,
                'unmatched_devices': 0,
                'unmatched_vms': 0
            },
            'device_matches': [],
            'vm_matches': [],
            'unmatched_agents': [],
            'unmatched_devices': [],
            'unmatched_vms': [],
            'details': {}
        }
        
        # Create lookup dictionaries by hostname
        agent_names = {self._extract_hostname(agent.get('name', '')): agent for agent in agents if agent and isinstance(agent, dict) and agent.get('name')}
        device_names = {self._extract_hostname(device.get('name', '')): device for device in devices if device and isinstance(device, dict) and device.get('name')}
        vm_names = {self._extract_hostname(vm.get('name', '')): vm for vm in vms if vm and isinstance(vm, dict) and vm.get('name')}
        
        # Create IP-based lookups
        device_ips = {}
        for device in devices:
            if device and isinstance(device, dict):
                ip = self._get_primary_ip(device)
                if ip:
                    device_ips[ip] = device
        
        vm_ips = {}
        for vm in vms:
            if vm and isinstance(vm, dict):
                ip = self._get_primary_ip(vm)
                if ip:
                    vm_ips[ip] = vm
        
        # Track matched items
        matched_agents = set()
        matched_devices = set()
        matched_vms = set()
        
        # First: Match agents with devices by hostname
        device_hostname_matches = set(agent_names.keys()) & set(device_names.keys())
        for name in tqdm(device_hostname_matches, desc="Matching agents/devices by hostname"):
            agent = agent_names[name]
            device = device_names[name]
            
            match_details = {
                'name': name,
                'match_type': 'hostname',
                'nessus_agent': {
                    'id': agent.get('id'),
                    'status': agent.get('status'),
                    'platform': agent.get('platform'),
                    'version': agent.get('version'),
                    'last_connect': agent.get('last_connect'),
                    'ip': agent.get('ip')
                },
                'netbox_device': {
                    'id': device.get('id'),
                    'status': device.get('status', {}).get('value') if device.get('status') else None,
                    'site': device.get('site', {}).get('name') if device.get('site') else None,
                    'platform': device.get('platform', {}).get('name') if device.get('platform') else None,
                    'device_type': device.get('device_type', {}).get('model') if device.get('device_type') else None,
                    'primary_ip': self._get_primary_ip(device),
                    'all_ips': self._get_all_ips(device)
                },
                'status_match': agent.get('status') == 'online' and device.get('status', {}).get('value') == 'active',
                'platform_match': agent.get('platform') == device.get('platform', {}).get('name') if device.get('platform') else False
            }
            
            comprehensive['device_matches'].append(match_details)
            comprehensive['summary']['matched_with_devices'] += 1
            matched_agents.add(agent.get('id'))
            matched_devices.add(device.get('id'))
        
        # Second: Match remaining agents with VMs by hostname
        vm_hostname_matches = set(agent_names.keys()) & set(vm_names.keys())
        for name in tqdm(vm_hostname_matches, desc="Matching agents/VMs by hostname"):
            if name not in device_hostname_matches:  # Only if not already matched with device
                agent = agent_names[name]
                vm = vm_names[name]
                
                match_details = {
                    'name': name,
                    'match_type': 'hostname',
                    'nessus_agent': {
                        'id': agent.get('id'),
                        'status': agent.get('status'),
                        'platform': agent.get('platform'),
                        'version': agent.get('version'),
                        'last_connect': agent.get('last_connect'),
                        'ip': agent.get('ip')
                    },
                    'netbox_vm': {
                        'id': vm.get('id'),
                        'status': vm.get('status', {}).get('value') if vm.get('status') else None,
                        'cluster': vm.get('cluster', {}).get('name') if vm.get('cluster') else None,
                        'platform': vm.get('platform', {}).get('name') if vm.get('platform') else None,
                        'site': vm.get('site', {}).get('name') if vm.get('site') else None,
                        'vcpus': vm.get('vcpus'),
                        'memory': vm.get('memory'),
                        'disk': vm.get('disk'),
                        'primary_ip': self._get_primary_ip(vm),
                        'all_ips': self._get_all_ips(vm)
                    },
                    'status_match': agent.get('status') == 'online' and vm.get('status', {}).get('value') == 'active',
                    'platform_match': agent.get('platform') == vm.get('platform', {}).get('name') if vm.get('platform') else False
                }
                
                comprehensive['vm_matches'].append(match_details)
                comprehensive['summary']['matched_with_vms'] += 1
                matched_agents.add(agent.get('id'))
                matched_vms.add(vm.get('id'))
        
        # Third: IP-based matching for remaining agents
        for agent in agents:
            if agent and isinstance(agent, dict) and agent.get('id') not in matched_agents:
                agent_ip = agent.get('ip')
                if agent_ip:
                    # Try device first
                    if agent_ip in device_ips and device_ips[agent_ip].get('id') not in matched_devices:
                        device = device_ips[agent_ip]
                        name = self._extract_hostname(agent.get('name', ''))
                        
                        match_details = {
                            'name': name,
                            'match_type': 'ip',
                            'nessus_agent': {
                                'id': agent.get('id'),
                                'status': agent.get('status'),
                                'platform': agent.get('platform'),
                                'version': agent.get('version'),
                                'last_connect': agent.get('last_connect'),
                                'ip': agent.get('ip')
                            },
                            'netbox_device': {
                                'id': device.get('id'),
                                'status': device.get('status', {}).get('value') if device.get('status') else None,
                                'site': device.get('site', {}).get('name') if device.get('site') else None,
                                'platform': device.get('platform', {}).get('name') if device.get('platform') else None,
                                'device_type': device.get('device_type', {}).get('model') if device.get('device_type') else None,
                                'primary_ip': self._get_primary_ip(device),
                                'all_ips': self._get_all_ips(device)
                            },
                            'status_match': agent.get('status') == 'online' and device.get('status', {}).get('value') == 'active',
                            'platform_match': agent.get('platform') == device.get('platform', {}).get('name') if device.get('platform') else False
                        }
                        
                        comprehensive['device_matches'].append(match_details)
                        comprehensive['summary']['matched_with_devices'] += 1
                        matched_agents.add(agent.get('id'))
                        matched_devices.add(device.get('id'))
                    
                    # Try VM if not matched with device
                    elif agent_ip in vm_ips and vm_ips[agent_ip].get('id') not in matched_vms:
                        vm = vm_ips[agent_ip]
                        name = self._extract_hostname(agent.get('name', ''))
                        
                        match_details = {
                            'name': name,
                            'match_type': 'ip',
                            'nessus_agent': {
                                'id': agent.get('id'),
                                'status': agent.get('status'),
                                'platform': agent.get('platform'),
                                'version': agent.get('version'),
                                'last_connect': agent.get('last_connect'),
                                'ip': agent.get('ip')
                            },
                            'netbox_vm': {
                                'id': vm.get('id'),
                                'status': vm.get('status', {}).get('value') if vm.get('status') else None,
                                'cluster': vm.get('cluster', {}).get('name') if vm.get('cluster') else None,
                                'platform': vm.get('platform', {}).get('name') if vm.get('platform') else None,
                                'site': vm.get('site', {}).get('name') if vm.get('site') else None,
                                'vcpus': vm.get('vcpus'),
                                'memory': vm.get('memory'),
                                'disk': vm.get('disk'),
                                'primary_ip': self._get_primary_ip(vm),
                                'all_ips': self._get_all_ips(vm)
                            },
                            'status_match': agent.get('status') == 'online' and vm.get('status', {}).get('value') == 'active',
                            'platform_match': agent.get('platform') == vm.get('platform', {}).get('name') if vm.get('platform') else False
                        }
                        
                        comprehensive['vm_matches'].append(match_details)
                        comprehensive['summary']['matched_with_vms'] += 1
                        matched_agents.add(agent.get('id'))
                        matched_vms.add(vm.get('id'))
        
        # Find unmatched agents
        for agent in agents:
            if agent and isinstance(agent, dict) and agent.get('id') not in matched_agents:
                name = self._extract_hostname(agent.get('name', ''))
                comprehensive['unmatched_agents'].append({
                    'name': name,
                    'id': agent.get('id'),
                    'status': agent.get('status'),
                    'platform': agent.get('platform'),
                    'version': agent.get('version'),
                    'ip': agent.get('ip')
                })
                comprehensive['summary']['unmatched_agents'] += 1
        
        # Find unmatched devices (not matched by hostname or IP)
        for device in devices:
            if device and isinstance(device, dict) and device.get('id') not in matched_devices:
                name = self._extract_hostname(device.get('name', ''))
                comprehensive['unmatched_devices'].append({
                    'name': name,
                    'id': device.get('id'),
                    'status': device.get('status', {}).get('value') if device.get('status') else None,
                    'site': device.get('site', {}).get('name') if device.get('site') else None,
                    'platform': device.get('platform', {}).get('name') if device.get('platform') else None,
                    'primary_ip': self._get_primary_ip(device)
                })
                comprehensive['summary']['unmatched_devices'] += 1
        
        # Find unmatched VMs (not matched by hostname or IP)
        for vm in vms:
            if vm and isinstance(vm, dict) and vm.get('id') not in matched_vms:
                name = self._extract_hostname(vm.get('name', ''))
                comprehensive['unmatched_vms'].append({
                    'name': name,
                    'id': vm.get('id'),
                    'status': vm.get('status', {}).get('value') if vm.get('status') else None,
                    'cluster': vm.get('cluster', {}).get('name') if vm.get('cluster') else None,
                    'platform': vm.get('platform', {}).get('name') if vm.get('platform') else None,
                    'site': vm.get('site', {}).get('name') if vm.get('site') else None,
                    'primary_ip': self._get_primary_ip(vm)
                })
                comprehensive['summary']['unmatched_vms'] += 1
        
        # Generate detailed statistics
        comprehensive['details'] = self._generate_comprehensive_details(comprehensive)
        
        # Otomatik kaydet
        self.save_comparison_results(comprehensive, "output/comprehensive_comparison_results.json")
        
        # Generate HTML report
        html_file = self.html_reporter.generate_comparison_report(comprehensive, "comprehensive")
        print(f"✓ HTML report saved to {html_file}")
        
        return comprehensive

    def _generate_comprehensive_details(self, comprehensive: Dict) -> Dict:
        """
        Generate detailed statistics for comprehensive comparison
        
        Args:
            comprehensive: Comprehensive comparison results
            
        Returns:
            Detailed statistics dictionary
        """
        details = {
            'coverage_analysis': {
                'total_netbox_items': comprehensive['summary']['total_devices'] + comprehensive['summary']['total_vms'],
                'total_matched': comprehensive['summary']['matched_with_devices'] + comprehensive['summary']['matched_with_vms'],
                'coverage_percentage': 0,
                'unmatched_netbox_items': comprehensive['summary']['unmatched_devices'] + comprehensive['summary']['unmatched_vms']
            },
            'match_type_analysis': {
                'hostname_matches': 0,
                'ip_matches': 0
            },
            'status_analysis': {
                'status_matches': 0,
                'status_mismatches': 0
            },
            'platform_analysis': {
                'platform_matches': 0,
                'platform_mismatches': 0
            }
        }
        
        # Calculate coverage percentage
        total_netbox = details['coverage_analysis']['total_netbox_items']
        if total_netbox > 0:
            details['coverage_analysis']['coverage_percentage'] = round(
                (details['coverage_analysis']['total_matched'] / total_netbox) * 100, 2
            )
        
        # Analyze device matches
        for match in comprehensive['device_matches']:
            if match.get('match_type') == 'hostname':
                details['match_type_analysis']['hostname_matches'] += 1
            elif match.get('match_type') == 'ip':
                details['match_type_analysis']['ip_matches'] += 1
            
            if match.get('status_match'):
                details['status_analysis']['status_matches'] += 1
            else:
                details['status_analysis']['status_mismatches'] += 1
            
            if match.get('platform_match'):
                details['platform_analysis']['platform_matches'] += 1
            else:
                details['platform_analysis']['platform_mismatches'] += 1
        
        # Analyze VM matches
        for match in comprehensive['vm_matches']:
            if match.get('match_type') == 'hostname':
                details['match_type_analysis']['hostname_matches'] += 1
            elif match.get('match_type') == 'ip':
                details['match_type_analysis']['ip_matches'] += 1
            
            if match.get('status_match'):
                details['status_analysis']['status_matches'] += 1
            else:
                details['status_analysis']['status_mismatches'] += 1
            
            if match.get('platform_match'):
                details['platform_analysis']['platform_matches'] += 1
            else:
                details['platform_analysis']['platform_mismatches'] += 1
        
        return details

    def _get_all_ips(self, item: Dict) -> List[str]:
        """
        Get all IP addresses for a Netbox item (device or VM)
        
        Args:
            item: Netbox device or VM dictionary
            
        Returns:
            List of all IP addresses
        """
        ips = []
        
        # Primary IP
        primary_ip = self._get_primary_ip(item)
        if primary_ip:
            ips.append(primary_ip)
        
        # Check if item has interface information (from fetch_all_virtual_machines)
        interfaces = item.get('interfaces', [])
        for interface in interfaces:
            if isinstance(interface, dict):
                # Interface IPs
                interface_ips = interface.get('ip_addresses', [])
                for ip_data in interface_ips:
                    if isinstance(ip_data, dict):
                        ip_addr = ip_data.get('address', '')
                        if ip_addr:
                            clean_ip = ip_addr.split('/')[0]  # Remove CIDR
                            if clean_ip not in ips:
                                ips.append(clean_ip)
        
        # If no interface data available, try API calls as fallback
        if not interfaces:
            try:
                if 'virtualization.virtualmachine' in item.get('url', ''):
                    # This is a VM
                    vm_id = item.get('id')
                    if vm_id:
                        vm_ips = self.netbox_service.get_ips_for_vm(vm_id)
                        for ip_data in vm_ips:
                            ip_addr = ip_data.get('address', '')
                            if ip_addr:
                                clean_ip = ip_addr.split('/')[0]  # Remove CIDR
                                if clean_ip not in ips:
                                    ips.append(clean_ip)
                else:
                    # This is a device
                    device_id = item.get('id')
                    if device_id:
                        device_ips = self.netbox_service.get_ips_for_device(device_id)
                        for ip_data in device_ips:
                            ip_addr = ip_data.get('address', '')
                            if ip_addr:
                                clean_ip = ip_addr.split('/')[0]  # Remove CIDR
                                if clean_ip not in ips:
                                    ips.append(clean_ip)
            except Exception as e:
                # If API call fails, just use primary IP
                pass
        
        return ips

 