from datetime import datetime

def run(config):
    """
    Module de Diagnostic (Template Standardisé).
    Exécute les tests de connectivité de base.
    """
    # 1. Récupération des paramètres depuis la config injectée
    try:
        # Exemple : Récupération de l'IP du DC01
        # On utilise la structure définie dans config.yaml
        dc01_ip = config['infrastructure']['ad_dns'][0]['ip']
    except (KeyError, IndexError):
        return {
            "module": "diagnostic",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "ERROR",
            "code": 1,
            "message": "Configuration invalide : IP DC01 introuvable."
        }

    # Exemple : Récupération sécurisée d'un secret
    ad_password = config['secrets'].get('ad_password')

    # 2. Exécution de la logique métier (Simulation)
    # TODO: Implémenter les vrais tests (ping, socket, etc.)
    print(f"[DEBUG] Test de connexion vers {dc01_ip}...")
    
    # Simulation de succès
    test_success = True 

    # 3. Construction du résultat standardisé
    result = {
        "module": "diagnostic",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "OK" if test_success else "ERROR",
        "code": 0 if test_success else 1,
        "target": dc01_ip,
        "data": {
            "check_type": "connectivity",
            "has_credentials": bool(ad_password) # Ne jamais logger le mot de passe !
        },
        "message": "Diagnostic de connectivité réussi." if test_success else "Échec de la connexion."
    }

    return result

if __name__ == "__main__":
    # Bloc de test local (ne s'exécute pas lors de l'import par main.py)
    print("--- Mode Test Local ---")
    mock_config = {
        'infrastructure': {
            'ad_dns': [{'ip': '192.168.10.10', 'name': 'DC01'}]
        },
        'secrets': {
            'ad_password': 'SecretPassword123'
        }
    }
    print(run(mock_config))