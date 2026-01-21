import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

def load_config(config_filename="config.yaml"):
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent
    config_path = project_root / config_filename
    env_path = project_root / ".env"

    load_dotenv(dotenv_path=env_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Fichier de configuration introuvable : {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    # Smart Override: Process all environment variables starting with NTL_
    # This allows overriding ANY key in the YAML without modifying this script
    for env_key, env_val in os.environ.items():
        if env_key.startswith("NTL_"):
            # NTL__INFRASTRUCTURE__WMS__DB_IP -> ['infrastructure', 'wms', 'db_ip']
            # We use double underscore '__' as a nesting separator
            keys = env_key.lower().replace("ntl__", "").split("__")
            
            # Dynamic navigation into the config dictionary
            current = config
            for key in keys[:-1]:
                # setdefault creates the sub-dict if it doesn't exist
                current = current.setdefault(key, {})
            
            # Update the final value
            current[keys[-1]] = env_val

    return config