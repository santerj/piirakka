"""Device control view handlers."""

from http import HTTPMethod

from starlette.background import BackgroundTask
from starlette.responses import JSONResponse
from starlette.routing import Route

from piirakka.model.device import BluetoothDevice
from piirakka.services.bluetooth import BluetoothDeviceManager

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
        available_audio_devices = context.player.list_devices()
        device_exists = any(device.name == device_name for device in available_audio_devices)
        if device_exists:
            context.player.set_device(device_name)
            return JSONResponse({"message": "Audio device selected"})
        else:
            return JSONResponse({"message": "Audio device not found"}, status_code=404)
    
    async def list_devices(request) -> JSONResponse:
        devices = context.player.list_devices()
        return JSONResponse({"message": [dev.model_dump() for dev in devices]})

    async def list_bluetooth_devices(request) -> JSONResponse:
        devices = context.available_bluetooth_devices
        return JSONResponse({"message": [dev.model_dump() for dev in devices]})

    async def pair_bluetooth_device(request) -> JSONResponse:
        device_mac = request.path_params["device_mac"].replace("%3A", ":")
        b = BluetoothDeviceManager()
        await b.connect(device_mac)
        return JSONResponse({"message": "ok"})

    async def find_bt_audio_match(request) -> JSONResponse:
        """Find matching audio device for a given MAC address."""
        device_mac = request.path_params["device_mac"].replace("%3A", ":")
        available_audio_devices = context.player.list_devices()

        for dev in available_audio_devices:
            if dev.name.find(device_mac.replace(":", "_")) != -1:
                return JSONResponse({"message": dev.model_dump()})
        return JSONResponse({"message": "Matching audio device not found."}, status_code=404)


    return [
        Route("/api/devices/audio/all", list_devices, methods=[HTTPMethod.GET]),
        Route("/api/devices/audio/current", get_device, methods=[HTTPMethod.GET]),
        Route("/api/devices/audio/{device_name:path}", set_device, methods=[HTTPMethod.PUT]),
        Route("/api/devices/bluetooth/all", list_bluetooth_devices, methods=[HTTPMethod.GET]),
        Route("/api/devices/bluetooth/{device_mac}", pair_bluetooth_device, methods=[HTTPMethod.PUT]),
        Route("/api/devices/bluetooth/match/{device_mac}", find_bt_audio_match, methods=[HTTPMethod.GET])
    ]
