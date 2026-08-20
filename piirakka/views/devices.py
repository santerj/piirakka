"""Device control view handlers."""

from http import HTTPMethod

from starlette.background import BackgroundTask
from starlette.responses import JSONResponse
from starlette.routing import Route

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
        # TODO: mpv set_property audio-device "pipewire/bluez_output.<mac underscored>".1
        # TODO: or "auto" / "pipewire"
        # TODO: rename to include mpv in name?
        pass
    
    async def list_devices(request) -> JSONResponse:
        # TODO: serialize raw ipc output into pydantic AudioDevice class for validation
        return JSONResponse({"message": context.player.list_devices()})

    async def list_bluetooth_devices(request) -> JSONResponse:
        # TODO: clean up code, adjust timeout
        from services.bluetooth import BluetoothDeviceScanner
        x = BluetoothDeviceScanner()
        asd = await x.scan()
        return JSONResponse({"message": [a.model_dump() for a in asd]})

    async def pair_bluetooth_device(request) -> JSONResponse:
        # TODO: use BluetoothDeviceManager, also call set_device too?
        pass

    return [
        Route("/api/devices/audio/all", list_devices, methods=[HTTPMethod.GET]),
        Route("/api/devices/audio/current", get_device, methods=[HTTPMethod.GET]),
        Route("/api/devices/audio/{device}", set_device, methods=[HTTPMethod.PUT]),
        Route("/api/devices/bluetooth/all", list_bluetooth_devices, methods=[HTTPMethod.GET]),
        Route("/api/devices/bluetooth/{device}", pair_bluetooth_device, methods=[HTTPMethod.PUT])
    ]