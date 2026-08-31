const wsEndpoint = `ws://${window.location.host}/ws/subscribe`;

// Open websocket
const socket = new WebSocket(wsEndpoint);

// Listen for connection open event
socket.addEventListener("open", function (event) {
  console.log("WebSocket is connected.");
});

// Listen for messages from the server
socket.addEventListener("message", function (event) {
  try {
    // Parse the incoming message
    const data = JSON.parse(event.data);

    // Check if 'events' exists and is an array
    if (Array.isArray(data.events)) {
      data.events.forEach((eventItem) => {
        console.log("Received event", eventItem.event_type);
        const content = eventItem.content;

        switch (eventItem.event_type) {
          case "player_bar_updated": {
            const player_bar = document.getElementById("ControlBar");
            if (!player_bar) {
              break;
            }
            player_bar.innerHTML = content;
            updateTitleFromPlayerBar(player_bar);
            break;
          }
          case "track_history_changed": {
            const trackHistoryContainer =
              document.getElementById("trackHistory");
            if (!trackHistoryContainer) {
              break;
            }
            trackHistoryContainer.innerHTML = content;
            break;
          }
          case "sidebar_changed": {
            const sidebar = document.getElementById("sidebar");
            if (!sidebar) {
              break;
            }
            sidebar.innerHTML = content;
            sidebar.dispatchEvent(new CustomEvent("sidebar:updated"));
            break;
          }
          case "stations_changed": {
            const stationSettings = document.getElementById("StationSettings");
            if (!stationSettings) {
              break;
            }
            stationSettings.innerHTML = content;
            stationSettings.dispatchEvent(
              new CustomEvent("station-settings:updated"),
            );
            break;
          }
          case "bluetooth_list_changed": {
            const settings = document.getElementById("Settings");
            if (!settings) {
              break;
            }
            const bluetoothDevices =
              settings.querySelector("#bluetoothDevices");
            if (!bluetoothDevices) {
              break;
            }
            bluetoothDevices.outerHTML = content;
            settings.dispatchEvent(
              new CustomEvent("bluetooth-devices:updated"),
            );
            break;
          }
          default:
            console.log("Event type unknown:", eventItem.event_type);
        }
      });
    } else {
      console.warn("No events array found in message.");
    }
  } catch (error) {
    console.error("Failed to parse message:", error);
  }
});

// Listen for connection close event
socket.addEventListener("close", function (event) {
  console.log("WebSocket is closed", event);
});

// Listen for errors
socket.addEventListener("error", function (event) {
  console.error("WebSocket error:", event);
});

/**
 * Refresh currently playing track (or station) in browser tab title
 */
function updateTitle(track, station) {
  const playingMediaTitle = track || station || "piirakka";
  document.title =
    playingMediaTitle === "piirakka"
      ? playingMediaTitle
      : `${playingMediaTitle} | piirakka`;
}

function updateTitleFromPlayerBar(playerBar) {
  const track = playerBar
    .querySelector("#player_bar_track_name")
    ?.textContent.trim();
  const station = playerBar
    .querySelector("#player_bar_station_name")
    ?.textContent.trim();
  updateTitle(track, station);
}
