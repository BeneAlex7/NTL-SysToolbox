# NTL-SysToolbox - Installation and User Manual (Linux)

**Version:** 1.0.0
**Target Audience:** Information Systems Department (ISD)
**Purpose:** Deployment and exploitation procedure for the NTL audit and diagnostic tool on Linux.

---

## 1. Technical Prerequisites

To ensure the full operation of all modules, the host machine must have:
* **Operating System:** Ubuntu 20.04+, Debian 11+, RHEL 8/9, or CentOS Stream.
* **Python:** Version 3.8 or higher with the `venv` module.
* **Nmap:** Installed via the package manager (Required for the Network Scan module).
* **Permissions:** `sudo` or `root` access is required for the network scanner (OS Fingerprinting).

## 2. Installation

1. **Installing system dependencies**
* **Debian / Ubuntu:**
```bash
sudo apt update
sudo apt install python3 python3-venv nmap mariadb-client -y
```
*(mariadb-client or default-mysql-client is useful if you run mysqldump locally)*

* **RHEL / CentOS / Fedora:**
```bash
sudo dnf install python3 nmap mariadb -y
```

2. **Fetching sources**
Unzip the file and go to the directory:
```bash
tar -xzf NTL-SysToolbox.zip
cd NTL-SysToolbox
```

3. **Initializing the virtual environment**
This step isolates Python libraries.
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Configuration & Security

The application uses a `config.yaml` file. A **Vault** system is integrated to protect credentials and passwords.

### A. Infrastructure Configuration
The `config.yaml` file defines alert thresholds, network ranges for auditing, and the list of your servers (Windows, Linux, AD/DNS, WMS).

**To add a new machine for diagnostics:**
Open `config.yaml` and append an entry under `infrastructure.windows_servers` or `infrastructure.linux_servers`:
```yaml
infrastructure:
  linux_servers:
    - { ip: "192.168.10.50", name: "NEW-SRV", os: "ubuntu", secret_ref: "new_srv_ssh" }
```
*The `secret_ref` field links the server to its authentication credentials defined in the Vault.*

### B. Secret Management (Vault)
To secure credentials (like `new_srv_ssh` above):
1. Fill in all connection information in the `secret.yaml` file:
```yaml
new_srv_ssh:
  user: "admin_user"
  password: "SuperPassword123"
```
2. Launch the tool and choose the **[6] Encrypt Vault** option.
3. Set a password. The file is encrypted into `secret.yaml.enc` and the original `secret.yaml` is **deleted**.
4. This master password will be required to decrypt the configuration in memory upon each use.

*(Note: If you need to add a new secret later, you must first use **[7] Decrypt Vault**, edit `secret.yaml`, and encrypt it again with **[6] Encrypt Vault**).*

## 4. Interactive Mode Usage (CLI Menu)

Startup:
```bash
# Using 'sudo' is recommended to unlock the Network Scan component.
sudo ./.venv/bin/python3 main.py
```

**Available Options:**
1. **OS Lifecycle Information:** EOL (End of Life) API query to identify the end of support for one or more systems.
2. **Audit Obsolescence (CSV):** Lifecycle analysis based on the provided inventory (`inventory.csv`).
3. **Network Scan & OS Detection:** Network mapping via Nmap and OS detection.
4. **System Diagnostic:** Powerful diagnostic tool to check:
   - AD / DNS (Verification of ports 53, 389, 636)
   - MySQL (Connection to the WMS database)
   - System Metrics (CPU, RAM, Disk load, and uptime verification via WinRM/SSH)
5. **WMS Backup Menu:** Business backup utility for the WMS database:
   - Full SQL Export (Via `mysqldump` executed on the remote machine)
   - Direct CSV export of a specific table
6. **Encrypt Vault:** Encrypt the configuration.
7. **Decrypt Vault:** Decrypt the configuration.
8. **Exit:** Quit the tool.

## 5. Automated Mode (Command Line)

Ideal for scheduled tasks (via cron) or continuous integration, `main.py` accepts various startup arguments to bypass the menu.

**Action parameter (`--action`):** 
`audit_os`, `audit_csv`, `audit_network`, `diag_ad`, `diag_mysql`, `diag_metrics`, `diag_all`, `backup_sql`, `backup_csv`

**Additional arguments:**
* `--targets`: Target IP addresses separated by commas (e.g., `192.168.1.10,192.168.1.11`). Useful for filtering diagnostics to specific servers.
* `--table`: Name of the SQL table to target (required for `backup_csv`).
* `--vault-password`: Vault password (passed without user prompt).
* `--json`: Generates output strictly in JSON format, ideal for parsing.

**Automation examples:**
```bash
# Full metrics diagnostic for the entire infrastructure, returned in JSON
sudo ./.venv/bin/python3 main.py --action diag_all --vault-password "MyPass" --json

# Trigger remote SQL backup
./.venv/bin/python3 main.py --action backup_sql --vault-password "MyPass"
```

## 6. Locating Reports and Backups

- **JSON Network Audit Reports:** `./audit/data/` (by default)
- **CSV Network Audit Reports:** `./data/audit/csv/`
- **WMS Backups:** `./data/backups/`

Final files are timestamped (e.g., `network_scan_20261010_1430.csv`) to ensure traceability.
