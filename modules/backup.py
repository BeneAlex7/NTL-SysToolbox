import os
import subprocess
import hashlib
import gzip
import csv
import mysql.connector
from datetime import datetime
from rich.console import Console
from rich.table import Table

def generate_hash(filepath):
    """Generate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_file(filepath):
    """Verify file exists and its size > 0."""
    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
        return True
    return False

def get_wms_tables(config):
    """Fetch list of tables from the WMS database."""
    db_config = config.get("infrastructure", {}).get("wms", {})
    db_ip = db_config.get("db_ip", "127.0.0.1")
    db_name = db_config.get("db_name", "wms_prod")
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
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        connection.close()
        return tables
    except Exception as e:
        return []

def backup_sql(config, backup_dir, timestamp):
    """Perform mysqldump over SSH and gzip the output."""
    db_config = config.get("infrastructure", {}).get("wms", {})
    db_name = db_config.get("db_name", "wms_prod")
    
    # We must find the WMS-DB credentials in linux_servers
    linux_servers = config.get("infrastructure", {}).get("linux_servers", [])
    wms_server = next((s for s in linux_servers if s.get("name") == "WMS-DB" or s.get("name") == "wms_db"), None)
    if not wms_server:
        wms_server = linux_servers[0] if linux_servers else None
        
    ssh_ip = wms_server.get("ip") if wms_server else db_config.get("db_ip", "127.0.0.1")
    secret_ref = wms_server.get("secret_ref") if wms_server else "wms_db_ssh"
    
    credentials = config.get(secret_ref, {})
    ssh_user = credentials.get("user", "root")
    ssh_password = credentials.get("password", "")
    
    db_user = config.get("wms_db_user", "root")
    db_password = config.get("wms_db_password", "")
    
    output_file = os.path.join(backup_dir, f"wms_backup_{timestamp}.sql.gz")
    
    cmd = f"mysqldump -u{db_user}"
    if db_password:
        cmd += f" -p{db_password}"
    cmd += f" {db_name}"
    
    try:
        import paramiko
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ssh_ip, username=ssh_user, password=ssh_password, timeout=5)
        
        stdin, stdout, stderr = client.exec_command(cmd)
        
        with gzip.open(output_file, 'wb') as f_out:
            while True:
                chunk = stdout.read(4096)
                if not chunk:
                    break
                f_out.write(chunk)
                
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            err = stderr.read().decode('utf-8')
            client.close()
            return {"status": "ERROR", "message": f"mysqldump failed remotely: {err}", "type": "SQL"}
            
        client.close()
            
        if verify_file(output_file):
            file_hash = generate_hash(output_file)
            return {"status": "OK", "file": output_file, "hash": file_hash, "type": "SQL"}
        else:
            return {"status": "ERROR", "message": "Backup generated but file is empty or missing", "type": "SQL"}
            
    except Exception as e:
        return {"status": "ERROR", "message": str(e), "type": "SQL"}

def backup_csv(config, backup_dir, timestamp, table_name):
    """Export a specific table to CSV using mysql-connector."""
    db_config = config.get("infrastructure", {}).get("wms", {})
    db_ip = db_config.get("db_ip", "127.0.0.1")
    db_name = db_config.get("db_name", "wms_prod")
    db_user = config.get("wms_db_user", "root")
    db_password = config.get("wms_db_password", "")
    
    output_file = os.path.join(backup_dir, f"wms_{table_name}_{timestamp}.csv")
    
    try:
        connection = mysql.connector.connect(
            host=db_ip,
            user=db_user,
            password=db_password,
            database=db_name
        )
        cursor = connection.cursor()
        
        if not table_name.isidentifier():
             raise ValueError("Invalid table name")
             
        query = f"SELECT * FROM `{table_name}`"
        cursor.execute(query)
        
        rows = cursor.fetchall()
        headers = [i[0] for i in cursor.description]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f_out:
            writer = csv.writer(f_out, delimiter=';')
            writer.writerow(headers)
            writer.writerows(rows)
            
        cursor.close()
        connection.close()
        
        if verify_file(output_file):
            file_hash = generate_hash(output_file)
            return {"status": "OK", "file": output_file, "hash": file_hash, "type": "CSV", "table": table_name}
        else:
            return {"status": "ERROR", "message": "Export generated but file is empty or missing", "type": "CSV"}
            
    except Exception as e:
        return {"status": "ERROR", "message": str(e), "type": "CSV"}

def run(config, mode="sql", table_name=None):
    """Main execution function for backup module."""
    console = Console()
    
    # Configure path
    backup_dir = config.get("backup", {}).get("output_dir", "./data/backups")
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir, exist_ok=True)
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = []
    
    console.print(f"[italic]Starting WMS Backup (Mode: {mode.upper()})...[/italic]")
    
    if mode == "sql":
        res = backup_sql(config, backup_dir, timestamp)
        results.append(res)
    elif mode == "csv" and table_name:
        res = backup_csv(config, backup_dir, timestamp, table_name)
        results.append(res)
    else:
        results.append({"status": "ERROR", "message": "Invalid backup mode or missing table name"})

    # Determine overall status
    has_error = any(r.get("status") == "ERROR" for r in results)
    overall_status = "ERROR" if has_error else "OK"
    code = 1 if has_error else 0
    
    # Format report
    table = Table(title="BACKUP REPORT", header_style="bold cyan")
    table.add_column("Type", style="bold")
    table.add_column("Result")
    table.add_column("Status", justify="center")
    
    for r in results:
        color = "green" if r["status"] == "OK" else "red"
        if r["status"] == "OK":
            details = f"File: {r['file']}\nHash: {r['hash'][:16]}..."
        else:
            details = f"Msg: {r['message']}"
        type_str = f"CSV ({r.get('table')})" if r.get('type') == "CSV" else "SQL Full"
        
        table.add_row(type_str, details, f"[{color}]{r['status']}[/{color}]")

    console.print(table)
    
    return {
        "module": "backup",
        "status": overall_status,
        "code": code,
        "data": results,
        "message": f"Backup completed with status: {overall_status}"
    }