// Define the event listener for form submission
document.getElementById('myForm').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent the default form submission behavior

    // Get the selected values from the form
    const playerName = document.getElementById('searchInput').value.trim();
    const selectedStat = document.getElementById('statDropdown').value;
    const propValue = document.getElementById('propInput').value.trim();
    const overUnderValue = document.getElementById('overUnderDropdown').value;

    // Perform further actions as needed
    // For example, you can call a function defined in this script or in another JavaScript file
    handleFormSubmission(playerName, selectedStat, propValue, overUnderValue);

    // Reset the form fields if needed
    document.getElementById('myForm').reset();
});

// Function to handle form submission
// Function to handle form submission
function handleFormSubmission(playerName, selectedStat, propValue, overUnderValue) {
    // Extract player ID from playerName
    const playerNameParts = playerName.split('#');
    const playerId = playerNameParts.length > 1 ? playerNameParts[1].trim() : null;

    // Perform actions based on the form data
    // You can fetch player information, make AJAX requests, etc.
    console.log('Player Name:', playerNameParts[0].trim()); // Log player name without ID
    console.log('Player ID:', playerId); // Log player ID
    console.log('Selected Stat:', selectedStat);
    console.log('Prop Value:', propValue);
    console.log('Over/Under:', overUnderValue);
}

