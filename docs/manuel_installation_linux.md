# NTL-SysToolbox - Manuel d'Utilisation et d'Installation (Linux)

**Version :** 1.0.0
**Destinataire :** Direction des Systèmes d'Information (DSI)
**Objet :** Procédure de déploiement et d'exploitation de l'outil d'audit et de diagnostic NTL sous Linux.

---

## 1. Prérequis Techniques

Pour garantir le fonctionnement complet des modules, la machine hôte doit disposer de :
* **Système d'exploitation :** Ubuntu 20.04+, Debian 11+, RHEL 8/9 ou CentOS Stream.
* **Python :** Version 3.8 ou supérieure avec le module `venv`.
* **Nmap :** Installé via le gestionnaire de paquets (Requis pour le module Network Scan).
* **Droits :** Accès `sudo` ou `root` requis pour le scanner réseau (OS Fingerprinting).

## 2. Installation

1. **Installation des dépendances système**
* **Debian / Ubuntu :**
```bash
sudo apt update
sudo apt install python3 python3-venv nmap mariadb-client -y
```
*(mariadb-client ou default-mysql-client est utile si vous exécutez mysqldump localement)*

* **RHEL / CentOS / Fedora :**
```bash
sudo dnf install python3 nmap mariadb -y
```

2. **Récupération des sources**
Désarchivez le fichier et allez dans le dossier :
```bash
tar -xzf NTL-SysToolbox.zip
cd NTL-SysToolbox
```

3. **Initialisation de l'environnement virtuel**
Cette étape isole les bibliothèques Python.
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Configuration & Sécurité

L'application utilise un fichier `config.yaml`. Le système de **Vault** (Coffre-fort) est intégré pour protéger les identifiants et mots de passe.

### A. Configuration de l'Infrastructure
Le fichier `config.yaml` définit les seuils d'alerte, les plages réseau pour l'audit, ainsi que la liste de vos serveurs (Windows, Linux, AD/DNS, WMS).

**Pour rajouter une machine à scanner (Diagnostic) :**
Ouvrez `config.yaml` et ajoutez une entrée dans `infrastructure.windows_servers` ou `infrastructure.linux_servers` :
```yaml
infrastructure:
  linux_servers:
    - { ip: "192.168.10.50", name: "NEW-SRV", os: "ubuntu", secret_ref: "new_srv_ssh" }
```
*Le champ `secret_ref` fait le lien avec la clé d'authentification définie dans le Vault.*

### B. Gestion des Secrets (Vault)
Pour sécuriser les identifiants (comme `new_srv_ssh` ci-dessus) :
1. Renseignez toutes les informations de connexion dans le fichier `secret.yaml` :
```yaml
new_srv_ssh:
  user: "admin_user"
  password: "SuperPassword123"
```
2. Lancez l'outil et choisissez l'option **[6] Encrypt Vault**.
3. Définissez un mot de passe. Le fichier est chiffré en `secret.yaml.enc` et l'original `secret.yaml` est **supprimé**.
4. Ce mot de passe principal sera demandé pour déchiffrer la configuration en mémoire à chaque utilisation.

*(Note : Si vous devez ajouter un nouveau secret plus tard, il faut d'abord utiliser **[7] Decrypt Vault**, modifier `secret.yaml`, puis rechiffrer avec **[6] Encrypt Vault**).*

## 4. Utilisation Mode Interactif (Menu CLI)

Lancement :
```bash
# L'usage de 'sudo' est recommandé pour débloquer le composant Network Scan.
sudo ./.venv/bin/python3 main.py
```

**Options disponibles :**
1. **OS Lifecycle Information :** Interrogation API EOL (End of Life) pour identifier la fin de support d'un ou plusieurs systèmes.
2. **Audit Obsolescence (CSV) :** Analyse du cycle de vie à partir de l'inventaire fourni (`inventory.csv`).
3. **Network Scan & OS Detection :** Cartographie d'un réseau via Nmap et détection des OS.
4. **System Diagnostic :** Outil de diagnostic performant pour vérifier :
   - AD / DNS (Vérification des ports 53, 389, 636)
   - MySQL (Connexion à la base de données WMS)
   - System Metrics (Vérification de charge CPU, RAM, Disque, temps de disponibilité via WinRM/SSH)
5. **WMS Backup Menu :** Utilitaire de sauvegarde métier pour la base WMS :
   - Export SQL complet (Via `mysqldump` exécuté sur la machine distante)
   - Export CSV direct d'une table spécifique
6. **Encrypt Vault :** Chiffrement de la configuration.
7. **Decrypt Vault :** Déchiffrement de la configuration.
8. **Exit :** Quitter l'outil.

## 5. Mode Automatisé (Ligne de Commande)

Idéal pour des tâches planifiées (via cron) ou pour l'intégration continue, main.py accepte divers arguments de lancement pour contourner le menu.

**Action paramètre (`--action`) :** 
`audit_os`, `audit_csv`, `audit_network`, `diag_ad`, `diag_mysql`, `diag_metrics`, `diag_all`, `backup_sql`, `backup_csv`

**Arguments supplémentaires :**
* `--targets` : Adresses IP cibles séparées par des virgules (ex: `192.168.1.10,192.168.1.11`). Utile pour filtrer les diagnostics à certain serveurs.
* `--table` : Nom de la table SQL à cibler (obligatoire pour `backup_csv`).
* `--vault-password` : Mot de passe du Vault (passage sans prompt de l'utilisateur).
* `--json` : Génère une sortie uniquement au format JSON strict, idéal pour un parseur externe.

**Exemples de commandes d'automatisation :**
```bash
# Diagnostic complet des métriques pour tout le parc, retourné en JSON
sudo ./.venv/bin/python3 main.py --action diag_all --vault-password "MonPass" --json

# Lancer la sauvegarde SQL distante
./.venv/bin/python3 main.py --action backup_sql --vault-password "MonPass"
```

## 6. Localisation des Fichiers et Rapports

- **Rapports d'audit réseau JSON :** `./audit/data/` (par défaut)
- **Rapports d'audit réseau CSV :** `./data/audit/csv/`
- **Sauvegardes (Backups WMS) :** `./data/backups/`

Les fichiers finaux sont horodatés (ex: `network_scan_20261010_1430.csv`) pour fiabiliser la traçabilité.