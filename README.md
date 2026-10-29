# ijustate-server

The shared food catalog behind the [IJustAte](https://github.com/davidsonpoole/IJustAte)
iOS app. Serves approved foods, accepts new submissions, and holds them for
manual approval in the Django admin.

Django 4.1 + DRF, SQLite, Python 3.9+.

## Setup

Settings that differ per deployment are not committed. Create your own before
starting:

```sh
cp ijustateserver/local_settings.example.py ijustateserver/local_settings.py
```

Set `SECRET_KEY` and `ALLOWED_HOSTS` in it. Generate a key with:

```sh
./venv/bin/python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

`local_settings.py` is gitignored, and Django will refuse to start without it.
Keep `DEBUG = False` on anything reachable from the internet: Django's debug
pages disclose your settings, paths and hostnames to anyone who can trigger a
500.

Then:

```sh
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/python manage.py migrate
./venv/bin/python manage.py create_foods      # seed from food_data/*.csv
./venv/bin/python manage.py createsuperuser   # needed to approve submissions
```

`create_foods` is keyed on food name, so re-running it refreshes the catalog
rather than duplicating it.

## Running

```sh
./run_server      # binds 0.0.0.0:8000, logs to EVENT.LOG
./kill_server
./restart_server
```

Port 8000 must match `ServerConfig.port` in the iOS client.

Note that `run_server` uses Django's development server. It is not a production
server; a real deployment wants gunicorn behind nginx, with TLS.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/foods/api/foods/` | The approved catalog |
| `GET` | `/foods/api/foods/?time=<ISO8601>` | Only foods modified since that time |
| `POST` | `/foods/api/foods/` | Submit a food (stored unapproved) |

Responses are shaped for the client's `ServerUpdateMessage`:

```json
{ "foods": [ { "id": 1, "name": "Apple", "cal": 95.0, "fat": 0.3, "car": 25.1, "pro": 0.5, "serving": "" } ],
  "timestamp": "2026-10-28T20:00:00.000000Z",
  "reset": false }
```

`reset` means "replace your whole catalog with this payload". It is true only
when the response contains the entire approved catalog and that catalog is
non-empty — the client deletes its cached global foods when it sees it, so it
must never be set with nothing to repopulate from.

Submissions arrive unauthenticated and land with `approved=False`, so they are
invisible to clients until approved at `/admin/`. Only list and create routes
exist; there are deliberately no detail routes to retrieve, update or delete.

## Tests

```sh
./venv/bin/python manage.py test foods
```

Covers the response contract, the `reset` conditions, and the write surface.
