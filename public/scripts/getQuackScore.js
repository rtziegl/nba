
function calculateQuackScore(gameCount, allGamesOverCount, allGamesUnderCount, recent12GamesOverCount, recent12GamesUnderCount, recent3GamesOverCount, recent3GamesUnderCount, matchupGamesOverCount, matchupGamesUnderCount, matchupDataNumGames, overUnderSelected, minsGameOver, minsGameUnder) {

    let allGamesCalc = 0.0;
    let recent12GamesCalc = 0.0;
    let matchupGamesCalc = 0.0;
    let recent3GamesCalc = 0.0;
    let tallyUpCalc = 0.0;
    let amt12RecentGames = 12;
    let amt3RecentGames = 3;
    let allGamesPercent = .25;
    let recent12GamesPercent = .5;
    let matchupGamesPercent = .15;
    let recent3GamesPercent = .10;
    let minsGame = 0.0;

    if (overUnderSelected == 'Over') {

        minsGame = minsGameOver;
        allGamesCalc = allGamesOverCount / gameCount;
        allGamesCalc *= allGamesPercent;

        console.log("huntint allgamescalc", allGamesCalc)

        recent12GamesCalc = recent12GamesOverCount / amt12RecentGames;
        recent12GamesCalc *= recent12GamesPercent;

        console.log("huntint recent12", recent12GamesCalc)

        recent3GamesCalc = recent3GamesOverCount / amt3RecentGames;
        recent3GamesCalc *= recent3GamesPercent;

        console.log("huntint recent3", recent3GamesCalc)


        // Replacing matchup percentage with recent 3 game percentage when no matchups found.
        if (matchupDataNumGames == 0) {
            matchupGamesCalc = recent3GamesOverCount / amt3RecentGames;
            matchupGamesCalc *= matchupGamesPercent;

        }
        else {
            matchupGamesCalc = matchupGamesOverCount / matchupDataNumGames;
            matchupGamesCalc *= matchupGamesPercent;
        }

        console.log("matchupgamescalc: " + matchupGamesCalc + "num games: " + matchupDataNumGames)

        console.log("huntint matchup", matchupGamesCalc)

        tallyUpCalc = allGamesCalc + recent12GamesCalc + matchupGamesCalc + recent3GamesCalc;

        console.log("huntint nan", tallyUpCalc)

        tallyUpCalc *= 10;
        console.log("QUack ove rmins", minsGameOver)
        return {tallyUpCalc, minsGame};

    }

    else if (overUnderSelected == 'Under') {
        minsGame = minsGameUnder;
        allGamesCalc = allGamesUnderCount / gameCount;
        allGamesCalc *= allGamesPercent;

        console.log("huntint allgamescalc", allGamesCalc)

        recent12GamesCalc = recent12GamesUnderCount / amt12RecentGames;
        recent12GamesCalc *= recent12GamesPercent;

        console.log("huntint recent12", recent12GamesCalc)

        recent3GamesCalc = recent3GamesUnderCount / amt3RecentGames;
        recent3GamesCalc *= recent3GamesPercent;

        console.log("huntint recent3", recent3GamesCalc)


        // Replacing matchup percentage with recent 3 game percentage when no matchups found.
        if (matchupDataNumGames == 0) {
            matchupGamesCalc = recent3GamesUnderCount / amt3RecentGames;
            matchupGamesCalc *= matchupGamesPercent;

        }
        else {
            matchupGamesCalc = matchupGamesUnderCount / matchupDataNumGames;
            matchupGamesCalc *= matchupGamesPercent;
        }

        console.log("huntint matchup", matchupGamesCalc)

        tallyUpCalc = allGamesCalc + recent12GamesCalc + matchupGamesCalc + recent3GamesCalc;

        console.log("huntint nan", tallyUpCalc)

        tallyUpCalc *= 10;
        return {tallyUpCalc, minsGame};
    }

    // return null;
}

