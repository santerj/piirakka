# piirakka

**Internet radio playback for social spaces.**

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/846ea04459dc4aaf8a20ee15d9667fca)](https://app.codacy.com/gh/santerj/piirakka/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)

---

Piirakka aims to bring the shared control of a physical radio receiver into the context of online radio streaming.

With a physical FM radio, anyone in the room can adjust the tuner or volume. Internet radio offers a much wider selection of what to listen, but streaming is usually tied to a single physical device. This tends to limit the control of radio playback to a single person.

Piirakka is designed to allow anyone within the network to control internet radio playback from their own device. Hook it up to an audio system and a HTTP interface becomes the physical controls.

## Features

- Real-time, multi-user UI in the browser
- Import any station (Icecast, SHOUTcast, HLS, MPEG-DASH...)
- Bluetooth audio streaming support (with bluez, dbus, pipewire and wireplumber)
- CRUD and playback controls available through REST API – pick your station with `curl` if you wish.
- Desktop and mobile support

## TODO

- Docker example
- wheel example
- screenshots
- where to find stations
