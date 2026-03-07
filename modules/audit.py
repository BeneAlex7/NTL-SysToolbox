from datetime import datetime
import requests
import nmap
from rich.console import Console
from rich.table import Table
from rich import box
import io
import csv
import json
import os

def format_table(data, os_names_list, mode=1):
    """
    MODE 1: General Info
    MODE 2: Obsolescence Audit
    MODE 3: Network Scan Results
    """
    
    console = Console(file=io.StringIO(), force_terminal=True, width=120)

    # Ensure os_names_list is a list to avoid indexing errors
    if isinstance(os_names_list, str):
        labels = [os_names_list] * len(data)
    else:
        labels = os_names_list

    for i, content in enumerate(data):
        # Label management
        current_label = labels[i] if i < len(labels) else "Target"
        display_label = str(current_label).upper()

        # MODE 1: GENERAL OS INFO
        if mode == 1:
            table = Table(
                title=f"OS INFO: {display_label}", 
                box=box.ROUNDED, 
                header_style="bold cyan"
            )
            table.add_column("Code Name", style="dim", width=25)
            table.add_column("Main Version", justify="center")
            table.add_column("End of Life", justify="center")
            table.add_column("Latest Version", justify="center")

            if not content:
                table.add_row("N/A", "N/A", "No data found", "N/A")
            
            for row in content:
                codename = str(row.get('codename') or display_label)
                cycle = str(row.get('cycle') or "")
                support = str(row.get('support') or "")
                latest = str(row.get('latest') or "")
                table.add_row(codename, cycle, support, latest)

        # MODE 2: AUDIT & RISK ASSESSMENT
        elif mode == 2:
            table = Table(
                title=f"AUDIT REPORT: {display_label}", 
                box=box.ROUNDED,       
                header_style="bold cyan" 
            )
            table.add_column("Status", justify="center", style="bold")
            table.add_column("Version", justify="center")
            table.add_column("EOL Date", justify="center")
            table.add_column("Remaining Days", justify="center")

            if not content:
                 table.add_row("[grey]?[/grey]", "Unknown", "N/A", "-")

            for row in content:
                # 1. Data extraction
                eol_date_str = row.get('eolFrom')
                is_eol = row.get('isEol')
                version_name = str(row.get('name') or "N/A")

                # 2. Time delta calculation
                days_left = "N/A"
                if eol_date_str:
                    try:
                        eol_dt = datetime.strptime(eol_date_str, "%Y-%m-%d")
                        today = datetime.now()
                        delta = eol_dt - today
                        days_left = delta.days
                    except ValueError:
                        days_left = "?"

                # 3. User-defined Risk Logic
                if is_eol is True or (isinstance(days_left, int) and days_left < 0):
                    # EXPIRED (Violet)
                    status_display = "[bold white on violet] EXPIRED [/bold white on violet]"
                    date_display = f"[violet]{eol_date_str}[/violet]"
                    days_display = "0"
                    
                elif isinstance(days_left, int):
                    if days_left < 180: # Critical: Less than 6 months -> RED
                        status_display = "[bold white on red] CRITICAL [/bold white on red]"
                        date_display = f"[red]{eol_date_str}[/red]"
                        days_display = f"[red]{days_left} d[/red]"
                        
                    elif days_left < 365: # Warning: Less than 1 year -> ORANGE
                        status_display = "[bold black on orange3] WARNING [/bold black on orange3]"
                        date_display = f"[orange3]{eol_date_str}[/orange3]"
                        days_display = f"[orange3]{days_left} d[/orange3]"
                        
                    else: # Supported: More than 1 year -> GREEN
                        status_display = "[bold black on green] SUPPORTED [/bold black on green]"
                        date_display = f"[green]{eol_date_str}[/green]"
                        days_display = f"[green]{days_left} d[/green]"
                else:
                    status_display = "[grey]UNKNOWN[/grey]"
                    date_display = str(eol_date_str)
                    days_display = "-"

                table.add_row(status_display, version_name, date_display, days_display)

        # MODE 3: NETWORK SCAN (NMAP)
        elif mode == 3:
            table = Table(
                title=f"NETWORK SCAN: {display_label}", 
                box=box.ROUNDED, 
                header_style="bold cyan"
            )
            table.add_column("IP Address", style="bold green", justify="left")
            table.add_column("MAC Address", justify="center")
            table.add_column("Vendor", style="dim")
            table.add_column("OS Detection (Best Guess)", style="bold yellow")

            if not content:
                table.add_row("-", "-", "-", "[red]No hosts found or permission denied[/red]")
            
            for host in content:
                ip = host.get('ip')
                mac = host.get('mac', 'Unknown')
                vendor = host.get('vendor', '')
                
                # Retrieve the first OS match found by Nmap
                os_guess = host.get('os_matches', [{'name': 'Unknown'}])[0]['name']
                accuracy = host.get('os_matches', [{'accuracy': '0'}])[0]['accuracy']
                
                # Format OS display with accuracy percentage
                os_display = f"{os_guess} ({accuracy}%)" if os_guess != 'Unknown' else "[dim]Detection failed[/dim]"
                
                table.add_row(ip, mac, vendor, os_display)

        else:
             console.print(f"[red]Mode {mode} not recognized[/red]")
             continue

        console.print(table)
        console.print("\n")

    return console.file.getvalue()

