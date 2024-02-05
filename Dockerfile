FROM almalinux:9.3-minimal

LABEL maintainer="https://github.com/santerj"

EXPOSE 8000/tcp

# Install dependencies with microdnf + create nonroot user
RUN \
    microdnf update -y && \
    microdnf install -y \
        python3.11-3.11.5 \
        python3.11-pip-22.3.1 \
        shadow-utils-2:4.9 && \
    useradd -u 1001 -r -s /sbin/nologin -c "Default Application User" default && \
    microdnf remove -y shadow-utils && \
    microdnf clean all

# Install Python dependencies
COPY requirements/requirements.txt /tmp/requirements.txt

RUN \
    python3.11 -m pip install --upgrade pip -r /tmp/requirements.txt && \
    rm -f /tmp/requirements.txt

# Copy sources
COPY --chown=default:default piirakka/ /opt/piirakka/

# Fix for when 'python' is not in $PATH
RUN sed -i 's/python/python3.11/g' /opt/piirakka/piirakka
RUN mkdir /tmp/sockets

# Fix for when 'python' is not in $PATH
#RUN sed -i 's/python/python3.11/g' /opt/piirakka/piirakka && \
#    touch /tmp/piirakka.sock && \
#    chown default:default /tmp/piirakka.sock

WORKDIR /opt/piirakka
#USER 1001
ENTRYPOINT [ "/opt/piirakka/piirakka", "--no-mpv" ]
#CMD [ "main.py" ]
