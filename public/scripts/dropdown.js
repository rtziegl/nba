// // Fetch data from the Express.js endpoint
// fetch('/fetch-players-names-id')
//     .then(response => response.json())
//     .then(data => {
//         // Get the dropdown element
//         const playerDropdown = $('#searchResults');

//         // Populate the dropdown with player names and IDs
//         data.forEach(player => {
//             playerDropdown.append($('<option>', {
//                 value: player.id,
//                 text: player.full_name
//             }));
//         });

//         // // Initialize the Select2 plugin on the dropdown
//         // playerDropdown.select2();
//     })
//     .catch(error => console.error('Error fetching player data:', error));

// Function to populate dropdown with search results
function populateDropdown(searchData) {
    const searchResults = document.getElementById('searchResults');
    searchResults.innerHTML = ''; // Clear previous results
    searchData.forEach(item => {
        const resultItem = document.createElement('li');
        resultItem.classList.add('dropdown-item');
        resultItem.textContent = item.full_name;
        resultItem.setAttribute('data-id', item.id); // Set data attribute for player ID
        searchResults.appendChild(resultItem);
    });
}

// Event listener for click event in search input
document.getElementById('searchInput').addEventListener('click', function () {
    // Fetch player data from the Express.js endpoint
    fetch('/fetch-players-names-id')
        .then(response => response.json())
        .then(data => {
            populateDropdown(data); // Populate dropdown with player data
            // Open the dropdown programmatically
            document.getElementById('searchInput').classList.add('show');
        })
        .catch(error => console.error('Error fetching player data:', error));
});
