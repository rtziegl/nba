# fetch_nba_data.py
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.library.parameters import SeasonAll
import json

# Set the player ID for the player you're interested in
player_id = '201935'  # Example: James Harden's player ID

# Retrieve player game logs for the previous 10 games
gamelog = playergamelog.PlayerGameLog(player_id=player_id, season=SeasonAll.all)
player_stats = gamelog.get_data_frames()[0]

# Convert the data to JSON format
json_data = player_stats.to_json(orient='records')

# Print the JSON data (to be captured by Node.js)
print(json_data)
