# Documentation du Projet de Prévisions Commerciales

## Table des matières

1. [Introduction](#1-introduction)
2. [Architecture du système](#2-architecture-du-système)
3. [Configuration requise](#3-configuration-requise)
4. [Installation](#4-installation)
5. [Structure du projet](#5-structure-du-projet)
6. [Base de données](#6-base-de-données)
7. [Fonctionnalités clés](#7-fonctionnalités-clés)
8. [Aspects techniques](#8-aspects-techniques)
9. [Modules et composants](#9-modules-et-composants)
10. [API et points d'accès](#10-api-et-points-daccès)
11. [Tests et validation](#11-tests-et-validation)
12. [Déploiement](#12-déploiement)
13. [Maintenance](#13-maintenance)
14. [Conclusion](#14-conclusion)

## 1. Introduction

### 1.1 Contexte du projet

Le projet de Prévisions Commerciales est un système d'analyse et de prévision conçu pour les entreprises souhaitant exploiter leurs données de ventes historiques afin d'anticiper les tendances futures. Cette application web permet d'analyser les ventes selon deux axes principaux : par client et par produit.

### 1.2 Objectifs

- Fournir une interface intuitive pour analyser les données commerciales
- Générer des prévisions de ventes fiables basées sur l'historique des transactions
- Visualiser les tendances de ventes par client et par produit
- Offrir des outils d'aide à la décision pour optimiser la stratégie commerciale

### 1.3 Public cible

- Équipes commerciales et marketing
- Responsables de la planification des ventes
- Directeurs financiers
- Analystes de données commerciales

## 2. Architecture du système

### 2.1 Architecture globale

Le système est construit selon une architecture web classique client-serveur avec les composants suivants :

- **Frontend** : Interface utilisateur en HTML, CSS et JavaScript
- **Backend** : Serveur Flask en Python
- **Base de données** : Système MySQL pour le stockage des données
- **Moteur de prévision** : Bibliothèque Prophet de Facebook pour les modèles prédictifs

### 2.2 Diagramme d'architecture

```
+----------------+      +----------------+      +----------------+
|                |      |                |      |                |
|  Client Web    |----->|  Serveur Flask |----->|  Base de       |
|  (Navigateur)  |<-----|  (Python)      |<-----|  données MySQL |
|                |      |                |      |                |
+----------------+      +----------------+      +----------------+
                              |
                              v
                        +----------------+
                        |                |
                        |  Prophet       |
                        |  (Prévisions)  |
                        |                |
                        +----------------+
```

### 2.3 Flux de données

1. L'utilisateur accède à l'interface web via son navigateur
2. Le serveur Flask traite les requêtes et interroge la base de données
3. Les données sont extraites, transformées et analysées
4. Les modèles de prévision sont appliqués aux données historiques
5. Les résultats sont présentés à l'utilisateur sous forme de graphiques et tableaux

## 3. Configuration requise

### 3.1 Environnement serveur

- Système d'exploitation : Windows, Linux ou macOS
- Python 3.8 ou supérieur
- Serveur web compatible WSGI (pour le déploiement en production)
- MySQL 5.7 ou supérieur

### 3.2 Dépendances Python

Les principales bibliothèques Python requises sont :

```
flask==2.0.1
pandas==1.3.3
numpy==1.21.2
matplotlib==3.4.3
prophet==1.0.1
mysql-connector-python==8.0.26
```

### 3.3 Navigateurs supportés

- Google Chrome (version 90+)
- Mozilla Firefox (version 88+)
- Microsoft Edge (version 90+)
- Safari (version 14+)

## 4. Installation

### 4.1 Préparation de l'environnement

1. Installer Python 3.8 ou supérieur
2. Installer MySQL 5.7 ou supérieur
3. Créer une base de données nommée `pfe1`

### 4.2 Installation des dépendances

```bash
# Cloner le dépôt (si applicable)
git clone <url-du-repository>
cd souha

# Créer un environnement virtuel Python
python -m venv venv

# Activer l'environnement virtuel
# Sur Windows
venv\Scripts\activate
# Sur Linux/macOS
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

### 4.3 Configuration de la base de données

1. Créer la base de données MySQL :

```sql
CREATE DATABASE pfe1;
```

2. Exécuter le script SQL fourni pour initialiser les tables :

```bash
mysql -u root -p pfe1 < schema.sql
```

### 4.4 Configuration de l'application

Vérifier les paramètres de connexion à la base de données dans `app.py` :

```python
# Database connection function
def get_db_connection():
    server = '127.0.0.1'
    database = 'pfe1'
    username = 'root'
    password = ''
    
    conn = mysql.connector.connect(
        host=server,
        database=database,
        user=username,
        password=password
    )
    return conn
```

### 4.5 Téléchargement des images de produits (optionnel)

Pour télécharger automatiquement les images de produits depuis une source externe :

```bash
python download_product_images.py
```

## 5. Structure du projet

### 5.1 Organisation des fichiers

```
app.py                     # Application principale Flask
product_analysis.py        # Module d'analyse des produits
download_product_images.py # Utilitaire de téléchargement d'images
requirements.txt           # Liste des dépendances Python
static/                    # Ressources statiques
  ├── css/                 # Feuilles de style CSS
  │   └── style.css        # Styles personnalisés
  └── product_images/      # Images des produits
templates/                 # Templates HTML
  ├── index.html           # Page d'accueil
  ├── clients.html         # Liste des clients
  ├── dashboard.html       # Tableau de bord client
  ├── products.html        # Liste des produits
  ├── product_dashboard.html # Tableau de bord produit
  └── error.html           # Page d'erreur
```

### 5.2 Modèles de données

Les principales entités de la base de données sont :

- **clients** : Informations sur les clients
- **entetecommercials** : En-têtes des transactions commerciales
- **lignecommercials** : Détails des lignes de transactions
- **produits** : Catalogue des produits

## 6. Base de données

### 6.1 Schéma de la base de données

#### Table `clients`
| Colonne | Type | Description |
|---------|------|-------------|
| code | VARCHAR(50) | Code unique du client (clé primaire) |
| nom | VARCHAR(100) | Nom du client |
| prenom | VARCHAR(100) | Prénom du client |
| adresse | TEXT | Adresse du client |
| telephone | VARCHAR(20) | Numéro de téléphone |

#### Table `produits`
| Colonne | Type | Description |
|---------|------|-------------|
| code | VARCHAR(50) | Code unique du produit (clé primaire) |
| libelle | VARCHAR(255) | Nom/libellé du produit |
| prix | DECIMAL(10,2) | Prix du produit |
| description | TEXT | Description du produit |
| famille_libelle | VARCHAR(100) | Catégorie du produit |

#### Table `entetecommercials`
| Colonne | Type | Description |
|---------|------|-------------|
| code | VARCHAR(50) | Code unique de la transaction (clé primaire) |
| date | DATE | Date de la transaction |
| client_code | VARCHAR(50) | Code client (clé étrangère) |
| net_a_payer | DECIMAL(10,2) | Montant total à payer |

#### Table `lignecommercials`
| Colonne | Type | Description |
|---------|------|-------------|
| id | INT | Identifiant unique (clé primaire) |
| entetecommercial_code | VARCHAR(50) | Code de l'en-tête (clé étrangère) |
| produit_code | VARCHAR(50) | Code produit (clé étrangère) |
| quantite | INT | Quantité vendue |
| prix_unitaire | DECIMAL(10,2) | Prix unitaire |

### 6.2 Relations

- Un client peut avoir plusieurs transactions (entetecommercials)
- Une transaction appartient à un seul client
- Une transaction peut contenir plusieurs lignes de détail (lignecommercials)
- Chaque ligne de détail concerne un seul produit

## 7. Fonctionnalités clés

### 7.1 Analyse par client

- **Vue d'ensemble client** : Affichage des informations générales du client
- **Panier moyen** : Calcul du panier moyen sur une période définie
- **Top produits** : Identification des produits les plus achetés par le client
- **Prévisions** : Génération de prévisions d'achats futurs basées sur l'historique

### 7.2 Analyse par produit

- **Évolution des ventes** : Graphique d'évolution des ventes mensuelles du produit
- **Top clients** : Classement des principaux clients pour un produit spécifique
- **Historique détaillé** : Tableau des ventes historiques du produit
- **Prévisions** : Projection des ventes futures du produit

### 7.3 Prévisions

- **Modélisation** : Utilisation de Prophet pour créer des modèles de prévision
- **Composantes** : Décomposition des prévisions en tendances, saisonnalités et résidus
- **Intervalles de confiance** : Affichage des limites inférieures et supérieures des prévisions
- **Exportation** : Possibilité d'exporter les données prévisionnelles au format Excel

### 7.4 Interface utilisateur

- **Navigation par onglets** : Interface à onglets pour basculer entre les analyses
- **Recherche** : Fonctionnalité de recherche rapide de clients ou produits
- **Visualisations interactives** : Graphiques et tableaux interactifs
- **Design responsive** : Interface adaptable aux différentes tailles d'écran

## 8. Aspects techniques

### 8.1 Framework web

Le projet utilise Flask, un micro-framework web pour Python, qui offre :

- Un routage simplifié des URL
- Un moteur de templating Jinja2 intégré
- Une architecture légère et modulaire
- Une simplicité d'extension avec des modules complémentaires

### 8.2 Visualisation de données

Les visualisations sont générées avec :

- **Matplotlib** : Pour la création des graphiques côté serveur
- **Bootstrap** : Pour le rendu responsive des contenus
- **DataTables** : Pour les tableaux interactifs

### 8.3 Modèle prédictif

Le système utilise Prophet, une bibliothèque de prévisions temporelles développée par Facebook :

- **Robustesse** : Gestion efficace des données manquantes et des valeurs aberrantes
- **Saisonnalité** : Détection automatique des motifs saisonniers (hebdomadaires, mensuels, annuels)
- **Tendances** : Identification des tendances à long terme
- **Points de rupture** : Détection des changements significatifs dans les tendances

### 8.4 Sécurité

Mesures de sécurité implémentées :

- **Requêtes paramétrées** : Protection contre les injections SQL
- **Validation des entrées** : Vérification des paramètres utilisateur
- **Gestion des erreurs** : Capture et journalisation des exceptions

## 9. Modules et composants

### 9.1 Module principal (app.py)

Le module principal contient :

- La configuration de l'application Flask
- Les fonctions de connexion à la base de données
- Les routes principales de l'application
- Les fonctions d'analyse et de prévision client

### 9.2 Module d'analyse produit (product_analysis.py)

Module spécifique pour l'analyse des produits :

- Extraction des données de vente par produit
- Génération des graphiques d'évolution des ventes
- Analyse des clients principaux par produit
- Prévisions de ventes futures par produit

### 9.3 Module de téléchargement d'images (download_product_images.py)

Utilitaire pour télécharger et gérer les images des produits :

- Récupération d'images depuis des sources externes
- Redimensionnement et optimisation des images
- Sauvegarde locale dans le répertoire static/product_images
- Journalisation des opérations de téléchargement

## 10. API et points d'accès

### 10.1 Routes principales

| URL | Méthode | Description |
|-----|---------|-------------|
| / | GET | Page d'accueil avec onglets client et produit |
| /clients | GET | Liste de tous les clients |
| /products | GET | Liste de tous les produits |
| /dashboard/<client_code> | GET | Tableau de bord d'un client spécifique |
| /product_dashboard/<product_code> | GET | Tableau de bord d'un produit spécifique |

### 10.2 API REST

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| /api/forecast/<client_code> | GET | Prévisions pour un client |
| /api/top_products/<client_code> | GET | Top produits pour un client |
| /api/average_basket/<client_code> | GET | Panier moyen d'un client |
| /api/product_sales/<product_code> | GET | Données de vente d'un produit |
| /api/product_forecast/<product_code> | GET | Prévisions pour un produit |

### 10.3 Points d'accès auxiliaires

| URL | Méthode | Description |
|-----|---------|-------------|
| /search_clients | GET | Recherche de clients |
| /search_products | GET | Recherche de produits |
| /download_forecast/<client_code> | GET | Téléchargement des prévisions client en Excel |
| /download_product_sales/<product_code> | GET | Téléchargement des ventes produit en Excel |
| /product_image/<product_code> | GET | Récupération de l'image d'un produit |

## 11. Tests et validation

### 11.1 Tests unitaires

Les tests unitaires valident :

- Le fonctionnement des fonctions clés du système
- Les calculs statistiques et les prévisions
- La manipulation correcte des données

### 11.2 Tests d'intégration

Vérification de :
- La communication entre les composants
- L'interaction avec la base de données
- L'intégrité des flux de données

### 11.3 Tests de l'interface utilisateur

- Validation de l'expérience utilisateur sur différents navigateurs
- Tests de responsive design (mobile, tablette, desktop)
- Vérification des interactions et comportements dynamiques

## 12. Déploiement

### 12.1 Déploiement local

Pour exécuter l'application en mode développement :

```bash
# Activer l'environnement virtuel
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Lancer l'application
python app.py
```

L'application sera accessible à l'adresse http://localhost:5000

### 12.2 Déploiement en production

Pour un déploiement en production, il est recommandé d'utiliser :

- **Serveur WSGI** : Gunicorn (Linux/macOS) ou Waitress (Windows)
- **Proxy inverse** : Nginx ou Apache
- **SSL** : Configuration HTTPS pour la sécurisation des communications

Exemple de configuration avec Gunicorn et Nginx :

```bash
# Installation de Gunicorn
pip install gunicorn

# Lancement de l'application avec Gunicorn
gunicorn -w 4 -b 127.0.0.1:8000 app:app
```

Configuration Nginx :

```nginx
server {
    listen 80;
    server_name votre-domaine.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 12.3 Automatisation du déploiement

Possibilités d'automatisation :

- Scripts shell pour le déploiement
- Intégration continue (CI/CD)
- Conteneurs Docker pour la standardisation de l'environnement

## 13. Maintenance

### 13.1 Sauvegarde des données

Processus recommandé :

- Sauvegarde quotidienne de la base de données
- Conservation des sauvegardes pendant au moins 30 jours
- Test régulier de restauration des sauvegardes

### 13.2 Mises à jour

Procédure de mise à jour :

1. Sauvegarde préalable de l'application et de la base de données
2. Application des mises à jour du code
3. Migration de la base de données si nécessaire
4. Tests de non-régression
5. Redémarrage du service

### 13.3 Surveillance

Outils de surveillance à mettre en place :

- Journalisation des erreurs applicatives
- Surveillance des performances du serveur
- Alertes en cas de problèmes détectés

## 14. Conclusion

### 14.1 Bilan du projet

Le système de Prévisions Commerciales offre une solution complète pour l'analyse et la prévision des ventes. Il permet aux utilisateurs de visualiser les tendances passées, d'identifier les produits et clients clés, et d'anticiper les ventes futures grâce à des modèles prédictifs avancés.

### 14.2 Perspectives d'évolution

Améliorations futures envisageables :

- **Apprentissage automatique avancé** : Intégrer d'autres algorithmes de prévision
- **Tableau de bord personnalisable** : Permettre aux utilisateurs de configurer leur vue
- **Alertes automatiques** : Notifier les utilisateurs en cas d'anomalie détectée
- **Application mobile** : Développer une version mobile de l'application
- **Intégration avec d'autres systèmes** : Connecter l'application à des CRM, ERP, etc.

### 14.3 Remerciements

Ce projet a été réalisé dans le cadre d'un projet de fin d'études avec le soutien de l'équipe encadrante et des différents intervenants qui ont apporté leur expertise et leurs conseils tout au long du développement.

---

© 2025 - Projet de Prévisions Commerciales