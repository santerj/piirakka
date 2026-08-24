Files for building piirakka as a container live here. There are two builds available:

- Bundled: contains a bundled mpv binary inside the container. Running this container requires exposing the host system's PulseAudio runtime to the container for playback.
- Standalone: contains only the built web service ("bring your own mpv"). Running this container requires for an mpv process to exist within the host system and an IPC socket mounted to the container.

The root directory has a Dockerfile which links to the standalone build here.

The GitHub Actions workflow builds both Containerfiles for `linux/amd64` and
`linux/arm/v7`, and publishes them to GitHub Container Registry. Version tags
are generated from `piirakka/__version__.py`, for example
`ghcr.io/santerj/piirakka:0.5.0-standalone` and
`ghcr.io/santerj/piirakka-bundled:0.5.0-bundled`.

`piirakka.container` is a rootful Quadlet example for the bundled image.
Copy it to `/etc/containers/systemd/`, update the version tag, desktop user
path, UID, and PulseAudio runtime path if needed, then run
`systemctl daemon-reload` and enable the service.

Podman runs that use Bluetooth audio must also mount the host system D-Bus socket
and `/dev/rfkill` into the container. The application uses D-Bus to reconnect
previously selected Bluetooth devices.
