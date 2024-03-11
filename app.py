from nba_api.stats.endpoints import PlayerNextNGames, PlayerGameLog, CommonPlayerInfo
from nba_api.stats.library.parameters import SeasonAll
from nba_api.stats.endpoints import commonallplayers
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import playergamelog

from datetime import datetime
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

from pymongo import MongoClient, DESCENDING
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

import pandas as pd
import json
import os
import certifi
import requests

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
        player_id = int(request.args.get('playerId'))
        
        player_matchup_collection = get_data_from_db('playersmatchuplog')

        for game in player_matchup_collection:
            if game['player_id'] == player_id:
                game['_id'] = str(game['_id'])
                # Create Dict
                matchup_data = {
                    'num_games': game.get('num_games', 0),  # Default value if 'num_games' is not present
                    'recent_matchups': []  # Initialize empty list for recent match-ups
                }

                # Check if num_games is 0
                if matchup_data['num_games'] == 0:
                    # Assign default value for recent_matchups
                    matchup_data['recent_matchups'] = None
                else:
                    # Convert recent_matchups array objects
                    for matchup in game['recent_matchups']:
                        matchup['_id'] = str(matchup['_id'])  # Convert ObjectId to string
                        matchup_data['recent_matchups'].append(matchup)

        # Convert the dictionary to JSON format
        return jsonify(matchup_data), 200

    except Exception as e:
        # Send error response
        error_message = {'error': str(e)}
        return jsonify(error_message), 500


   
# -------------------- GET ACTIVE PLAYERS --------------------------
@app.route('/nba_get_active_players', methods=['GET'])
def nba_get_active_players():
    try:
        # Get all active players from the database
        active_players = get_data_from_db('players')

        # Sanitize player data
        sanitized_players = []
        for player in active_players:
            sanitized_player = {
                'full_name': sanitize_string(player.get('full_name', '')),
                'id': sanitize_string(player.get('id', ''))
            }
            sanitized_players.append(sanitized_player)

        # Convert the sanitized data to JSON format
        return jsonify(sanitized_players), 200

    except Exception as e:
        # Send error response
        error_message = {'error': str(e)}
        return jsonify(error_message), 500



# -------------------- GET PLAYER GAME DATA --------------------------
    
@app.route('/nba_get_player_game_data', methods=['GET'])
def nba_get_player_game_data():
    try:
        player_game_data = []
        # Extract player ID from the query parameters
        player_id = int(request.args.get('playerId'))

        # Player games from DB
        player_game_collection = get_data_from_db('playersgamelog')
        
        
        # Filter player game data based on player ID
        for game in player_game_collection:
            if game['player_id'] == player_id:
                # Convert ObjectId to string
                game['_id'] = str(game['_id'])
                player_game_data.append(game)
                
        # Sort player game data based on 'GAME_DATE' in descending order (most recent first)
        player_game_data.sort(key=lambda x: x['GAME_DATE'], reverse=True)
        return jsonify(player_game_data), 200
    
    except Exception as e:
        # Send error response
        error_message = {'error': str(e)}
        return jsonify(error_message), 500


# Get DB based on collection   
def get_data_from_db(collection_name):
    collection = db[collection_name]  # corrected the string formatting
    data = collection.find()
    data_list = list(data)  # Convert cursor to list for JSON serialization
    return data_list

# Sanatize
def sanitize_string(value):
    """Sanitize string to prevent XSS attacks."""
    # Example: Escape special characters using markupsafe.escape
    from markupsafe import escape
    return escape(value)
    
    
# Load environment variables from .env file
load_dotenv()

# Retrieve the MongoDB Atlas URI from the environment
uri = os.getenv("MONGODB_URI_ENDUSER")

# Create a MongoClient instance
client = MongoClient(uri, tlsCAFile=certifi.where())

db = client["nba"]

if __name__ == '__main__':
    app.run(debug=True)
