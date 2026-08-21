"""Device control view handlers."""

from http import HTTPMethod

from starlette.background import BackgroundTask
from starlette.responses import JSONResponse
from starlette.routing import Route

from piirakka.model.device import BluetoothDevice

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
        context.player.set_device("pulse/bluez_output.F8_DF_15_ED_1D_A9.1")
        return JSONResponse({"message": "ok"})
    
    async def list_devices(request) -> JSONResponse:
        # TODO: serialize raw ipc output into pydantic AudioDevice class for validation
        return JSONResponse({"message": context.player.list_devices()})

    async def list_bluetooth_devices(request) -> JSONResponse:
        # TODO: clean up code, adjust timeout
        from services.bluetooth import BluetoothDeviceScanner
        x = BluetoothDeviceScanner()
        asd = await x.scan(timeout_seconds=8)
        return JSONResponse({"message": [a.model_dump() for a in asd]})

    async def pair_bluetooth_device(request) -> JSONResponse:
        from services.bluetooth import BluetoothDeviceManager
        device = BluetoothDevice(
            name="JBL Xtreme",
            address="F8:DF:15:ED:1D:A9",
            path="/org/bluez/hci0/dev_F8_DF_15_ED_1D_A9",
            paired=False,
            connected=False
        )
        b = BluetoothDeviceManager()
        await b.connect(device)
        return JSONResponse({"message": "ok"})

    return [
        Route("/api/devices/audio/all", list_devices, methods=[HTTPMethod.GET]),
        Route("/api/devices/audio/current", get_device, methods=[HTTPMethod.GET]),
        Route("/api/devices/audio/{device}", set_device, methods=[HTTPMethod.PUT]),
        Route("/api/devices/bluetooth/all", list_bluetooth_devices, methods=[HTTPMethod.GET]),
        Route("/api/devices/bluetooth/{device}", pair_bluetooth_device, methods=[HTTPMethod.PUT])
    ]