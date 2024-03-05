from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.endpoints import PlayerNextNGames, PlayerGameLog, CommonPlayerInfo
from nba_api.stats.library.parameters import SeasonAll

from flask import Flask, jsonify, request, render_template

import json
import os
import certifi
import requests
import pandas as pd


# If the player's name and ID match an existing record, it doesn't add a duplicate 
# If the name matches but the ID is different, it updates the ID 
# If neither the name nor the ID match any existing records, it inserts the new player 
# This ensures data integrity and avoids duplicates in the database
def nba_update_active_players(db):
    try:
        # Get all active players (assuming this function returns a list of players)
        active_players = players.get_active_players()

        # Extract player names and IDs
        players_data = [{'full_name': player['full_name'], 'id': player['id']} for player in active_players]

       
        # Insert new players into the "players" collection
        players_collection = db["players"]

        for player in players_data:
            # Check if the player already exists in the database based on name and ID
            existing_player = players_collection.find_one({'full_name': player['full_name'], 'id': player['id']})
            if not existing_player:
                # If the player doesn't exist, insert the new player
                players_collection.insert_one(player)
            else:
                # If the player exists, update its information
                players_collection.update_one({'_id': existing_player['_id']}, {'$set': player})

        # Return success response
        response = {'message': 'Players added or updated in the database successfully.'}
        return json.dumps(response), 200, {'Content-Type': 'application/json'}

    except Exception as e:
        # Send error response
        error_message = {'error': str(e)}
        return json.dumps(error_message), 500, {'Content-Type': 'application/json'}
    
# ##### ALL PLAYERS ALL GAMES STATS PER GAME #####
    
# def nba_update_player_game_data(db):
#     try:
#         # Fetch all players from the players collection
#         players = db.players.find()

#         # Iterate over each player
#         for player in players:
#             player_id = player['id']

#             # Fetch game data for the player
#             player_game_data = fetch_player_game_data(player_id)

#             # Convert JSON data to Python dictionary
#             game_data = json.loads(player_game_data)

#             # Check and insert new game data
#             for game in game_data:
#                 game_id = game['Game_ID']

#                 # Check if the game already exists in the player_games collection
#                 if db.playersgamelog.find_one({"player_id": player_id, "Game_ID": game_id}) is None:
#                     # Insert the new game data
#                     db.playersgamelog.insert_one({
#                         "player_id": player_id,
#                         "Game_ID": game_id,
#                         "AST": game.get('AST', 0),
#                         "BLK": game.get('BLK', 0),
#                         "DREB": game.get('DREB', 0),
#                         "FG3A": game.get('FG3A', 0),
#                         "FG3M": game.get('FG3M', 0),
#                         "FG3_PCT": game.get('FG3_PCT', 0),
#                         "FGA": game.get('FGA', 0),
#                         "FGM": game.get('FGM', 0),
#                         "FG_PCT": game.get('FG_PCT', 0),
#                         "FTA": game.get('FTA', 0),
#                         "FTM": game.get('FTM', 0),
#                         "FT_PCT": game.get('FT_PCT', 0),
#                         "GAME_DATE": game.get('GAME_DATE', ''),
#                         "Game_ID": game.get('Game_ID', ''),
#                         "MATCHUP": game.get('MATCHUP', ''),
#                         "MIN": game.get('MIN', ''),
#                         "OREB": game.get('OREB', 0),
#                         "PF": game.get('PF', 0),
#                         "PLUS_MINUS": game.get('PLUS_MINUS', 0),
#                         "PTS": game.get('PTS', 0),
#                         "REB": game.get('REB', 0),
#                         "SEASON_ID": game.get('SEASON_ID', ''),
#                         "STL": game.get('STL', 0),
#                         "TOV": game.get('TOV', 0),
#                         "WL": game.get('WL', ''),
#                         # Add other relevant fields from the game data
#                     })

#         # Return success response
#         response = {'message': 'Players added or updated in the database successfully.'}
#         return json.dumps(response), 200, {'Content-Type': 'application/json'}

#     except Exception as e:
#         return str(e)

# def fetch_player_game_data(player_id):
#     try:
#         # Retrieve player game logs for the entire season
#         gamelog = playergamelog.PlayerGameLog(player_id=player_id, season=SeasonAll.current_season)
#         player_stats = gamelog.get_data_frames()[0]

#         date_format = "%b %d, %Y"

