#!/usr/bin/env python3
"""
Netbox-Nessus Integration Tool

Main application that integrates Nessus vulnerability scanner with Netbox
network infrastructure management system.
"""

import sys
import os
import json
from typing import Dict, List
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from api.nessus_client import NessusClient
from api.netbox_client import NetboxClient
from services.nessus_service import NessusService
from services.netbox_service import NetboxService
from services.comparison_service import ComparisonService
from utils.helpers import save_to_json, create_output_data, format_timestamp, create_output_data_dict


def initialize_clients():
    """Initialize API clients"""
    clients = {}
    
    # Initialize Nessus client
    if settings.validate_nessus_config():
        nessus_config = settings.get_nessus_config()
        clients['nessus'] = NessusClient(
            base_url=nessus_config['base_url'],
            access_key=nessus_config['access_key'],
            secret_key=nessus_config['secret_key'],
            verify_ssl=nessus_config['verify_ssl']
        )
        print("✓ Nessus client initialized")
    else:
        print("✗ Nessus configuration is invalid")
    
    # Initialize Netbox client
    if settings.validate_netbox_config():
        netbox_config = settings.get_netbox_config()
        clients['netbox'] = NetboxClient(
            base_url=netbox_config['base_url'],
            token=netbox_config['token'],
            verify_ssl=netbox_config['verify_ssl']
        )
        print("✓ Netbox client initialized")
    else:
        print("✗ Netbox configuration is invalid")
    
    return clients


def initialize_services(clients: Dict):
    """Initialize service layers"""
    services = {}
    
    if 'nessus' in clients:
        services['nessus'] = NessusService(clients['nessus'])
        print("✓ Nessus service initialized")
    
    if 'netbox' in clients:
        services['netbox'] = NetboxService(clients['netbox'])
        print("✓ Netbox service initialized")
    
    # Initialize comparison service if both services are available
    if 'nessus' in services and 'netbox' in services:
        services['comparison'] = ComparisonService(services['nessus'], services['netbox'])
        print("✓ Comparison service initialized")
    
    return services


def test_connections(services: Dict):
    """Test connections to all services"""
    print("\nTesting connections...")
    
    for service_name, service in services.items():
        print(f"Testing {service_name} connection...")
        if service.test_connection():
            print(f"✓ {service_name} connection successful")
        else:
            print(f"✗ {service_name} connection failed")
            return False
    
    return True


def fetch_nessus_agents(nessus_service: NessusService) -> List[Dict]:
    """Fetch agents from Nessus"""
    print("\n=== Fetching Nessus Agents ===")
    
    agents = nessus_service.fetch_all_agents(include_details=True)
    
    if agents:
        # Generate statistics
        stats = nessus_service.get_agent_statistics(agents)
        print(f"\nAgent Statistics:")
        print(f"  Total: {stats['total_agents']}")
        print(f"  By Status: {stats['by_status']}")
        print(f"  By Platform: {stats['by_platform']}")
        
        # Save to file
        output_config = settings.get_output_config()
        filename = output_config.get('file', 'nessus_agents.json')
        if nessus_service.save_agents_to_file(agents, filename):
            print(f"✓ Agents saved to {filename}")
        else:
            print(f"✗ Failed to save agents to {filename}")
    else:
        print("No agents found")
    
    return agents


def fetch_netbox_devices(netbox_service: NetboxService) -> List[Dict]:
    """Fetch devices from Netbox"""
    print("\n=== Fetching Netbox Devices ===")
    
    devices = netbox_service.fetch_all_devices()
    
    if devices:
        # Generate statistics
        stats = netbox_service.get_device_statistics(devices)
        print(f"\nDevice Statistics:")
        print(f"  Total: {stats['total_devices']}")
        print(f"  By Status: {stats['by_status']}")
        print(f"  By Site: {stats['by_site']}")
        
        # Save to file
        output_config = settings.get_output_config()
        filename = output_config.get('file', 'netbox_devices.json')
        if netbox_service.save_devices_to_file(devices, filename):
            print(f"✓ Devices saved to {filename}")
        else:
            print(f"✗ Failed to save devices to {filename}")
    else:
        print("No devices found")
    
    return devices


def fetch_netbox_vms(netbox_service: NetboxService) -> List[Dict]:
    """Fetch virtual machines from Netbox"""
    print("\n=== Fetching Netbox Virtual Machines ===")
    
    vms = netbox_service.fetch_all_virtual_machines()
    
    if vms:
        # Generate statistics
        stats = netbox_service.get_vm_statistics(vms)
        print(f"\nVirtual Machine Statistics:")
        print(f"  Total: {stats['total_vms']}")
        print(f"  By Status: {stats['by_status']}")
        print(f"  By Site: {stats['by_site']}")
        print(f"  By Cluster: {stats['by_cluster']}")
        
        # Save to file
        output_config = settings.get_output_config()
        filename = output_config.get('file', 'netbox_vms.json')
        if netbox_service.save_vms_to_file(vms, filename):
            print(f"✓ Virtual machines saved to {filename}")
        else:
            print(f"✗ Failed to save virtual machines to {filename}")
    else:
        print("No virtual machines found")
    
    return vms


