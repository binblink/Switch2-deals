# Switch2 Deals

Suivi automatique des prix Amazon des jeux Nintendo Switch 2. Le pipeline récupère régulièrement les prix et permet de visualiser leur évolution dans le temps via un dashboard web.

## Stack

- **Python** — ETL, scraping
- **PostgreSQL** — stockage des données
- **Playwright** — scraping Amazon
- **APScheduler** — orchestration des jobs automatiques
- **Flask** — API et dashboard web
- **Docker** — containerisation

## Prérequis

- Python 3.12+
- Docker Desktop

## Installation

### 1. Cloner le repo

```bash
git clone https://github.com/binblink/Switch2-deals.git
cd Switch2-deals
```

### 2. Créer l'environnement virtuel

```bash
python -m venv src/venv

# Windows
.\src\venv\Scripts\Activate.ps1

# Linux / Mac
source src/venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

### 4. Configurer les variables d'environnement

Copie le fichier `.env.example` et renseigne tes valeurs :

```bash
cp .env.example .env
```

```env
IGDB_CLIENT_ID=ton_client_id
IGDB_CLIENT_SECRET=ton_client_secret
DB_HOST=localhost
DB_NAME=switchdeals
DB_USER=postgres
DB_PASSWORD=postgres
FLASK_SECRET_KEY=une_chaine_aleatoire_longue
```

Pour obtenir un `IGDB_CLIENT_ID` et `IGDB_CLIENT_SECRET` :
1. Crée un compte sur [dev.twitch.tv](https://dev.twitch.tv)
2. Crée une application
3. Récupère le Client ID et génère un Client Secret

### 5. Démarrer la base de données

```bash
docker compose up -d
```

pgAdmin est accessible sur [http://localhost:5050](http://localhost:5050)
- Email : `admin@admin.com`
- Password : `admin`

## Utilisation

```bash
cd src
$env:PYTHONPATH="."  # Windows PowerShell

# Synchroniser le catalogue de jeux depuis IGDB
python main.py sync

# Scraper les prix Amazon
python main.py scrape

# Lancer le scheduler automatique (sync 1x/jour, scrape toutes les 2h)
python scheduler.py

# Lancer le dashboard web
python api/app.py
```

## Dashboard

Le dashboard est accessible sur [http://localhost:5000](http://localhost:5000)

- **Page principale** — liste des jeux avec prix actuels, tendances hausse/baisse, recherche
- **Page admin** — correction manuelle des ASINs Amazon (`/admin`)
  - Correction d'ASIN par jeu avec mise à jour immédiate du prix et de l'image
  - Exclusion individuelle ou en masse des jeux non disponibles sur Amazon
- **API prix** — historique des prix par jeu (`/api/game/<id>/prices`)

## Structure du projet

```
Switch2-deals/
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── README.md
└── src/
    ├── igdb/
    │   ├── client.py       # Auth OAuth2 + appels API IGDB
    │   └── sync.py         # Synchronisation du catalogue
    ├── amazon/
    │   ├── scraper.py      # Scraping des prix Amazon
    │   └── sync.py         # Résolution ASINs + insertion en base
    ├── db/
    │   ├── connection.py   # Pool de connexions PostgreSQL
    │   ├── schema.py       # Création des tables
    │   └── queries.py      # Requêtes SQL
    ├── api/
    │   └── app.py          # Flask — routes et dashboard
    ├── templates/
    │   ├── index.html      # Dashboard principal
    │   └── admin.html      # Page d'administration
    ├── static/
    │   ├── css/
    │   │   └── style.css
    │   └── js/
    │       └── app.js
    ├── scheduler.py        # Jobs automatiques (APScheduler)
    └── main.py             # Point d'entrée CLI
```

## Pipeline

```
IGDB API  →  sync catalogue (1x/jour)   →  PostgreSQL (games)
                                                  │
Amazon.fr →  resolve ASINs              →  PostgreSQL (products)
                                                  │
Amazon.fr →  scrape prix (toutes 2h)   →  PostgreSQL (prices)
                                                  │
                                         Flask Dashboard
                                         └── /         (liste des jeux)
                                         └── /admin    (gestion ASINs)
```

## Schéma de base de données

```
games        →  catalogue IGDB
products     →  correspondance Amazon (ASIN, image)
prices       →  historique des prix (1 entrée max par produit par jour)
```