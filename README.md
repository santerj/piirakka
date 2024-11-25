# piirakka

## acknowledgements

## development

### initialize dev environment

    $ python -m venv venv
    $ venv/bin/python -m pip install -r dev-requirements.txt
    $ source venv/bin/activate
    $ npm install

### update python dependencies

    $ pip-compile -o requirements/requirements.txt requirements/requirements.in
    $ pip-compile -o requirements/dev-requirements.txt requirements/dev-requirements.in

### run fastapi in development mode

    $ uvicorn piirakka.main:app --reload

### run tailwind in watch mode

    $ npx tailwindcss -i piirakka/static/css/tailwind.css -o piirakka/static/css/output.css --watch

### build tailwind

    $ npm run build:css 

### edit icons

    1. open https://remixicon.com/
    2. click on file icon, import collection
    3. select the .remixicon file in project root
    4. make whatever changes to icon collection
    5. download in svg format
    6. unzip file, move contents to piirakka/static/icons
    7. 👍

