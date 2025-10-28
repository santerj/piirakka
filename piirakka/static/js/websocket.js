const wsEndpoint = `ws://${window.location.host}/api/websocket`;
console.log('wahuu!!');

// Open websocket
const socket = new WebSocket(wsEndpoint);

// Listen for connection open event
socket.addEventListener('open', function(event) {
    console.log('WebSocket is connected.');
});

// Listen for messages from the server
socket.addEventListener('message', function(event) {
    // Parse the incoming message
    const message = JSON.parse(event.data);

    // check event type
    if (message.event === 'track_changed') {
        // set track history
        const trackHistoryElement = document.getElementById('TrackHistory');
        trackHistoryElement.innerHTML = message.html;
    }

    else if (message.event === 'control_bar_updated') {
        const controlBar = document.getElementById('ControlBar');
        controlBar.innerHTML = message.html;
    }
});

// Listen for connection close event
socket.addEventListener('close', function(event) {
    console.log('WebSocket is closed.');
});

// Listen for errors
socket.addEventListener('error', function(event) {
    console.error('WebSocket error:', event);
});