def run(config):
    """Main module entry point complying with the interface contract."""
    # Retrieve target OS from config
    os_name = config.get('audit', {}).get('target_os', 'windows')
    # Standardize target_os as a list
    if isinstance(os_name, str):
        os_name = [os_name]

    key_dict = ['codename', 'support', 'latest', 'cycle']
    all_filtered_data = []
    
    for target_os in os_name:
        url = f"https://endoflife.date/api/{target_os.lower()}.json"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            response_json = response.json()
            filtered_data = []
            for item in response_json:
                new_mini_dict = {}
                for value in key_dict:
                    if value in item:
                        new_mini_dict[value] = item.get(value)
                filtered_data.append(new_mini_dict)
            all_filtered_data.append(filtered_data)
        except requests.RequestException as e:
            return {
                "module": "audit_obsolescence",
                "status": "ERROR",
                "code": 1,
                "target": os_name,
                "data": {},
                "message": f"API Request failed for {target_os}: {str(e)}"
            }
        except ValueError as e:
            return {
                "module": "audit_obsolescence",
                "status": "ERROR",
                "code": 1,
                "target": os_name,
                "data": {},
                "message": f"Invalid JSON response for {target_os}: {str(e)}"
            }
            
    return {
        "module": "audit_obsolescence",
        "status": "OK",
        "code": 0,
        "target": os_name,
        "data": all_filtered_data,
        "message": f"\n{format_table(all_filtered_data, os_name, mode=1)}" 
    }

def eol_csv(config):
    """Audit module using a CSV file and mapping dictionary."""
    csv_path = config.get('audit', {}).get('csv_path', {})
    mapping_os_dict = config.get('audit', {}).get('mapping_os', {})
    print(mapping_os_dict)
    key_dict = ['name', 'eolFrom', 'isEol', 'eoasFrom', 'isMaintained', 'isEoes']
    final_list = []
    
    try:
        with open(csv_path, mode='r') as file:
            csvFile = csv.reader(file, delimiter=';')
            next(csvFile)
            for lines in csvFile:
                if not lines: continue
                os_name = lines[0].strip()
                os_version = lines[1].strip()
                map_os = f"{os_name} {os_version}"
                mapped_val = mapping_os_dict.get(map_os)
                if mapped_val:
                    final_list.append(mapped_val)
    except Exception as e:
        return {
            "module": "audit_obsolescence",
            "status": "ERROR",
            "code": 1,
            "message": f"CSV reading error: {str(e)}"
        }

    all_filtered_data = []
    for info in final_list:
        info_about_os = info.split(":")
        url = f"https://endoflife.date/api/v1/products/{info_about_os[0]}/releases/{info_about_os[1]}"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            result_data = response.json().get('result', {})
            filtered_data = []
            new_mini_dict = {}
            
            for value in key_dict:
                new_mini_dict[value] = result_data.get(value)
            
            filtered_data.append(new_mini_dict)
            all_filtered_data.append(filtered_data)

        except Exception:
            all_filtered_data.append([]) 

    return {
        "module": "audit_obsolescence",
        "status": "OK",
        "code": 0,
        "target": final_list,
        "data": all_filtered_data,
        "message": f"\n{format_table(all_filtered_data, final_list, mode=2)}"
    }

