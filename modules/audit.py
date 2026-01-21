from datetime import datetime
import requests

from rich.console import Console
from rich.table import Table
from rich import box
import io

def format_table(data, os_names_list):
    """Generates a professional CLI table using the Rich library."""
    # Using StringIO to capture Rich output into a string for the 'message' field
    console = Console(file=io.StringIO(), force_terminal=True, width=120)
    
    for os_index, os_content in enumerate(data):
        # Retrieve the current OS name from the list and format it
        # Sécurité : on s'assure que os_names_list est bien une liste avant d'accéder à l'index
        if isinstance(os_names_list, list):
            current_os_name = os_names_list[os_index].capitalize()
        else:
            # Si c'est juste une chaîne (ex: 'windows'), on l'utilise directement
            current_os_name = str(os_names_list).capitalize()

        table = Table(
            title=f"OS TARGET: {current_os_name.upper()}", 
            box=box.ROUNDED, 
            header_style="bold cyan"
        )
        
        # Defining columns
        table.add_column("CodeName", style="dim", width=25)
        table.add_column("Main version", justify="center")
        table.add_column("End of life", justify="center")
        table.add_column("Minor Version", justify="center")

        for version in os_content:
            # Fallback logic: Use OS name if 'codename' is None or empty
            name_display = str(version.get('codename') or current_os_name)

            table.add_row(
                name_display,
                str(version.get('cycle') or ""),
                str(version.get('support') or ""),
                str(version.get('latest') or "")
            )
        
        console.print(table)
        console.print("\n")

    return console.file.getvalue()

def run(config):
    """Main module entry point complying with the interface contract."""
    # Retrieve OS choice from config to avoid hardcoding
    os_name = config.get('audit', {}).get('target_os', 'windows')
    
    # If os_name is a simple string “windows,” we put it in a list [‘windows’].
    if isinstance(os_name, str):
        os_name = [os_name]

    key_dict = ['codename', 'support', 'latest', 'cycle']
    all_filtered_data = []
    
    for target_os in os_name:
        url = f"https://endoflife.date/api/{target_os.lower()}.json"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            # Filter raw API data to retain only required fields
            filtered_data = []
            for item in response.json() :
                new_mini_dict={}
                for value in key_dict:
                    if value in item:
                        new_mini_dict[value]=item.get(value)
                filtered_data.append(new_mini_dict)
            # Return standardized dictionary for main.py logging
            all_filtered_data.append(filtered_data)
        except Exception as e:
            return {
                "module": "audit_obsolescence",
                "status": "ERROR",
                "code": 1,
                "target": os_name,
                "data": {},
                "message": f"{target_os} n'existe pas dans l'API"
            }
            
    return {
    "module": "audit_obsolescence",
    "status": "OK",
    "code": 0,
    "target": os_name,
    "data": all_filtered_data,
    "message": f"\n{format_table(all_filtered_data, os_name)}" 
}