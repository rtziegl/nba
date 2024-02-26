from datetime import datetime, timedelta
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.library.parameters import SeasonAll
import json
import sys
import pandas as pd  # Import pandas library


def fetch_player_game_data(player_id):
    try:
        # Retrieve player game logs for the entire season
        gamelog = playergamelog.PlayerGameLog(player_id=player_id, season=SeasonAll.all)
        player_stats = gamelog.get_data_frames()[0]

        # Convert the 'GAME_DATE' column to datetime
        player_stats['GAME_DATE'] = pd.to_datetime(player_stats['GAME_DATE'])

        # Sort the data by game date in descending order (most recent first)
        player_stats = player_stats.sort_values(by='GAME_DATE', ascending=False)

        # Select the first 12 games (most recent)
        player_stats_recent = player_stats.head(12)

        # Convert the selected data to JSON format
        json_data = player_stats_recent.to_json(orient='records')

        # Print the JSON data to be captured by Node.js
        print(json_data)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fetch_nba_player_game_data.py <player_id>")
    else:
        player_id = sys.argv[1]
        fetch_player_game_data(player_id)
