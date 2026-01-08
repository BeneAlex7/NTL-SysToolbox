from core.logger import NTL_Logger
from datetime import datetime

# On initialise le logger
my_logger = NTL_Logger()

# Simulation d'un résultat venant du module Diagnostic
test_result = {
    "module": "diagnostic",
    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "status": "OK",
    "target": "192.168.10.10", # IP du DC01 [cite: 162]
    "data": {
        "ad_status": "Running",
        "dns_status": "Running",
        "cpu_usage": "12%"
    },
    "message": "Contrôleur de domaine opérationnel."
}

# On lance le log
print("--- Test du Logger NTL ---")
my_logger.log(test_result)
print("--- Test terminé, vérifie le dossier /logs ---")