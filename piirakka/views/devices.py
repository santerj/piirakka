"""Device control view handlers."""

import asyncio
from http import HTTPMethod

from starlette.responses import JSONResponse
from starlette.routing import Route

from piirakka.core.context import Context
from piirakka.model.device import AudioDevice
from piirakka.services.bluetooth import BluetoothDeviceManager, BluetoothDeviceScanner

# TODO: use urllib parsing / something from starlette to parse special
# TODO: characters in path_params

async def device_exists(context: Context, device_name: str) -> bool:
    """Checks whether a given audio device is available for mpv."""
    available_audio_devices = context.player.list_devices()
    device_exists = any(device.name == device_name for device in available_audio_devices)
    return device_exists

async def match_devices(context: Context, mac_address) -> AudioDevice | None:
    """For a given bluetooth device's MAC address, find a matching output device in bluez"""
    available_audio_devices = context.player.list_devices()
    for dev in available_audio_devices:
        if dev.name.find(mac_address.replace(":", "_")) != -1:
            return dev
    return None

def create_routes(context):
    """Factory function that creates device control route handlers with dependencies injected.

    Args:
    context: The application Context (for player control)

    Returns:
    List of Route objects.

    """

    async def get_device(request) -> JSONResponse:
        # TODO: rename to include mpv in name?
        return JSONResponse({"message": context.player.get_device()})

    async def set_device(request) -> JSONResponse:
        device_name = request.path_params["device_name"].replace("%2F", "/")
        if await device_exists(context, device_name):
            context.player.set_device(device_name)
            return JSONResponse({"message": "Audio device selected"})
        else:
            return JSONResponse({"message": "Audio device not found"}, status_code=404)

    async def list_devices(request) -> JSONResponse:
        devices = context.player.list_devices()
        return JSONResponse({"message": [dev.model_dump() for dev in devices]})

    async def scan_bluetooth_devices(request) -> JSONResponse:
        devices = await BluetoothDeviceScanner().scan()
        return JSONResponse({"message": [dev.model_dump() for dev in devices]})

    async def lazy_list_bluetooth_devices(request) -> JSONResponse:
        """Return the cached background scan. Useful for initial page loads."""
        devices = context.available_bluetooth_devices
        return JSONResponse({"message": [dev.model_dump() for dev in devices]})

    async def find_bt_audio_match(request) -> JSONResponse:
        """Find matching audio device for a given MAC address."""
        device_mac = request.path_params["device_mac"].replace("%3A", ":")

        if match := await match_devices(context, device_mac):
            return JSONResponse({"message": match.model_dump()})
        else:
            return JSONResponse({"message": "Matching audio device not found."}, status_code=404)

    async def pair_bluetooth_device(request) -> JSONResponse:
        device_mac = request.path_params["device_mac"].replace("%3A", ":")
        try:
            await BluetoothDeviceManager.pair(device_mac)
        except ValueError:
            return JSONResponse({"message": "Device not found"}, status_code=404)
        return JSONResponse({"message": "ok"})

    async def unpair_bluetooth_device(request) -> JSONResponse:
        device_mac = request.path_params["device_mac"].replace("%3A", ":")
        await BluetoothDeviceManager.unpair(device_mac)
        return JSONResponse({"message": "ok"})

    async def connect_bluetooth_device(request) -> JSONResponse:
        device_mac = request.path_params["device_mac"].replace("%3A", ":")
        await BluetoothDeviceManager.connect(device_mac)
        return JSONResponse({"message": "ok"})

    async def disconnect_bluetooth_device(request) -> JSONResponse:
        device_mac = request.path_params["device_mac"].replace("%3A", ":")
        await BluetoothDeviceManager.disconnect(device_mac)
        return JSONResponse({"message": "ok"})

    async def setup_bluetooth_device(request) -> JSONResponse:
        """Convenience endpoint - pair, connect and set the output device."""
        device_mac = request.path_params["device_mac"].replace("%3A", ":")
        await BluetoothDeviceManager.pair_and_connect(device_mac)
        await asyncio.sleep(1.5)  # wait for device to become available in mpv
        output_device = await match_devices(context, device_mac)
        context.player.set_device(output_device.name)

        return JSONResponse({"message": "ok"})

    route_prefix = "/api/devices/"

    # TODO: check whether PUT and DELETE methods work as idempotent
    # TODO: add previously used mac to db and try to auto-connect after reboot

    return [
        Route(route_prefix + "audio/all", list_devices, methods=[HTTPMethod.GET]),
        Route(route_prefix + "audio/current", get_device, methods=[HTTPMethod.GET]),
        Route(route_prefix + "audio/{device_name:path}", set_device, methods=[HTTPMethod.PUT]),
        Route(route_prefix + "bluetooth/scan", scan_bluetooth_devices, methods=[HTTPMethod.GET]),
        Route(route_prefix + "bluetooth/lazy", lazy_list_bluetooth_devices, methods=[HTTPMethod.GET]),
        Route(route_prefix + "bluetooth/{device_mac}/match", find_bt_audio_match, methods=[HTTPMethod.GET]),
        Route(route_prefix + "bluetooth/{device_mac}/pair", pair_bluetooth_device, methods=[HTTPMethod.PUT]),
        Route(route_prefix + "bluetooth/{device_mac}/unpair", unpair_bluetooth_device, methods=[HTTPMethod.PUT]),
        Route(route_prefix + "bluetooth/{device_mac}/connect", connect_bluetooth_device, methods=[HTTPMethod.PUT]),
        Route(route_prefix + "bluetooth/{device_mac}/disconnect", disconnect_bluetooth_device, methods=[HTTPMethod.PUT]),
        Route(route_prefix + "bluetooth/{device_mac}/setup", setup_bluetooth_device, methods=[HTTPMethod.PUT]),
    ]
