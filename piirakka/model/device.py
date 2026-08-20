"""Definitions of audio devices for playback"""

from pydantic import BaseModel

class BluetoothDevice(BaseModel):
    """Bluetooth devices as scanned by dbus-fast"""
    name: str
    address: str  # MAC address
    path: str  # bluez path
    paired: bool
    connected: bool

class AudioDevice(BaseModel):
    """Audio devices reported by mpv"""
    name: str
    description: str