function calculate5GameAvg(recent5GamesOverCount, recent5GamesUnderCount, overUnderSelected){

    let outOf5calc = '';

    if (overUnderSelected == 'Over') {
        outOf5calc = recent5GamesOverCount + ' / 5'
    }
    else if (overUnderSelected == 'Under') {
        outOf5calc = recent5GamesUnderCount + ' / 5'
    }

    return outOf5calc;

}

function displayScorecard(tallyUpCalc, minsGame, outOfFiveCalc, totalFouls) {
    const quackScoreDisplay = document.getElementById('quackScoreDisplay');
    // Update the content of the element with the Quack Score, Minutes, and Times prop hit
    quackScoreDisplay.innerHTML = `
        <span class="big-text">Overall Score: ${tallyUpCalc.toFixed(2)}</span><br>
        <span class="small-text">Minutes/Season averaged while hitting prop: ${minsGame.toFixed(2)}</span><br>
        <span class="small-text">Fouls/Season averaged: ${totalFouls.toFixed(2)}</span><br>
        <span class="small-text">Prop hits out of last five games: ${outOfFiveCalc}</span>`;
}





// Json data has abreviated datapoints
function mapStatToAbrv(statSelected) {
    switch (statSelected) {
        case 'Points':
            return 'PTS';
        case 'Assists':
            return 'AST';
        case 'Rebounds':
            return 'REB';
        case '3 Pointers':
            return 'FG3M'
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

    // Don't want to run loop on 0 matchup games
    if (matchupData.num_games != 0) {
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
    }

    return { matchupGamesOverCount, matchupGamesUnderCount };
}

function countOverUnderOccurrences(gameData, statSelected, propValue) {
    // Convert propValue to number if it's numerical
    const propValueNumber = isNaN(propValue) ? propValue : parseFloat(propValue);

    // Initialize counters for over and under occurrences for all games, recent games, and the most recent 3 games
    let allGamesOverCount = 0;
    let allGamesUnderCount = 0;
    let recent12GamesOverCount = 0;
    let recent12GamesUnderCount = 0;
    let recent3GamesOverCount = 0;
    let recent3GamesUnderCount = 0;
    let recent5GamesOverCount = 0;
    let recent5GamesUnderCount = 0;
    let minsGameOver = 0;
    let minsGameUnder = 0;
    let gameCount = 0;
    let totalFouls = 0;

    let statMappedToAbrv = mapStatToAbrv(statSelected);
    let minsMappedToAbrv = 'MIN';
    let foulsMappedToAbrv = 'PF';

    // Iterate through the game data
    gameData.forEach((game, index) => {
        // Get the value of the selected stat for the current game
        const statValue = game[statMappedToAbrv];
        console.log(statValue)
        const minsValue = game[minsMappedToAbrv];
        const foulsValue = game[foulsMappedToAbrv];
        
        // Determine if the stat value is over or under the propValue for all games
        if (statValue >= propValueNumber) {
            allGamesOverCount++;
            console.log("MINS VALUE OVER:" ,minsValue)
            minsGameOver += minsValue;
        } else if (statValue < propValueNumber) {
            allGamesUnderCount++;
            minsGameUnder += minsValue;
            console.log("MINS VALUE UNDERR:" ,minsValue)
        }

        // Count only the first 12 games for recent games
        if (index < 12) {
            if (statValue >= propValueNumber) {
                recent12GamesOverCount++;
            } else if (statValue < propValueNumber) {
                recent12GamesUnderCount++;
            }
        }

        // Count only the most recent 3 games
        if (index < 3) {
            if (statValue >= propValueNumber) {
                recent3GamesOverCount++;
            } else if (statValue < propValueNumber) {
                recent3GamesUnderCount++;
            }
        }

        // Count only the most recent 5 games
        if (index < 5) {
            if (statValue >= propValueNumber) {
                recent5GamesOverCount++;
            } else if (statValue < propValueNumber) {
                recent5GamesUnderCount++;
            }
        }

        gameCount = index;
        totalFouls += foulsValue;
    });

    minsGameOver /= allGamesOverCount;
    minsGameUnder /= allGamesUnderCount;

    // Fix missing one game
    gameCount += 1;

    // Total fouls averaged fom the season.
    totalFouls /= gameCount;

    console.log(allGamesOverCount)
    console.log(allGamesUnderCount)
    // Return the counts of over and under occurrences for all games, recent games, and the most recent 3 games
    return { gameCount, allGamesOverCount, allGamesUnderCount, recent12GamesOverCount, recent12GamesUnderCount, recent3GamesOverCount, recent3GamesUnderCount, recent5GamesOverCount, recent5GamesUnderCount , minsGameOver, minsGameUnder, totalFouls};
}


document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('myForm').addEventListener('submit', function (event) {
        event.preventDefault(); // Prevent the default form submission behavior

        // Display the loading animation
        // displayLoadingAnimation();

        // Get the selected values from the form
        const playerName = document.getElementById('searchInput').value.trim();
        const statSelected = document.getElementById('statDropdownButton').innerText.trim();
        const propValue = document.getElementById('propInput').value.trim();
        const overUnderSelected = document.getElementById('overUnderDropdownButton').innerText.trim();
        const playerId = getPlayerId(playerName); // Function to extract player ID from playerName
        // Get the element where you want to display the Quack Score
        
        const submitButton = document.getElementById('submitButton');
        const statDropdownItems = document.querySelectorAll('#statDropdownButton + .dropdown-menu .dropdown-item');
        const overUnderDropdownItems = document.querySelectorAll('#overUnderDropdownButton + .dropdown-menu .dropdown-item');

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

                // All games and recent games
                const { gameCount, allGamesOverCount, allGamesUnderCount, recent12GamesOverCount, recent12GamesUnderCount, recent3GamesOverCount, recent3GamesUnderCount, recent5GamesOverCount, recent5GamesUnderCount, minsGameOver, minsGameUnder, totalFouls} = countOverUnderOccurrences(allGameData, statSelected, propValue);
            
                // Matchups
                const { matchupGamesOverCount, matchupGamesUnderCount } = countMatchupOverUnderOccurrences(matchupData, statSelected, propValue);
                const {tallyUpCalc, minsGame} = calculateQuackScore(gameCount, allGamesOverCount, allGamesUnderCount, recent12GamesOverCount, recent12GamesUnderCount, recent3GamesOverCount, recent3GamesUnderCount, matchupGamesOverCount, matchupGamesUnderCount, matchupData.num_games, overUnderSelected, minsGameOver, minsGameUnder)
                const outOfFiveCalc = calculate5GameAvg(recent5GamesOverCount, recent5GamesUnderCount, overUnderSelected)

                // Displays stats for card 
                displayScorecard(tallyUpCalc, minsGame, outOfFiveCalc, totalFouls)
                
            })
            .catch(error => {
                console.error('Error processing data:', error);
            });
        
        // Resets form
        const resetButton = document.getElementById('resetButton');

        resetButton.addEventListener('click', function () {
            // Reset the form fields
            document.getElementById('myForm').reset();
            document.getElementById('statDropdownButton').textContent = 'Select a Stat';
            document.getElementById('overUnderDropdownButton').textContent = 'Over/Under';
            statDropdownItems.forEach(item => item.classList.remove('active'));
            overUnderDropdownItems.forEach(item => item.classList.remove('active'));
            submitButton.disabled = true;
        });

    });
});



// Function to extract player ID from playerName
function getPlayerId(playerName) {
    // Extract player ID from playerName
    const playerNameParts = playerName.split('#');
    const playerId = playerNameParts.length > 1 ? playerNameParts[1].trim() : null;
    return playerId;
}

