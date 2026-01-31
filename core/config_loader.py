import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
import core.security as sec

def deep_merge(source, destination):
    for key, value in source.items():
        if isinstance(value, dict):
            node = destination.setdefault(key, {})
            deep_merge(value, node)
        else:
            destination[key] = value
    return destination

def load_config(vault_password=None):
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent
    
    config_path = project_root / "config.yaml"
    env_path = project_root / ".env"

    load_dotenv(dotenv_path=env_path)

    # 1. Load public config
    config = {}
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}

    # 2. Load encrypted secrets (via core.security)
    if vault_password:
        secrets = sec.load_secrets_dict(vault_password)
        if secrets:
            deep_merge(secrets, config)

    # 3. Load Env Vars
    for env_key, env_val in os.environ.items():
        if env_key.startswith("NTL_"):
            keys = env_key.lower().replace("ntl__", "").split("__")
            current = config
            for key in keys[:-1]:
                current = current.setdefault(key, {})
            current[keys[-1]] = env_val

    return config