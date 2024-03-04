
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
        return { tallyUpCalc, minsGame };

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
        return { tallyUpCalc, minsGame };
    }

    // return null;
}

function calculateAllGameAvg(gameCount, allGamesOverCount, allGamesUnderCount, overUnderSelected) {

    let outOfAllCalc = '';

    if (overUnderSelected == 'Over') {
        outOfAllCalc = allGamesOverCount + ` / ${gameCount}`;
    }
    else if (overUnderSelected == 'Under') {
        outOfAllCalc = allGamesUnderCount + ` / ${gameCount}`;
    }

    return outOfAllCalc;

}

function calculate5GameAvg(recent5GamesOverCount, recent5GamesUnderCount, overUnderSelected) {

    let outOf5calc = '';

    if (overUnderSelected == 'Over') {
        outOf5calc = recent5GamesOverCount + ' / 5'
    }
    else if (overUnderSelected == 'Under') {
        outOf5calc = recent5GamesUnderCount + ' / 5'
    }

    return outOf5calc;

}

function displayScorecard(tallyUpCalc, minsGame, outOfFiveCalc, totalFouls, outOfAllCalc) {

    let consistencyRating = '';
    let consistencyColorClass = '';

    if (tallyUpCalc >= 6.5 && totalFouls <= 2.5) {
        consistencyRating = 'CONSISTENT';
        consistencyColorClass = 'consistent-color';
    }
    else if (tallyUpCalc >= 6.5 && totalFouls > 2.5) {
        consistencyRating = 'NEUTRAL';
        consistencyColorClass = 'neutral-color';
    }

    else if (tallyUpCalc < 6.5 || totalFouls > 2.5) {
        consistencyRating = 'INCONSISTENT';
        consistencyColorClass = 'inconsistent-color';
    }

    const quackScoreDisplay = document.getElementById('quackScoreDisplay');
    // Update the content of the element with the Quack Score, Minutes, and Times prop hit

    console.log(minsGame)

    if (!isNaN(minsGame)) {
        // Handle the case when minsGame is not NaN
        quackScoreDisplay.innerHTML = `
            <span class="big-text">Overall Score: ${tallyUpCalc.toFixed(2)}</span><br>
            <span class="small-text">Mallard Consistency Rating: <span class="${consistencyColorClass}">${consistencyRating}</span></span><br>
            <span class="small-text">Minutes/Season averaged while hitting prop: ${minsGame.toFixed(2)}</span><br>
            <span class="small-text">Fouls/Season averaged: ${totalFouls.toFixed(2)}</span><br>
            <span class="small-text">Prop hits this season: ${outOfAllCalc}</span><br>
            <span class="small-text">Prop hits out of last five games: ${outOfFiveCalc}</span>`;
    } else {
        // Handle the case when minsGame is NaN
        quackScoreDisplay.innerHTML = `
            <span class="big-text">Overall Score: ${tallyUpCalc.toFixed(2)}</span><br>
            <span class="small-text">Mallard Consistency Rating: <span class="${consistencyColorClass}">${consistencyRating}</span></span><br>
            <span class="small-text"><strong>Player prop has yet to hit this season</strong></span><br>
            <span class="small-text">Fouls/Season averaged: ${totalFouls.toFixed(2)}</span><br>
            <span class="small-text">Prop hits this season: ${outOfAllCalc}</span><br>
            <span class="small-text">Prop hits out of last five games: ${outOfFiveCalc}</span>`;
    }
}

