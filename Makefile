# ijustate-server
#
# Portable across macOS and Linux: gunicorn handles its own daemonising and
# writes a pidfile, so start/stop/restart act on a known pid rather than
# pattern-matching the process table.
#
# Run `make` for the available targets.

PY       := ./venv/bin/python
PIP      := ./venv/bin/pip
GUNICORN := ./venv/bin/gunicorn
APP      := ijustateserver.wsgi:application

HOST     ?= 0.0.0.0
PORT     ?= 8000
WORKERS  ?= 3

PIDFILE  := gunicorn.pid
LOG      := EVENT.LOG

.DEFAULT_GOAL := help
.PHONY: help setup migrate static seed superuser serve start stop restart status logs test check-deploy clean

help: ## Show this help
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk -F':.*?## ' '{printf "  \033[1m%-13s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "  Bind address: HOST=$(HOST) PORT=$(PORT) WORKERS=$(WORKERS) (override on the command line)."
	@echo "  PORT must match ServerConfig.port in the iOS client."

setup: ## Create the venv and install dependencies
	python3 -m venv venv
	$(PIP) install -q --upgrade pip
	$(PIP) install -q -r requirements.txt
	@echo "venv ready."
	@test -f ijustateserver/local_settings.py \
		|| echo "next: cp ijustateserver/local_settings.example.py ijustateserver/local_settings.py"

migrate: ## Apply database migrations
	$(PY) manage.py migrate

static: ## Collect static files (needed for the admin under gunicorn)
	$(PY) manage.py collectstatic --noinput

seed: ## Load/refresh the food catalog from food_data/*.csv
	$(PY) manage.py create_foods

superuser: ## Create an admin user (needed to approve submissions)
	$(PY) manage.py createsuperuser

serve: ## Run in the foreground with auto-reload (ctrl-c to stop)
	$(GUNICORN) $(APP) --bind $(HOST):$(PORT) --reload

start: ## Start in the background, logging to EVENT.LOG
	@if [ -f $(PIDFILE) ] && kill -0 `cat $(PIDFILE)` 2>/dev/null; then \
		echo "already running (pid `cat $(PIDFILE)`)"; exit 1; \
	fi
	@rm -f $(PIDFILE)
	@$(GUNICORN) $(APP) --bind $(HOST):$(PORT) --workers $(WORKERS) \
		--daemon --pid $(PIDFILE) --log-file $(LOG) --access-logfile $(LOG)
	@host=$(HOST); if [ "$$host" = "0.0.0.0" ]; then host=127.0.0.1; fi; \
	for i in `seq 1 60`; do \
		if $(PY) -c "import socket,sys; socket.create_connection((sys.argv[1],int(sys.argv[2])),1).close()" \
				$$host $(PORT) 2>/dev/null; then \
			echo "started on $(HOST):$(PORT) (pid `cat $(PIDFILE)`), logging to $(LOG)"; \
			exit 0; \
		fi; \
		if [ -s $(PIDFILE) ] && ! kill -0 `cat $(PIDFILE)` 2>/dev/null; then break; fi; \
		sleep 0.2; \
	done; \
	echo "failed to start; last lines of $(LOG):"; \
	tail -3 $(LOG) 2>/dev/null | sed 's/^/  /'; \
	rm -f $(PIDFILE); \
	exit 1

stop: ## Stop the background server
	@if [ ! -f $(PIDFILE) ]; then echo "not running"; exit 0; fi
	@pid=`cat $(PIDFILE)`; \
	if kill -0 $$pid 2>/dev/null; then \
		echo "stopping pid $$pid"; \
		kill $$pid; \
		while kill -0 $$pid 2>/dev/null; do sleep 0.1; done; \
		echo "stopped"; \
	else \
		echo "stale pidfile, removing"; \
	fi; \
	rm -f $(PIDFILE)

restart: ## Restart the background server
	@$(MAKE) --no-print-directory stop
	@$(MAKE) --no-print-directory start

status: ## Report whether the server is running
	@if [ -f $(PIDFILE) ] && kill -0 `cat $(PIDFILE)` 2>/dev/null; then \
		echo "running (pid `cat $(PIDFILE)`) on $(HOST):$(PORT)"; \
	else \
		echo "not running"; \
	fi

logs: ## Follow EVENT.LOG
	tail -f $(LOG)

test: ## Run the test suite
	$(PY) manage.py test foods

check-deploy: ## Run Django's deployment checklist
	$(PY) manage.py check --deploy

clean: ## Remove __pycache__, collected static files and logs
	find . -path ./venv -prune -o -name __pycache__ -type d -print0 | xargs -0 rm -rf
	rm -rf staticfiles
	rm -f $(LOG) $(PIDFILE)
