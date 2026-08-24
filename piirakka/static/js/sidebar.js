function initializeStationList(sidebar) {
  const stationList = sidebar.querySelector("#stationList");
  if (!stationList || stationList.sortable) {
    return;
  }

  stationList.sortable = Sortable.create(stationList, {
    animation: 150,
    onEnd: async function () {
      const order = [...stationList.querySelectorAll("li")].map(
        (li) => li.querySelector("p").dataset.stationid,
      );

      await fetch("/api/stations/reorder", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ order }),
      });
    },
  });
}

function initializeSidebar() {
  const sidebar = document.getElementById("sidebar") || document.querySelector("aside");
  if (!sidebar || sidebar.sidebarInitialized) {
    return;
  }

  sidebar.addEventListener("click", function (event) {
    const station = event.target.closest("p[data-stationid]");
    if (!station || !sidebar.contains(station)) {
      return;
    }

    const stationId = station.dataset.stationid;
    fetch(`/api/radio/station/${stationId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ stationId }),
    })
      .then((response) => response.json())
      .then((data) => console.log(data))
      .catch((error) => console.error("Error:", error));
  });

  sidebar.addEventListener("input", function (event) {
    if (event.target.id !== "stationSearch") {
      return;
    }

    const query = event.target.value.toLowerCase();
    sidebar.querySelectorAll("p[data-stationid]").forEach((station) => {
      const name = station.textContent.toLowerCase();
      station.parentElement.style.display = name.includes(query) ? "" : "none";
    });
  });

  sidebar.addEventListener("sidebar:updated", function () {
    initializeStationList(sidebar);
  });

  sidebar.sidebarInitialized = true;
  initializeStationList(sidebar);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeSidebar);
} else {
  initializeSidebar();
}
