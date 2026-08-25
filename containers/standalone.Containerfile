FROM almalinux:10-minimal as build-app

WORKDIR /build

RUN microdnf install -y python pip npm

COPY . /build/

RUN npm install && \
    python -m pip install build && \
    npm run build:css && \
    python -m build


FROM almalinux:10-minimal

COPY --from=build-app /build/dist/*.whl /tmp/

RUN microdnf install -y python pip shadow-utils && \
    python -m pip install /tmp/*.whl && \
    useradd --uid 23332 --create-home --shell /bin/bash --no-log-init piirakka && \
    chown piirakka:piirakka /usr/local/bin/piirakka && \
    microdnf remove -y pip shadow-utils && \
    microdnf clean all

USER piirakka

ENTRYPOINT ["piirakka", "--no-mpv"]
