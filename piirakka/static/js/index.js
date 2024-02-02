let lastPlayedTrack = null;
let recentlyPlayed = [];

const playPauseText = document.getElementById('playPauseText');
const hamburgerMenu = document.getElementById('hamburgerMenu');
const stationsTitle = document.getElementById('stationsTitle');
const stationDropdown = document.getElementById('stationDropdown');
const nowPlayingInfoElement = document.getElementById('nowPlayingInfo');
const recentlyPlayedElement = document.getElementById('recentlyPlayed');

document.getElementById('reloadButton').addEventListener('click', () => {
  window.location.reload();
});

document.getElementById('cancelButton').addEventListener('click', () => {
  errorDialog.close();
});

function togglePlayback() {
  axios.post('/api/radio/toggle')
    .then(response => {
      console.log('Toggle response:', response.data);
      nowPlaying();
    })
    .catch(error => {
      console.error('Error toggling playback:', error);
    });
}

function changeStation() {
  const selectedStationIndex = stationDropdown.value;

  axios.put(`/api/radio/station/${selectedStationIndex}`, { }, { headers: {'Reload-Token': reloadToken} })
    .then(response => {
      console.log('Station change response:', response.data);
    })
    .catch(error => {
      console.error('Error changing station:', error);
      if (error.response.status === 412) {
        const errorMessage = document.getElementById('errorMessage');
        errorMessage.textContent = 'Stations have been updated! Reload page?';
        errorDialog.showModal();
      }
    });
}

function toggleDropdown() {
  const isDropdownVisible = (stationDropdown.style.display === 'block');
  stationDropdown.style.display = (isDropdownVisible) ? 'none' : 'block';
  stationsTitle.style.display = (isDropdownVisible) ? 'none' : 'block';
}

function nowPlaying() {
  axios.get('/api/radio/now')
    .then(response => {

      const nowPlayingInfoHTML = `
        <div>
          <span title="Genre: ${response.data.icy_genre}">${response.data.icy_name}</span>
        </div>
      `;

      nowPlayingInfoElement.innerHTML = nowPlayingInfoHTML;

      updatePlayPauseText(response.data.status);

      if (!lastPlayedTrack || lastPlayedTrack.icy_title !== response.data.icy_title) {
        recentlyPlayed.unshift(response.data);
        recentlyPlayed = recentlyPlayed.slice(0, 10);

        lastPlayedTrack = response.data;

        displayRecentlyPlayed();
      }
      presetChannel();
    })
    .catch(error => {
      console.error('Error getting playback data:', error);
    });
}

function updatePlayPauseText(status) {
  playPauseText.classList.remove('playing', 'paused');
  playPauseText.classList.add(status);

  playPauseText.innerText = (status === 'playing') ? 'pause' : 'play';
}

function displayRecentlyPlayed() {
  let recentlyPlayedHTML = '<h3>recently played:</h3>';
  recentlyPlayed.forEach(track => {
    recentlyPlayedHTML += `<p>${track.icy_title}</p>`;
  });
  recentlyPlayedElement.innerHTML = recentlyPlayedHTML;
}

function presetChannel() {
  axios.get('/api/radio/station_id', { headers: {'Reload-Token': reloadToken} })
    .then(response => {
      const id = response.data;
      stationDropdown[id].selected = "selected";
    })
    .catch(error => {
      console.error('Error fetching stations:', error);
    });
}

nowPlaying();

setInterval(nowPlaying, 2500);
