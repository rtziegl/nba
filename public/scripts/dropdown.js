// Fetch data from the Express.js endpoint
fetch('/fetch-players-names-id')
    .then(response => response.json())
    .then(data => {
        // Get the dropdown element
        const playerDropdown = $('#playerDropdown');

        // Populate the dropdown with player names and IDs
        data.forEach(player => {
            playerDropdown.append($('<option>', {
                value: player.id,
                text: player.full_name
            }));
        });

        // Initialize the Select2 plugin on the dropdown
        playerDropdown.select2();
    })
    .catch(error => console.error('Error fetching player data:', error));