import sys
import os
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
import argparse

# Module imports
from modules.audit import run as run_audit_os, eol_csv, scan_network
from modules.diagnostic import run as run_diagnostic
from modules.backup import run as run_backup
from core.config_loader import load_config
from core.logger import NTL_Logger
import core.security as sec

def main():
    """
    Main entry point for NTL-SysToolbox.
    Provides an interactive CLI menu to trigger different audit modules.
    """
    console = Console()
    logger = NTL_Logger()
    
    # --- SECURITY BOOT SEQUENCE ---
    os.system('cls' if os.name == 'nt' else 'clear')
    console.print(Panel.fit("[bold yellow]NTL Secure Boot[/bold yellow]", border_style="yellow"))
    
    config = None

def load_interactive_config(console):
    """Refactored vault prompt to allow API integration later."""
    while True:
        try:
            # Ask for Vault Password
            vault_password = Prompt.ask("Enter Vault Password to LOAD config (leave empty if none)", password=True)
            
            if not vault_password:
                vault_password = None

            # Try to Load configuration
            config = load_config(vault_password)
            
            if vault_password:
                console.print("[dim]Secrets loaded into memory.[/dim]")
            
            break 

        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] Failed to load config: {e}")
            console.print("[italic]Please try again or leave empty to skip secrets.[/italic]\n")

    return config, vault_password

def parse_args():
    parser = argparse.ArgumentParser(description="NTL-SysToolbox CLI Interface")
    parser.add_argument("--action", type=str, choices=[
        "audit_os", "audit_csv", "audit_network", 
        "diag_ad", "diag_mysql", "diag_metrics", "diag_all",
        "backup_sql", "backup_csv"
    ], help="Directly trigger an action without interactive menu.")
    parser.add_argument("--targets", type=str, help="Comma-separated Server execution IPs (For network/metric actions)")
    parser.add_argument("--table", type=str, help="Specific SQL table name (For backup_csv action)")
    parser.add_argument("--vault-password", type=str, help="Password for vault decryption", default=None)
    parser.add_argument("--json", action="store_true", help="Output STDOUT strictly as raw JSON (requires --action)")
    
    return parser.parse_args()

def execute_cli_action(args, config, logger, is_admin):
    """Execute a single module programmatic sequence without prompts."""
    console = Console()
    origin_stdout = sys.stdout
    
    if args.json:
        sys.stdout = open(os.devnull, 'w')
        
    res = None
    
    if args.action == "audit_os":
        if args.targets: config['audit']['target_os'] = [t.strip() for t in args.targets.split(",")]
        res = run_audit_os(config)
        
    elif args.action == "audit_csv":
        res = eol_csv(config)
        
    elif args.action == "audit_network":
        if not is_admin:
            console.print("[bold red]Admin permissions required for network scan.[/bold red]")
            sys.exit(1)
        if args.targets: config['audit']['network_range'] = args.targets
        res = scan_network(config)
        
    elif args.action.startswith("diag_"):
        mode = args.action.split("_")[1]
        
        linux_servers = config.get("infrastructure", {}).get("linux_servers", [])
        windows_servers = config.get("infrastructure", {}).get("windows_servers", [])
        all_servers = linux_servers + windows_servers
        targets = all_servers
        
        if args.targets:
            target_ip_list = [t.strip() for t in args.targets.split(",")]
            targets = [s for s in all_servers if s.get("ip") in target_ip_list]
            if not targets:
                console.print(f"[bold red]Targets {args.targets} not found in configuration list.[/bold red]")
                sys.exit(1)
                
        res = run_diagnostic(config, mode=mode, targets=targets)
        
    elif args.action == "backup_sql":
        res = run_backup(config, mode="sql")
        
    elif args.action == "backup_csv":
        if args.table:
            res = run_backup(config, mode="csv", table_name=args.table)
        else:
            # We must gracefully log an error as JSON if run silently without correct configs
            res = {"module": "backup_csv", "status": "ERROR", "code": 1, "message": "Missing --table parameter."}

    # Restore STDOUT if we silenced it
    if args.json:
        sys.stdout = origin_stdout

    if res is not None:
        logger.log(res)

    sys.exit(0)

