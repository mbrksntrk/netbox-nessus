# Netbox-Nessus Integration Tool

This Python application integrates the Nessus vulnerability scanner with the Netbox network infrastructure management system, enabling automated inventory synchronization, comparison, and reporting.

## Features

### Nessus Integration
- Connects and authenticates with the Nessus API
- Fetches all agents with detailed information
- Filters agents by status and platform
- Retrieves scan results
- Generates agent statistics

### Netbox Integration
- Connects and authenticates with the Netbox API
- Fetches, lists, and manages devices and virtual machines (VMs)
- Filters devices by site and status
- Retrieves all interfaces and IP addresses for devices and VMs
- Generates device and VM statistics

### Integration & Automation
- Synchronizes Nessus agents as Netbox devices (auto-create/update)
- Compares Nessus agents with Netbox devices and VMs (hostname/IP matching)
- Generates comprehensive comparison reports (JSON & HTML)
- Searches both systems by IP address
- Modular, extensible, and interactive CLI

### Reporting
- Saves all fetched and comparison data in JSON format
- Generates detailed HTML reports for devices, VMs, and comparison results
- Output files are stored in the `output/` directory

### Security & Best Practices
- Sensitive data (JSON, HTML, logs, etc.) is excluded from version control via `.gitignore`
- Real credentials and sensitive output files should never be committed to git

## Project Structure

```
netbox-nessus/
├── api/                    # API clients
│   ├── __init__.py
│   ├── base_client.py      # Base API client class
│   ├── nessus_client.py    # Nessus API client
│   └── netbox_client.py    # Netbox API client
├── config/                 # Configuration
│   ├── __init__.py
│   ├── settings.py         # Configuration management
│   └── config.json.example # Example configuration
├── services/               # Business logic layer
│   ├── __init__.py
│   ├── comparison_service.py # Comparison logic
│   ├── nessus_service.py   # Nessus operations
│   └── netbox_service.py   # Netbox operations
├── utils/                  # Utility functions
│   ├── __init__.py
│   ├── config_loader.py    # Config loader
│   ├── helpers.py          # Common helpers
│   └── html_reporter.py    # HTML report generation
├── models/                 # Data models
│   └── __init__.py
├── output/                 # Output files (JSON, HTML, etc.)
├── logs/                   # Log files
├── main.py                 # Main application
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## Installation

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment:**
   ```bash
   # Windows PowerShell
   .\venv\Scripts\Activate.ps1

   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create your configuration file:**
   ```bash
   cp config/config.json.example config/config.json
   ```

5. **Edit `config/config.json` with your credentials:**
   ```json
   {
     "nessus": {
       "base_url": "https://your-nessus-server:8834",
       "access_key": "your-access-key",
       "secret_key": "your-secret-key",
       "verify_ssl": false
     },
     "netbox": {
       "base_url": "https://your-netbox-server",
       "token": "your-netbox-token",
       "verify_ssl": false
     },
     "output": {
       "file": "output/data.json",
       "format": "json"
     },
     "logging": {
       "level": "INFO",
       "file": "logs/app.log"
     }
   }
   ```

## Usage

### Running the Main Application

```bash
python main.py
```

The application provides an interactive menu:

1. **Fetch Nessus Agents** – Retrieve agents from Nessus
2. **Fetch Netbox Devices** – Retrieve devices from Netbox
3. **Fetch Netbox Virtual Machines** – Retrieve VMs from Netbox
4. **Compare Nessus with Netbox** – Compare agents with devices/VMs
5. **Search by IP Address** – Search both systems by IP
6. **Sync Nessus Agents to Netbox** – Synchronize agents as Netbox devices
7. **Exit** – Exit the application

### Using Environment Variables

You can also provide credentials via environment variables:

