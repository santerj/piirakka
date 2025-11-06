# piirakka

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/846ea04459dc4aaf8a20ee15d9667fca)](https://app.codacy.com/gh/santerj/piirakka/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)

## development

### initialize dev environment

    python -m venv venv
    venv/bin/python -m pip install -r requirements/dev-requirements.txt
    source venv/bin/activate
    npm install

### (in VS Code) start all dev tasks

- Open command palette (`Cmd+Shift+P` / `Ctrl+Shift+P`)
- type `'Run Task'` > select `Start All`

This will open the stack of dev tools in the Terminal tab. Prerequisite is that the python env and
node packages have been installed. Websocat and sqlite3 are also required.

Due to subprocess spawning, uvicorn doesn't have the development server (hot reloading)
enabled. That task will have to be rerun manually by clicking on the task.

### update python dependencies

    pip-compile -o requirements/requirements.txt requirements/requirements.in
    pip-compile -o requirements/dev-requirements.txt requirements/dev-requirements.in
    pip-sync requirements/dev-requirements.txt

### run starlette

    python -m piirakka.main

### build tailwind

    npm run build:css

### run tailwind in watch mode

    npm run watch:css

### edit icons

    1. go to https://remixicon.com/
    2. click on file icon, import collection
    3. select the .remixicon file in project root
    4. make changes to icon collection
    5. download in svg format
    6. unzip file, move contents to piirakka/static/icons
    7. export collection, replace .remixicon file

### subscribe to websockets in shell (needs [websocat](https://github.com/vi/websocat))

    websocat ws://localhost:8000/ws/subscribe

### run alembic

    alembic revision -m "New migration"
    alembic revision --autogenerate -m "Refresh model"
    alembic upgrade head

### build app

    python -m build

### install app

    pip install dist/piirakka-*-py3-none-any.whl

### look at included files in dist

    unzip -l piirakka-*-py3-none-any.whl

### run bandit

    bandit -c pyproject.toml piirakka/

### run ruff

    ruff check piirakka/
    ruff format piirakka/

### run djlint

    djlint piirakka/templates/ --check
    djlint piirakka/templates/ --reformat
