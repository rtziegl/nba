from http.server import BaseHTTPRequestHandler
from nba_api.stats.endpoints import PlayerNextNGames, PlayerGameLog, CommonPlayerInfo
from nba_api.stats.library.parameters import SeasonAll

import json
import sys

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
            
            print("PLAYYERRRR", player_id)
            # Get the player's team abbreviation
            player_team_abbreviation = self.get_player_team_abbreviation(player_id)

            print("TEAM ABRV", player_team_abbreviation)
            if player_team_abbreviation:
                # Get the opponent team abbreviation
                opponent_team_abbreviation = self.get_opponent_team(player_team_abbreviation, player_id)
                print("OPPENT ABRv", opponent_team_abbreviation)
                if opponent_team_abbreviation:
                    # Retrieve recent games stats
                    opponent_games, num_games = self.get_recent_games_stats(player_id, opponent_team_abbreviation)
                    print("OPPENENT ANDN NUMGAMES", opponent_games, num_games)
                    if opponent_games is not None:
                        # Prepare data dictionary for JSON conversion
                        data_dict = {
                            'recent_matchups': opponent_games.to_dict(orient='records'),
                            'num_games': num_games
                        }
                    else:
                        # Prepare data dictionary if no matchups yet
                        data_dict = {
                            'recent_matchups': None,
                            'num_games': num_games
                        }
                else:
                    # If cannot find opponent team abbreviation, send empty JSON
                    data_dict = {
                        'recent_matchups': None,
                        'num_games': 0
                    }
            else:
                data_dict = {
                    'recent_matchups': None,
                    'num_games': 0
                }

            # Convert the dictionary to JSON format
            json_data = json.dumps(data_dict)

            # Send response headers
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            # Send the JSON data in the response body
            self.wfile.write(json_data.encode('utf-8'))

        except Exception as e:
            # Send error response
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_message = json.dumps({'error': str(e)})
            self.wfile.write(error_message.encode('utf-8'))

    def get_recent_games_stats(self, player_id, opponent_team_abbr):
        try:
            # Get player's game logs for the current season
            player_logs = PlayerGameLog(player_id=player_id, season=SeasonAll.current_season)
            print("PLAYER LOGS", player_logs)
            player_logs_df = player_logs.get_data_frames()[0]
            print("PLAYER LOGA DF", player_logs_df)

            # Filter logs to games against the opponent team
            opponent_logs = player_logs_df[player_logs_df['MATCHUP'].str.contains(opponent_team_abbr)]

            print("OPPENENTS logs", opponent_logs)

            # Take the most recent 3 games against the opponent team in the current season
            recent_games = opponent_logs.head(3)

            return recent_games, len(opponent_logs)
        except Exception as e:
            print(f"Error retrieving recent games stats: {e}")
            return None, 0

    def get_opponent_team(self, player_team_abbr, player_id):
        try:
            # Get the next game for the player
            next_games = PlayerNextNGames(player_id=player_id)
            next_games_data = next_games.get_normalized_dict()["NextNGames"]

            # Check if there are any upcoming games
            if next_games_data:
                # Retrieve details of the next game
                next_game = next_games_data[0]
                
                # Extract the team abbreviations
                home_team_abbr = next_game['HOME_TEAM_ABBREVIATION']
                visitor_team_abbr = next_game['VISITOR_TEAM_ABBREVIATION']

                # Determine the opponent team abbreviation
                opponent_team_abbr = home_team_abbr if player_team_abbr != home_team_abbr else visitor_team_abbr

                return opponent_team_abbr
            else:
                print("No upcoming games found for the player.")
                return None
        except Exception as e:
            # print(f"Error retrieving opponent team: {e}")
            return None

    def get_player_team_abbreviation(self, player_id):
        try:
            # Retrieve player information
            player_info = CommonPlayerInfo(player_id=player_id)
            player_info = player_info.get_data_frames()[0]

            # Extract the team abbreviation
            team_abbreviation = player_info['TEAM_ABBREVIATION'].iloc[0]
            return team_abbreviation
        except Exception as e:
            print(f"Error retrieving player team abbreviation: {e}")
            return None
