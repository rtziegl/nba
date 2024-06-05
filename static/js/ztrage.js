document.addEventListener('DOMContentLoaded', function() {
    // Check the timer state on page load
    fetch('/check_timer')
    .then(response => response.json())
    .then(data => {
        if (data.button_used) {
            // Disable the button if it has been used
            document.getElementById('startButton').disabled = true;
            // Continue the countdown
            startCountdown(new Date(data.end_timer));
        }
    });
});



document.getElementById('startButton').addEventListener('click', function() {
    this.disabled = true; // Disable the button after it's clicked

    // Make an AJAX POST request to the Flask endpoint
    fetch('/start_countdown', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        // Start the countdown with the end_timer from the server
        startCountdown(new Date(data.end_timer));
    });
});

function startCountdown(endTime) {
    var interval = setInterval(function() {
        var now = new Date().getTime();
        var distance = endTime - now;
        console.log(distance)
        
        // Calculate and display the countdown
        var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        var seconds = Math.floor((distance % (1000 * 60)) / 1000);
        document.getElementById('timerDisplay').style.color = "#ADD8E6";
        document.getElementById('timerDisplay').innerHTML = "Search available in "+ seconds + "s";
        
        // If the countdown is finished
        if (distance < 0) {
            clearInterval(interval);
            document.getElementById('timerDisplay').style.color = "#cdffcd";
            document.getElementById('timerDisplay').innerHTML = "Search Ready";
            
            document.getElementById('startButton').disabled = false;
            // Optionally, handle the expired state by making a new request to the server
            // fetch('/start_countdown', {
            //     method: 'POST'
            // })
            // .then(response => response.json())
            // .then(data => {
            //     // Start the countdown again with the new end_timer
            //     startCountdown(new Date(data.end_timer));
            // });
        }
    }, 1000);
}

