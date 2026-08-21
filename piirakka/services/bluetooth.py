import asyncio
from dbus_fast.aio import MessageBus
from dbus_fast import BusType, Variant

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
    async def connect(mac_address: str):
        bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
    
        # 1. Find device path dynamically from ObjectManager
        om_intro = await bus.introspect("org.bluez", "/")
        om_proxy = bus.get_proxy_object("org.bluez", "/", om_intro)
        om = om_proxy.get_interface("org.freedesktop.DBus.ObjectManager")
        
        objects = await om.call_get_managed_objects()
        target_mac = mac_address.upper()
        target_path = None

        for path, interfaces in objects.items():
            if "org.bluez.Device1" in interfaces:
                addr = interfaces["org.bluez.Device1"].get("Address")
                if addr and addr.value.upper() == target_mac:
                    target_path = path
                    break

        if not target_path:
            raise ValueError(f"Device {mac_address} not found. Run scan first.")

        # 2. Introspect only after verifying target_path exists
        intro = await bus.introspect("org.bluez", target_path)
        proxy = bus.get_proxy_object("org.bluez", target_path, intro)
        
        device = proxy.get_interface("org.bluez.Device1")
        props = proxy.get_interface("org.freedesktop.DBus.Properties")

        await props.call_set("org.bluez.Device1", "Trusted", Variant("b", True))
        
        is_paired = await props.call_get("org.bluez.Device1", "Paired")
        if not is_paired.value:
            await device.call_pair()

        await device.call_connect()
