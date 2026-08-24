"""Definitions of audio devices for playback."""

from pydantic import BaseModel


class BluetoothDevice(BaseModel):
    """Available Bluetooth device as scanned by dbus-fast."""
    name: str
    address: str  # MAC address
    path: str  # bluez path
    paired: bool
    connected: bool


class AudioDevice(BaseModel):
    """Available audio device as reported by mpv."""
    name: str
    description: str