#         # Convert the 'GAME_DATE' column to datetime using the specified format
#         player_stats['GAME_DATE'] = pd.to_datetime(player_stats['GAME_DATE'], format=date_format)

#         # Sort the data by game date in descending order (most recent first)
#         player_stats = player_stats.sort_values(by='GAME_DATE', ascending=False)

#         # Convert the selected data to JSON format
#         json_data = player_stats.to_json(orient='records')

#         return json_data

#     except Exception as e:
#         # Send error response
#         error_message = {'error': str(e)}
#         return json.dumps(error_message), 500, {'Content-Type': 'application/json'} 


def nba_update_player_game_data(db):
    try:
        # Fetch all players from the players collection
        players = db.players.find()

        # Iterate over each player
        for player in players:
            player_id = player['id']

            # Fetch game data for the player from the API
            player_game_data_from_api = fetch_player_game_data(player_id)

            # Convert JSON data to Python dictionary
            game_data_from_api = json.loads(player_game_data_from_api)

            # Retrieve existing game data for the player from the database
            existing_game_data = db.playersgamelog.find({"player_id": player_id})

            # Extract existing game IDs for the player
            existing_game_ids = {game['Game_ID'] for game in existing_game_data}

            # Check and insert new game data
            for game in game_data_from_api:
                game_id = game['Game_ID']

                # Check if the game already exists in the player_games collection
                if game_id not in existing_game_ids:
                    # Insert the new game data
                    db.playersgamelog.insert_one({
                        "player_id": player_id,
                        "Game_ID": game_id,
                        "AST": game.get('AST', 0),
                        "BLK": game.get('BLK', 0),
                        "DREB": game.get('DREB', 0),
                        "FG3A": game.get('FG3A', 0),
                        "FG3M": game.get('FG3M', 0),
                        "FG3_PCT": game.get('FG3_PCT', 0),
                        "FGA": game.get('FGA', 0),
                        "FGM": game.get('FGM', 0),
                        "FG_PCT": game.get('FG_PCT', 0),
                        "FTA": game.get('FTA', 0),
                        "FTM": game.get('FTM', 0),
                        "FT_PCT": game.get('FT_PCT', 0),
                        "GAME_DATE": game.get('GAME_DATE', ''),
                        "Game_ID": game.get('Game_ID', ''),
                        "MATCHUP": game.get('MATCHUP', ''),
                        "MIN": game.get('MIN', ''),
                        "OREB": game.get('OREB', 0),
                        "PF": game.get('PF', 0),
                        "PLUS_MINUS": game.get('PLUS_MINUS', 0),
                        "PTS": game.get('PTS', 0),
                        "REB": game.get('REB', 0),
                        "SEASON_ID": game.get('SEASON_ID', ''),
                        "STL": game.get('STL', 0),
                        "TOV": game.get('TOV', 0),
                        "WL": game.get('WL', ''),
                    })

        # Return success response
        response = {'message': 'Players added or updated in the database successfully.'}
        return json.dumps(response), 200, {'Content-Type': 'application/json'}

    except Exception as e:
        return str(e)

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

        # Convert the most recent game to JSON format [0] or head(1)
        json_data = player_stats.head(1).to_json(orient='records')

        return json_data

    except Exception as e:
        # Send error response
        error_message = {'error': str(e)}
        return json.dumps(error_message), 500, {'Content-Type': 'application/json'} 
    
def update_player_next_game_matchup(db):
    try:
        # Fetch all players from the players collection
        players = db.players.find()

        # Iterate over each player
        for player in players:
            player_id = player['id']

            next_game_matchup = fetch_next_game_matchup(player_id)
    
    except Exception as e:
        # Send error response
        error_message = {'error': str(e)}
        return json.dumps(error_message), 500, {'Content-Type': 'application/json'} 

def fetch_next_game_matchup(player_id):
    try:
    
    except Exception as e:
        return None


# Load environment variables from .env file
load_dotenv()

# Retrieve the MongoDB Atlas URI from the environment
uri = os.getenv("MONGODB_URI")
print(uri)

# Create a MongoClient instance
client = MongoClient(uri, tlsCAFile=certifi.where())
print(client)

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
     # Connect to MongoDB
    db = client['nba']

    nba_update_active_players(db)
    print("NBA PLAYER NAME and ID DATA UPDATED")

    nba_update_player_game_data(db)
    print("NBA PLAYER GAME DATA UPDATED")

    client.close()

except Exception as e:
    print(e)















