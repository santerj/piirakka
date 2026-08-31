# Development Guide

This guide explains the necessary steps to get a local dev environment set up.

## Quick start

What is needed for local development:

- Python interpreter (>=3.10)
- A way to create isolated Python environments, e.g. with `python -m venv`
- npm

### From scratch

    # create venv
    python -m venv venv

    # install python dependencies
    venv/bin/python -m pip install -r requirements/dev-requirements.txt

    # install node dependencies
    npm install

    # build style sheets
    npm run build:css

    # activate virtual env
    source venv/bin/activate

    # run app
    python -m piirakka.main

### Useful software

- [curl](https://curl.se/) for querying HTTP endpoints
- [websocat](https://github.com/vi/websocat) for inspecting websockets
- [sqlite3](https://sqlite.org/index.html) or other SQLite-compatible tool for inspecting databases
- [Podman](https://podman.io/) or other OCI compliant build/runtime for containers, e.g. Docker

### VS Code tasks

If [VS Code](https://code.visualstudio.com/) is used as the editor/IDE, there are some preconfigured tasks ready for use through the command palette (`Cmd+Shift+P` / `Ctrl+Shift+P`) -> **Run Task**.

Note: due to subprocess spawning, uvicorn doesn't have the development server (hot reloading) enabled. That task will have to be rerun manually by clicking on the task.

## Architecture

The app is built around the [Starlette](https://starlette.dev/) framework on the [uvicorn](https://uvicorn.dev/) ASGI server. The app has HTTP endpoints for manipulating audio playback, database, and device connections. Audio playback (and streaming) is handled by [mpv](https://mpv.io/).

As the app (viewed through the browser) is real-time and multi-user, the backend broadcasts [state changes as HTML fragments](https://github.com/guettli/frow--fragments-over-the-wire) through a WebSocket connection. The WebSocket endpoint only broadcasts pre-rendered HTML, so other clients will have to implement a polling mechanism.

### Security considerations

Piirakka is not designed to be a security-hardened application. In a nutshell, it's a CRUD app that plays back Internet audio streams from user-submitted URLs, thus being inherently vulnerable to [SSRF](https://owasp.org/www-community/attacks/Server_Side_Request_Forgery) attacks. Care should be taken on where the app is deployed.

## Containers

Two flavours of Containerfile are maintained: _bundled_ and _standalone_. The former contains a mpv binary, and the latter is meant for users who prefer to deploy their own mpv instance.

## Usual commands cheat sheet

### Run the app

    python -m piirakka.main

    # without mpv
    MPV_SOCKET=/path/to/socket python -m piirakka.main --no-mpv

    # without bluetooth
    python -m piirakka.main --no-bluetooth

### Update python dependencies with pip-tools

    pip-compile -o requirements/requirements.txt requirements/requirements.in
    pip-compile -o requirements/dev-requirements.txt requirements/dev-requirements.in
    pip-sync requirements/dev-requirements.txt

### Build stylesheets

    npm run build:css

    # in watch mode
    npm run watch:css

### Edit icons

    1. go to https://remixicon.com/
    2. click on file icon, import collection
    3. select the .remixicon file in .icons
    4. make changes to icon collection
    5. download in svg format
    6. unzip file, move contents to piirakka/static/icons
    7. export collection, replace .remixicon file

### Subscribe with websocat

    websocat ws://localhost:8000/ws/subscribe

### Alembic

    alembic revision -m "New migration"
    alembic revision --autogenerate -m "Refresh model"
    alembic upgrade head

### Build app

    python -m build

### Install app from wheel

    pip install dist/piirakka-*-py3-none-any.whl

### Inspect included files in wheel

    unzip -l piirakka-*-py3-none-any.whl

### Linters and formatters

    # Bandit
    bandit -c pyproject.toml piirakka/

    # Ruff
    ruff check piirakka/
    ruff format piirakka/

    # djlint
    djlint piirakka/templates/ --check
    djlint piirakka/templates/ --reformat

    # isort
    isort piirakka/ --check
    isort piirakka/

    # prettier
    npx prettier . --write

### Build image

    podman build -f containers/bundled.Containerfile -t piirakka:bundled-latest .
    podman build -f containers/standalone.Containerfile -t piirakka:standalone-latest .

---

These might be useful, need validation:

### Run with podman (bundled mpv)

Works with Linux and PulseAudio.
Make sure the host data directory (`~/.local/share/piirakka`, `/etc/piirakka`, etc) has 755 permissions.

    podman run --rm -it \
        --userns=keep-id \
        --device /dev/snd \
        --device /dev/rfkill \
        -p 8000:8000 \
        -v /run/dbus/system_bus_socket:/run/dbus/system_bus_socket:ro \
        -v /run/user/$(id -u)/pulse/native:/tmp/pulse-socket \
        -v ~/.local/share/piirakka:/home/piirakka/.local/share/piirakka:Z \
        -e PULSE_SERVER=unix:/tmp/pulse-socket \
        -e XDG_RUNTIME_DIR=/tmp \
        --security-opt label=disable \
        localhost/piirakka:bundled-latest

### Run with podman (standalone)

Create a socket and start mpv

    TMPDIR=$(mktemp -d)
    chmod 777 $TMPDIR

    mpv \
      --idle \
      --volume=50 \
      --volume-max=130 \
      --cache=no \
      --really-quiet \
      --input-ipc-server=$TMPDIR/piirakka.sock

Start standalone container

    podman run --rm -it \
        --userns=keep-id \
        --device /dev/rfkill \
        -p 8000:8000 \
        -v $TMPDIR:/tmp/piirakka \
        -v /run/dbus/system_bus_socket:/run/dbus/system_bus_socket:ro \
        -v ~/.local/share/piirakka:/home/piirakka/.local/share/piirakka:Z \
        -e MPV_SOCKET=/tmp/piirakka/piirakka.sock \
        --security-opt label=disable \
        localhost/piirakka:byom-latest
