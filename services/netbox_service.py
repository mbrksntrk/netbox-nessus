"""
Netbox Service

Business logic layer for Netbox operations.
"""

from typing import Dict, List, Optional
from api.netbox_client import NetboxClient
from utils.helpers import create_output_data, create_output_data_dict, save_to_json
from tqdm import tqdm
from datetime import datetime
import time
import threading
import sys
import random
import json
import os
from utils.html_reporter import HTMLReporter


class Spinner:
    def __init__(self, desc: str = "Loading"):
        self.desc = desc
        self.spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.stop_running = threading.Event()
        self.thread = threading.Thread(target=self.animate)
        self.i = 0

    def animate(self):
        while not self.stop_running.is_set():
            sys.stdout.write(f'\r{self.desc} {self.spinner[self.i % len(self.spinner)]}')
            sys.stdout.flush()
            time.sleep(0.1)
            self.i += 1
        sys.stdout.write('\r' + ' ' * (len(self.desc) + 4) + '\r')
        sys.stdout.flush()

    def start(self):
        self.thread.start()

    def stop(self):
        self.stop_running.set()
        self.thread.join()


class NetboxService:
    """Service layer for Netbox operations"""
    
    def __init__(self, client: NetboxClient):
        """
        Initialize Netbox service
        
        Args:
            client: Netbox API client instance
        """
        self.client = client
        self.html_reporter = HTMLReporter()
    
    def test_connection(self) -> bool:
        """Test connection to Netbox"""
        return self.client.test_connection()
    
    def fetch_all_devices(self, **filters) -> List[Dict]:
        """
        Fetch all devices from Netbox
        
        Args:
            **filters: Optional filters for devices
            
        Returns:
            List of device dictionaries
        """
        print("Fetching devices from Netbox...")
        spinner = Spinner("Loading devices")
        spinner.start()
        devices = self.client.get_devices(**filters)
        spinner.stop()
        print(f"Found {len(devices)} devices")
        
        # Fetch interface information for all devices
        print("Fetching interface information...")
        all_device_interfaces = self.client.get_all_device_interfaces()
        
        # Fetch all IP addresses with pagination
        print("Fetching IP addresses...")
        all_ips = self.client.get_ip_addresses()
        print(f"Found {len(all_ips)} IP addresses")
        
        # Group interfaces by device ID
        device_interfaces = {}
        for interface in all_device_interfaces:
            device_id = interface.get('device', {}).get('id')
            if device_id:
                if device_id not in device_interfaces:
                    device_interfaces[device_id] = []
                device_interfaces[device_id].append(interface)
        
        # Group IP addresses by interface ID for device interfaces
        device_interface_ips = {}
        for ip_data in all_ips:
            if (ip_data.get('assigned_object_type') == 'dcim.interface' and 
                ip_data.get('assigned_object_id')):
                interface_id = ip_data.get('assigned_object_id')
                if interface_id not in device_interface_ips:
                    device_interface_ips[interface_id] = []
                device_interface_ips[interface_id].append(ip_data)
        
        # Add interface information to devices
        for device in devices:
            device_id = device.get('id')
            if device_id in device_interfaces:
                device['interfaces'] = device_interfaces[device_id]
                # Add IP addresses to interfaces
                for interface in device['interfaces']:
                    interface_id = interface.get('id')
                    if interface_id in device_interface_ips:
                        interface['ip_addresses'] = device_interface_ips[interface_id]
                    else:
                        interface['ip_addresses'] = []
            else:
                device['interfaces'] = []
        
        self.save_devices_to_file(devices, "output/netbox_devices.json")
        
        # Otomatik kaydet
        output_data = create_output_data(devices, "netbox_devices")
        save_to_json(output_data, "output/netbox_devices.json")
        
        # Generate HTML report
        html_file = self.html_reporter.generate_fetch_report(output_data, "devices")
        print(f"✓ HTML report saved to {html_file}")
        
        return devices
    
    def fetch_device_by_name(self, name: str) -> Optional[Dict]:
        """
        Fetch a specific device by name
        
        Args:
            name: Device name
            
        Returns:
            Device dictionary or None if not found
        """
        devices = self.client.get_devices(name=name)
        return devices[0] if devices else None
    
    def fetch_devices_by_site(self, site: str) -> List[Dict]:
        """
        Fetch devices filtered by site
        
        Args:
            site: Site name or slug
            
        Returns:
            List of filtered device dictionaries
        """
        return self.client.get_devices(site=site)
    
    def fetch_devices_by_status(self, status: str) -> List[Dict]:
        """
        Fetch devices filtered by status
        
        Args:
            status: Device status (active, inactive, etc.)
            
        Returns:
            List of filtered device dictionaries
        """
        return self.client.get_devices(status=status)
    
    def create_device(self, device_data: Dict) -> Optional[Dict]:
        """
        Create a new device in Netbox
        
        Args:
            device_data: Device data dictionary
            
        Returns:
            Created device dictionary or None if error
        """
        print(f"Creating device: {device_data.get('name', 'Unknown')}")
        return self.client.create_device(device_data)
    
    def update_device(self, device_id: int, device_data: Dict) -> Optional[Dict]:
        """
        Update an existing device in Netbox
        
        Args:
            device_id: Device ID
            device_data: Updated device data
            
        Returns:
            Updated device dictionary or None if error
        """
        print(f"Updating device {device_id}")
        return self.client.update_device(device_id, device_data)
    
    def delete_device(self, device_id: int) -> bool:
        """
        Delete a device from Netbox
        
        Args:
            device_id: Device ID
            
        Returns:
            True if successful, False otherwise
        """
        print(f"Deleting device {device_id}")
        return self.client.delete_device(device_id)
    
    def fetch_all_sites(self) -> List[Dict]:
        """
        Fetch all sites from Netbox
        
        Returns:
            List of site dictionaries
        """
        print("Fetching sites from Netbox...")
        sites = self.client.get_sites()
        print(f"Found {len(sites)} sites")
        return sites
    
    def fetch_all_ip_addresses(self, **filters) -> List[Dict]:
        """
        Fetch all IP addresses from Netbox
        
        Args:
            **filters: Optional filters for IP addresses
            
        Returns:
            List of IP address dictionaries
        """
        print("Fetching IP addresses from Netbox...")
        ip_addresses = self.client.get_ip_addresses(**filters)
        print(f"Found {len(ip_addresses)} IP addresses")
        return ip_addresses
    
    def create_ip_address(self, ip_data: Dict) -> Optional[Dict]:
        """
        Create a new IP address in Netbox
        
        Args:
            ip_data: IP address data dictionary
            
        Returns:
            Created IP address dictionary or None if error
        """
        print(f"Creating IP address: {ip_data.get('address', 'Unknown')}")
        return self.client.create_ip_address(ip_data)
    
    def save_devices_to_file(self, devices: List[Dict], filename: str) -> bool:
        """
        Save devices data to file
        
        Args:
            devices: List of device dictionaries
            filename: Output filename
            
        Returns:
            True if successful, False otherwise
        """
        output_data = create_output_data(devices, "devices")
        return save_to_json(output_data, filename)
    
    def get_device_statistics(self, devices: List[Dict]) -> Dict:
        """
        Generate statistics from devices data
        
        Args:
            devices: List of device dictionaries
            
        Returns:
            Statistics dictionary
        """
        if not devices:
            return {}
        
        stats = {
            'total_devices': len(devices),
            'by_status': {},
            'by_site': {},
            'by_device_type': {},
            'by_platform': {}
        }
        
        for device in devices:
            if not device:  # Skip None or empty device objects
                continue
                
            # Status statistics
            status_obj = device.get('status')
            status = status_obj.get('value', 'unknown') if status_obj else 'unknown'
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
            
            # Site statistics
            site_obj = device.get('site')
            site = site_obj.get('name', 'unknown') if site_obj else 'unknown'
            stats['by_site'][site] = stats['by_site'].get(site, 0) + 1
            
            # Device type statistics
            device_type_obj = device.get('device_type')
            device_type = device_type_obj.get('model', 'unknown') if device_type_obj else 'unknown'
            stats['by_device_type'][device_type] = stats['by_device_type'].get(device_type, 0) + 1
            
            # Platform statistics
            platform_obj = device.get('platform')
            platform = platform_obj.get('name', 'unknown') if platform_obj else 'unknown'
            stats['by_platform'][platform] = stats['by_platform'].get(platform, 0) + 1
        
        return stats
    
    def fetch_all_virtual_machines(self, **filters) -> List[Dict]:
        """
        Fetch all virtual machines from Netbox
        
        Args:
            **filters: Optional filters for VMs
            
        Returns:
            List of VM dictionaries with interface information
        """
        print("Fetching virtual machines from Netbox...")
        spinner = Spinner("Loading VMs")
        spinner.start()
        vms = self.client.get_virtual_machines(**filters)
        spinner.stop()
        print(f"Found {len(vms)} virtual machines")
        
        # Fetch interface information for all VMs
        print("Fetching interface information...")
        all_interfaces = self.client.get_all_vm_interfaces()
        
        # Fetch all IP addresses with pagination
        print("Fetching IP addresses...")
        all_ips = self.client.get_ip_addresses()
        print(f"Found {len(all_ips)} IP addresses")
        
        # Group interfaces by VM ID
        vm_interfaces = {}
        for interface in all_interfaces:
            vm_id = interface.get('virtual_machine', {}).get('id')
            if vm_id:
                if vm_id not in vm_interfaces:
                    vm_interfaces[vm_id] = []
                vm_interfaces[vm_id].append(interface)
        
        # Group IP addresses by interface ID for VM interfaces
        vm_interface_ips = {}
        for ip_data in all_ips:
            if (ip_data.get('assigned_object_type') == 'virtualization.vminterface' and 
                ip_data.get('assigned_object_id')):
                interface_id = ip_data.get('assigned_object_id')
                if interface_id not in vm_interface_ips:
                    vm_interface_ips[interface_id] = []
                vm_interface_ips[interface_id].append(ip_data)
        
        # Add interface information to VMs
        for vm in vms:
            vm_id = vm.get('id')
            if vm_id in vm_interfaces:
                vm['interfaces'] = vm_interfaces[vm_id]
                # Add IP addresses to interfaces
                for interface in vm['interfaces']:
                    interface_id = interface.get('id')
                    if interface_id in vm_interface_ips:
                        interface['ip_addresses'] = vm_interface_ips[interface_id]
                    else:
                        interface['ip_addresses'] = []
            else:
                vm['interfaces'] = []
        
        # Save VMs with interfaces to file
        self.save_vms_to_file(vms, "output/netbox_vms.json")
        
        # Generate HTML report
        output_data = create_output_data(vms, "netbox_vms")
        html_file = self.html_reporter.generate_fetch_report(output_data, "virtual_machines")
        print(f"✓ HTML report saved to {html_file}")
        
        return vms
    
    def fetch_vm_by_name(self, name: str) -> Optional[Dict]:
        """
        Fetch a specific virtual machine by name
        
        Args:
            name: Virtual machine name
            
        Returns:
            Virtual machine dictionary or None if not found
        """
        vms = self.client.get_virtual_machines(name=name)
        return vms[0] if vms else None
    
    def save_vms_to_file(self, vms: List[Dict], filename: str) -> bool:
        """
        Save virtual machines data to file
        
        Args:
            vms: List of virtual machine dictionaries
            filename: Output filename
            
        Returns:
            True if successful, False otherwise
        """
        output_data = create_output_data(vms, "netbox_vms")
        save_to_json(output_data, "output/netbox_vms.json")
        
        # Generate HTML report
        html_file = self.html_reporter.generate_fetch_report(output_data, "vms")
        print(f"✓ HTML report saved to {html_file}")
        
        return True
    
    def get_vm_statistics(self, vms: List[Dict]) -> Dict:
        """
        Generate statistics from virtual machines data
        
        Args:
            vms: List of virtual machine dictionaries
            
        Returns:
            Statistics dictionary
        """
        if not vms:
            return {}
        
        stats = {
            'total_vms': len(vms),
            'by_status': {},
            'by_site': {},
            'by_platform': {},
            'by_cluster': {}
        }
        
        for vm in vms:
            if not vm:  # Skip None or empty VM objects
                continue
                
            # Status statistics
            status_obj = vm.get('status')
            status = status_obj.get('value', 'unknown') if status_obj else 'unknown'
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
            
            # Site statistics
            site_obj = vm.get('site')
            site = site_obj.get('name', 'unknown') if site_obj else 'unknown'
            stats['by_site'][site] = stats['by_site'].get(site, 0) + 1
            
            # Platform statistics
            platform_obj = vm.get('platform')
            platform = platform_obj.get('name', 'unknown') if platform_obj else 'unknown'
            stats['by_platform'][platform] = stats['by_platform'].get(platform, 0) + 1
            
            # Cluster statistics
            cluster_obj = vm.get('cluster')
            cluster = cluster_obj.get('name', 'unknown') if cluster_obj else 'unknown'
            stats['by_cluster'][cluster] = stats['by_cluster'].get(cluster, 0) + 1
        
        return stats
    
    def search_devices_by_ip(self, ip_address: str) -> List[Dict]:
        """
        Search devices by IP address
        
        Args:
            ip_address: IP address to search for
            
        Returns:
            List of matching device dictionaries
        """
        print(f"Searching for devices with IP: {ip_address}")
        devices = self.client.get_devices_by_ip(ip_address)
        print(f"Found {len(devices)} devices with IP {ip_address}")
        return devices
    
    def search_vms_by_ip(self, ip_address: str) -> List[Dict]:
        """
        Search for virtual machines by IP address
        
        Args:
            ip_address: IP address to search for
            
        Returns:
            List of VM dictionaries with matching IP
        """
        print(f"Searching for virtual machines with IP: {ip_address}")
        vms = self.client.get_vms_by_ip(ip_address)
        print(f"Found {len(vms)} virtual machines with IP {ip_address}")
        return vms
    
    def get_ips_for_vm(self, vm_id: int) -> List[Dict]:
        """
        Get all IP addresses for a virtual machine
        
        Args:
            vm_id: Virtual machine ID
            
        Returns:
            List of IP address dictionaries
        """
        return self.client.get_ips_for_vm(vm_id)
    
    def get_ips_for_device(self, device_id: int) -> List[Dict]:
        """
        Get all IP addresses for a device
        
        Args:
            device_id: Device ID
            
        Returns:
            List of IP address dictionaries
        """
        return self.client.get_ips_for_device(device_id)
    
    def search_all_by_ip(self, ip_address: str) -> Dict:
        """
        Search both devices and virtual machines by IP address
        
        Args:
            ip_address: IP address to search for
            
        Returns:
            Dictionary with 'devices', 'vms' lists and 'total_found' count
        """
        print(f"Searching Netbox for IP: {ip_address}")
        
        devices = self.search_devices_by_ip(ip_address)
        vms = self.search_vms_by_ip(ip_address)
        
        return {
            'devices': devices,
            'vms': vms,
            'total_found': len(devices) + len(vms)
        }
    
    def sync_nessus_agents_to_devices(self, nessus_agents: List[Dict]) -> List[Dict]:
        """
        Sync Nessus agents to Netbox devices
        
        Args:
            nessus_agents: List of Nessus agent dictionaries
            
        Returns:
            List of created/updated device dictionaries
        """
        synced_devices = []
        
        for agent in tqdm(nessus_agents, desc="Syncing agents to Netbox"):
            agent_name = agent.get('name', 'Unknown Agent')
            agent_ip = agent.get('distro', 'Unknown IP')
            
            # Check if device already exists
            existing_device = self.fetch_device_by_name(agent_name)
            
            if existing_device:
                # Update existing device
                print(f"Updating existing device: {agent_name}")
                updated_device = self.update_device(existing_device['id'], {
                    'name': agent_name,
                    'status': 'active' if agent.get('status') == 'online' else 'inactive',
                    'platform': agent.get('platform', 'Unknown'),
                    'serial': agent.get('uuid', ''),
                    'comments': f"Nessus Agent - Version: {agent.get('version', 'Unknown')}"
                })
                if updated_device:
                    synced_devices.append(updated_device)
            else:
                # Create new device
                print(f"Creating new device: {agent_name}")
                new_device = self.create_device({
                    'name': agent_name,
                    'device_type': {'name': 'Server'},
                    'status': 'active' if agent.get('status') == 'online' else 'inactive',
                    'platform': agent.get('platform', 'Unknown'),
                    'serial': agent.get('uuid', ''),
                    'comments': f"Nessus Agent - Version: {agent.get('version', 'Unknown')}"
                })
                if new_device:
                    synced_devices.append(new_device)
        
        # Sync sonuçlarını kaydet
        sync_results = {
            'total_agents': len(nessus_agents),
            'synced_devices': len(synced_devices),
            'sync_details': synced_devices,
            'timestamp': datetime.now().isoformat()
        }
        output_data = create_output_data_dict(sync_results)
        save_to_json(output_data, "output/sync_results.json")
        
        return synced_devices

def show_loading(desc: str, duration: Optional[float] = None):
    """
    Show a spinning loading animation
    
    Args:
        desc: Description text
        duration: Optional duration in seconds
    """
    spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    start_time = time.time()
    i = 0
    
    def animate():
        nonlocal i
        while True:
            if duration is not None and time.time() - start_time > duration:
                break
            sys.stdout.write(f'\r{desc} {spinner[i % len(spinner)]}')
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1
    
    # Start animation in background
    thread = threading.Thread(target=animate)
    thread.daemon = True
    thread.start()
    
    return thread

def show_loading_simple(desc: str):
    """
    Show a simple loading message with spinner
    
    Args:
        desc: Description text
    """
    spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    return f"{desc} {random.choice(spinner)}" 