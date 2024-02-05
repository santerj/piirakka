console.log(reloadToken);

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
        location.reload();
    })
    .catch(error => {
        // Handle error, if needed
        console.error(error);
    });
}

function deleteStation(index) {
    axios.delete(`/api/radio/station/${index}`, { headers: {'Reload-Token': reloadToken} })
      .then(response => {
        console.log('Delete response:', response.data);
        location.reload();
    })
      .catch(error => {
        console.error('Error deleting station:', error);
    });
}
