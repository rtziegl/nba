// fetchPlayersNamesId.js
const { exec } = require('child_process');

module.exports = async (req, res) => {
    const pythonScriptPath = './pyfetch/fetch_nba_player_names_id.py';

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
            res.json(playersData);
        } catch (parseError) {
            console.error('Error parsing JSON:', parseError);
            res.status(500).send('Internal Server Error');
        }
    });
};
