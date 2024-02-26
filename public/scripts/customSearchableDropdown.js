// Define searchData as a global variable
let searchData = []; // Initialize as an empty array to avoid 'undefined' errors

function populateDropdown(searchData) {
    const searchResults = document.getElementById('searchResults');
    searchResults.innerHTML = ''; // Clear previous results
    searchData.forEach(item => {
        const resultItem = document.createElement('li');
        resultItem.classList.add('dropdown-item');
        resultItem.textContent = `${item.full_name} #${item.id}`; // Include player name and ID
        resultItem.setAttribute('data-id', item.id); // Set data attribute for player ID
        resultItem.addEventListener('click', function () {
            // Set the selected value in the search input
            document.getElementById('searchInput').value = `${item.full_name} #${item.id}`; // Include player name and ID
            // Close the dropdown
            document.getElementById('searchResults').classList.remove('show');
        });
        searchResults.appendChild(resultItem);
    });
}


// Function to filter search results based on input value
function filterResults(inputValue) {
    const filteredData = searchData.filter(item => {
        const fullName = item.full_name.toLowerCase();
        return fullName.includes(inputValue.toLowerCase());
    });
    populateDropdown(filteredData);
}

// Event listener for click event in search input
document.getElementById('searchInput').addEventListener('click', function () {
    // Open the dropdown programmatically
    document.getElementById('searchResults').classList.add('show');
});

// Event listener for input event in search input
document.getElementById('searchInput').addEventListener('input', function () {
    const inputValue = this.value.trim(); // Get the trimmed input value
    filterResults(inputValue); // Filter search results based on input value
});

// Event listener for click event in the document body to close dropdown
document.body.addEventListener('click', function (event) {
    if (!event.target.closest('#searchResults') && event.target !== document.getElementById('searchInput')) {
        // Close the dropdown if the click is outside the search input and search results
        document.getElementById('searchResults').classList.remove('show');
    }
});

// Fetch player data from the Express.js endpoint and populate dropdown
fetch('/fetch-players-names-id')
    .then(response => response.json())
    .then(data => {
        searchData = data; // Assign fetched data to searchData variable
        populateDropdown(searchData); // Populate dropdown with player data
    })
    .catch(error => console.error('Error fetching player data:', error));