def scan_network(config):
    """
    Module 3: Scans a complete network range to list components and identify OS.
    Requires Root/Admin privileges for OS detection.
    """

    # 1. Retrieve config and paths
    raw_targets = config.get('audit', {}).get('network_range', '192.168.10.0/24')
    
    audit_path_json = config.get('audit', {}).get('audit_obsolescence_doc_path', 'audit/data')
    audit_path_csv = config.get('audit', {}).get('audit_obsolescence_doc_path_csv', 'data/audit/csv')

    # 2. TYPE CORRECTION
    if isinstance(raw_targets, list):
        target_range = " ".join(raw_targets)
    else:
        target_range = str(raw_targets)

    nm = nmap.PortScanner()
    scan_results = []
    
    print(f"[INFO] Scanning target: {target_range} ... (This might take a while)")

    try:
        # -O: OS Detection (Requires Root) | -T4: (Faster)
        nm.scan(hosts=target_range, arguments='-O --osscan-guess -T4')
        
        hosts_data = []
        for host in nm.all_hosts():
            # Safely retrieve MAC address
            mac_address = nm[host]['addresses'].get('mac', 'N/A')
            
            # Handle Vendor info
            vendor_info = 'Unknown'
            if 'vendor' in nm[host] and nm[host]['vendor']:
                vendor_info = list(nm[host]['vendor'].values())[0]

            # Handle OS Match
            os_matches = nm[host].get('osmatch', [])
            
            host_info = {
                'ip': host,
                'mac': mac_address,
                'vendor': vendor_info,
                'os_matches': os_matches
            }
            hosts_data.append(host_info)
            
        scan_results.append(hosts_data)

    except Exception as e:
        return {
            "module": "audit_network",
            "status": "ERROR",
            "code": 1,
            "target": target_range,
            "data": {},
            "message": f"Nmap Scan Error: {str(e)} (Check permissions or path)"
        }

    # REPORT GENERATION
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 3. Automatic JSON Reporting
    if not os.path.exists(audit_path_json):
        try: os.makedirs(audit_path_json)
        except OSError: audit_path_json = "."

    json_filename = os.path.join(audit_path_json, f"network_scan_{timestamp}.json")
    try:
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(), 
                "target": target_range, 
                "host_count": len(hosts_data),
                "results": hosts_data
            }, f, indent=4)
    except Exception as e:
        print(f"[WARN] Could not save JSON report: {e}")

    # 4. Automatic CSV Reporting
    if not os.path.exists(audit_path_csv):
        try: os.makedirs(audit_path_csv)
        except OSError: audit_path_csv = "."

    csv_filename = os.path.join(audit_path_csv, f"network_scan_{timestamp}.csv")
    try:
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['IP Address', 'MAC Address', 'Vendor', 'OS Best Guess', 'OS Accuracy']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')

            writer.writeheader()
            for host in hosts_data:
                best_os = "Unknown"
                accuracy = "0"
                if host['os_matches']:
                    best_os = host['os_matches'][0]['name']
                    accuracy = host['os_matches'][0]['accuracy']

                writer.writerow({
                    'IP Address': host['ip'],
                    'MAC Address': host['mac'],
                    'Vendor': host['vendor'],
                    'OS Best Guess': best_os,
                    'OS Accuracy': f"{accuracy}%"
                })
    except Exception as e:
        print(f"[WARN] Could not save CSV report: {e}")

    return {
        "module": "audit_network",
        "status": "OK",
        "code": 0,
        "target": target_range,
        "data": scan_results, 
        "message": f"\n{format_table(scan_results, [target_range], mode=3)}\nReports saved:\n- JSON: {json_filename}\n- CSV:  {csv_filename}"
    }