# piirakka

# development

### initialize dev environment

    $ python -m venv venv
    $ venv/bin/python -m pip install -r dev-requirements.txt
    $ source venv/bin/activate
    $ npm install

### update python dependencies

    $ pip-compile -o requirements/requirements.txt requirements/requirements.in
    $ pip-compile -o requirements/dev-requirements.txt requirements/dev-requirements.in

### run app in development mode

    $ uvicorn piirakka.main:app --reload

### build tailwind

    $ npm run build:css 

