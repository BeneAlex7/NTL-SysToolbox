import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

def load_config(config_filename="config.yaml"):
    """
    Charge la configuration depuis le fichier YAML et applique les surcharges
    depuis le fichier .env et les variables d'environnement.
    """
    # Définition des chemins
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent
    config_path = project_root / config_filename
    env_path = project_root / ".env"

    # Chargement des variables d'environnement
    load_dotenv(dotenv_path=env_path)

    # Chargement du YAML
    if not config_path.exists():
        raise FileNotFoundError(f"Fichier de configuration introuvable : {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    # 1. Injection des Secrets (depuis .env)
    config["secrets"] = {
        "ad_user": os.getenv("AD_USER"),
        "ad_password": os.getenv("AD_PASSWORD"),
        "mysql_user": os.getenv("MYSQL_USER"),
        "mysql_password": os.getenv("MYSQL_PASSWORD"),
        "mysql_port": int(os.getenv("MYSQL_PORT", 3306)),
    }

    # 2. Surcharges Infrastructure (depuis .env)
    # Surcharge IP WMS DB
    wms_db_ip = os.getenv("WMS_DB_IP")
    if wms_db_ip:
        # On s'assure que la structure existe
        if "infrastructure" in config and "wms" in config["infrastructure"]:
            config["infrastructure"]["wms"]["db_ip"] = wms_db_ip

    # Surcharge IP DC01
    dc01_ip = os.getenv("DC01_IP")
    if dc01_ip:
        if "infrastructure" in config and "ad_dns" in config["infrastructure"]:
            ad_dns = config["infrastructure"]["ad_dns"]
            if isinstance(ad_dns, list) and len(ad_dns) > 0:
                # On suppose que DC01 est le premier élément comme défini dans le YAML par défaut
                ad_dns[0]["ip"] = dc01_ip

    return config