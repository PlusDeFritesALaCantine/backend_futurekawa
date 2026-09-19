# backend_futurekawa

Backend central siège FastAPI — agrège les données de tous les pays (Brésil, Équateur, Colombie)
et relaie les écritures vers l'API du pays concerné. **Point d'entrée unique du front.**

## Fonctionnalités

- **Proxy par pays, lecture et écriture** : relaie chaque requête `/pays/{pays}/...` vers l'API
  `api_futurekawa` correspondante (une instance par pays en théorie ; en démo locale, `BRESIL_API_URL`,
  `EQUATEUR_API_URL` et `COLOMBIE_API_URL` pointent vers la même instance `api_futurekawa`
  qui sert les 3 jeux de données par filtre `?pays=`).
- **Dashboard consolidé** (`/dashboard`) : agrège pour les 3 pays le nombre de lots, les
  alertes actives et la dernière mesure, avec dégradation gracieuse si une API pays est hors ligne.
- **Écritures relayées** : `POST` / `PATCH` / `DELETE` sur les lots. Le front n'écrit plus
  jamais en direct vers une API pays. Le **code de statut de l'API pays est préservé** : un
  `409 Lot déjà existant` arrive tel quel, seul un vrai défaut réseau produit un `503`.
- **Intégration Odoo** (`odoo/`) : réplique chaque lot FutureKawa dans Odoo comme un
  `stock.lot` traçable (statut qualité, alertes en note de chatter + activité planifiée),
  **et remonte les corrections saisies dans l'ERP** — voir `odoo/README.md`.

> ⚠️ `odoo/` est une copie du dépôt autonome `odoo_integration`, montée sur `/odoo` par
> `app/main.py`. Les deux doivent être modifiées ensemble tant que le doublon existe.

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
| POST    | `/pays/{pays}/lots`          | Créer un lot — le pays de l'URL fait foi                |
| PATCH   | `/pays/{pays}/lots/{id}`     | Mise à jour partielle d'un lot                          |
| DELETE  | `/pays/{pays}/lots/{id}`     | Supprimer un lot                                        |
| GET     | `/pays/{pays}/lots/{id}/mesures` | Relevés d'un lot                                    |
| GET     | `/pays/{pays}/mesures`       | Mesures paginées (`?entrepot_id=&lot_id=&debut=&fin=&limit=&offset=`) |
| GET     | `/pays/{pays}/mesures/latest`| Un relevé par entrepôt, sans rapatrier l'historique     |
| GET     | `/pays/{pays}/alertes`       | État courant calculé (proxy)                            |
| GET     | `/pays/{pays}/alertes/journal` | Alertes persistées, paginées                          |
| POST    | `/pays/{pays}/alertes/synchroniser` | Force un cycle d'alignement                      |
| PATCH   | `/pays/{pays}/alertes/{id}/acquitter` | Prise en charge                                |
| PATCH   | `/pays/{pays}/alertes/{id}/resoudre`  | Clôture manuelle                               |
| GET     | `/pays/{pays}/parametres`    | Paramétrage du pays                                     |
| PATCH   | `/pays/{pays}/parametres`    | Modifier seuils / péremption / destinataire             |
| GET     | `/dashboard`                 | Vision consolidée : nb lots, alertes, dernière mesure   |
| POST    | `/odoo/sync?dry_run=`        | Synchronisation Odoo, dans les deux sens                |

## Variables d'environnement

| Variable          | Description               | Défaut                          |
|-------------------|---------------------------|---------------------------------|
| `BRESIL_API_URL`  | URL API Brésil            | `http://api_futurekawa:8001`    |
| `EQUATEUR_API_URL`| URL API Équateur (simulé) | `http://equateur-api:8001`      |
| `COLOMBIE_API_URL`| URL API Colombie (simulé) | `http://colombie-api:8001`      |
| `API_PORT`        | Port d'écoute             | `8002`                          |

## Comportement dégradé

Si une API pays est hors ligne, le `/dashboard` retourne `"status": "indisponible"` pour ce pays sans faire planter la réponse globale.

Sur les autres routes, la distinction est nette : **`503` uniquement si l'API pays est
injoignable**. Une erreur métier (`404`, `409`, `422`) est relayée avec son code et son
message d'origine — sans quoi l'utilisateur croirait le service en panne au lieu de corriger
sa saisie.

## Tests

⚠️ `pytest` seul échoue à la racine (`ImportPathMismatchError`) : deux répertoires `tests/`
avec un `conftest.py` chacun sous la même racine. Il faut préciser le chemin.

```bash
pip install -r requirements.txt
pytest tests -q        # 26 tests — dashboard, proxy, écritures relayées
pytest odoo/tests -q   # 51 tests — intégration Odoo (montante et descendante)
```
