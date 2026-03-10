NTL-SysToolbox v1.0

Outil CLI d'administration système développé pour Nord Transit Logistics. Ce programme centralise le diagnostic, l'audit d'obsolescence et la gestion des sauvegardes sur les sites de Lille (Siège), Lens, Valenciennes et Arras.
Fonctions principales

    Audit d'obsolescence : Scan réseau (Nmap) et vérification des dates de fin de support (EOL) via l'API endoflife.date.

    Diagnostic : Monitoring des ressources (CPU/RAM/Disque) et état des services critiques (AD, DNS, MySQL).

    Sauvegarde : Exports SQL et CSV de la base de données WMS.

    Sécurité : Chiffrement Fernet/AES-128 des identifiants et gestion des privilèges Root/Admin.

Utilisation

    Lancer l'outil : python main.py.

    Saisir le Master Password pour charger les secrets en mémoire vive.

    Naviguer dans le menu interactif (librairie Rich) pour choisir un module.
