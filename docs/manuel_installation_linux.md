# NTL-SysToolbox - Manuel d'Installation (Linux)

**Version :** 1.0.0

**Destinataire :** Direction des Systèmes d'Information (DSI)

**Objet :** Procédure de déploiement et d'exploitation de l'outil d'audit NTL sous Linux.

---

## 1. Prérequis Techniques

Pour garantir le fonctionnement complet des modules sur un serveur ou un poste d'administration Linux, la machine hôte doit disposer de :

* **Système d'exploitation :** Ubuntu 20.04+, Debian 11+, RHEL 8/9 ou CentOS Stream.
* **Python :** Version 3.8 ou supérieure avec le module `venv`.
* **Nmap :** Installé via le gestionnaire de paquets (Requis pour le Module 3).
* **Droits :** Accès `sudo` ou `root` requis pour le scanneur réseau (OS Fingerprinting).

## 2. Installation

1. **Installation des dépendances système**
Avant de récupérer le projet, installez Python et Nmap.
* **Debian / Ubuntu :**
```bash
sudo apt update
sudo apt install python3 python3-venv nmap -y

```


* **RHEL / CentOS / Fedora :**
```bash
sudo dnf install python3 nmap -y

```




2. **Récupération des sources**
Désarchivez le fichier et allez dans le dossier :
```bash
tar -xzf NTL-SysToolbox.zip
cd NTL-SysToolbox

```


3. **Initialisation de l'environnement virtuel**
Cette étape est cruciale pour isoler les bibliothèques Python.
```bash
# Création du venv
python3 -m venv .venv

# Activation
source .venv/bin/activate

```


*(Le prompt de votre terminal doit maintenant afficher `(.venv)`)*.
4. **Installation des librairies Python**
```bash
pip install -r requirements.txt

```



## 3. Configuration & Sécurité

L'application utilise un fichier `config.yaml` standard. Le système de **Vault** (Coffre-fort) est intégré pour chiffrer les secrets.

### A. Configuration Standard

Éditez le fichier `config.yaml` à la racine :

```yaml
audit:
  target_os: ["windows", "ubuntu"]
  network_range: "192.168.10.0/24"

```

### B. Gestion des Secrets (Vault)

Pour sécuriser les identifiants sensibles :

1. Créez un fichier `secret.yaml` à la racine.
2. Lancez l'outil et choisissez l'option **[4] Encrypt**.
3. Définissez un mot de passe : le fichier est chiffré (`secret.yaml.enc`) et l'original est **supprimé**.

*Ce mot de passe sera demandé à chaque lancement pour déchiffrer la configuration en mémoire RAM.*

## 4. Utilisation

### Lancement standard (Utilisateur)

Pour les modules d'audit API et CSV :

```bash
# Assurez-vous que le venv est actif
python3 main.py

```

### Lancement avec Scan Réseau (Module 3)

Le module Nmap nécessite les privilèges `root` pour l'analyse d'OS. Il faut utiliser l'interpréteur Python de l'environnement virtuel avec `sudo`.

```bash
# Méthode recommandée
sudo ./.venv/bin/python3 main.py

```

### Options du Menu

* **[1] OS Lifecycle Information :** Interrogation API pour le statut EOL.
* **[2] Audit Obsolescence (CSV) :** Analyse du fichier `inventory.csv`.
* **[3] Network Scan :** Cartographie réseau (Nmap).
* *Note :* Si lancé sans `sudo`, ce module sera désactivé.


* **[4] Encrypt / [5] Decrypt :** Utilitaires de gestion du fichier de secrets.

## 5. Localisation des Rapports

Les rapports sont générés automatiquement dans l'arborescence du projet et sont à cet emplacement par défaut :

* **Rapports JSON** : `./data/audit/`
* **Rapports CSV** (Compatibles LibreOffice/Excel) : `./data/audit/csv/`

Les fichiers sont horodatés (ex: `network_scan_20260131_1430.csv`) pour assurer la traçabilité.