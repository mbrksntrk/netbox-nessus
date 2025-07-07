"""
Netbox API Client

Client for interacting with the Netbox network infrastructure management API.
"""

from typing import Dict, List, Optional
from .base_client import BaseAPIClient


class NetboxClient(BaseAPIClient):
    """Netbox API client for managing network infrastructure data"""
    
    def __init__(self, base_url: str, token: str, verify_ssl: bool = False):
        """
        Initialize Netbox API client
        
        Args:
            base_url: Netbox server URL (e.g., https://netbox-server)
            token: API token
            verify_ssl: Whether to verify SSL certificates
        """
        super().__init__(base_url, verify_ssl)
        # Set Netbox-specific headers
        self.session.headers.update({
            'Authorization': f'Token {token}'
        })
    
    def test_connection(self) -> bool:
        """Test connection to Netbox API"""
        try:
            response = self.get('/api/')
            return response is not None
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    def get_devices(self, **params) -> List[Dict]:
        """
        Fetch devices from Netbox (with pagination)
        
        Args:
            **params: Query parameters (name, site, status, etc.)
            
        Returns:
            List of device dictionaries
        """
        devices = []
        limit = 1000
        offset = 0
        
        # Add include parameter to get interface details
        if 'include' not in params:
            params['include'] = 'interfaces,interfaces.ip_addresses'
        
        while True:
            page_params = params.copy()
            page_params['limit'] = limit
            page_params['offset'] = offset
            response = self.get('/api/dcim/devices/', params=page_params)
            if response and 'results' in response:
                results = response['results']
                devices.extend(results)
                if response.get('next'):
                    offset += limit
                else:
                    break
            else:
                break
        return devices
    
    def get_device(self, device_id: int) -> Optional[Dict]:
        """
        Fetch a specific device by ID
        
        Args:
            device_id: Device ID
            
        Returns:
            Device dictionary or None if error
        """
        return self.get(f'/api/dcim/devices/{device_id}/')
    
    def create_device(self, device_data: Dict) -> Optional[Dict]:
        """
        Create a new device
        
        Args:
            device_data: Device data dictionary
            
        Returns:
            Created device dictionary or None if error
        """
        return self.post('/api/dcim/devices/', data=device_data)
    
    def update_device(self, device_id: int, device_data: Dict) -> Optional[Dict]:
        """
        Update an existing device
        
        Args:
            device_id: Device ID
            device_data: Updated device data
            
        Returns:
            Updated device dictionary or None if error
        """
        return self.put(f'/api/dcim/devices/{device_id}/', data=device_data)
    
    def delete_device(self, device_id: int) -> bool:
        """
        Delete a device
        
        Args:
            device_id: Device ID
            
        Returns:
            True if successful, False otherwise
        """
        response = self.delete(f'/api/dcim/devices/{device_id}/')
        return response is not None
    
    def get_sites(self, **params) -> List[Dict]:
        """
        Fetch sites from Netbox
        
        Args:
            **params: Query parameters
            
        Returns:
            List of site dictionaries
        """
        response = self.get('/api/dcim/sites/', params=params)
        if response:
            return response.get('results', [])
        return []
    
    def get_ip_addresses(self, **params) -> List[Dict]:
        """
        Fetch IP addresses from Netbox (with pagination)
        
        Args:
            **params: Query parameters
            
        Returns:
            List of IP address dictionaries
        """
        ip_addresses = []
        limit = 1000
        offset = 0
        
        while True:
            page_params = params.copy()
            page_params['limit'] = limit
            page_params['offset'] = offset
            response = self.get('/api/ipam/ip-addresses/', params=page_params)
            if response and 'results' in response:
                results = response['results']
                ip_addresses.extend(results)
                if response.get('next'):
                    offset += limit
                else:
                    break
            else:
                break
        return ip_addresses
    
    def create_ip_address(self, ip_data: Dict) -> Optional[Dict]:
        """
        Create a new IP address
        
        Args:
            ip_data: IP address data dictionary
            
        Returns:
            Created IP address dictionary or None if error
        """
        return self.post('/api/ipam/ip-addresses/', data=ip_data)
    
    def get_vulnerabilities(self, **params) -> List[Dict]:
        """
        Fetch vulnerabilities from Netbox (if vulnerability plugin is installed)
        
        Args:
            **params: Query parameters
            
        Returns:
            List of vulnerability dictionaries
        """
        response = self.get('/api/vulnerabilities/vulnerabilities/', params=params)
        if response:
            return response.get('results', [])
        return []
    
    def get_vm_interfaces(self, vm_id: int) -> List[Dict]:
        """
        Fetch interfaces for a specific virtual machine
        
        Args:
            vm_id: Virtual machine ID
            
        Returns:
            List of interface dictionaries
        """
        response = self.get(f'/api/virtualization/interfaces/', params={'virtual_machine_id': vm_id})
        if response:
            return response.get('results', [])
        return []
    
    def get_device_interfaces(self, device_id: int) -> List[Dict]:
        """
        Fetch interfaces for a specific device
        
        Args:
            device_id: Device ID
            
        Returns:
            List of interface dictionaries
        """
        response = self.get(f'/api/dcim/interfaces/', params={'device_id': device_id})
        if response:
            return response.get('results', [])
        return []
    
    def get_virtual_machines(self, **params) -> List[Dict]:
        """
        Fetch virtual machines from Netbox (with pagination)
        
        Args:
            **params: Query parameters (name, site, status, etc.)
            
        Returns:
            List of virtual machine dictionaries
        """
        vms = []
        limit = 1000
        offset = 0
        
        while True:
            page_params = params.copy()
            page_params['limit'] = limit
            page_params['offset'] = offset
            response = self.get('/api/virtualization/virtual-machines/', params=page_params)
            if response and 'results' in response:
                results = response['results']
                vms.extend(results)
                if response.get('next'):
                    offset += limit
                else:
                    break
            else:
                break
        return vms
    
    def get_virtual_machine(self, vm_id: int) -> Optional[Dict]:
        """
        Fetch a specific virtual machine by ID
        
        Args:
            vm_id: Virtual machine ID
            
        Returns:
            Virtual machine dictionary or None if error
        """
        return self.get(f'/api/virtualization/virtual-machines/{vm_id}/')
    
    def get_devices_by_ip(self, ip_address: str) -> List[Dict]:
        """
        Fetch devices by IP address
        
        Args:
            ip_address: IP address to search for
            
        Returns:
            List of device dictionaries with matching IP
        """
        # First get IP addresses that match
        ip_response = self.get('/api/ipam/ip-addresses/', params={'address': ip_address})
        if not ip_response:
            return []
        
        matching_ips = ip_response.get('results', [])
        devices = []
        
        for ip_info in matching_ips:
            # Check if IP is assigned to a device
            if ip_info.get('assigned_object_type') == 'dcim.device':
                device_id = ip_info.get('assigned_object_id')
                if device_id:
                    device = self.get_device(device_id)
                    if device:
                        devices.append(device)
        
        return devices
    
    def get_vms_by_ip(self, ip_address: str) -> List[Dict]:
        """
        Fetch virtual machines by IP address
        
        Args:
            ip_address: IP address to search for
            
        Returns:
            List of virtual machine dictionaries with matching IP
        """
        # First get IP addresses that match
        ip_response = self.get('/api/ipam/ip-addresses/', params={'address': ip_address})
        if not ip_response:
            return []
        
        matching_ips = ip_response.get('results', [])
        vms = []
        
        for ip_info in matching_ips:
            # Check if IP is assigned to a virtual machine
            if ip_info.get('assigned_object_type') == 'virtualization.virtualmachine':
                vm_id = ip_info.get('assigned_object_id')
                if vm_id:
                    vm = self.get_virtual_machine(vm_id)
                    if vm:
                        vms.append(vm)
        
        return vms
    
    def get_ips_for_vm(self, vm_id: int) -> List[Dict]:
        """
        Fetch all IP addresses for a virtual machine
        
        Args:
            vm_id: Virtual machine ID
            
        Returns:
            List of IP address dictionaries
        """
        response = self.get(f'/api/ipam/ip-addresses/', params={'virtual_machine_id': vm_id})
        if response:
            return response.get('results', [])
        return []
    
    def get_ips_for_device(self, device_id: int) -> List[Dict]:
        """
        Fetch all IP addresses for a device
        
        Args:
            device_id: Device ID
            
        Returns:
            List of IP address dictionaries
        """
        response = self.get(f'/api/ipam/ip-addresses/', params={'device_id': device_id})
        if response:
            return response.get('results', [])
        return []
    
    def get_all_vm_interfaces(self, limit=1000) -> list:
        """
        Fetch all VM interfaces from Netbox, including their IP addresses and associated VM IDs.
        Args:
            limit: Number of results per page (default 1000)
        Returns:
            List of interface dicts
        """
        interfaces = []
        offset = 0
        while True:
            params = {'limit': limit, 'offset': offset}
            response = self.get('/api/virtualization/interfaces/', params=params)
            if response and 'results' in response:
                interfaces.extend(response['results'])
                if response.get('next'):
                    offset += limit
                else:
                    break
            else:
                break
        return interfaces
    
    def get_all_device_interfaces(self, limit=1000) -> list:
        """
        Fetch all device interfaces from Netbox, including their IP addresses and associated device IDs.
        Args:
            limit: Number of results per page (default 1000)
        Returns:
            List of interface dicts
        """
        interfaces = []
        offset = 0
        while True:
            params = {'limit': limit, 'offset': offset}
            response = self.get('/api/dcim/interfaces/', params=params)
            if response and 'results' in response:
                interfaces.extend(response['results'])
                if response.get('next'):
                    offset += limit
                else:
                    break
            else:
                break
        return interfaces 