def sync_nessus_to_netbox(nessus_service: NessusService, netbox_service: NetboxService):
    """Sync Nessus agents to Netbox devices"""
    print("\n=== Syncing Nessus Agents to Netbox ===")
    
    # Fetch agents from Nessus
    agents = nessus_service.fetch_all_agents(include_details=True)
    
    if not agents:
        print("No agents found in Nessus")
        return
    
    # Sync to Netbox
    synced_devices = netbox_service.sync_nessus_agents_to_devices(agents)
    
    print(f"✓ Synced {len(synced_devices)} devices to Netbox")
    
    # Save sync results
    sync_data = create_output_data(synced_devices, "synced_devices")
    save_to_json(sync_data, "output/sync_results.json")


def compare_nessus_with_netbox(comparison_service: ComparisonService):
    """Compare Nessus agents with Netbox devices and VMs"""
    print("\n=== Nessus-Netbox Comparison ===")
    print("1. Individual comparisons (separate device and VM comparisons)")
    print("2. Comprehensive comparison (smart matching with priority)")
    
    sub_choice = input("Select comparison type (1-2): ").strip()
    
    if sub_choice == '1':
        # Compare with devices
        print("\n1. Comparing with Netbox Devices...")
        device_comparison = comparison_service.compare_agents_with_devices()
        comparison_service.print_comparison_summary(device_comparison, "devices")
        
        # Save device comparison results
        if comparison_service.save_comparison_results(device_comparison, "output/device_comparison.json"):
            print("✓ Device comparison saved to output/device_comparison.json")
        
        # Compare with virtual machines
        print("\n2. Comparing with Netbox Virtual Machines...")
        vm_comparison = comparison_service.compare_agents_with_vms()
        comparison_service.print_comparison_summary(vm_comparison, "vms")
        
        # Save VM comparison results
        if comparison_service.save_comparison_results(vm_comparison, "output/vm_comparison.json"):
            print("✓ VM comparison saved to output/vm_comparison.json")
        
        # Generate combined summary
        print("\n=== Combined Summary ===")
        total_agents = device_comparison['summary']['total_agents']
        total_devices = device_comparison['summary']['total_devices']
        total_vms = vm_comparison['summary']['total_vms']
        total_matched = device_comparison['summary']['matched'] + vm_comparison['summary']['matched']
        
        print(f"Total Nessus Agents: {total_agents}")
        print(f"Total Netbox Devices: {total_devices}")
        print(f"Total Netbox VMs: {total_vms}")
        print(f"Total Matched Items: {total_matched}")
        
        if total_agents > 0:
            overall_coverage = (total_matched / total_agents) * 100
            print(f"Overall Coverage: {overall_coverage:.1f}%")
    
    elif sub_choice == '2':
        # Comprehensive comparison
        print("\n=== Comprehensive Comparison ===")
        comprehensive = comparison_service.comprehensive_comparison()
        
        # Print comprehensive summary
        print("\n=== Comprehensive Comparison Summary ===")
        summary = comprehensive['summary']
        print(f"Total Nessus Agents: {summary['total_agents']}")
        print(f"Total Netbox Devices: {summary['total_devices']}")
        print(f"Total Netbox VMs: {summary['total_vms']}")
        print(f"Matched with Devices: {summary['matched_with_devices']}")
        print(f"Matched with VMs: {summary['matched_with_vms']}")
        print(f"Unmatched Agents: {summary['unmatched_agents']}")
        print(f"Unmatched Devices: {summary['unmatched_devices']}")
        print(f"Unmatched VMs: {summary['unmatched_vms']}")
        
        # Print match type analysis
        details = comprehensive['details']
        print(f"\nMatch Type Analysis:")
        print(f"  Hostname Matches: {details['match_type_analysis']['hostname_matches']}")
        print(f"  IP Matches: {details['match_type_analysis']['ip_matches']}")
        
        # Print coverage analysis
        coverage = details['coverage_analysis']
        print(f"\nCoverage Analysis:")
        print(f"  Total Netbox Items: {coverage['total_netbox_items']}")
        print(f"  Total Matched: {coverage['total_matched']}")
        print(f"  Coverage Percentage: {coverage['coverage_percentage']}%")
        print(f"  Unmatched Netbox Items: {coverage['unmatched_netbox_items']}")
        
        print("✓ Comprehensive comparison saved to output/comprehensive_comparison_results.json")
    
    else:
        print("Invalid choice. Please select 1 or 2.")


