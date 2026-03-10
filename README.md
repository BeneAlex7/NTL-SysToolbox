Voici une version épurée, factuelle et professionnelle du README.md, adaptée à un rendu académique et technique.
NTL-SysToolbox v1.0

NTL-SysToolbox est une solution d'administration système centralisée conçue pour la DSI de Nord Transit Logistics. L'outil permet de piloter l'infrastructure des sites de Lille, Lens, Valenciennes et Arras via une interface en ligne de commande (CLI).
Fonctionnalités principales

    Audit d'obsolescence : Identification de la dette technique par croisement entre scans Nmap et l'API endoflife.date.

    Diagnostic de santé : Monitoring à distance des ressources (CPU, RAM, Disque) et des services critiques (AD, DNS, MySQL).

    Module de sauvegarde : Automatisation des extractions SQL complètes et des exports métier au format CSV.

    Sécurité des accès : Chiffrement des identifiants via AES-128 et gestion d'un mot de passe maître pour le déchiffrement en mémoire vive.

Architecture du projet

Le projet est structuré de manière modulaire pour faciliter la maintenance :

    core/ : Gestion de la configuration, de la sécurité et du moteur de l'application.

    modules/ : Contient la logique métier (audit.py, diagnostic.py, backup.py).

    data/ : Répertoire de stockage des rapports générés et des archives de sauvegarde.

    main.py : Point d'entrée principal de l'application.

Installation

    Clonage du dépôt :

    Installation des dépendances :

    Note : Les bibliothèques principales incluent rich, paramiko, pywinrm, mysql-connector-python et cryptography.

Utilisation

Le lancement s'effectue par la commande :

L'utilisateur doit saisir le mot de passe maître pour déverrouiller l'accès aux serveurs distants. Pour les fonctions de détection d'OS (Module Audit), l'exécution avec des privilèges élevés (Administrateur ou Sudo) est requise.
Gestion des sources et versioning

Le code source, l'historique des modifications et la documentation technique sont hébergés sur GitLab.
