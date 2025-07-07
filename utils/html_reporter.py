"""
HTML Report Generator

Utility for generating beautiful HTML reports from various data sources.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from jinja2 import Template


class HTMLReporter:
    """HTML report generator for various data types"""
    
    def __init__(self):
        """Initialize the HTML reporter"""
        self.template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.output_dir = 'output'
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _format_ip_comparison(self, nessus_ip: str, netbox_ip: str, netbox_all_ips: Optional[List[str]] = None) -> str:
        """
        Format IP address comparison for display
        
        Args:
            nessus_ip: IP address from Nessus
            netbox_ip: Primary IP address from Netbox
            netbox_all_ips: All IP addresses from Netbox (optional)
            
        Returns:
            Formatted HTML string for IP comparison
        """
        if not nessus_ip and not netbox_ip:
            return 'N/A'
        
        if not nessus_ip:
            if netbox_all_ips and len(netbox_all_ips) > 1:
                # Show all Netbox IPs
                ip_list = [f'<span class="ip-netbox-only">{ip}</span>' for ip in netbox_all_ips]
                return '<br>'.join(ip_list)
            else:
                return f'<span class="ip-netbox-only">{netbox_ip}</span>'
        
        if not netbox_ip:
            return f'<span class="ip-nessus-only">{nessus_ip}</span>'
        
        # Clean IP addresses (remove CIDR notation)
        nessus_clean = nessus_ip.split('/')[0] if nessus_ip else ''
        netbox_clean = netbox_ip.split('/')[0] if netbox_ip else ''
        
        if nessus_clean == netbox_clean:
            # Same IP - show only one
            result = f'<span class="ip-match">{nessus_clean}</span>'
            
            # Add additional Netbox IPs if available
            if netbox_all_ips and len(netbox_all_ips) > 1:
                additional_ips = [ip for ip in netbox_all_ips if ip != netbox_clean]
                if additional_ips:
                    additional_html = [f'<span class="ip-netbox-only">{ip}</span>' for ip in additional_ips]
                    result += '<br>' + '<br>'.join(additional_html)
            
            return result
        else:
            # Different IPs - show both in red
            result = f'<span class="ip-mismatch">{nessus_clean}</span> / <span class="ip-mismatch">{netbox_clean}</span>'
            
            # Add additional Netbox IPs if available
            if netbox_all_ips and len(netbox_all_ips) > 1:
                additional_ips = [ip for ip in netbox_all_ips if ip != netbox_clean]
                if additional_ips:
                    additional_html = [f'<span class="ip-netbox-only">{ip}</span>' for ip in additional_ips]
                    result += '<br>' + '<br>'.join(additional_html)
            
            return result
    
    def generate_comparison_report(self, comparison_data: Dict, report_type: str = "comprehensive") -> str:
        """
        Generate HTML report for comparison results
        
        Args:
            comparison_data: Comparison results dictionary
            report_type: Type of comparison (comprehensive, devices, vms)
            
        Returns:
            Path to generated HTML file
        """
        if report_type == "comprehensive":
            return self._generate_comprehensive_comparison_report(comparison_data)
        elif report_type == "devices":
            return self._generate_device_comparison_report(comparison_data)
        elif report_type == "vms":
            return self._generate_vm_comparison_report(comparison_data)
        else:
            raise ValueError(f"Unknown report type: {report_type}")
    
    def generate_fetch_report(self, data: Dict, data_type: str) -> str:
        """
        Generate HTML report for fetch results
        
        Args:
            data: Fetch results data
            data_type: Type of data (agents, devices, vms)
            
        Returns:
            Path to generated HTML file
        """
        return self._generate_fetch_report(data, data_type)
    
    def _generate_comprehensive_comparison_report(self, data: Dict) -> str:
        """Generate comprehensive comparison HTML report"""
        
        # Prepare data for template
        summary = data.get('summary', {})
        details = data.get('details', {})
        
        # Process matched items
        device_matches = data.get('device_matches', [])
        vm_matches = data.get('vm_matches', [])
        
        # Process unmatched items
        unmatched_agents = data.get('unmatched_agents', [])
        unmatched_devices = data.get('unmatched_devices', [])
        unmatched_vms = data.get('unmatched_vms', [])
        
        # Calculate statistics
        total_matches = len(device_matches) + len(vm_matches)
        hostname_matches = details.get('match_type_analysis', {}).get('hostname_matches', 0)
        ip_matches = details.get('match_type_analysis', {}).get('ip_matches', 0)
        
        # Generate HTML
        html_content = self._get_comparison_template().render(
            title="Comprehensive Nessus-Netbox Comparison Report",
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            summary=summary,
            details=details,
            device_matches=device_matches,
            vm_matches=vm_matches,
            unmatched_agents=unmatched_agents,
            unmatched_devices=unmatched_devices,
            unmatched_vms=unmatched_vms,
            total_matches=total_matches,
            hostname_matches=hostname_matches,
            ip_matches=ip_matches,
            report_type="comprehensive",
            format_ip=self._format_ip_comparison
        )
        
        # Save file
        filename = f"comprehensive_comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filepath
    
    def _generate_device_comparison_report(self, data: Dict) -> str:
        """Generate device comparison HTML report"""
        
        summary = data.get('summary', {})
        details = data.get('details', {})
        matched_items = data.get('matched_items', [])
        unmatched_agents = data.get('unmatched_agents', [])
        unmatched_devices = data.get('unmatched_devices', [])
        
        html_content = self._get_comparison_template().render(
            title="Nessus-Netbox Device Comparison Report",
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            summary=summary,
            details=details,
            device_matches=matched_items,
            vm_matches=[],
            unmatched_agents=unmatched_agents,
            unmatched_devices=unmatched_devices,
            unmatched_vms=[],
            total_matches=len(matched_items),
            hostname_matches=len([m for m in matched_items if m.get('match_type') == 'hostname']),
            ip_matches=len([m for m in matched_items if m.get('match_type') == 'ip']),
            report_type="devices",
            format_ip=self._format_ip_comparison
        )
        
        filename = f"device_comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filepath
    
    def _generate_vm_comparison_report(self, data: Dict) -> str:
        """Generate VM comparison HTML report"""
        
        summary = data.get('summary', {})
        details = data.get('details', {})
        matched_items = data.get('matched_items', [])
        unmatched_agents = data.get('unmatched_agents', [])
        unmatched_vms = data.get('unmatched_vms', [])
        
        html_content = self._get_comparison_template().render(
            title="Nessus-Netbox VM Comparison Report",
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            summary=summary,
            details=details,
            device_matches=[],
            vm_matches=matched_items,
            unmatched_agents=unmatched_agents,
            unmatched_devices=[],
            unmatched_vms=unmatched_vms,
            total_matches=len(matched_items),
            hostname_matches=len([m for m in matched_items if m.get('match_type') == 'hostname']),
            ip_matches=len([m for m in matched_items if m.get('match_type') == 'ip']),
            report_type="vms",
            format_ip=self._format_ip_comparison
        )
        
        filename = f"vm_comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filepath
    
    def _generate_fetch_report(self, data: Dict, data_type: str) -> str:
        """Generate fetch results HTML report"""
        
        items = data.get('data', [])
        metadata = data.get('metadata', {})
        
        html_content = self._get_fetch_template().render(
            title=f"Netbox-Nessus {data_type.title()} Fetch Report",
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data_type=data_type,
            items=items,
            metadata=metadata,
            total_count=len(items)
        )
        
        filename = f"{data_type}_fetch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filepath
    
    def _get_comparison_template(self) -> Template:
        """Get comparison report HTML template"""
        template_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header .timestamp {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .summary-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        
        .card h3 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        
        .card .number {
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }
        
        .card .label {
            color: #666;
            font-size: 0.9em;
        }
        
        .section {
            background: white;
            margin-bottom: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        
        .section-header {
            background: #f8f9fa;
            padding: 20px;
            border-bottom: 1px solid #e9ecef;
        }
        
        .section-header h2 {
            color: #333;
            font-size: 1.5em;
        }
        
        .table-container {
            overflow-x: auto;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9em;
        }
        
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e9ecef;
        }
        
        th {
            background-color: #f8f9fa;
            font-weight: 600;
            color: #495057;
        }
        
        tr:hover {
            background-color: #f8f9fa;
        }
        
        .status-online {
            color: #28a745;
            font-weight: bold;
        }
        
        .status-offline {
            color: #dc3545;
            font-weight: bold;
        }
        
        .status-active {
            color: #28a745;
            font-weight: bold;
        }
        
        .status-inactive {
            color: #6c757d;
            font-weight: bold;
        }
        
        .match-hostname {
            background-color: #d4edda;
            color: #155724;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
        }
        
        .match-ip {
            background-color: #d1ecf1;
            color: #0c5460;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
        }
        
        .coverage-high {
            color: #28a745;
        }
        
        .coverage-medium {
            color: #ffc107;
        }
        
        .coverage-low {
            color: #dc3545;
        }
        
        .ip-match {
            color: #28a745;
            font-weight: bold;
        }
        
        .ip-mismatch {
            color: #dc3545;
            font-weight: bold;
        }
        
        .ip-nessus-only {
            color: #007bff;
            font-weight: bold;
        }
        
        .ip-netbox-only {
            color: #6f42c1;
            font-weight: bold;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        
        .stat-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        
        .stat-number {
            font-size: 1.8em;
            font-weight: bold;
            color: #667eea;
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }
        
        .empty-message {
            text-align: center;
            padding: 40px;
            color: #666;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ title }}</h1>
            <div class="timestamp">Generated on {{ timestamp }}</div>
        </div>
        
        <!-- Summary Cards -->
        <div class="summary-cards">
            <div class="card">
                <h3>Total Agents</h3>
                <div class="number">{{ summary.total_agents }}</div>
                <div class="label">Nessus Agents</div>
            </div>
            
            {% if report_type == "comprehensive" %}
            <div class="card">
                <h3>Total Devices</h3>
                <div class="number">{{ summary.total_devices }}</div>
                <div class="label">Netbox Devices</div>
            </div>
            
            <div class="card">
                <h3>Total VMs</h3>
                <div class="number">{{ summary.total_vms }}</div>
                <div class="label">Netbox VMs</div>
            </div>
            
            <div class="card">
                <h3>Total Matched</h3>
                <div class="number">{{ total_matches }}</div>
                <div class="label">Successfully Matched</div>
            </div>
            {% else %}
            <div class="card">
                <h3>Total Items</h3>
                <div class="number">{{ summary.total_devices if report_type == "devices" else summary.total_vms }}</div>
                <div class="label">{{ "Netbox Devices" if report_type == "devices" else "Netbox VMs" }}</div>
            </div>
            
            <div class="card">
                <h3>Matched Items</h3>
                <div class="number">{{ summary.matched }}</div>
                <div class="label">Successfully Matched</div>
            </div>
            
            <div class="card">
                <h3>Unmatched</h3>
                <div class="number">{{ summary.unmatched_agents + (summary.unmatched_devices if report_type == "devices" else summary.unmatched_vms) }}</div>
                <div class="label">Unmatched Items</div>
            </div>
            {% endif %}
        </div>
        
        <!-- Match Type Analysis -->
        <div class="section">
            <div class="section-header">
                <h2>Match Analysis</h2>
            </div>
            <div style="padding: 20px;">
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-number">{{ hostname_matches }}</div>
                        <div class="stat-label">Hostname Matches</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">{{ ip_matches }}</div>
                        <div class="stat-label">IP Matches</div>
                    </div>
                    {% if details.coverage_analysis %}
                    <div class="stat-item">
                        <div class="stat-number">{{ "%.1f"|format(details.coverage_analysis.coverage_percentage) }}%</div>
                        <div class="stat-label">Coverage</div>
                    </div>
                    {% endif %}
                </div>
            </div>
        </div>
        
        <!-- Matched Items -->
        {% if device_matches %}
        <div class="section">
            <div class="section-header">
                <h2>Matched Devices ({{ device_matches|length }})</h2>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Match Type</th>
                            <th>Nessus Status</th>
                            <th>Netbox Status</th>
                            <th>Platform</th>
                            <th>Site/Cluster</th>
                            <th>IP Address</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for match in device_matches %}
                        <tr>
                            <td><strong>{{ match.name }}</strong></td>
                            <td>
                                <span class="match-{{ match.match_type }}">{{ match.match_type.upper() }}</span>
                            </td>
                            <td>
                                <span class="status-{{ match.nessus_agent.status }}">{{ match.nessus_agent.status.upper() }}</span>
                            </td>
                            <td>
                                <span class="status-{{ match.netbox_device.status if match.netbox_device.status else 'inactive' }}">
                                    {{ match.netbox_device.status.upper() if match.netbox_device.status else 'N/A' }}
                                </span>
                            </td>
                            <td>{{ match.nessus_agent.platform }} / {{ match.netbox_device.platform or 'N/A' }}</td>
                            <td>{{ match.netbox_device.site or 'N/A' }}</td>
                            <td>{{ format_ip(match.nessus_agent.ip, match.netbox_device.primary_ip, match.netbox_device.all_ips) | safe }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        {% endif %}
        
        {% if vm_matches %}
        <div class="section">
            <div class="section-header">
                <h2>Matched VMs ({{ vm_matches|length }})</h2>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Match Type</th>
                            <th>Nessus Status</th>
                            <th>Netbox Status</th>
                            <th>Platform</th>
                            <th>Cluster</th>
                            <th>Site</th>
                            <th>Resources</th>
                            <th>Interfaces</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for match in vm_matches %}
                        <tr>
                            <td><strong>{{ match.name }}</strong></td>
                            <td>
                                <span class="match-{{ match.match_type }}">{{ match.match_type.upper() }}</span>
                            </td>
                            <td>
                                <span class="status-{{ match.nessus_agent.status }}">{{ match.nessus_agent.status.upper() }}</span>
                            </td>
                            <td>
                                <span class="status-{{ match.netbox_vm.status if match.netbox_vm.status else 'inactive' }}">
                                    {{ match.netbox_vm.status.upper() if match.netbox_vm.status else 'N/A' }}
                                </span>
                            </td>
                            <td>{{ match.nessus_agent.platform }} / {{ match.netbox_vm.platform or 'N/A' }}</td>
                            <td>{{ match.netbox_vm.cluster or 'N/A' }}</td>
                            <td>{{ match.netbox_vm.site or 'N/A' }}</td>
                            <td>{{ match.netbox_vm.vcpus or 'N/A' }} vCPU, {{ match.netbox_vm.memory or 'N/A' }} MB</td>
                            <td>
                                {% set interfaces = match.netbox_vm.interfaces if match.netbox_vm and match.netbox_vm.interfaces is defined else [] %}
                                {% if interfaces|length == 1 %}
                                    <div>
                                        <strong>{{ interfaces[0].name }}</strong>
                                        {% if interfaces[0].ip_addresses %}
                                            <ul style="margin:0; padding-left:15px;">
                                            {% for ip in interfaces[0].ip_addresses %}
                                                <li>{{ ip.address }}</li>
                                            {% endfor %}
                                            </ul>
                                        {% else %}
                                            <span style="color:#888;">No IP</span>
                                        {% endif %}
                                    </div>
                                {% elif interfaces|length > 1 %}
                                    <button class="accordion-btn" onclick="toggleAccordion('acc-{{ loop.index0 }}')">Show Interfaces ({{ interfaces|length }})</button>
                                    <div id="acc-{{ loop.index0 }}" class="accordion-content" style="display:none;">
                                        <ul style="margin:0; padding-left:15px;">
                                        {% for iface in interfaces %}
                                            <li>
                                                <strong>{{ iface.name }}</strong>
                                                {% if iface.ip_addresses %}
                                                    <ul style="margin:0; padding-left:15px;">
                                                    {% for ip in iface.ip_addresses %}
                                                        <li>{{ ip.address }}</li>
                                                    {% endfor %}
                                                    </ul>
                                                {% else %}
                                                    <span style="color:#888;">No IP</span>
                                                {% endif %}
                                            </li>
                                        {% endfor %}
                                        </ul>
                                    </div>
                                {% else %}
                                    <span style="color:#888;">No Interface</span>
                                {% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        <script>
        function toggleAccordion(id) {
            var el = document.getElementById(id);
            if (el.style.display === "none") {
                el.style.display = "block";
            } else {
                el.style.display = "none";
            }
        }
        </script>
        <style>
        .accordion-btn {
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 4px 10px;
            cursor: pointer;
            font-size: 0.95em;
            margin-bottom: 4px;
        }
        .accordion-btn:hover {
            background: #4b5bdc;
        }
        .accordion-content {
            background: #f8f9fa;
            border-radius: 5px;
            margin-top: 4px;
            padding: 6px 10px;
        }
        </style>
        {% endif %}
        
        <!-- Unmatched Items -->
        {% if unmatched_agents %}
        <div class="section">
            <div class="section-header">
                <h2>Unmatched Agents ({{ unmatched_agents|length }})</h2>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Status</th>
                            <th>Platform</th>
                            <th>Version</th>
                            <th>IP Address</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for agent in unmatched_agents %}
                        <tr>
                            <td><strong>{{ agent.name }}</strong></td>
                            <td>
                                <span class="status-{{ agent.status }}">{{ agent.status.upper() }}</span>
                            </td>
                            <td>{{ agent.platform }}</td>
                            <td>{{ agent.version }}</td>
                            <td>{{ agent.ip or 'N/A' }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        {% endif %}
        
        {% if unmatched_devices %}
        <div class="section">
            <div class="section-header">
                <h2>Unmatched Devices ({{ unmatched_devices|length }})</h2>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Status</th>
                            <th>Platform</th>
                            <th>Site</th>
                            <th>Interfaces</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for device in unmatched_devices %}
                        <tr>
                            <td><strong>{{ device.name }}</strong></td>
                            <td>
                                <span class="status-{{ device.status if device.status else 'inactive' }}">
                                    {{ device.status.upper() if device.status else 'N/A' }}
                                </span>
                            </td>
                            <td>{{ device.platform or 'N/A' }}</td>
                            <td>{{ device.site or 'N/A' }}</td>
                            <td>
                                {% set interfaces = device.interfaces if device.interfaces is defined else [] %}
                                {% if interfaces|length == 1 %}
                                    <div>
                                        <strong>{{ interfaces[0].name }}</strong>
                                        {% if interfaces[0].ip_addresses %}
                                            <ul style="margin:0; padding-left:15px;">
                                            {% for ip in interfaces[0].ip_addresses %}
                                                <li>{{ ip.address }}</li>
                                            {% endfor %}
                                            </ul>
                                        {% else %}
                                            <span style="color:#888;">No IP</span>
                                        {% endif %}
                                    </div>
                                {% elif interfaces|length > 1 %}
                                    <button class="accordion-btn" onclick="toggleAccordion('dev-acc-{{ loop.index0 }}')">Show Interfaces ({{ interfaces|length }})</button>
                                    <div id="dev-acc-{{ loop.index0 }}" class="accordion-content" style="display:none;">
                                        <ul style="margin:0; padding-left:15px;">
                                        {% for iface in interfaces %}
                                            <li>
                                                <strong>{{ iface.name }}</strong>
                                                {% if iface.ip_addresses %}
                                                    <ul style="margin:0; padding-left:15px;">
                                                    {% for ip in iface.ip_addresses %}
                                                        <li>{{ ip.address }}</li>
                                                    {% endfor %}
                                                    </ul>
                                                {% else %}
                                                    <span style="color:#888;">No IP</span>
                                                {% endif %}
                                            </li>
                                        {% endfor %}
                                        </ul>
                                    </div>
                                {% else %}
                                    <span style="color:#888;">No Interface</span>
                                {% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        {% endif %}
        
        {% if unmatched_vms %}
        <div class="section">
            <div class="section-header">
                <h2>Unmatched VMs ({{ unmatched_vms|length }})</h2>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Status</th>
                            <th>Platform</th>
                            <th>Cluster</th>
                            <th>Site</th>
                            <th>Interfaces</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for vm in unmatched_vms %}
                        <tr>
                            <td><strong>{{ vm.name }}</strong></td>
                            <td>
                                <span class="status-{{ vm.status if vm.status else 'inactive' }}">
                                    {{ vm.status.upper() if vm.status else 'N/A' }}
                                </span>
                            </td>
                            <td>{{ vm.platform or 'N/A' }}</td>
                            <td>{{ vm.cluster or 'N/A' }}</td>
                            <td>{{ vm.site or 'N/A' }}</td>
                            <td>
                                {% set interfaces = vm.interfaces if vm.interfaces is defined else [] %}
                                {% if interfaces|length == 1 %}
                                    <div>
                                        <strong>{{ interfaces[0].name }}</strong>
                                        {% if interfaces[0].ip_addresses %}
                                            <ul style="margin:0; padding-left:15px;">
                                            {% for ip in interfaces[0].ip_addresses %}
                                                <li>{{ ip.address }}</li>
                                            {% endfor %}
                                            </ul>
                                        {% else %}
                                            <span style="color:#888;">No IP</span>
                                        {% endif %}
                                    </div>
                                {% elif interfaces|length > 1 %}
                                    <button class="accordion-btn" onclick="toggleAccordion('vm-acc-{{ loop.index0 }}')">Show Interfaces ({{ interfaces|length }})</button>
                                    <div id="vm-acc-{{ loop.index0 }}" class="accordion-content" style="display:none;">
                                        <ul style="margin:0; padding-left:15px;">
                                        {% for iface in interfaces %}
                                            <li>
                                                <strong>{{ iface.name }}</strong>
                                                {% if iface.ip_addresses %}
                                                    <ul style="margin:0; padding-left:15px;">
                                                    {% for ip in iface.ip_addresses %}
                                                        <li>{{ ip.address }}</li>
                                                    {% endfor %}
                                                    </ul>
                                                {% else %}
                                                    <span style="color:#888;">No IP</span>
                                                {% endif %}
                                            </li>
                                        {% endfor %}
                                        </ul>
                                    </div>
                                {% else %}
                                    <span style="color:#888;">No Interface</span>
                                {% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        {% endif %}
        
        <!-- Empty state messages -->
        {% if not device_matches and not vm_matches %}
        <div class="section">
            <div class="empty-message">
                <h3>No Matches Found</h3>
                <p>No items were successfully matched between Nessus and Netbox.</p>
            </div>
        </div>
        {% endif %}
        
        {% if not unmatched_agents and not unmatched_devices and not unmatched_vms %}
        <div class="section">
            <div class="empty-message">
                <h3>Perfect Match!</h3>
                <p>All items were successfully matched. No unmatched items found.</p>
            </div>
        </div>
        {% endif %}
    </div>
</body>
</html>
        """
        return Template(template_content)
    
    def _get_fetch_template(self) -> Template:
        """Get fetch report HTML template"""
        template_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header .timestamp {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .summary-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            text-align: center;
            margin-bottom: 30px;
        }
        
        .summary-card h3 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        
        .summary-card .number {
            font-size: 3em;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }
        
        .summary-card .label {
            color: #666;
            font-size: 1.1em;
        }
        
        .section {
            background: white;
            margin-bottom: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        
        .section-header {
            background: #f8f9fa;
            padding: 20px;
            border-bottom: 1px solid #e9ecef;
        }
        
        .section-header h2 {
            color: #333;
            font-size: 1.5em;
        }
        
        .table-container {
            overflow-x: auto;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9em;
        }
        
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e9ecef;
        }
        
        th {
            background-color: #f8f9fa;
            font-weight: 600;
            color: #495057;
        }
        
        tr:hover {
            background-color: #f8f9fa;
        }
        
        .status-online {
            color: #28a745;
            font-weight: bold;
        }
        
        .status-offline {
            color: #dc3545;
            font-weight: bold;
        }
        
        .status-active {
            color: #28a745;
            font-weight: bold;
        }
        
        .status-inactive {
            color: #6c757d;
            font-weight: bold;
        }
        
        .empty-message {
            text-align: center;
            padding: 40px;
            color: #666;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ title }}</h1>
            <div class="timestamp">Generated on {{ timestamp }}</div>
        </div>
        
        <!-- Summary Card -->
        <div class="summary-card">
            <h3>Total {{ data_type.title() }}</h3>
            <div class="number">{{ total_count }}</div>
            <div class="label">Items Retrieved</div>
        </div>
        
        <!-- Data Table -->
        <div class="section">
            <div class="section-header">
                <h2>{{ data_type.title() }} Details ({{ total_count }})</h2>
            </div>
            <div class="table-container">
                {% if data_type == "agents" %}
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Status</th>
                            <th>Platform</th>
                            <th>Version</th>
                            <th>Last Connect</th>
                            <th>IP Address</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for item in items %}
                        <tr>
                            <td><strong>{{ item.name }}</strong></td>
                            <td>
                                <span class="status-{{ item.status }}">{{ item.status.upper() }}</span>
                            </td>
                            <td>{{ item.platform }}</td>
                            <td>{{ item.version }}</td>
                            <td>{{ item.last_connect or 'N/A' }}</td>
                            <td>{{ item.ip or 'N/A' }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% elif data_type == "devices" %}
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Status</th>
                            <th>Site</th>
                            <th>Platform</th>
                            <th>Device Type</th>
                            <th>Primary IP</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for item in items %}
                        <tr>
                            <td><strong>{{ item.name }}</strong></td>
                            <td>
                                <span class="status-{{ item.status.value if item.status else 'inactive' }}">
                                    {{ item.status.value.upper() if item.status else 'N/A' }}
                                </span>
                            </td>
                            <td>{{ item.site.name if item.site else 'N/A' }}</td>
                            <td>{{ item.platform.name if item.platform else 'N/A' }}</td>
                            <td>{{ item.device_type.model if item.device_type else 'N/A' }}</td>
                            <td>{{ item.primary_ip.address if item.primary_ip else 'N/A' }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% elif data_type == "vms" %}
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Status</th>
                            <th>Cluster</th>
                            <th>Site</th>
                            <th>Platform</th>
                            <th>vCPUs</th>
                            <th>Memory (MB)</th>
                            <th>Disk (GB)</th>
                            <th>Primary IP</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for item in items %}
                        <tr>
                            <td><strong>{{ item.name }}</strong></td>
                            <td>
                                <span class="status-{{ item.status.value if item.status else 'inactive' }}">
                                    {{ item.status.value.upper() if item.status else 'N/A' }}
                                </span>
                            </td>
                            <td>{{ item.cluster.name if item.cluster else 'N/A' }}</td>
                            <td>{{ item.site.name if item.site else 'N/A' }}</td>
                            <td>{{ item.platform.name if item.platform else 'N/A' }}</td>
                            <td>{{ item.vcpus or 'N/A' }}</td>
                            <td>{{ item.memory or 'N/A' }}</td>
                            <td>{{ item.disk or 'N/A' }}</td>
                            <td>{{ item.primary_ip.address if item.primary_ip else 'N/A' }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% endif %}
            </div>
        </div>
        
        {% if not items %}
        <div class="section">
            <div class="empty-message">
                <h3>No Data Found</h3>
                <p>No {{ data_type }} were retrieved from the system.</p>
            </div>
        </div>
        {% endif %}
    </div>
</body>
</html>
        """
        return Template(template_content) 