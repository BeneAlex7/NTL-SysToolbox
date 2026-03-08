# Dossier Technique et Fonctionnel - NTL-SysToolbox

**Version :** 1.0.0
**Auteur :** Équipe d'Ingénierie
**Date :** 8 Mars 2026

---

## 1. Introduction et Objectifs
Le **NTL-SysToolbox** est un outil en ligne de commande (CLI) développé en Python visant à centraliser les opérations critiques d'audit, de diagnostic et de sauvegarde pour l'infrastructure mixte (Windows/Linux) de Nord Transit Logistics. 
Ce document justifie les choix architecturaux, l'ergonomie, la démarche d'audit retenue, ainsi que les compromis techniques assumés lors de sa conception.

## 2. Architecture Logique et Répartition par Modules

L'outil adopte une architecture **modulaire** et **extensible**. Le point d'entrée central (`main.py`) agit comme un chef d'orchestre interactif ou automatisable, qui délègue les tâches spécialisées à des modules isolés.

### Structuration du projet :
* **`main.py`** : Point d'entrée. Gère l'interface interactive (CLI avec la librairie `rich`), le parsing des arguments (`argparse`), la vérification des privilèges (Admin/Root) et le chargement sécurisé (Vault).
* **`core/`** : Composants transverses.
  * `config_loader.py` : Chargeur de la configuration YAML et intégration du Vault.
  * `security.py` : Logique de chiffrement/déchiffrement des secrets (Fernet/Cryptography).
  * `logger.py` : Formateur de logs (Sortie standard lisible ou JSON).
* **`modules/`** : Logiques métier isolées.
  * `audit.py` : Interrogation réseau (Nmap), parsing de CSV (Inventaire) et appels API externes pour analyser l'obsolescence.
  * `diagnostic.py` : Vérifications de santé Active Directory/DNS, base de données WMS (MySQL), et métriques systèmes via requêtes distantes (WinRM pour Windows, SSH pour Linux).
  * `backup.py` : Opérations de sauvegarde (SQL complet via `mysqldump` distant ou extraction CSV ciblée via base MySQL).

**Justification du choix :** 
L'isolation modulaire permet à plusieurs ingénieurs de travailler en parallèle, facilite l'ajout ultérieur de nouveaux diagnostics (ex: module Cloud) sans impacter le cœur de l'application, et rend le débogage plus granulaire.

## 3. Mode de Configuration et Gestion des Secrets

