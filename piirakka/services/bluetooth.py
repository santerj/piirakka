import asyncio

from dbus_fast import BusType, Variant
from dbus_fast.aio import MessageBus

from piirakka.model.device import BluetoothDevice

# TODO: merge these classes into one manager


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
                            connected=dev_props.get("Connected", False).value,
                        )
                    )

        return devices


class BluetoothDeviceManager:
    @staticmethod
    async def _get_device_proxy(bus, mac_address: str):
        """Helper to resolve DBus object path for a MAC address."""
        om_intro = await bus.introspect("org.bluez", "/")
        om_proxy = bus.get_proxy_object("org.bluez", "/", om_intro)
        om = om_proxy.get_interface("org.freedesktop.DBus.ObjectManager")

        objects = await om.call_get_managed_objects()
        target_mac = mac_address.upper()

        for path, interfaces in objects.items():
            if "org.bluez.Device1" in interfaces:
                addr = interfaces["org.bluez.Device1"].get("Address")
                if addr and addr.value.upper() == target_mac:
                    intro = await bus.introspect("org.bluez", path)
                    proxy = bus.get_proxy_object("org.bluez", path, intro)
                    return path, proxy

        raise ValueError(f"Device {mac_address} not found. Run scan first.")

    @classmethod
    async def pair(cls, mac_address: str):
        """Pairs and trusts a device (does not establish active audio link)."""
        bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
        _, proxy = await cls._get_device_proxy(bus, mac_address)

        device = proxy.get_interface("org.bluez.Device1")
        props = proxy.get_interface("org.freedesktop.DBus.Properties")

        await props.call_set("org.bluez.Device1", "Trusted", Variant("b", True))

        is_paired = await props.call_get("org.bluez.Device1", "Paired")
        if not is_paired.value:
            await device.call_pair()

    @classmethod
    async def unpair(cls, mac_address: str):
        """Removes the paired bond and forgets the device from BlueZ."""
        bus = await MessageBus(bus_type=BusType.SYSTEM).connect()

        # 1. Get the target device's object path
        device_path, _ = await cls._get_device_proxy(bus, mac_address)

        # 2. Introspect the Bluetooth Adapter (usually hci0)
        # We can extract the adapter path directly from the device path: /org/bluez/hci0/dev_XX_XX...
        adapter_path = "/".join(device_path.split("/")[:-1])

        adapter_intro = await bus.introspect("org.bluez", adapter_path)
        adapter_proxy = bus.get_proxy_object("org.bluez", adapter_path, adapter_intro)
        adapter = adapter_proxy.get_interface("org.bluez.Adapter1")

        # 3. Call RemoveDevice on the adapter interface with the device's object path
        await adapter.call_remove_device(device_path)

    @classmethod
    async def connect(cls, mac_address: str):
        """Connects an already paired device."""
        bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
        _, proxy = await cls._get_device_proxy(bus, mac_address)

        device = proxy.get_interface("org.bluez.Device1")
        await device.call_connect()

    @classmethod
    async def disconnect(cls, mac_address: str):
        """Disconnects an active device without unpairing it."""
        bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
        _, proxy = await cls._get_device_proxy(bus, mac_address)

        device = proxy.get_interface("org.bluez.Device1")
        await device.call_disconnect()

    @classmethod
    async def pair_and_connect(cls, mac_address: str):
        """Convenience method: Pairs if necessary, then connects."""
        await cls.pair(mac_address)
        await cls.connect(mac_address)
