const express = require('express');
const { exec } = require('child_process');
const path = require('path');

const app = express();
const port = 3000;

app.use(express.static(path.join(__dirname, 'public')));

// Define endpoint to fetch NBA player names and id data.
app.get('/fetch-players-names-id', (req, res) => {
    const pythonScriptPath = 'pyfetch/fetch_nba_player_names_id.py';

    // Execute the Python script
    exec(`python3 "${pythonScriptPath}"`, (error, stdout, stderr) => {
        if (error) {
            console.error('Error executing Python script:', error);
            res.status(500).send('Internal Server Error');
            return;
        }

        // Parse the JSON data received from the Python script
        let playersData;
        try {
            playersData = JSON.parse(stdout);
        } catch (parseError) {
            console.error('Error parsing JSON:', parseError);
            res.status(500).send('Internal Server Error');
            return;
        }

        // Send the player data as JSON response
        res.json(playersData);
    });
});

// Define endpoint to fetch NBA player game data
app.get('/fetch-player-game-data/:playerId', (req, res) => {
    const { playerId } = req.params;
    const pythonScriptPath = './pyfetch/fetch_nba_player_game_data.py';

    // Execute the Python script
    exec(`python3 "${pythonScriptPath}" ${playerId}`, (error, stdout, stderr) => {
        if (error) {
            console.error('Error executing Python script:', error);
            res.status(500).send('Internal Server Error');
            return;
        }

        // Parse the JSON data received from the Python script
        let playerGameData;
        try {
            playerGameData = JSON.parse(stdout);
        } catch (parseError) {
            console.error('Error parsing JSON:', parseError);
            res.status(500).send('Internal Server Error');
            return;
        }

        // Send the player game data as JSON response
        res.json(playerGameData);
    });
});

// Define endpoint to fetch NBA player game data
app.get('/fetch-player-game-data-against-next-team/:playerId', (req, res) => {
    const { playerId } = req.params;
    const pythonScriptPath = './pyfetch/fetch_nba_next_matchup.py';

    // Execute the Python script
    exec(`python3 "${pythonScriptPath}" ${playerId}`, (error, stdout, stderr) => {
        if (error) {
            console.error('Error executing Python script:', error);
            res.status(500).send('Internal Server Error');
            return;
        }

        // Parse the JSON data received from the Python script
        let playerGameData;
        try {
            playerGameData = JSON.parse(stdout);
        } catch (parseError) {
            console.error('Error parsing JSON:', parseError);
            res.status(500).send('Internal Server Error');
            return;
        }

        // Send the player game data as JSON response
        res.json(playerGameData);
    });
});


app.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
});

