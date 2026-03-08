import json
import os
import gzip
import shutil
from datetime import datetime
import sys

class NTL_Logger:
    def __init__(self, log_dir="logs", json_output=False, max_bytes=5*1024*1024):
        self.log_dir = log_dir
        self.json_output = json_output
        self.max_bytes = max_bytes
        self.log_filename = "ntl_systoolbox.json"
        
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def rotative_compress(self, filepath):
        """If filepath exceeds max_bytes, archive it into a gz file and clear."""
        if not os.path.exists(filepath):
            return
            
        if os.path.getsize(filepath) > self.max_bytes:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archive_name = f"ntl_systoolbox_{timestamp}.json.gz"
            archive_path = os.path.join(self.log_dir, archive_name)
            
            with open(filepath, 'rb') as f_in:
                with gzip.open(archive_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
                    
            # Wipe old file
            open(filepath, 'w').close()

    def log(self, result_dict):
        module = result_dict.get("module", "unknown")
        timestamp = result_dict.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        status = result_dict.get("status", "INFO")
        message = result_dict.get("message", "")
        
        # Override object timestamp just in case
        result_dict["timestamp"] = timestamp

        # Return code deduction logic
        if "code" not in result_dict:
            result_dict["code"] = 0 if status == "OK" else 1
        
        code = result_dict["code"]

        # Formatted Payload logic vs Console Print
        if self.json_output:
            # We strictly output the raw JSON so Zabbix / external scripts can parse it clean.
            # No print formatting or rich panels
            print(json.dumps(result_dict))
        else:
            # Console Display
            color = "\033[92m" if status == "OK" else "\033[91m"
            reset = "\033[0m"
            print(f"[{timestamp}] {color}{status}{reset} | Module: {module} | Code: {code} | {message}")

        # Unified Json Save
        filepath = os.path.join(self.log_dir, self.log_filename)
        
        self.rotative_compress(filepath)

        logs = []
        if os.path.getsize(filepath) > 0 if os.path.exists(filepath) else False:
            with open(filepath, "r") as f:
                try:
                    logs = json.load(f)
                except json.JSONDecodeError:
                    logs = []
        
        logs.append(result_dict)

        with open(filepath, "w") as f:
            json.dump(logs, f, indent=4)

        return code