def search_by_ip_address(nessus_service: NessusService, netbox_service: NetboxService):
    """Search for items by IP address across both systems"""
    print("\n=== Search by IP Address ===")
    ip_address = input("Enter IP address to search: ").strip()
    
    if ip_address:
        # Search in Nessus
        nessus_results = nessus_service.search_agents_by_ip(ip_address)
        
        # Search in Netbox
        netbox_results = netbox_service.search_all_by_ip(ip_address)
        
        # Combine results
        search_results = {
            'ip_address': ip_address,
            'nessus_agents': nessus_results,
            'netbox_devices': netbox_results.get('devices', []),
            'netbox_vms': netbox_results.get('vms', []),
            'total_found': len(nessus_results) + netbox_results.get('total_found', 0),
            'timestamp': datetime.now().isoformat()
        }
        
        # Otomatik kaydet
        output_data = create_output_data_dict(search_results, "ip_search_results")
        save_to_json(output_data, "output/ip_search_results.json")
        
        # Display results
        print(f"\nSearch Results for IP: {ip_address}")
        print(f"Total items found: {search_results['total_found']}")
        
        if nessus_results:
            print(f"\nNessus Agents ({len(nessus_results)}):")
            for agent in nessus_results:
                print(f"  - {agent.get('name', 'Unknown')} ({agent.get('status', 'Unknown')})")
        
        if netbox_results.get('devices'):
            print(f"\nNetbox Devices ({len(netbox_results['devices'])}):")
            for device in netbox_results['devices']:
                print(f"  - {device.get('name', 'Unknown')} ({device.get('status', {}).get('value', 'Unknown')})")
        
        if netbox_results.get('vms'):
            print(f"\nNetbox VMs ({len(netbox_results['vms'])}):")
            for vm in netbox_results['vms']:
                print(f"  - {vm.get('name', 'Unknown')} ({vm.get('status', {}).get('value', 'Unknown')})")
        
        if not search_results['total_found']:
            print("No items found with this IP address.")
    else:
        print("Invalid IP address.")


def main():
    """Main application function"""
    print("Netbox-Nessus Integration Tool")
    print("=" * 40)
    
    # Initialize clients
    print("Initializing clients...")
    clients = initialize_clients()
    
    if not clients:
        print("No valid clients could be initialized. Please check your configuration.")
        sys.exit(1)
    
    # Initialize services
    print("Initializing services...")
    services = initialize_services(clients)
    
    if not services:
        print("No services could be initialized.")
        sys.exit(1)
    
    # Test connections
    if not test_connections(services):
        print("Connection test failed. Please check your configuration.")
        sys.exit(1)
    
    # Main menu
    while True:
        print("\n" + "=" * 40)
        print("Available Operations:")
        print("1. Fetch Nessus Agents")
        print("2. Fetch Netbox Devices")
        print("3. Fetch Netbox Virtual Machines")
        print("4. Compare Nessus with Netbox")
        print("5. Search by IP Address")
        print("6. Sync Nessus Agents to Netbox")
        print("7. Exit")
        
        choice = input("\nSelect operation (1-7): ").strip()
        
        try:
            if choice == '1':
                if 'nessus' in services:
                    fetch_nessus_agents(services['nessus'])
                else:
                    print("Nessus service not available")
            
            elif choice == '2':
                if 'netbox' in services:
                    fetch_netbox_devices(services['netbox'])
                else:
                    print("Netbox service not available")
            
            elif choice == '3':
                if 'netbox' in services:
                    fetch_netbox_vms(services['netbox'])
                else:
                    print("Netbox service not available")
            
            elif choice == '4':
                if 'comparison' in services:
                    compare_nessus_with_netbox(services['comparison'])
                else:
                    print("Both Nessus and Netbox services are required for comparison")
            
            elif choice == '5':
                if 'nessus' in services and 'netbox' in services:
                    search_by_ip_address(services['nessus'], services['netbox'])
                else:
                    print("Both Nessus and Netbox services are required for IP search")
            
            elif choice == '6':
                if 'nessus' in services and 'netbox' in services:
                    sync_nessus_to_netbox(services['nessus'], services['netbox'])
                else:
                    print("Both Nessus and Netbox services are required for sync")
            
            elif choice == '7':
                print("Exiting...")
                break
            
            else:
                print("Invalid choice. Please select 1-7.")
        
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
        except Exception as e:
            print(f"Error during operation: {e}")
    
    # Cleanup
    for client in clients.values():
        client.close()

    # Restore previous config loading logic
    NB_URL = os.environ.get('NETBOX_URL') or 'http://10.19.51.32'
    NB_TOKEN = os.environ.get('NETBOX_TOKEN') or 'YOUR_TOKEN_HERE'
    # Use these variables to initialize NetboxClient and services as before


if __name__ == "__main__":
    main()
    # DEBUG: Fetch and print all VM interfaces with their IPs
    from api.netbox_client import NetboxClient
    import os
    NB_URL = os.environ.get('NETBOX_URL') or 'http://10.19.51.32'
    NB_TOKEN = os.environ.get('NETBOX_TOKEN') or 'YOUR_TOKEN_HERE'
    client = NetboxClient(NB_URL, NB_TOKEN, verify_ssl=False)
    interfaces = client.get_all_vm_interfaces()
    print(f"Total VM interfaces: {len(interfaces)}")
    for iface in interfaces[:10]:
        print({
            'name': iface.get('name'),
            'virtual_machine': iface.get('virtual_machine'),
            'ip_addresses': iface.get('ip_addresses')
        })

    # Use these variables to initialize clients/services
    # Remove all get_config_value lines and config_path/section logic
    # ... existing code ... 