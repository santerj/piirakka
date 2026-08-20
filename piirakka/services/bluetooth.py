import asyncio
from dbus_fast.aio import MessageBus
from dbus_fast import BusType

from piirakka.model.device import BluetoothDevice

class BluetoothDeviceScanner:
    # Major device class 0x0400 indicates Audio/Video devices (headphones, speakers)
    AUDIO_CLASS_MASK = 0x0400

    async def scan(self, timeout_seconds: int = 5) -> list[BluetoothDevice]:
        bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
        
        # 1. Get Adapter interface and start scanning
        adapter_path = "/org/bluez/hci0"
        intro = await bus.introspect("org.bluez", adapter_path)
        adapter_proxy = bus.get_proxy_object("org.bluez", adapter_path, intro)
        adapter = adapter_proxy.get_interface("org.bluez.Adapter1")
        
        await adapter.call_start_discovery()
        await asyncio.sleep(timeout_seconds)
        await adapter.call_stop_discovery()

        # 2. Query ObjectManager for all discovered objects under BlueZ
        om_intro = await bus.introspect("org.bluez", "/")
        om_proxy = bus.get_proxy_object("org.bluez", "/", om_intro)
        object_manager = om_proxy.get_interface("org.freedesktop.DBus.ObjectManager")
        
        objects = await object_manager.call_get_managed_objects()
        
        devices = []
        for path, interfaces in objects.items():
            if "org.bluez.Device1" in interfaces:
                dev_props = interfaces["org.bluez.Device1"]
                
                name = dev_props.get("Name", dev_props.get("Alias"))
                mac = dev_props.get("Address")
                dev_class = dev_props.get("Class")
                
                # Unwrap Variant values returned by dbus-fast
                name_str = name.value if name else "Unknown"
                mac_str = mac.value if mac else ""
                class_val = dev_class.value if dev_class else 0
                
                # Filter to include audio devices (or named unknown targets)
                is_audio = bool(class_val & self.AUDIO_CLASS_MASK)
                if is_audio and mac_str:
                    devices.append(
                        BluetoothDevice(
                            name=name_str,
                            address=mac_str,
                            path=path,
                            paired=dev_props.get("Paired", False).value,
                            connected=dev_props.get("Connected", False).value
                        )
                    )
                    
        return devices

class BluetoothDeviceManager:
    def __init__(self):
        pass

    @staticmethod
    async def connect(device: BluetoothDevice):
        bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
        
        # Introspect the BlueZ device object natively
        introspection = await bus.introspect("org.bluez", device.path)
        proxy = bus.get_proxy_object("org.bluez", device.path, introspection)
        
        device_interface = proxy.get_interface("org.bluez.Device1")
        properties_interface = proxy.get_interface("org.freedesktop.DBus.Properties")

        # Set 'Trusted' property to True (so it auto-reconnects in the future)
        await properties_interface.call_set("org.bluez.Device1", "Trusted", True)

        # Pair if not already paired
        is_paired = await properties_interface.call_get("org.bluez.Device1", "Paired")
        if not is_paired.value:
            await device_interface.call_pair()

        # Connect audio profiles (A2DP / HFP)
        await device_interface.call_connect()
        print(f"Successfully connected to {device.path}")
