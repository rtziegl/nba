// document.addEventListener('DOMContentLoaded', function() {
//     let interval; // Declare interval outside to clear it later

//     // Function to start the countdown
//     function startCountdown() {
//         fetch('/arbitrage')
//             .then(response => response.json())
//             .then(data => {
//                 const timestamp = new Date(data[0].timestamp);
//                 const endTime = new Date(timestamp.getTime() + 60000); // One minute after the timestamp
//                 updateCountdown(endTime);
//             })
//             .catch(error => console.error('Error fetching player data:', error));
//     // 

//     // Function to update the countdown every second
//     function updateCountdown(endTime) {
//         const countdownElement = document.getElementById('countdown');
//         clearInterval(interval); // Clear any existing intervals
//         interval = setInterval(function() {
//             const now = new Date();
//             const timeLeft = endTime - now;

//             if (timeLeft <= 0) {
//                 clearInterval(interval);
//                 countdownElement.textContent = 'Time is up!';
//                 // Wait for a minute before updating the timestamp
//                 setTimeout(updateTimestamp, 60000); // Wait for 60 seconds
//             } else {
//                 const seconds = Math.floor((timeLeft / 1000) % 60);
//                 const minutes = Math.floor((timeLeft / 1000 / 60) % 60);
//                 countdownElement.textContent = `Time left: ${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
//             }
//         }, 1000);
//     }

//     // Function to update the timestamp
//     function updateTimestamp() {
//         fetch('/update-timestamp', {
//             method: 'POST',
//             headers: {
//                 'Content-Type': 'application/json'
//             },
//             body: JSON.stringify({}) // You can pass any data if needed
//         })
//             .then(response => response.json())
//             .then(data => {
//                 startCountdown(); // Fetch new timestamp and restart countdown
//             })
//             .catch(error => console.error('Error updating timestamp:', error));
//     }
    
//     // Start the countdown
//     startCountdown();
// });
