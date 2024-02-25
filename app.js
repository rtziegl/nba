const express = require('express');
const { exec } = require('child_process');
const path = require('path');

const app = express();
const port = 3000;

app.use(express.static(path.join(__dirname, 'public')));

app.get('/fetch-data', (req, res) => {
    const pythonScriptPath = 'pyfetch/fetch_nba_data.py';
    // Execute the Python script
    exec(`python3 "${pythonScriptPath}"`, (error, stdout, stderr) => {
        if (error) {
            console.error('Error executing Python script:', error);
            res.status(500).send('Internal Server Error');
            return;
        }
        // Send the output from the Python script to the client
        res.send(stdout);
    });
});

app.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
});