function displayScoreList(tallyUpCalc, decimalPropValue, overUnderSelected, statSelected, playerName) {
    // Select the list element
    const listScoreDisplayVar = document.getElementById('listScoreDisplay');

    // Create a new anchor element
    const listItem = document.createElement('a');
    listItem.classList.add('list-group-item', 'list-group-item-action', 'bg-dark', 'text-white');

    let hashIndex = playerName.indexOf('#');

    // If '#' is found, remove everything after it
    if (hashIndex !== -1) {
        playerName = playerName.substring(0, hashIndex).trim();
    }

    // Set the content of the list item
    listItem.textContent = `${playerName} ${overUnderSelected} ${decimalPropValue} ${statSelected}, Score: ${tallyUpCalc.toFixed(2)}`;

    // Append the new list item to the list
    listScoreDisplayVar.appendChild(listItem);

    // Update the card's body content
    const cardBody = document.querySelector('.score-history-card-body');

    // Find the waiting-score div
    const waitingScoreDiv = cardBody.querySelector('.waiting-score');

    // Replace its content with the big text and clipboard icon
    waitingScoreDiv.innerHTML = `
        <div class="d-flex justify-content-between">
            <div class="big-text mb-3">Score History</div>
            <div class="float-end">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-clipboard2 clipboard-icon" viewBox="0 0 16 16">
            <path d="M3.5 2a.5.5 0 0 0-.5.5v12a.5.5 0 0 0 .5.5h9a.5.5 0 0 0 .5-.5v-12a.5.5 0 0 0-.5-.5H12a.5.5 0 0 1 0-1h.5A1.5 1.5 0 0 1 14 2.5v12a1.5 1.5 0 0 1-1.5 1.5h-9A1.5 1.5 0 0 1 2 14.5v-12A1.5 1.5 0 0 1 3.5 1H4a.5.5 0 0 1 0 1z"/>
            <path d="M10 .5a.5.5 0 0 0-.5-.5h-3a.5.5 0 0 0-.5.5.5.5 0 0 1-.5.5.5.5 0 0 0-.5.5V2a.5.5 0 0 0 .5.5h5A.5.5 0 0 0 11 2v-.5a.5.5 0 0 0-.5-.5.5.5 0 0 1-.5-.5"/>
          </svg>
            </div>
        </div>`;

    const clipboardIcon = waitingScoreDiv.querySelector('.clipboard-icon');
    clipboardIcon.addEventListener('click', function () {
        let copiedText = '';
        // Iterate over each list item
        const listItems = document.querySelectorAll('.list-group-item');
        listItems.forEach((item) => {
            copiedText += item.textContent + '\n';
        });

        // Copy the concatenated text to the clipboard
        navigator.clipboard.writeText(copiedText)
            .then(() => {
                console.log('Text copied to clipboard:', copiedText);
                // Show a dark-themed alert at the bottom center of the screen
                showAlert('Score history copied to clipboard ');
            })
            .catch((error) => {
                console.error('Error copying text to clipboard:', error);
            });
    });

    function showAlert(message) {
        // Create the alert div
        const alertDiv = document.createElement('div');
        alertDiv.classList.add('copy-alert');

        // Set the message content
        alertDiv.textContent = message;

        // Create the checkmark icon
        const checkMarkIcon = document.createElement('div');
        checkMarkIcon.innerHTML = `
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-clipboard2-check" viewBox="0 0 16 16">
        <path d="M9.5 0a.5.5 0 0 1 .5.5.5.5 0 0 0 .5.5.5.5 0 0 1 .5.5V2a.5.5 0 0 1-.5.5h-5A.5.5 0 0 1 5 2v-.5a.5.5 0 0 1 .5-.5.5.5 0 0 0 .5-.5.5.5 0 0 1 .5-.5z"/>
        <path d="M3 2.5a.5.5 0 0 1 .5-.5H4a.5.5 0 0 0 0-1h-.5A1.5 1.5 0 0 0 2 2.5v12A1.5 1.5 0 0 0 3.5 16h9a1.5 1.5 0 0 0 1.5-1.5v-12A1.5 1.5 0 0 0 12.5 1H12a.5.5 0 0 0 0 1h.5a.5.5 0 0 1 .5.5v12a.5.5 0 0 1-.5.5h-9a.5.5 0 0 1-.5-.5z"/>
        <path d="M10.854 7.854a.5.5 0 0 0-.708-.708L7.5 9.793 6.354 8.646a.5.5 0 1 0-.708.708l1.5 1.5a.5.5 0 0 0 .708 0z"/>
    </svg>
`;

        // Style the elements for inline display
        alertDiv.style.display = 'flex';
        alertDiv.style.alignItems = 'center';
        alertDiv.style.gap = '5px';
        checkMarkIcon.style.display = 'inline';

        // Append the checkmark icon to the alert div
        alertDiv.appendChild(checkMarkIcon);

        // Append the alert div to the document body
        document.body.appendChild(alertDiv);

        // Fade in the alert
        setTimeout(() => {
            alertDiv.style.opacity = 1;
        }, 100);

        // Remove the alert after 3 seconds
        setTimeout(() => {
            alertDiv.style.opacity = 0;
            setTimeout(() => {
                alertDiv.remove();
            }, 100); // Adjust the timing to match the fade-out transition duration
        }, 3000); // Duration of alert visibility
    }

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
            console.log("MINS VALUE OVER:", minsValue)
            minsGameOver += minsValue;
        } else if (statValue < propValueNumber) {
            allGamesUnderCount++;
            minsGameUnder += minsValue;
            console.log("MINS VALUE UNDERR:", minsValue)
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
    return { gameCount, allGamesOverCount, allGamesUnderCount, recent12GamesOverCount, recent12GamesUnderCount, recent3GamesOverCount, recent3GamesUnderCount, recent5GamesOverCount, recent5GamesUnderCount, minsGameOver, minsGameUnder, totalFouls };
}


