from http.server import BaseHTTPRequestHandler
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.library.parameters import SeasonAll
import json
import sys
import pandas as pd

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Extract player ID from the URL query parameters
            # Split the path by '?' to separate the path and the query string
            path_parts = self.path.split('?')

            # Extract the query string
            query_string = path_parts[1] if len(path_parts) > 1 else ''

            # Split the query string by '&' to separate individual parameters
            query_params = query_string.split('&')

            # Iterate through the query parameters to find the playerId parameter
            player_id = None
            for param in query_params:
                key, value = param.split('=')
                if key == 'playerId':
                    player_id = value
                    break

            # Fetch player game data
            player_game_data = self.fetch_player_game_data(player_id)

            # Send response headers
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            # Send the JSON data in the response body
            self.wfile.write(player_game_data.encode('utf-8'))

        except Exception as e:
            # Send error response
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_message = json.dumps({'error': str(e)})
            self.wfile.write(error_message.encode('utf-8'))

    def fetch_player_game_data(self, player_id):
        try:
            # Retrieve player game logs for the entire season
            gamelog = playergamelog.PlayerGameLog(player_id=player_id, season=SeasonAll.current_season)
            player_stats = gamelog.get_data_frames()[0]

            date_format = "%b %d, %Y"

            # Convert the 'GAME_DATE' column to datetime using the specified format
            player_stats['GAME_DATE'] = pd.to_datetime(player_stats['GAME_DATE'], format=date_format)

            # Sort the data by game date in descending order (most recent first)
            player_stats = player_stats.sort_values(by='GAME_DATE', ascending=False)

            # Select the first 12 games (most recent)
            # player_stats_recent = player_stats.head(12)

            # Convert the selected data to JSON format
            json_data = player_stats.to_json(orient='records')

            print(json_data)

            return json_data

        except Exception as e:
            return json.dumps({'error': str(e)})


if __name__ == "__main__":
    pass  # This ensures that the code under `if __name__ == "__main__":` doesn't execute when the module is imported
