function initializeBluetoothDevices() {
  const settings = document.getElementById("Settings");
  if (!settings || settings.bluetoothDevicesInitialized) {
    return;
  }

  settings.addEventListener("click", async function (event) {
    const actionButton = event.target.closest("[data-device-action]");
    if (!actionButton || !settings.contains(actionButton)) {
      return;
    }

    const device = actionButton.closest("[data-mac-address]");
    if (!device) {
      return;
    }

    const action = actionButton.dataset.deviceAction;
    const macAddress = encodeURIComponent(device.dataset.macAddress);
    try {
      let response;
      if (action === "select-audio") {
        response = await selectAudioDevice(macAddress);
      } else if (action === "connect") {
        response = device.dataset.connected === "true"
          ? await selectAudioDevice(macAddress)
          : await connectAudioDevice(macAddress);
      } else {
        response = await fetch(`/api/devices/bluetooth/${macAddress}/${action}`, { method: "PUT" });
      }
      if (!response.ok) {
        throw new Error(`Bluetooth ${action} failed: ${response.status}`);
      }
      window.location.reload();
    } catch (error) {
      console.error("Bluetooth device action failed:", error);
    }
  });

  settings.addEventListener("bluetooth-devices:updated", function () {
    initializeBluetoothDevices();
  });

  settings.bluetoothDevicesInitialized = true;
}

async function selectAudioDevice(macAddress) {
  const matchResponse = await fetch(`/api/devices/bluetooth/${macAddress}/match`);
  if (!matchResponse.ok) {
    return matchResponse;
  }

  const matchData = await matchResponse.json();
  const deviceName = encodeURIComponent(matchData.message.name);
  return fetch(`/api/devices/audio/${deviceName}`, { method: "PUT" });
}

async function connectAudioDevice(macAddress) {
  const connectResponse = await fetch(`/api/devices/bluetooth/${macAddress}/connect`, { method: "PUT" });
  if (!connectResponse.ok) {
    return connectResponse;
  }

  return selectAudioDevice(macAddress);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeBluetoothDevices);
} else {
  initializeBluetoothDevices();
}
