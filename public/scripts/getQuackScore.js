// document.addEventListener('DOMContentLoaded', function() {
//     document.getElementById('myForm').addEventListener('submit', function(event) {
//         event.preventDefault(); // Prevent the default form submission behavior

//         // Get the selected values from the form
//         const playerName = document.getElementById('searchInput').value.trim();
//         const propValue = document.getElementById('propInput').value.trim();
//         const selectedStat = document.getElementById('statDropdownButton').textContent.trim(); // Get text content of the dropdown button
//         const selectedOverUnder = document.getElementById('overUnderDropdownButton').textContent.trim(); // Get text content of the dropdown button

//         // Perform form submission actions
//         handleFormSubmission(playerName, selectedStat, propValue, selectedOverUnder);

//         // Reset the form fields if needed
//         document.getElementById('myForm').reset();
//     });
// });

// // Function to handle form submission
// function handleFormSubmission(playerName, selectedStat, propValue, selectedOverUnder) {
//     // Extract player ID from playerName
//     const playerNameParts = playerName.split('#');
//     const playerId = playerNameParts.length > 1 ? playerNameParts[1].trim() : null;

//     // Perform actions based on the form data
//     console.log('Player Name:', playerNameParts[0].trim()); // Log player name without ID
//     console.log('Player ID:', playerId); // Log player ID
//     console.log('Selected Stat:', selectedStat);
//     console.log('Prop Value:', propValue);
//     console.log('Over/Under:', selectedOverUnder);
// }

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('myForm').addEventListener('submit', function(event) {
        event.preventDefault(); // Prevent the default form submission behavior

        // Get the selected values from the form
        const playerName = document.getElementById('searchInput').value.trim();
        const playerId = getPlayerId(playerName); // Function to extract player ID from playerName

        console.log(playerId);

        // Make a GET request to your Express.js server
        fetch(`/fetch-player-game-data/${playerId}`)
            .then(response => response.json())
            .then(data => {
                // Handle the response data
                console.log('Response from server:', data);
            })
            .catch(error => {
                console.error('Error:', error);
            });

        // Reset the form fields if needed
        document.getElementById('myForm').reset();
    });
});

// Function to extract player ID from playerName
function getPlayerId(playerName) {
    // Extract player ID from playerName
    const playerNameParts = playerName.split('#');
    const playerId = playerNameParts.length > 1 ? playerNameParts[1].trim() : null;
    return playerId;
}

