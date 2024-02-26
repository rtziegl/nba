// Json data has abreviated datapoints
function mapStatToAbrv(statSelected) {
    switch (statSelected) {
        case 'Points':
            return 'PTS';
        case 'Assists':
            return 'AST';
        case 'Rebounds':
            return 'REB';
        default:
            return null; // Return null for unsupported stats
    }
}

function countMatchupOverUnderOccurrences(matchupData, statSelected, propValue) {
    const propValueNumber = isNaN(propValue) ? propValue : parseFloat(propValue);

    // Initialize counters for over and under occurrences for all games and recent games
    let matchupGamesOverCount = 0;
    let matchupGamesUnderCount = 0;

    let statMappedToAbrv = mapStatToAbrv(statSelected)
    console.log(matchupData.recent_matchups)

    matchupData = matchupData.recent_matchups;
    // Iterate through the game data
    matchupData.forEach((game) => {
        // Get the value of the selected stat for the current game
        const statValue = game[statMappedToAbrv];
        // Determine if the stat value is over or under the propValue for all games
        if (statValue >= propValueNumber) {
            matchupGamesOverCount++;
        } else if (statValue < propValueNumber) {
            matchupGamesUnderCount++;
        }
    });

    return { matchupGamesOverCount, matchupGamesUnderCount };
}

function countOverUnderOccurrences(gameData, statSelected, propValue) {
    // Convert propValue to number if it's numerical
    const propValueNumber = isNaN(propValue) ? propValue : parseFloat(propValue);

    // Initialize counters for over and under occurrences for all games and recent games
    let allGamesOverCount = 0;
    let allGamesUnderCount = 0;
    let recentGamesOverCount = 0;
    let recentGamesUnderCount = 0;
    let gameCount = 0;

    let statMappedToAbrv = mapStatToAbrv(statSelected)

    // Iterate through the game data
    gameData.forEach((game, index) => {
        // Get the value of the selected stat for the current game
        const statValue = game[statMappedToAbrv];

        // Determine if the stat value is over or under the propValue for all games
        if (statValue >= propValueNumber) {
            allGamesOverCount++;
        } else if (statValue < propValueNumber) {
            allGamesUnderCount++;
        }

        // Count only the first 12 games for recent games
        if (index < 12) {
            if (statValue >= propValueNumber) {
                recentGamesOverCount++;
            } else if (statValue < propValueNumber) {
                recentGamesUnderCount++;
            }
        }

        gameCount = index;
    });

    // Fix missing one game
    gameCount += 1;

    // Return the counts of over and under occurrences for all games and recent games
    return { gameCount, allGamesOverCount, allGamesUnderCount, recentGamesOverCount, recentGamesUnderCount };
}

document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('myForm').addEventListener('submit', function (event) {
        event.preventDefault(); // Prevent the default form submission behavior

        // Get the selected values from the form
        const playerName = document.getElementById('searchInput').value.trim();
        const statSelected = document.getElementById('statDropdownButton').innerText.trim();
        const propValue = document.getElementById('propInput').value.trim();
        const overUnderSelected = document.getElementById('overUnderDropdownButton').innerText.trim();
        const playerId = getPlayerId(playerName); // Function to extract player ID from playerName

        //Logging form values for testing.
        console.log(playerName)
        console.log(statSelected)
        console.log(propValue)
        console.log(overUnderSelected)

        // Create an array to store promises for each fetch request
        const fetchPromises = [];

        // Make a GET request to your Express.js server for all game stats
        const fetchAllGameData = fetch(`/fetch-player-game-data/${playerId}`)
            .then(response => response.json())
            .then(data => {
                // Return the data for further processing
                return data;
            })
            .catch(error => {
                console.error('Error fetching player game data:', error);
                throw error; // Propagate the error for Promise.all()
            });

        // Push the fetch promise to the array
        fetchPromises.push(fetchAllGameData);

        // Make a GET request to your Express.js server for matchups
        const fetchMatchupData = fetch(`/fetch-player-game-data-against-next-team/${playerId}`)
            .then(response => response.json())
            .then(data => {
                // Return the data for further processing
                return data;
            })
            .catch(error => {
                console.error('Error fetching player matchup data:', error);
                throw error; // Propagate the error for Promise.all()
            });

        // Push the fetch promise to the array
        fetchPromises.push(fetchMatchupData);

        // Use Promise.all() to wait for all fetch requests to complete
        Promise.all(fetchPromises)
            .then(([allGameData, matchupData]) => {
                // Process the combined data from all fetch requests
                console.log('All game data:', allGameData);
                console.log('Matchup data:', matchupData);

                // Now you can combine and process the data as needed
                const { gameCount, allGamesOverCount, allGamesUnderCount, recentGamesOverCount, recentGamesUnderCount } = countOverUnderOccurrences(allGameData, statSelected, propValue);
                // Dont want to call a loop if theres no games to search through.
                if (matchupData.num_games !=0) {
                    const { matchupGamesOverCount, matchupGamesUnderCount } = countMatchupOverUnderOccurrences(matchupData, statSelected, propValue);
                }
                
                if (overUnderSelected == 'Over'){

                }
                else if (overUnderSelected == 'Under'){

                }
            })
            .catch(error => {
                console.error('Error processing data:', error);
            });

        // Reset the form fields
        document.getElementById('myForm').reset();
        document.getElementById('statDropdownButton').textContent = 'Select a Stat';
        document.getElementById('overUnderDropdownButton').textContent = 'Over/Under';
    });
});

// Function to extract player ID from playerName
function getPlayerId(playerName) {
    // Extract player ID from playerName
    const playerNameParts = playerName.split('#');
    const playerId = playerNameParts.length > 1 ? playerNameParts[1].trim() : null;
    return playerId;
}

