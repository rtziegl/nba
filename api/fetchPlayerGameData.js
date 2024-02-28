
// Import the necessary modules
const { exec } = require('child_process');

// Define the serverless function
module.exports = (req, res) => {
    const { playerId } = req.query; // Assuming the player ID is sent as a query parameter
    const pythonScriptPath = './pyfetch/fetch_nba_player_game_data.py';

    // Execute the Python script
    exec(`python3 "${pythonScriptPath}" ${playerId}`, (error, stdout, stderr) => {
        if (error) {
            console.error('Error executing Python script:', error);
            res.status(500).json({ error: 'Internal Server Error' });
            return;
        }

        // Parse the JSON data received from the Python script
        let playerGameData;
        try {
            playerGameData = JSON.parse(stdout);
            // Send the player game data as JSON response
            res.json(playerGameData);
        } catch (parseError) {
            console.error('Error parsing JSON:', parseError);
            res.status(500).json({ error: 'Internal Server Error' });
            return;
        }
    });
};
