# NTL-SysToolbox - Manuel d'Installation (Windows)

**Version :** 1.0.0

**Destinataire :** Direction des Systèmes d'Information (DSI)

**Objet :** Procédure de déploiement et d'exploitation de l'outil d'audit NTL sous Windows.

---

## 1. Prérequis Techniques

Pour garantir le fonctionnement complet des modules sur un poste de travail ou un serveur Windows, la machine hôte doit disposer de :

* **Système d'exploitation :** Windows 10, 11 ou Windows Server 2016+.
* **Python :** Version 3.8 ou supérieure (Cochez "Add Python to PATH" lors de l'installation).
* **Nmap :** Télécharger et installer l'exécutable officiel ([https://nmap.org/download.html](https://nmap.org/download.html)).
* *Important :* Assurez-vous d'installer le composant **Npcap** inclus dans l'installateur (requis pour le scan sous Windows).


* **Droits :** Privilèges Administrateur requis pour le scanneur réseau (Module 3).

## 2. Installation

1. **Récupération des sources**
extraire l'archive `.zip` dans un dossier et ouvrir un powershell dans le dossier (ex: `C:\NTL-SysToolbox`).

2. **Initialisation de l'environnement virtuel**
Cette étape isole les bibliothèques du projet pour ne pas interférer avec le système.
```powershell
# Création du venv
python -m venv .venv

# Activation (Le prompt doit afficher (.venv) au début)
.venv\Scripts\activate

```


*Note : Si l'exécution de scripts est désactivée sur votre machine, lancez d'abord : `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser*`
3. **Installation des librairies**
```powershell
pip install -r requirements.txt

```



## 3. Configuration & Sécurité

L'application utilise un fichier `config.yaml` standard. Un système de **Vault** (Coffre-fort) est intégré pour protéger les mots de passe.

### A. Configuration Standard

Éditez le fichier `config.yaml` à la racine (avec Notepad ou VS Code) pour modifier les cibles :

```yaml
audit:
  target_os: ["windows", "ubuntu"]
  network_range: "192.168.10.0/24"

```

### B. Gestion des Secrets (Vault)

Pour sécuriser vos identifiants (ne jamais laisser de mot de passe en clair) :

1. Créez un fichier `secret.yaml` à la racine.
2. Lancez l'outil et choisissez l'option **[4] Encrypt**.
3. Définissez un mot de passe : le fichier est chiffré en `secret.yaml.enc` et l'original est **supprimé**.

*Ce mot de passe sera demandé à chaque lancement pour déchiffrer la configuration en mémoire RAM.*

## 4. Utilisation

### Lancement standard

Depuis votre terminal PowerShell (avec l'environnement virtuel activé) :

```powershell
python main.py

```

### Lancement avec Scan Réseau (Module 3)

Le module de détection d'OS (Nmap) nécessite des droits élevés pour envoyer des paquets bruts.

1. Faites un clic droit sur PowerShell ou CMD.
2. Sélectionnez **"Exécuter en tant qu'administrateur"**.
3. Naviguez vers le dossier et activez l'environnement :
```powershell
cd C:\Chemin\Vers\NTL-SysToolbox
.venv\Scripts\activate
python main.py

```



### Options du Menu

* **[1] OS Lifecycle Information :** Interroge l'API publique pour vérifier le statut de support (EOL).
* **[2] Audit Obsolescence (CSV) :** Analyse un fichier `inventory.csv` local.
* **[3] Network Scan :** Cartographie le réseau et détecte les OS actifs (Mode Admin requis).
* **[4] Encrypt / [5] Decrypt :** Utilitaires de chiffrement/déchiffrement du fichier de secrets.

## 5. Localisation des Rapports

Les rapports sont générés automatiquement dans l'arborescence du projet et sont à cet emplacement par défaut :

* **Rapports JSON** : `.\data\audit\`
* **Rapports CSV** (Compatibles Excel) : `.\data\audit\csv\`

Les fichiers sont horodatés (ex: `network_scan_20260131_1430.csv`) pour assurer la traçabilité.