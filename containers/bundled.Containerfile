FROM almalinux:10-minimal as build-app

WORKDIR /build

RUN microdnf install -y python pip npm

COPY . /build/

RUN npm install && \
    python -m pip install build && \
    npm run build:css && \
    python -m build


FROM almalinux:10-minimal as build-mpv

WORKDIR /tmp

RUN microdnf install -y epel-release && \
    sed -i 's/enabled=0/enabled=1/' /etc/yum.repos.d/almalinux-crb.repo && \
    rpm -i https://mirrors.rpmfusion.org/free/el/rpmfusion-free-release-10.noarch.rpm && \
    microdnf install -y mpv


FROM almalinux:10-minimal

COPY --from=build-app /build/dist/*.whl /tmp/
COPY --from=build-mpv /usr/bin/mpv /usr/bin/mpv
COPY --from=build-mpv /usr/lib64 /usr/lib64
COPY --from=build-mpv /etc/mpv* /etc/mpv/

RUN microdnf install -y python pip shadow-utils pipewire-jack-audio-connection-kit && \
    python -m pip install /tmp/*.whl && \
    useradd --create-home --shell /bin/bash --no-log-init piirakka && \
    chown piirakka:piirakka /usr/local/bin/piirakka && \
    microdnf remove -y pip shadow-utils && \
    microdnf clean all

USER piirakka

ENTRYPOINT ["piirakka"]
