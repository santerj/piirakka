function createStation(event) {
    event.preventDefault();

    // Get form data
    const url = document.getElementById('newStationUrl').value;
    const name = document.getElementById('newStationName').value;

    // Make API request to create a new station
    // You can use Axios or fetch here
    axios.post('/api/radio/station', {
        url: url,
        description: name
    })
    .then(response => {
        // Handle success, if needed
        console.log(response.data);
    })
    .catch(error => {
        // Handle error, if needed
        console.error(error);
    });
}

function editStation(index) {
    // Perform edit action based on the station index
    console.log(`Editing station ${index}`);
}

function deleteStation(index) {
    axios.post('/api/radio/station')
      .then(response => {
        console.log('Toggle response:', response.data);
        nowPlaying();
    })
      .catch(error => {
        console.error('Error toggling playback:', error);
    });
}