def main():
    """
    Main entry point for NTL-SysToolbox.
    Provides an interactive CLI menu to trigger different audit modules.
    """
    args = parse_args()
    
    if args.json and not args.action:
        print('{"module": "sys_toolbox", "status": "ERROR", "message": "--json flag requires --action to be used"}')
        sys.exit(1)
        
    console = Console()
    logger = NTL_Logger(json_output=args.json)
    
    # --- SECURITY BOOT SEQUENCE ---
    if not args.action:
        os.system('cls' if os.name == 'nt' else 'clear')
        console.print(Panel.fit("[bold yellow]NTL Secure Boot[/bold yellow]", border_style="yellow"))
    
    config = None
    
    if args.action and args.vault_password:
        config = load_config(args.vault_password)
    else:
        # Ask for interactive load when not bypassing automatically
        config, _ = load_interactive_config(console)

    # Check Admin Privileges
    is_admin = False
    try:
        if os.name == 'nt':
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            is_admin = os.geteuid() == 0
    except Exception:
        is_admin = False

    # Dispatch directly if --action was provided
    if args.action:
        execute_cli_action(args, config, logger, is_admin)
        
    # --- MAIN LOOP ---
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')

        # Check Admin Privileges
        is_admin = False
        try:
            if os.name == 'nt':
                import ctypes
                is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                is_admin = os.geteuid() == 0
        except Exception:
            is_admin = False

        # Header Panel
        console.print(Panel.fit(
            "[bold cyan]NTL-SysToolbox[/bold cyan]\n[dim]Exploitation & Audit Tool - Nord Transit Logistics[/dim]",
            border_style="cyan",
            subtitle="v1.0.0"
        ))

        # Global Warning if not admin
        if not is_admin:
            console.print("[bold red]Warning:[/bold red][bold yellow] You are not running as root/admin, the Network Scanner is disabled.[/bold yellow]")

        # Menu Options
        console.print("\n[1] [bold green]OS Lifecycle Information[/bold green]")
        console.print("[2] [bold yellow]Audit Obsolescence from CSV[/bold yellow]")
        
        # Only show Network Scan if Admin
        if is_admin:
            console.print("[3] [bold red]Network Scan & OS Detection[/bold red]")
        
        console.print("[4] [bold magenta]System Diagnostic (AD, MySQL, Metrics)[/bold magenta]")
        console.print("[5] [bold green]WMS Backup Menu[/bold green]")
        
        # Security Options
        console.print("[6] [bold blue]Encrypt Vault[/bold blue]")
        console.print("[7] [bold blue]Decrypt Vault[/bold blue]")

        console.print("[8] [bold white]Exit[/bold white]")

        valid_choices = ["1", "2", "3", "4", "5", "6", "7", "8"] if is_admin else ["1", "2", "4", "5", "6", "7", "8"]
        choice = Prompt.ask("\n[bold cyan]Select an option[/bold cyan]", choices=valid_choices, default="8")

        # --- OPTION 1: OS GENERAL INFO ---
        if choice == "1":
            current_os = config.get('audit', {}).get('target_os', 'windows')
            
            if isinstance(current_os, list):
                default_display = ",".join(current_os)
            else:
                default_display = str(current_os)

            console.print(f"\n[italic]Current target(s): {default_display}[/italic]")
            target_input = Prompt.ask("Enter target OS name(s) (comma separated)", default=default_display)
            
            if "," in target_input:
                target_list = [t.strip() for t in target_input.split(",")]
                config['audit']['target_os'] = target_list
            else:
                config['audit']['target_os'] = target_input
            
            with console.status("[bold green]Fetching API data..."):
                result = run_audit_os(config)
            logger.log(result)
            Prompt.ask("\n[dim]Press Enter to return to menu...[/dim]")

        # --- OPTION 2: CSV AUDIT ---
        elif choice == "2":
            csv_path = config.get('audit', {}).get('csv_path', 'inventory.csv')
            console.print(f"\n[italic]Analyzing inventory file: {csv_path}[/italic]")
            
            with console.status("[bold yellow]Processing audit..."):
                result = eol_csv(config)
            logger.log(result)
            Prompt.ask("\n[dim]Press Enter to return to menu...[/dim]")

        # --- OPTION 3: NETWORK SCAN ---
        elif choice == "3" and is_admin:
            current_net = config.get('audit', {}).get('network_range', '192.168.10.0/24')
            if isinstance(current_net, list):
                default_display = " ".join(current_net)
            else:
                default_display = str(current_net)

            console.print(f"\n[italic]Target Network: {default_display}[/italic]")
            target_net = Prompt.ask("Enter network range (CIDR)", default=default_display)
            config['audit']['network_range'] = target_net
            
            result = scan_network(config)
            logger.log(result)
            Prompt.ask("\n[dim]Press Enter to return to menu...[/dim]")

        # --- OPTION 4: SYSTEM DIAGNOSTIC ---
        elif choice == "4":
            while True:
                console.print("\n[bold magenta]System Diagnostic Menu[/bold magenta]")
                console.print("[1] Check AD/DNS")
                console.print("[2] Check MySQL (WMS)")
                console.print("[3] Check System Metrics (Linux/Windows)")
                console.print("[4] Run Diagnostics (Select Servers)")
                console.print("[5] Return to Main Menu")
                
                sub_choice = Prompt.ask("Select an option", choices=["1", "2", "3", "4", "5"], default="5")
                if sub_choice == "5":
                    break
                    
                linux_servers = config.get("infrastructure", {}).get("linux_servers", [])
                windows_servers = config.get("infrastructure", {}).get("windows_servers", [])
                all_servers = linux_servers + windows_servers
                
                if not all_servers:
                    console.print("[yellow]No servers configured in infrastructure.[/yellow]")
                    continue
                    
                console.print("\n[bold]Available Servers to target:[/bold]")
                for i, srv in enumerate(all_servers):
                    console.print(f"[{i+1}] {srv.get('name')} ({srv.get('ip')}) - {srv.get('os')}")
                console.print(f"[{len(all_servers)+1}] All Servers")
                
                choices_idx = [str(i) for i in range(1, len(all_servers)+2)]
                selected = Prompt.ask("Select server(s) to check (comma-separated)", default=str(len(all_servers)+1))
                
                selected_indices = [s.strip() for s in selected.split(",") if s.strip() in choices_idx]
                
                targets = []
                if str(len(all_servers)+1) in selected_indices:
                    targets = all_servers
                else:
                    for idx in selected_indices:
                        targets.append(all_servers[int(idx)-1])
                        
                mode_map = {"1": "ad", "2": "mysql", "3": "metrics", "4": "all"}
                mode = mode_map.get(sub_choice)
                
                if mode:
                    res = run_diagnostic(config, mode=mode, targets=targets)
                    if res.get("status") != "SKIPPED":
                        logger.log(res)
                
                Prompt.ask("\n[dim]Press Enter to continue in diagnostic menu...[/dim]")

        # --- OPTION 5: WMS BACKUP MENU ---
        elif choice == "5":
            console.print("\n[bold green]WMS Backup Options:[/bold green]")
            console.print("[1] Full SQL Export (mysqldump over SSH + gzip)")
            console.print("[2] Specific Table CSV Export")
            console.print("[3] Cancel")
            
            sub_choice = Prompt.ask("Select an option", choices=["1", "2", "3"], default="3")
            
            if sub_choice == "1":
                with console.status("[bold yellow]Running SQL Backup...[/bold yellow]"):
                    result = run_backup(config, mode="sql")
                logger.log(result)
            elif sub_choice == "2":
                console.print("[italic]Fetching available tables in WMS DB...[/italic]")
                from modules.backup import get_wms_tables
                tables = get_wms_tables(config)
                if not tables:
                    console.print("[red]Could not retrieve tables from WMS database, or it is empty.[/red]")
                else:
                    console.print("\n[bold]Available Tables:[/bold]")
                    for i, t in enumerate(tables):
                        console.print(f"[{i+1}] {t}")
                        
                    t_choice = Prompt.ask("Select the table to export by number", choices=[str(i+1) for i in range(len(tables))])
                    table_name = tables[int(t_choice)-1]
                    with console.status(f"[bold yellow]Exporting table '{table_name}' to CSV...[/bold yellow]"):
                        result = run_backup(config, mode="csv", table_name=table_name)
                    logger.log(result)
            
            Prompt.ask("\n[dim]Press Enter to return to menu...[/dim]")

        # --- OPTION 6: ENCRYPT FILE ---
        elif choice == "6":
            console.print("\n[italic]Encrypting 'secret.yaml'...[/italic]")
            console.print("[bold red]Warning: 'secret.yaml' will be securely deleted after encryption![/bold red]")
            
            pwd_enc = Prompt.ask("Confirm Password for encryption", password=True)
            
            if pwd_enc:
                msg = sec.encrypt_disk_file(pwd_enc)
                console.print(f"[bold]{msg}[/bold]")
            else:
                console.print("[red]Operation cancelled (Empty password).[/red]")
                
            Prompt.ask("\n[dim]Press Enter to return to menu...[/dim]")

        # --- OPTION 7: DECRYPT FILE ---
        elif choice == "7":
            console.print("\n[italic]Decrypting 'secret.yaml.enc' -> 'secret.yaml'[/italic]")
            
            pwd_dec = Prompt.ask("Enter Password to decrypt", password=True)
            
            if pwd_dec:
                msg = sec.decrypt_disk_file(pwd_dec)
                console.print(f"[bold]{msg}[/bold]")
            else:
                console.print("[red]Operation cancelled (Empty password).[/red]")
                
            Prompt.ask("\n[dim]Press Enter to return to menu...[/dim]")

        # --- EXIT ---
        elif choice == "8":
            console.print("[bold cyan]Exiting NTL-SysToolbox. Goodbye![/bold cyan]")
            sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nShutdown requested by user.")
        sys.exit(0)