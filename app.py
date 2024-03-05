from nba_api.stats.endpoints import PlayerNextNGames, PlayerGameLog, CommonPlayerInfo
from nba_api.stats.library.parameters import SeasonAll
from nba_api.stats.endpoints import commonallplayers
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import playergamelog
from datetime import datetime
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

import pandas as pd
import json

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')


# -------------------- GET MATCHUP DATA --------------------------

@app.route('/nba_get_next_matchup', methods=['GET'])
def nba_get_next_matchup():
    try:
        # Extract player ID from the query parameters
        player_id = request.args.get('playerId')

        # Get the player's team abbreviation
        player_team_abbreviation = get_player_team_abbreviation(player_id)

        if player_team_abbreviation:
            # Get the opponent team abbreviation
            opponent_team_abbreviation = get_opponent_team(player_team_abbreviation, player_id)

            if opponent_team_abbreviation:
                # Retrieve recent games stats
                opponent_games, num_games = get_recent_games_stats(player_id, opponent_team_abbreviation)

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
        return jsonify(data_dict), 200

    except Exception as e:
        # Send error response
        error_message = {'error': str(e)}
        return jsonify(error_message), 500

def get_recent_games_stats(player_id, opponent_team_abbr):
    try:
        # Get player's game logs for the current season
        player_logs = PlayerGameLog(player_id=player_id, season=SeasonAll.current_season)
        player_logs_df = player_logs.get_data_frames()[0]

        # Filter logs to games against the opponent team
        opponent_logs = player_logs_df[player_logs_df['MATCHUP'].str.contains(opponent_team_abbr)]

        # Take the most recent 3 games against the opponent team in the current season
        recent_games = opponent_logs.head(3)

        return recent_games, len(opponent_logs)
    except Exception as e:
        print("Error retrieving recent games stats: {e}")
        return None, 0

def get_opponent_team(player_team_abbr, player_id):
    try:
        # Get the next game for the player
        next_games = PlayerNextNGames(player_id=player_id)
        next_games_data = next_games.get_normalized_dict()["NextNGames"]

        print("NEXT GAMES DATA", next_games_data)

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
        return None

def get_player_team_abbreviation(player_id):
    try:
        # Retrieve player information
        player_info = CommonPlayerInfo(player_id=player_id)
        player_info = player_info.get_data_frames()[0]

        # Extract the team abbreviation
        team_abbreviation = player_info['TEAM_ABBREVIATION'].iloc[0]
        return team_abbreviation
    except Exception as e:
        print("Error retrieving player team abbreviation: {e}")
        return None
   
# -------------------- GET ACTIVE PLAYERS --------------------------
@app.route('/nba_get_active_players', methods=['GET'])
def nba_get_active_players():
    try:
     # Get all active players
        active_players = players.get_active_players()

        # Extract player names and IDs
        players_data = [{'full_name': player['full_name'], 'id': player['id']} for player in active_players]

        # Convert the data to JSON format
        return jsonify(players_data), 200

    except Exception as e:
        # Send error response
        error_message = {'error': str(e)}
        return jsonify(error_message), 500
    

# -------------------- GET PLAYER GAME DATA --------------------------
    
@app.route('/nba_get_player_game_data', methods=['GET'])
def nba_get_player_game_data():
    try:
        # Extract player ID from the query parameters
        player_id = request.args.get('playerId')

        # Fetch player game data
        player_game_data = fetch_player_game_data(player_id)

        return player_game_data
    
    except Exception as e:
        # Send error response
        error_message = {'error': str(e)}
        return jsonify(error_message), 500

def fetch_player_game_data(player_id):
    try:
        # Retrieve player game logs for the entire season
        gamelog = playergamelog.PlayerGameLog(player_id=player_id, season=SeasonAll.current_season)
        player_stats = gamelog.get_data_frames()[0]

        date_format = "%b %d, %Y"

        # Convert the 'GAME_DATE' column to datetime using the specified format
        player_stats['GAME_DATE'] = pd.to_datetime(player_stats['GAME_DATE'], format=date_format)

        # Sort the data by game date in descending order (most recent first)
        player_stats = player_stats.sort_values(by='GAME_DATE', ascending=False)

        print("HELLO", player_stats)
        print("First row:", player_stats.head(1))
        # Convert the selected data to JSON format
        json_data = player_stats.to_json(orient='records')

        

        return json_data

    except Exception as e:
        return json.dumps({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
