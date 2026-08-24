Files for building piirakka as a container live here. There are two builds available:

- Bundled: contains a bundled mpv binary inside the container. Running this container requires exposing the host system's PulseAudio runtime to the container for playback.
- Standalone: contains only the built web service ("bring your own mpv"). Running this container requires for an mpv process to exist within the host system and an IPC socket mounted to the container.

The root directory has a Dockerfile which links to the standalone build here.

Podman runs that use Bluetooth audio must also mount the host system D-Bus socket
and `/dev/rfkill` into the container. The application uses D-Bus to reconnect
previously selected Bluetooth devices.
