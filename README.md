# piirakka

## acknowledgements

## development

### initialize dev environment

    $ python -m venv venv
    $ venv/bin/python -m pip install -r requirements/dev-requirements.txt
    $ source venv/bin/activate
    $ npm install

### update python dependencies

    $ pip-compile -o requirements/requirements.txt requirements/requirements.in
    $ pip-compile -o requirements/dev-requirements.txt requirements/dev-requirements.in

### run fastapi in development mode

    $ uvicorn piirakka.main:app --timeout-graceful-shutdown 5 --workers 1

Note that shutdown with ctrl+C here will be very messy if there are existing SSE connections.

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

### subscribe to server-sent events

    $ curl -N http://localhost:8000/events
