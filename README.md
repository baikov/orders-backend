# Backend for Orders project

[![Based on Cookiecutter Django](https://img.shields.io/badge/based%20on-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Black code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Other parts:

1. [Revers-proxy](https://github.com/baikov/orders-traefik)
2. [Front](https://github.com/baikov/orders-frontend)
3. [Back](https://github.com/baikov/orders-backend)


## Local development

### Preparation

1. Create virtual environment
    ```shell
    python -m venv venv
    ```
1. Activate virtual environment
    ```shell
    source venv/bin/activate
    ```
1. Install requirements
    ```shell
    pip install -r requirements/local.txt
    ```
1. Install and activate all recomended `VSCode` extensions
1. Install `pre-commit`
    ```shell
    pre-commit install
    ```
1. Install `Docker Desktop`
1. Make sure `ruff` and `mypy` are working
    ```shell
    ruff check backend/
    ```
    ```shell
    mypy backend/
    ```
1. Copy `.env.example` and rename it to `.env`

Choose one of `.env` presets.

> To use `Mode 1` and `Mode 2`, a raised container from [this repo](https://github.com/baikov/tpl-traefik) with Traefik is required. Because an external network to which frontend and backend containers are connected is created in Traefik compose.

### Mode 0: As separate dev server on custom port

1. No need for a Traefik container
1. Set `uniqe` project name
    ```env
    COMPOSE_PROJECT_NAME=orders
    ```
1. Uncomment `Mode 0` block and set custom ports if needed:
    ```env
    # Mode 0: As separate dev server on custom port
    COMPOSE_FILE=local.yml
    DOMAIN=localhost
    DJANGO_DOCKER_PORT=8000
    MAILHOG_DOCKER_PORT=8025
    FLOWER_DOCKER_PORT=5555
    DOCS_DOCKER_PORT=9000
    ```
1. Run `docker compose build` and `docker compose up -d`

### Mode 1: As dev server behind the Traefik with http

> Avaliable paths: `dj-admin/`, `api/`, `ststic/`, `silk/`. Other paths are proxied to the frontend container

1. The Traefik container must be running in `Mode 1`
1. Rename `.env.example` to `.env`
1. Set the project name same as `COMPOSE_PROJECT_NAME` in Traefik `.env`
    ```env
    COMPOSE_PROJECT_NAME=orders
    ```
1. Uncomment `Mode 1` block:
    ```env
    # Mode 1: As dev server behind the Traefik with http
    # For Windows users: use `;` (semicolon) as separator - local.yml;local.traefik.yml
    COMPOSE_FILE=local.yml:local.traefik.yml
    DOMAIN=localhost  # or another aliace for 127.0.0.1 declared in etc/hosts, but same as DOMAIN in Traefik .env!
    ```
1. Run Traefik container, then run Django stack with `docker compose build` and `docker compose up -d`

### Mode 2: As dev server behind the Traefik + SSL and custom domain

> Avaliable paths: `dj-admin/`, `api/`, `ststic/`, `silk/`. Other paths are proxied to the frontend container

1. The Traefik container must be running in `Mode 2`
1. Rename `.env.example` to `.env`
1. Set the project name same as `COMPOSE_PROJECT_NAME` in Traefik `.env`
    ```env
    COMPOSE_PROJECT_NAME=orders
    ```
1. Uncomment `Mode 2` block:
    ```env
    # Mode 2: As dev server behind the Traefik + SSL and custom domain
    # For Windows users: use `;` (semicolon) as separator - local.yml;local.traefik.yml;local.traefik.ssl.yml
    COMPOSE_FILE=local.yml:local.traefik.yml:local.traefik.ssl.yml
    DOMAIN=orders.local  # same as DOMAIN in Traefik .env!
    ```
1. Run Traefik container, then run Django stack with `docker compose build` and `docker compose up -d`

### Usefull commands from django-cookiecutter

1. Show Logs (e.g. Django)
    ```shell
    docker logs -f django
    # or
    docker compose logs -f django
    ```
1. Migrations
    ```shell
    docker compose run --rm django python manage.py makemigrations
    ```
    ```shell
    docker compose run --rm django python manage.py migrate
    ```
1. Django shell_plus with ipython
    ```shell
    docker compose run --rm --name django_shell django python manage.py shell_plus --ipython
    ```
1. Create DB backup (placed in `./pg-backups`)
    ```shell
    docker compose exec postgres backup
    ```
1. Show backups list
    ```shell
    docker compose exec postgres backups
    ```
1. Restore backup (only from `gzip`)
    ```shell
    docker compose exec postgres restore backup_2023_05_26T12_34_08.sql.gz
    ```
1. Hot clean DB (close all connections)
    ```shell
    docker compose exec postgres restore clean
    ```

## Deploy to production

### Mode 3: when front in SSR mode

1. The Traefik container must be running in `Mode 3` on prod server
1. Copy `.env.production.example` and rename it to `.env`
1. Set the project name same as `COMPOSE_PROJECT_NAME` in Traefik `.env`
    ```env
    COMPOSE_PROJECT_NAME=orders
    ```
1. Uncomment `Mode 3` block:
    ```env
    # Mode 3: For production with SSR
    COMPOSE_FILE=production.yml
    DOMAIN=orders.baikov.dev
    ```
1. Change all secure variables
1. Add Sentry DSN and Email settings (optional)
1. Run container with `docker compose build` and `docker compose up -d`

### Mode 4: when front in SPA mode

coming soon...
