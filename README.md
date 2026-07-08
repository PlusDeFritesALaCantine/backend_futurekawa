# backend_futurekawa

Backend central siège FastAPI — agrège les données de tous les pays (Brésil, Équateur, Colombie) via proxy HTTP.

## Fonctionnalités

- **Proxy par pays** : relaie chaque requête `/pays/{pays}/...` vers l'API `api_futurekawa`
  correspondante (une instance par pays en théorie ; en démo locale, `BRESIL_API_URL`,
  `EQUATEUR_API_URL` et `COLOMBIE_API_URL` pointent vers la même instance `api_futurekawa`
  qui sert les 3 jeux de données par filtre `?pays=`).
- **Dashboard consolidé** (`/dashboard`) : agrège pour les 3 pays le nombre de lots, les
  alertes actives et la dernière mesure, avec dégradation gracieuse si une API pays est hors ligne.
- **Intégration Odoo** (`odoo/`) : réplique chaque lot FutureKawa dans Odoo comme un
  `stock.lot` traçable (statut qualité, alertes en note de chatter + activité planifiée) —
  voir `odoo/README.md`.

## Prérequis

- Docker & Docker Compose

## Lancement

```bash
cp .env.example .env
docker compose up --build
```

L'API démarre sur `http://localhost:8002`.

## Développement local

```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8002
```

## Endpoints

| Méthode | Route                        | Description                                             |
|---------|------------------------------|---------------------------------------------------------|
| GET     | `/health`                    | Healthcheck                                             |
| GET     | `/pays`                      | Liste des pays configurés                               |
| GET     | `/pays/{pays}/lots`          | Lots du pays (proxy)                                    |
| GET     | `/pays/{pays}/mesures`       | Mesures du pays (proxy, `?entrepot_id=` optionnel)      |
| GET     | `/pays/{pays}/alertes`       | Alertes du pays (proxy)                                 |
| GET     | `/dashboard`                 | Vision consolidée : nb lots, alertes, dernière mesure   |

## Variables d'environnement

| Variable          | Description               | Défaut                          |
|-------------------|---------------------------|---------------------------------|
| `BRESIL_API_URL`  | URL API Brésil            | `http://api_futurekawa:8001`    |
| `EQUATEUR_API_URL`| URL API Équateur (simulé) | `http://equateur-api:8001`      |
| `COLOMBIE_API_URL`| URL API Colombie (simulé) | `http://colombie-api:8001`      |
| `API_PORT`        | Port d'écoute             | `8002`                          |

## Comportement dégradé

Si une API pays est hors ligne, le `/dashboard` retourne `"status": "indisponible"` pour ce pays sans faire planter la réponse globale.

## Tests

```bash
pip install -r requirements.txt
pytest
```
