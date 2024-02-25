from nba_api.stats.static import players
import json

# Retrieve all NBA players' data
nba_players = players.get_players()

# Extract player names and IDs
players_data = [{'full_name': player['full_name'], 'id': player['id']} for player in nba_players]

# Convert the data to JSON format
json_data = json.dumps(players_data)

# Print the JSON data (to be captured by Node.js)
print(json_data)
