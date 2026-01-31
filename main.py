import sys
import os
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

# Module imports
from modules.audit import run, eol_csv, scan_network
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
        
        # Security Options
        console.print("[4] [bold blue]Encrypt[/bold blue]")
        console.print("[5] [bold blue]Decrypt[/bold blue]")

        console.print("[6] [bold white]Exit[/bold white]")

        valid_choices = ["1", "2", "3", "4", "5", "6"] if is_admin else ["1", "2", "4", "5", "6"]
        choice = Prompt.ask("\n[bold cyan]Select an option[/bold cyan]", choices=valid_choices, default="6")

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
                result = run(config)
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

        # --- OPTION 4: ENCRYPT FILE ---
        elif choice == "4":
            console.print("\n[italic]Encrypting 'secret.yaml'...[/italic]")
            console.print("[bold red]Warning: 'secret.yaml' will be deleted after encryption![/bold red]")
            
            pwd_enc = Prompt.ask("Confirm Password for encryption", password=True)
            
            if pwd_enc:
                msg = sec.encrypt_disk_file(pwd_enc)
                console.print(f"[bold]{msg}[/bold]")
            else:
                console.print("[red]Operation cancelled (Empty password).[/red]")
                
            Prompt.ask("\n[dim]Press Enter to return to menu...[/dim]")

        # --- OPTION 5: DECRYPT FILE ---
        elif choice == "5":
            console.print("\n[italic]Decrypting 'secret.yaml.enc' -> 'secret.yaml'[/italic]")
            
            pwd_dec = Prompt.ask("Enter Password to decrypt", password=True)
            
            if pwd_dec:
                msg = sec.decrypt_disk_file(pwd_dec)
                console.print(f"[bold]{msg}[/bold]")
            else:
                console.print("[red]Operation cancelled (Empty password).[/red]")
                
            Prompt.ask("\n[dim]Press Enter to return to menu...[/dim]")

        # --- EXIT ---
        elif choice == "6":
            console.print("[bold cyan]Exiting NTL-SysToolbox. Goodbye![/bold cyan]")
            sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nShutdown requested by user.")
        sys.exit(0)