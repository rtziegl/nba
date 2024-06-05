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

    // Fetch arbitrage opportunities and display them
    fetchArbitrageOpportunities();

    // Add event listener to the start button
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

        // Make an AJAX POST request to the Flask endpoint
        fetch('/fetch_arbitrages', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            fetchArbitrageOpportunities();
        });

        
    });
});

// Function to fetch arbitrage opportunities and display them
function fetchArbitrageOpportunities() {
    fetch('/get_arbitrage')
    .then(response => response.json())
    .then(data => {
        console.log(data[0].arbitrage)
        if (data[0].arbitrage) {
            // If there are arbitrage opportunities, display them
            if (data[0].arbitrage_opportunities.length > 0) {
                displayArbitrageOpportunities(data[0].arbitrage_opportunities);
            } else {
                displayNoArbitrage();
            }
        } else {
            // If no arbitrage opportunities, display a message
            displayNoArbitrage();
        }
    });
}

function decimalToAmerican(decimalOdds) {
    if (decimalOdds > 2) {
        return Math.round((decimalOdds - 1) * 100);
    } else {
        return Math.round(-100 / (decimalOdds - 1));
    }
}


// Function to display arbitrage opportunities
function displayArbitrageOpportunities(arbitrage_opportunities) {
    // Get the element where arbitrage information will be displayed
    var arbitrageContainer = document.getElementById('arbitrageContainer');

    // Clear any existing content
    arbitrageContainer.innerHTML = '';

    // Iterate over each arbitrage opportunity
    arbitrage_opportunities.forEach(opportunity => {
        // Create a new div for each opportunity
        var opportunityDiv = document.createElement('div');
        opportunityDiv.classList.add('opportunity');

        // Populate the div with arbitrage information
        opportunityDiv.innerHTML = `
            <div class="sport-key">${opportunity.sport_key}</div>
            <hr>
            <div>Home</div>
            <div class="home-team">${opportunity.home_team}, ${opportunity.best_odds.home}, ${decimalToAmerican(opportunity.best_odds.home)}, ${opportunity.best_bookmakers.home}</div>
            <div class="home-stake">$${opportunity.home_stake.toFixed(2)}</div>
            <hr>
            <div>Away</div>
            <div class="away-team">${opportunity.away_team}, ${opportunity.best_odds.away}, ${decimalToAmerican(opportunity.best_odds.away)}, ${opportunity.best_bookmakers.away}</div>
            <div class="away-stake">$${opportunity.away_stake.toFixed(2)}</div>
            <hr>
            ${opportunity.best_odds.draw ? `<div>Draw</div>` : ''}
            ${opportunity.best_odds.draw ? `<div class="draw-team">${opportunity.best_odds.draw}, ${decimalToAmerican(opportunity.best_odds.draw)},  ${opportunity.best_bookmakers.draw}</div>` : ''}
            ${opportunity.best_odds.draw ? `<div class="draw-stake">$${opportunity.draw_stake.toFixed(2)}</div>` : ''}
            ${opportunity.best_odds.draw ? `<hr>` : ''}
            <div class="profit">$${opportunity.profit.toFixed(2)}</div>
           
        `;

        // Append the opportunity div to the container
        arbitrageContainer.appendChild(opportunityDiv);
    });
}

// Function to display message when no arbitrage opportunities are available
function displayNoArbitrage() {
    // Get the element where arbitrage information will be displayed
    var arbitrageContainer = document.getElementById('arbitrageContainer');

    // Clear any existing content
    arbitrageContainer.innerHTML = '';

    // Display message
    var messageDiv = document.createElement('div');
    messageDiv.innerText = 'No arbitrage opportunities currently';
    arbitrageContainer.appendChild(messageDiv);
}

function startCountdown(endTime) {
    var interval = setInterval(function() {
        var now = new Date().getTime();
        var distance = endTime - now;
        
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
        }
    }, 1000);
}
