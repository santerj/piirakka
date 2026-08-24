function initializeStationSettings() {
  const stationSettings = document.getElementById("StationSettings");
  if (!stationSettings || stationSettings.stationSettingsInitialized) {
    return;
  }

  stationSettings.addEventListener("click", function (event) {
    const station = event.target.closest("li[data-station-id]");
    if (station && stationSettings.contains(station)) {
      document.getElementById("edit_station_id").value =
      station.dataset.stationId;
      document.getElementById("edit_station_name").value =
      station.dataset.stationName;
      document.getElementById("edit_station_url").value =
      station.dataset.stationUrl;
      document.getElementById("edit_station_modal").showModal();
      return;
    }

    if (event.target.id === "delete_station_button") {
      deleteStation();
    }
  });

  stationSettings.addEventListener("submit", function (event) {
    if (event.target.id === "editStationForm") {
      updateStation(event);
    }
  });

  stationSettings.addEventListener("station-settings:updated", function () {
    initializeStationSettings();
  });

  stationSettings.stationSettingsInitialized = true;
}

async function updateStation(event) {
  event.preventDefault();
  const id = document.getElementById("edit_station_id").value;
  const name = document.getElementById("edit_station_name").value.trim();
  const url = document.getElementById("edit_station_url").value.trim();

  if (!name || !url) {
    alert("Both fields are required.");
    return;
  }

  try {
    const response = await fetch(`/api/station/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ station_name: name, station_url: url }),
    });
    if (response.ok) {
      document.getElementById("edit_station_modal").close();
    } else {
      alert("Failed to update station: " + (await response.text()));
    }
  } catch (error) {
    console.error("Error:", error);
    alert("Something went wrong.");
  }
}

async function deleteStation() {
  if (!confirm("Are you sure you want to delete this station?")) {
    return;
  }

  const id = document.getElementById("edit_station_id").value;
  try {
    const response = await fetch(`/api/station/${id}`, { method: "DELETE" });
    if (response.ok) {
      document.getElementById("edit_station_modal").close();
    } else {
      alert("Failed to delete station: " + await response.text());
    }
  } catch (error) {
    console.error("Error:", error);
    alert("Something went wrong.");
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeStationSettings);
} else {
  initializeStationSettings();
}