### La Configuration (YAML)
Les paramètres non sensibles (seuils d'alerte, liste des IP des serveurs, plages réseaux à scanner, environnement courant) sont stockés dans un fichier texte clair `config.yaml`.
* **Pourquoi YAML ?** Moins verbeux que le XML et plus lisible humainement que le JSON, le YAML est un standard DevOps (utilisé par Docker, Kubernetes, Ansible) qui est facilement modifiable par les administrateurs systèmes.

### Le Vault (Chiffrement des Secrets)
Pour répondre aux exigences de sécurité et éviter les mots de passe en clair dans les scripts ou les fichiers de configuration, un module "Vault" maison a été conçu, basé sur la cryptographie symétrique Fernet (AES-128 en mode CBC).
* **Fonctionnement :** L'utilisateur renseigne les données sensibles (mots de passe BDD, identifiants SSH/WinRM) dans un fichier `secret.yaml`. Via le menu, ce fichier est chiffré pour devenir `secret.yaml.enc` via un mot de passe maître saisi dynamiquement. L'original est alors écrasé et supprimé.
* **Chargement en mémoire :** Au lancement (`main.py`), le programme demande ce mot de passe maître. Le fichier `.enc` est déchiffré *exclusivement en RAM*, fusionné dynamiquement dans le dictionnaire de configuration Python, et transmis aux modules sans jamais être réécrit sur le disque.

**Compromis assumé :** 
Nous avons choisi un Vault local chiffré symétriquement plutôt qu'une solution lourde type HashiCorp Vault. Le compromis est un déploiement simplifié n'exigeant aucune infrastructure supplémentaire, au prix d'une gestion de clé maître manuelle qui repose sur l'humain.

## 4. Ergonomie du Menu Interactif

L'interface a été conçue autour de la librairie **`rich`** pour offrir une expérience CLI moderne.
* **Couleurs et Panneaux :** Utilisation de codes couleurs stricts (Rouge=Critique/Erreur, Jaune=Avertissement, Vert=Succès/Supporté, Cyan=Information). Les panneaux encadrent visuellement l'application.
* **Guidage de l'utilisateur :** Le menu désactive dynamiquement les options non autorisées. Par exemple, si l'outil n'est pas lancé en Administrateur/Root, l'option de Scan Réseau (qui nécessite l'envoi de paquets bruts `SYN` via Nmap pour l'OS Fingerprinting) est affichée avec un avertissement préalable et bloquée pour éviter les plantages ou faux positifs.
* **Dualité Interactif / Automatisé :** Bien que l'outil propose un menu interactif riche, chaque action a été mappée vers un paramètre `--action`. Ceci permet une intégration totale dans une CI/CD ou des tâches `cron` sans briser l'ergonomie visuelle. (Le flag `--json` masque les artéfacts visuels `rich` pour offrir une sortie machine stricte).

## 5. Démarche de l'Audit d'Obsolescence

L'audit du cycle de vie des systèmes d'exploitation repose sur deux démarches complémentaires gérées par `audit.py` :
1. **Source de Référence API :** Appel dynamique à l'API publique `https://endoflife.date/api/`. 
2. **Audit Hors-Ligne (CSV) :** Croisement des données EOL (End of Life) téléchargées avec le parc déclaré dans `inventory.csv`.

**Date de validité et fiabilité :**
Les données EOL provenant de `endoflife.date` sont maintenues par une large communauté open-source et régulièrement mises à jour. L'outil effectue ces requêtes *en direct* lors de chaque lancement, ce qui garantit que l'audit reflète l'état officiel de l'industrie au moment *M*.

**Logique d'alerte métier :**
L'algorithme de calcul des risques a été ajusté en fonction de la criticité temporelle :
* **EXPIRED (Violet) :** Date dépassée, système non supporté, vulnérabilités critiques non corrigées.
* **CRITICAL (Rouge) :** Moins de 180 jours (6 mois) avant expiration. Exige un plan de migration prioritaire.
* **WARNING (Orange) :** Entre 6 mois et 1 an avant expiration. Le budget et la stratégie de renouvellement doivent être planifiés.
* **SUPPORTED (Vert) :** Plus d'un an de support.

## 6. Choix Techniques Globaux et Compromis

* **Python vs Go / Rust :** Python 3.8+ a été retenu pour son immense écosystème d'administration système (Paramiko, WinRM, mysql-connector, Nmap parser) et sa facilité de reprise par les équipes d'exploitation. Le compromis est que Python requiert un environnement (`venv`) contrairement à un binaire Go statique.
* **Nmap pour la détection :** La tâche de détection d'OS réseau a été confiée à Nmap (`-O --osscan-guess`) interfacé via `python-nmap`. Bien que plus lourd qu'un simple scan de port maison, Nmap est la norme absolue de l'industrie pour le Fingerprinting réseau (signature TCP/IP).
* **Diagnotics Distants sans Agent :** Nous avons choisi une approche _Agentless_ (WinRM pour Windows, SSH pour Linux) pour le module de métriques. Le grand avantage est de n'avoir aucun programme à installer ou maintenir sur le parc lourd. Le compromis est la variabilité des environnements (le service WinRM doit être pré-configuré sur les hôtes Windows).
* **Backup WMS via mysqldump :** Plutôt que de coder une solution de copie binaire de la base de données (sujette à des locks), le module invoque `mysqldump` à travers le tunnel SSH distant puis redirige sa sortie vers un pipeline de compression locale `gzip`. C'est robuste, respecte l'intégrité transactionnelle, mais requiert une bande passante stable durant le transfert du flux SQL.

---
*Ce document forme l'appendice technique final du projet NTL-SysToolbox livré à la DSI.*
