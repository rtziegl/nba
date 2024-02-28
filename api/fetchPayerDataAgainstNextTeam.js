// Import the necessary modules
const { exec } = require('child_process');
const path = require('path');

// Define the serverless function
module.exports = (req, res) => {
    const { playerId } = req.query; // Assuming the player ID is sent as a query parameter
    const pythonScriptPath = path.join(__dirname, '..', 'pyfetch', 'fetch_nba_next_matchup.py');

    // Execute the Python script
    exec(`python "${pythonScriptPath}" ${playerId}`, (error, stdout, stderr) => {
        if (error) {
            console.error('Error executing Python script:', error);
            res.status(500).json({ error: 'Internal Server Error' });
            return;
        }

        // Excepts the empty json in case cant find next matchup game.
        let trimmedStdout = stdout.trim();
        if (!trimmedStdout) {
            // If trimmed stdout is empty, send an empty response
            res.json({
                recent_matchups: null,
                num_games: 0
            });
            return;
        }

        // Parse the trimmed JSON data received from the Python script
        let playerGameData;
        try {
            playerGameData = JSON.parse(trimmedStdout);
            // Send the player game data as JSON response
            res.json(playerGameData);
        } catch (parseError) {
            console.error('Error parsing JSON:', parseError);
            res.status(500).json({ error: 'Internal Server Error' });
            return;
        }
    });
};
