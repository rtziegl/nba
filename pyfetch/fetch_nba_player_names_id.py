from nba_api.stats.endpoints import commonallplayers
from nba_api.stats.static import players
import json
from datetime import datetime

# Get the current year
current_year = datetime.now().year

# Get the current NBA season
all_players = commonallplayers.CommonAllPlayers(is_only_current_season=1)
all_players_dict = all_players.get_normalized_dict()

# Extract player IDs of players active in the current season
active_player_ids = [player['PERSON_ID'] for player in all_players_dict['CommonAllPlayers']]

# Retrieve all NBA players' data
nba_players = players.get_players()

# Filter players who are active in the current season
active_players = [player for player in nba_players if player['id'] in active_player_ids]

# Extract player names and IDs
players_data = [{'full_name': player['full_name'], 'id': player['id']} for player in active_players]

# Convert the data to JSON format
json_data = json.dumps(players_data)

# Print the JSON data (to be captured by Node.js)
print(json_data)
