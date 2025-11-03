const wsEndpoint = `ws://${window.location.host}/ws/socket`;

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
        switch (eventItem.event_type) {
          case 'player_bar_updated':
            // update fields in player bar
            const track_title = eventItem.content.track_title;
            const station_name = eventItem.content.current_station_name;
            const volume = eventItem.content.volume;
            const playback = eventItem.content.playback_status;

            document.getElementById('player_bar_track_name').innerText = track_title;
            document.getElementById('player_bar_station_name').innerText = station_name;
            document.getElementById("volumeControl").value = volume;
            if (!playback) {
              document.getElementById('pauseIcon').classList.add('hidden');
              document.getElementById('playIcon').classList.remove('hidden');
            } else {
              document.getElementById('pauseIcon').classList.remove('hidden');
              document.getElementById('playIcon').classList.add('hidden');
            }
            if (volume == 0) {
              document.getElementById('volumeUpIcon').classList.add('hidden');
              document.getElementById('volumeMuteIcon').classList.remove('hidden');
            } else {
              document.getElementById('volumeUpIcon').classList.remove('hidden');
              document.getElementById('volumeMuteIcon').classList.add('hidden');
            }
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
  console.log("WebSocket is closed.");
});

// Listen for errors
socket.addEventListener("error", function (event) {
  console.error("WebSocket error:", event);
});
