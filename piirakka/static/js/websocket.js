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
        const content = eventItem.content;

        switch (eventItem.event_type) {
          case "player_bar_updated":
            updatePlayerBar(content);
            break;
          case "track_changed":
            insertNewTrack(content);
            break;
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
 * update text fields, icons and slider
 * in player bar to match actual app state
 */
function updatePlayerBar(content) {
  const player_track_title = content.track_title;
  const player_station_name = content.current_station_name;
  const volume = content.volume;
  const playback = content.playback_status;

  document.getElementById("player_bar_track_name").innerText = player_track_title;
  document.getElementById("player_bar_station_name").innerText = player_station_name;
  document.getElementById("volumeControl").value = volume;
  if (!playback) {
    document.getElementById("pauseIcon").classList.add("hidden");
    document.getElementById("playIcon").classList.remove("hidden");
  } else {
    document.getElementById("pauseIcon").classList.remove("hidden");
    document.getElementById("playIcon").classList.add("hidden");
  }
  if (volume === 0) {
    document.getElementById("volumeUpIcon").classList.add("hidden");
    document.getElementById("volumeMuteIcon").classList.remove("hidden");
  } else {
    document.getElementById("volumeUpIcon").classList.remove("hidden");
    document.getElementById("volumeMuteIcon").classList.add("hidden");
  }
}

/**
 * due to track component being a prerendered jinja template, we have to hack
 * a little and clone an existing row + replace contents manually
 */
function insertNewTrack(content) {
  // due to track component being a prerendered jinja template, we have to hack
  // a bit and clone an existing row + replace contents manually
  const history_track_title = content.title;
  const history_station_name = content.station;
  const history_timestamp = content.timestamp;

  const tbody = document.querySelector("#trackHistory tbody");
  if (!tbody || tbody.rows.length === 0) return;

  // Clone the first row deeply
  const newRow = tbody.rows[0].cloneNode(true);

  // Update timestamp
  const timestampCell = newRow.querySelector("#timeStamp");
  if (timestampCell) timestampCell.innerText = history_timestamp;

  // Update title
  const titleCell = newRow.querySelector("th[title]");
  if (titleCell) {
    titleCell.innerText = history_track_title;
    titleCell.setAttribute("title", history_track_title);
  }

  // Update station
  const stationCell = newRow.querySelectorAll("th[title]")[1];
  if (stationCell) {
    stationCell.innerText = history_station_name;
    stationCell.setAttribute("title", history_station_name);
  }

  // Update dropdown links
  const appleLink = newRow.querySelector("a[href^='music://']");
  if (appleLink) {
    appleLink.href = `music://music.apple.com/us/search?term=${encodeURIComponent(history_track_title)}`;
  }

  const spotifyLink = newRow.querySelector("a[href^='spotify://']");
  if (spotifyLink) {
    spotifyLink.href = `spotify://search/${encodeURIComponent(history_track_title)}`;
  }

  // Insert at the top
  tbody.prepend(newRow);

  // Trim to 50 rows
  while (tbody.rows.length > 50) {
    tbody.deleteRow(tbody.rows.length - 1);
  }

  updateTitle(history_track_title, history_station_name);
}

/**
 * Refresh currently
 */
function updateTitle(track, station) {
  const playingMediaTitle = track !== "" ? track : station;
  document.title = `${playingMediaTitle} | piirakka`
}
