# ijustate-server

The shared food catalog behind the [IJustAte](https://github.com/davidsonpoole/IJustAte)
iOS app. Serves approved foods, accepts new submissions, and holds them for
manual approval in the Django admin.

Django 4.1 + DRF on gunicorn, SQLite, Python 3.9+. Runs the same on macOS and
Linux.

## Setup

Settings that differ per deployment are not committed. Create your own first:

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
make setup        # venv + dependencies
make migrate
make static       # collect admin static files for WhiteNoise to serve
make seed         # load food_data/*.csv
make superuser    # needed to approve submissions
```

`make seed` is keyed on food name, so re-running it refreshes the catalog
rather than duplicating it.

## Running

```sh
make serve        # foreground, auto-reload, for development
make start        # background, logging to EVENT.LOG
make status
make restart
make stop
make logs         # tail -f EVENT.LOG
```

`make` on its own lists every target.

`make start` waits until the port actually accepts a connection, so it fails
loudly rather than reporting success on a server that died during startup.
`stop`/`restart`/`status` act on gunicorn's pidfile, not on a process-table
search.

Override the bind address and worker count per invocation:

```sh
make start PORT=9000 WORKERS=2
```

`PORT` must match `ServerConfig.port` in the iOS client (default `8000`).

There is no start-on-boot or restart-on-crash here, since that is
platform-specific — wrap `make start` in a launchd agent on macOS or a systemd
unit on Linux if you want it supervised.

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
make test
make check-deploy
```

`make test` covers the response contract, the `reset` conditions, and the write
surface. `make check-deploy` runs Django's deployment checklist; its four
remaining warnings are all about TLS, which this server does not yet have.