document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('myForm').addEventListener('submit', function (event) {
        event.preventDefault(); // Prevent the default form submission behavior

        // Display the loading animation
        // displayLoadingAnimation();

        // Get the selected values from the form
        const playerName = document.getElementById('searchInput').value.trim();
        const statSelected = document.getElementById('statDropdownButton').innerText.trim();
        let propValue = document.getElementById('propInput').value.trim();
        const decimalPropValue = propValue;
        const overUnderSelected = document.getElementById('overUnderDropdownButton').innerText.trim();
        const playerId = getPlayerId(playerName); // Function to extract player ID from playerName
        // Get the element where you want to display the Quack Score

        const submitButton = document.getElementById('submitButton');
        const statDropdownItems = document.querySelectorAll('#statDropdownButton + .dropdown-menu .dropdown-item');
        const overUnderDropdownItems = document.querySelectorAll('#overUnderDropdownButton + .dropdown-menu .dropdown-item');

        // Check if propValue contains .5
        if (propValue.includes('.5')) {
            // Convert propValue to a number and add 0.5 to it
            propValue = (parseFloat(propValue) + 0.5).toFixed(1);
        }

        //Logging form values for testing.
        console.log(playerName)
        console.log(statSelected)
        console.log(propValue)
        console.log(overUnderSelected)

        console.log('Fetching all game data...');
        // Make a GET request to your Express.js server for all game stats
        const fetchAllGameData = fetch(`/nba_get_player_game_data?playerId=${playerId}`)
            .then(response => response.json())
            .then(async allGameData => {
                console.log('All game data fetched successfully.');
                console.log('Fetching matchup data...');
                // Make a GET request to your Express.js server for matchups
                const response = await fetch(`/nba_get_next_matchup?playerId=${playerId}`);
                const matchupData = await response.json();
                console.log('Matchup data fetched successfully.');
                return { allGameData, matchupData };
            })
            .catch(error => {
                console.error('Error fetching data:', error);
                throw error;
            });

        // Process the combined data from the fetch requests
        fetchAllGameData.then(({ allGameData, matchupData }) => {
            // Process the combined data from all fetch requests
            console.log('All game data:', allGameData);
            console.log('Matchup data:', matchupData);

            // All games and recent games
            const { gameCount, allGamesOverCount, allGamesUnderCount, recent12GamesOverCount, recent12GamesUnderCount, recent3GamesOverCount, recent3GamesUnderCount, recent5GamesOverCount, recent5GamesUnderCount, minsGameOver, minsGameUnder, totalFouls } = countOverUnderOccurrences(allGameData, statSelected, propValue);

            // Matchups
            const { matchupGamesOverCount, matchupGamesUnderCount } = countMatchupOverUnderOccurrences(matchupData, statSelected, propValue);
            const { tallyUpCalc, minsGame } = calculateQuackScore(gameCount, allGamesOverCount, allGamesUnderCount, recent12GamesOverCount, recent12GamesUnderCount, recent3GamesOverCount, recent3GamesUnderCount, matchupGamesOverCount, matchupGamesUnderCount, matchupData.num_games, overUnderSelected, minsGameOver, minsGameUnder)
            const outOfFiveCalc = calculate5GameAvg(recent5GamesOverCount, recent5GamesUnderCount, overUnderSelected)
            const outOfAllCalc = calculateAllGameAvg(gameCount, allGamesOverCount, allGamesUnderCount, overUnderSelected);
            // Displays stats for card 
            displayScorecard(tallyUpCalc, minsGame, outOfFiveCalc, totalFouls, outOfAllCalc)
            displayScoreList(tallyUpCalc, decimalPropValue, overUnderSelected, statSelected, playerName)
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

