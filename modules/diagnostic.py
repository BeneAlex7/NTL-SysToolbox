import socket
import os
import re
import paramiko
import winrm
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
import mysql.connector
from mysql.connector import Error as MySQLError

def test_port(ip, port, timeout=2):
    """Test if a port is open on a given IP."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((ip, port))
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

def check_ad_dns(ad_list):
    """Check DNS (53) and LDAP (389, 636) for a list of AD servers."""
    results = []
    all_ok = True
    for ad in ad_list:
        ip = ad.get("ip")
        name = ad.get("name")
        dns_ok = test_port(ip, 53)
        ldap_ok = test_port(ip, 389) or test_port(ip, 636)
        
        status = "OK" if dns_ok and ldap_ok else "CRITICAL"
        if status != "OK":
            all_ok = False
            
        results.append({
            "name": name,
            "ip": ip,
            "dns_53": dns_ok,
            "ldap_389_636": ldap_ok,
            "status": status
        })
    return results, all_ok

def check_mysql(config):
    """Check connectivity to MySQL database."""
    db_config = config.get("infrastructure", {}).get("wms", {})
    db_ip = db_config.get("db_ip", "127.0.0.1")
    db_name = db_config.get("db_name", "wms_prod")
    
    # Needs auth from config or environment variables
    # We will assume credentials are merged into config by config_loader from vault or env
    db_user = config.get("wms_db_user", "root")
    db_password = config.get("wms_db_password", "")
    
    try:
        connection = mysql.connector.connect(
            host=db_ip,
            user=db_user,
            password=db_password,
            database=db_name,
            connection_timeout=5
        )
        if connection.is_connected():
            connection.close()
            return {"status": "OK", "host": db_ip, "db": db_name, "message": "Connection successful"}, True
    except MySQLError as e:
        return {"status": "CRITICAL", "host": db_ip, "db": db_name, "message": str(e)}, False
    except Exception as e:
        return {"status": "CRITICAL", "host": db_ip, "db": db_name, "message": str(e)}, False

def get_system_metrics(targets, config, thresholds):
    """Retrieve system metrics from selected remote Linux and Windows servers."""
    results = []
    all_ok = True
    
    cpu_thresh = thresholds.get("cpu_percent", 90)
    ram_thresh = thresholds.get("ram_percent", 85)
    disk_thresh = thresholds.get("disk_percent", 90)

    for server in targets:
        ip = server.get("ip")
        name = server.get("name")
        os_type = str(server.get("os")).lower()
        secret_ref = server.get("secret_ref")
        
        credentials = config.get(secret_ref, {})
        user = credentials.get("user")
        password = credentials.get("password")
        
        if not all([ip, user, password]):
            results.append({
                "name": name,
                "ip": ip,
                "status": "CRITICAL",
                "message": "Missing credentials or IP"
            })
            all_ok = False
            continue
            
        if os_type == "windows":
            try:
                session = winrm.Session(ip, auth=(user, password), transport='ntlm')
                
                # --- CPU (Remis en place + Correction virgule) ---
                rs = session.run_ps("(Get-WmiObject -Class Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average")
                cpu_output = rs.std_out.decode('utf-8').strip()
                cpu_usage = float(cpu_output.replace(',', '.').strip()) if cpu_output else 0.0
                
                # --- RAM (Déjà là, vérifie le nettoyage) ---
                rs = session.run_ps("$os = Get-WmiObject -Class Win32_OperatingSystem; [math]::Round((($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / $os.TotalVisibleMemorySize) * 100, 1)")
                ram_output = rs.std_out.decode('utf-8').strip()
                ram_usage = float(ram_output.replace(',', '.').strip()) if ram_output else 0.0
                
                # --- Disk (Déjà là) ---
                rs = session.run_ps("$disk = Get-WmiObject -Class Win32_LogicalDisk -Filter \"DeviceID='C:'\"; if ($disk) { [math]::Round((($disk.Size - $disk.FreeSpace) / $disk.Size) * 100, 1) } else { 0 }")
                disk_output = rs.std_out.decode('utf-8').strip()
                disk_usage = float(disk_output.replace(',', '.').strip()) if disk_output else 0.0
                
                # --- Uptime (Déjà là) ---
                rs = session.run_ps("$os = Get-WmiObject -Class Win32_OperatingSystem; $uptime = (Get-Date) - $os.ConvertToDateTime($os.LastBootUpTime); [math]::Round($uptime.TotalHours, 2)")
                uptime_output = rs.std_out.decode('utf-8').strip()
                uptime_hours = float(uptime_output.replace(',', '.').strip()) if uptime_output else 0.0
                
                # Maintenant la comparaison fonctionnera car cpu_usage existe !
                status = "OK"
                if cpu_usage > cpu_thresh or ram_usage > ram_thresh or disk_usage > disk_thresh:
                    status = "WARNING"
                
                results.append({
                    "name": name,
                    "ip": ip,
                    "cpu_percent": cpu_usage,
                    "ram_percent": ram_usage,
                    "disk_percent": disk_usage,
                    "uptime_hours": uptime_hours,
                    "status": status,
                    "message": "Success"
                })
                if status != "OK":
                    all_ok = False
            except Exception as e:
                results.append({
                    "name": name,
                    "ip": ip,
                    "status": "CRITICAL",
                    "message": f"WinRM Error: {str(e)}"
                })
                all_ok = False

        else:
            # Assume Linux/Ubuntu
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            try:
                client.connect(ip, username=user, password=password, timeout=5)
                
                # CPU
                stdin, stdout, stderr = client.exec_command("top -bn1 | grep 'Cpu(s)'")
                cpu_output = stdout.read().decode('utf-8')
                cpu_match = re.search(r'(\d+\.\d+)\s+id', cpu_output)
                if cpu_match:
                    idle_cpu = float(cpu_match.group(1))
                    cpu_usage = round(100.0 - idle_cpu, 1)
                else:
                    cpu_usage = 0.0

                # RAM
                stdin, stdout, stderr = client.exec_command("free -m")
                ram_output = stdout.read().decode('utf-8')
                ram_match = re.search(r'Mem:\s+(\d+)\s+(\d+)', ram_output)
                if ram_match:
                    total_ram = float(ram_match.group(1))
                    used_ram = float(ram_match.group(2))
                    ram_usage = round((used_ram / total_ram) * 100, 1) if total_ram > 0 else 0.0
                else:
                    ram_usage = 0.0

                # Disk
                stdin, stdout, stderr = client.exec_command("df -h /")
                disk_output = stdout.read().decode('utf-8')
                disk_match = re.search(r'(\d+)%', disk_output.split('\n')[1])
                disk_usage = float(disk_match.group(1)) if disk_match else 0.0
                
                # Uptime
                stdin, stdout, stderr = client.exec_command("cat /proc/uptime")
                uptime_output = stdout.read().decode('utf-8')
                uptime_seconds = float(uptime_output.split()[0])
                uptime_hours = round(uptime_seconds / 3600, 2)
                
                status = "OK"
                if cpu_usage > cpu_thresh or ram_usage > ram_thresh or disk_usage > disk_thresh:
                    status = "WARNING"
                    
                results.append({
                    "name": name,
                    "ip": ip,
                    "cpu_percent": cpu_usage,
                    "ram_percent": ram_usage,
                    "disk_percent": disk_usage,
                    "uptime_hours": uptime_hours,
                    "status": status,
                    "message": "Success"
                })
                if status != "OK":
                    all_ok = False
                    
            except Exception as e:
                results.append({
                    "name": name,
                    "ip": ip,
                    "status": "CRITICAL",
                    "message": f"SSH Error: {str(e)}"
                })
                all_ok = False
            finally:
                client.close()
            
    return results, all_ok

def format_diagnostic_report(ad_results, mysql_result, sys_metrics):
    console = Console(force_terminal=True, width=120)
    
    table = Table(title="DIAGNOSTIC REPORT", header_style="bold cyan")
    table.add_column("Component", style="bold")
    table.add_column("Details")
    table.add_column("Status", justify="center")
    
    # AD/DNS
    if ad_results:
        for ad in ad_results:
            details = f"IP: {ad['ip']} | DNS: {'UP' if ad['dns_53'] else 'DOWN'} | LDAP: {'UP' if ad['ldap_389_636'] else 'DOWN'}"
            color = "green" if ad['status'] == "OK" else "red"
            table.add_row(f"AD/DNS ({ad['name']})", details, f"[{color}]{ad['status']}[/{color}]")
        
    # MySQL
    if mysql_result['status'] != "SKIPPED":
        color = "green" if mysql_result['status'] == "OK" else "red"
        mysql_details = f"Host: {mysql_result['host']} | DB: {mysql_result['db']} | Msg: {mysql_result['message']}"
        table.add_row("MySQL (WMS)", mysql_details, f"[{color}]{mysql_result['status']}[/{color}]")
    
    # Metrics
    for metric in sys_metrics:
        color = "green" if metric['status'] == "OK" else ("yellow" if metric['status'] == "WARNING" else "red")
        if metric.get("message") == "Success":
            sys_details = f"IP: {metric['ip']} | CPU: {metric['cpu_percent']}% | RAM: {metric['ram_percent']}% | Disk: {metric['disk_percent']}% | Uptime: {metric['uptime_hours']}h"
        else:
            sys_details = f"IP: {metric.get('ip', 'N/A')} | Error: {metric.get('message', 'Unknown')}"
        table.add_row(f"System Metrics ({metric['name']})", sys_details, f"[{color}]{metric['status']}[/{color}]")
    
    console.print(table)
    return "" # Output is printed to console, we can also capture it if needed

def run(config, mode="all", targets=None):
    """Execution function returning dictionaries for specific diagnostic tests."""
    
    linux_servers = config.get("infrastructure", {}).get("linux_servers", [])
    windows_servers = config.get("infrastructure", {}).get("windows_servers", [])
    all_servers = linux_servers + windows_servers
    
    if targets is None:
        targets = all_servers
        
    target_ips = [t.get("ip") for t in targets]
        
    ad_results, ad_ok = [], True
    mysql_result, mysql_ok = {"status": "SKIPPED", "host": "N/A", "db": "N/A", "message": "Not requested"}, True
    sys_metrics, sys_ok = [], True
    action_run = False
    
    if mode in ["ad", "all"]:
        ad_list = config.get("infrastructure", {}).get("ad_dns", [])
        ad_to_check = [ad for ad in ad_list if ad.get("ip") in target_ips]
        if ad_to_check:
            ad_results, ad_ok = check_ad_dns(ad_to_check)
            action_run = True
            if mode == "ad":
                format_diagnostic_report(ad_results, mysql_result, [])
                return {
                    "module": "diagnostic_ad",
                    "status": "OK" if ad_ok else "CRITICAL",
                    "code": 0 if ad_ok else 2,
                    "target": target_ips,
                    "data": ad_results,
                    "message": f"AD/DNS Checks completed on {len(ad_results)} servers."
                }
        
    if mode in ["mysql", "all"]:
        db_ip = config.get("infrastructure", {}).get("wms", {}).get("db_ip", "127.0.0.1")
        if db_ip in target_ips:
            mysql_result, mysql_ok = check_mysql(config)
            action_run = True
            if mode == "mysql":
                format_diagnostic_report([], mysql_result, [])
                return {
                    "module": "diagnostic_mysql",
                    "status": mysql_result["status"],
                    "code": 0 if mysql_ok else 2,
                    "target": db_ip,
                    "data": mysql_result,
                    "message": mysql_result.get("message", "MySQL Check completed.")
                }
        
    if mode in ["metrics", "all"]:
        if targets:
            thresholds = config.get("thresholds", {})
            sys_metrics, sys_ok = get_system_metrics(targets, config, thresholds)
            action_run = True
            if mode == "metrics":
                format_diagnostic_report([], {"status": "SKIPPED"}, sys_metrics)
                return {
                    "module": "diagnostic_metrics",
                    "status": "OK" if sys_ok else "WARNING", 
                    "code": 0 if sys_ok else 1,
                    "target": target_ips,
                    "data": sys_metrics,
                    "message": f"Metrics checks completed on {len(sys_metrics)} servers."
                }
            
    if not action_run:
        return {
            "module": "diagnostic",
            "status": "SKIPPED",
            "code": 0,
            "target": target_ips,
            "message": "No relevant tests matched the requested targets."
        }
        
    if mode == "all":
        format_diagnostic_report(ad_results, mysql_result, sys_metrics)
        # Combine returned objects for multi-run logic when called via code
        status = "OK"
        code = 0
        if not ad_ok or not mysql_ok:
            status, code = "CRITICAL", 2
        elif not sys_ok:
            status, code = "WARNING", 1
            
        return {
            "module": "diagnostic_all",
            "status": status,
            "code": code,
            "target": target_ips,
            "data": {
                "ad": ad_results,
                "mysql": mysql_result,
                "metrics": sys_metrics
            },
            "message": "Full Diagnostic evaluation complete."
        }