```bash
# Windows PowerShell
$env:NESSUS_URL="https://your-nessus-server:8834"
$env:NESSUS_ACCESS_KEY="your-access-key"
$env:NESSUS_SECRET_KEY="your-secret-key"
$env:NETBOX_URL="https://your-netbox-server"
$env:NETBOX_TOKEN="your-netbox-token"
python main.py

# Linux/Mac
export NESSUS_URL="https://your-nessus-server:8834"
export NESSUS_ACCESS_KEY="your-access-key"
export NESSUS_SECRET_KEY="your-secret-key"
export NETBOX_URL="https://your-netbox-server"
export NETBOX_TOKEN="your-netbox-token"
python main.py
```

## Obtaining API Keys

### Nessus API Keys
1. Log in to the Nessus web interface
2. Go to **Settings** > **My Account**
3. Click the **API Keys** tab
4. Click **Generate** to create new keys

### Netbox API Token
1. Log in to the Netbox web interface
2. Go to **Admin** > **Users**
3. Select your user
4. Click the **API Tokens** tab
5. Click **Add API Token**

## Output Formats

### Agent Data Example

```json
{
  "timestamp": "2024-01-15T10:30:00.123456",
  "data_type": "agents",
  "total_count": 5,
  "data": [
    {
      "id": 1,
      "name": "Agent-001",
      "status": "online",
      "platform": "Windows",
      "version": "10.5.0",
      "last_connect": "2024-01-15T10:25:00Z",
      "groups": ["Windows Agents"],
      "distro": "Windows 10",
      "uuid": "12345678-1234-1234-1234-123456789012"
    }
  ]
}
```

### Device Data Example

```json
{
  "timestamp": "2024-01-15T10:30:00.123456",
  "data_type": "devices",
  "total_count": 3,
  "data": [
    {
      "id": 1,
      "name": "Server-001",
      "status": {"value": "active"},
      "site": {"name": "Main Site"},
      "device_type": {"model": "Dell PowerEdge"},
      "platform": {"name": "Windows Server 2019"},
      "interfaces": [
        {
          "name": "eth0",
          "ip_addresses": ["10.0.0.1", "10.0.0.2"]
        }
      ]
    }
  ]
}
```

### Comparison Report Example

```json
{
  "timestamp": "2024-01-15T10:30:00.123456",
  "data_type": "comparison",
  "matched": [...],
  "unmatched_agents": [...],
  "unmatched_devices": [...],
  "unmatched_vms": [...],
  "summary": {
    "total_agents": 100,
    "total_devices": 80,
    "total_vms": 20,
    "matched_with_devices": 70,
    "matched_with_vms": 15,
    "unmatched_agents": 15,
    "unmatched_devices": 10,
    "unmatched_vms": 5
  }
}
```

## Advantages of Modular Design

- Easy to extend with new integrations or features
- Clear separation of API, business logic, and utilities
- Simple configuration and deployment

## Security Notice

- **Sensitive data** (JSON, HTML, logs, etc.) is excluded from version control via `.gitignore`.
- Never commit your real credentials or sensitive output files to git.

## Error Handling

The application handles the following scenarios:
- Connection errors
- Authentication errors
- JSON parse errors
- File writing errors
- SSL certificate errors
- API rate limiting

## Security Notes

- Keep your API keys secure
- Do not include sensitive data in version control
- Enable SSL verification in production
- Rotate your API keys regularly
- Use virtual environments

## Development

### Adding a New API
1. Create a new client in the `api/` directory
2. Inherit from `BaseAPIClient`
3. Create a new service in the `services/` directory
4. Add configuration in `config/settings.py`

### Adding a New Feature
1. Add a method to the relevant service file
2. Add a menu option in `main.py`
3. If necessary, add helper functions

## Troubleshooting

### Connection Errors
- Check URLs
- Check firewall settings
- Check SSL certificate settings

### Authentication Errors
- Verify your API keys are correct
- Your API keys may have expired

### Import Errors
- Verify your virtual environment is active
- Verify all required packages are installed

## License

This project is licensed under the MIT License. 