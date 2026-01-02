import json
import os
from datetime import datetime

class NTL_Logger:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def log(self, result_dict):
        module = result_dict.get("module", "unknown")
        # Utilisation de ISO 8601 si possible, sinon format par défaut
        timestamp = result_dict.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        status = result_dict.get("status", "INFO")
        message = result_dict.get("message", "")
        data = result_dict.get("data", {})

        # Logique de déduction du code de retour
        if "code" not in result_dict:
            result_dict["code"] = 0 if status == "OK" else 1
        
        code = result_dict["code"]

        # Affichage Console
        color = "\033[92m" if status == "OK" else "\033[91m"
        reset = "\033[0m"
        print(f"[{timestamp}] {color}{status}{reset} | Module: {module} | Code: {code} | {message}")
        if data:
            print(f"   Détails: {data}")

        # Sauvegarde JSON
        filename = f"{module}_{datetime.now().strftime('%Y%m%d')}.json"
        filepath = os.path.join(self.log_dir, filename)

        logs = []
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                try:
                    logs = json.load(f)
                except json.JSONDecodeError:
                    logs = []
        
        logs.append(result_dict)

        with open(filepath, "w") as f:
            json.dump(logs, f, indent=4)

        return code