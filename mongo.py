from pymongo import MongoClient, DESCENDING
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
import logging



#---- LOGGER SETUP ----#
def setup_logger(logger_name, log_file, level=logging.INFO):
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create a file handler and set its level
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

#---- UPDATES ACTIVE PLAYERS ----#
def nba_update_active_players(db, logging):
    logging.info(f"ACTION COMMITTED: nba_update_active_players")
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
                logging.info(f"Inserted a new player {player}")
            else:
                # If the player exists, update its information
                players_collection.update_one({'_id': existing_player['_id']}, {'$set': player})
                logging.info(f"Inserted and updated for player: {player}")

        # Return success response
        response = {'message': 'Players added or updated in the database successfully.'}
        return json.dumps(response), 200, {'Content-Type': 'application/json'}

    except Exception as e:
        # Send error response
        logging.error(f"Error updating active player: {str(e)}")
        error_message = {'error': str(e)}
        return json.dumps(error_message), 500, {'Content-Type': 'application/json'}
    

#---- UPDATE PLAYER GAME DATA FROM PREVIOUS DAY ----#
def nba_update_player_game_data(db, logging):
    logging.info(f"ACTION COMMITTED: nba_update_player_game_data")
    try:
        # Fetch all players from the players collection
        players = db.players.find()

        # Iterate over each player
        for player in players:
            player_id = player['id']
            full_name = player['full_name']
            
            print("fetching game data for", full_name)

            # Fetch game data for the player from the API
            player_game_data_from_api = fetch_player_game_data(player_id, logging)

            # Convert JSON data to Python dictionary
            game_data_from_api = json.loads(player_game_data_from_api)

            # Retrieve existing game data for the player from the database
            existing_game_data = db.playersgamelog.find({"player_id": player_id})

            # Extract existing game IDs for the player
            existing_game_ids = {game['Game_ID'] for game in existing_game_data}

            # Identify new games not present in the existing game data
            new_games = [game for game in game_data_from_api if game['Game_ID'] not in existing_game_ids]

            # Insert new game data
            for game in new_games:
                # Insert the new game data
                db.playersgamelog.insert_one({
                    "player_id": player_id,
                    "Game_ID": game['Game_ID'],
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

                # Log the insertion of game data
                logging.info(f"Inserted game data: Player ID: {player_id}, Player Name: {full_name}, Game ID: {game['Game_ID']}, Game Date: {game.get('GAME_DATE', 'N/A')}, Matchup: {game.get('MATCHUP', 'N/A')}")

        # Return success response
        response = {'message': 'Players added or updated in the database successfully.'}
        return json.dumps(response), 200, {'Content-Type': 'application/json'}

    except Exception as e:
        logging.error(f"Error updating player game data: {str(e)}")
        return str(e)

def fetch_player_game_data(player_id, logging):
    try:
        # Retrieve player game logs for the entire season
        gamelog = playergamelog.PlayerGameLog(player_id=player_id, season=SeasonAll.current_season)
        player_stats = gamelog.get_data_frames()[0]
        
        print(player_stats)

        date_format = "%b %d, %Y"

        # Convert the 'GAME_DATE' column to datetime using the specified format
        player_stats['GAME_DATE'] = pd.to_datetime(player_stats['GAME_DATE'], format=date_format)

        # Sort the data by game date in descending order (most recent first)
        player_stats = player_stats.sort_values(by='GAME_DATE', ascending=False)

        # Convert the game data to JSON format
        json_data = player_stats.to_json(orient='records')

        logging.info(f"Fetched game data for player {player_id}")

        return json_data

    except Exception as e:
        # Send error response
        logging.error(f"Error fetching game data for player {player_id}: {str(e)}")
        error_message = {'error': str(e)}
        return json.dumps(error_message), 500, {'Content-Type': 'application/json'}

    

#---- UPDATE NEXT MATCHUP DATA FROM PREVIOUS DAY ----#
def nba_update_player_next_game_matchup(db, logging):
    logging.info(f"ACTION COMMITTED: nba_update_player_next_game_matchup")
    try:
        # Fetch all players from the players collection
        players = db.players.find()
        # Iterate over each player
        for player in players:
            player_id = player['id']
            
            matchup = get_upcoming_game_matchup(player_id, logging)

            if matchup is None:
                db.playersmatchuplog.update_one(
                {"player_id": player_id},
                {"$set": {
                    "num_games": 0,
                    "recent_matchups": None
                }},
                upsert=True  # Insert a new document if it doesn't exist
            )
                logging.info(f"Couldn't find Next Game for {player_id}") 
                
            else:
                finding_abrv_compare_insert(db, player_id, matchup, logging)
        
        # Return success response
        response = {'message': 'Players next Matchup or updated in the database successfully.'}
        return json.dumps(response), 200, {'Content-Type': 'application/json'}
    
    except Exception as e:
        logging.error(f"Error fetching or updating game data: {str(e)}")
        error_message = {'error': str(e)}
        return json.dumps(error_message), 500, {'Content-Type': 'application/json'} 
    
# Calls api and grabs the next matchup value
def get_upcoming_game_matchup(player_id, logging):
    try:
        next_games = PlayerNextNGames(player_id=player_id)
        next_games_data = next_games.get_normalized_dict()["NextNGames"]

        # Check if there are any upcoming games
        if next_games_data:
            # Retrieve details of the next game
            next_game = next_games_data[0]
            return next_game
        else:
            return None
            
    except Exception as e:
        logging.error(f"Error get_upcoming_game_matchup from api Matchup data: {str(e)}")
        print("Error:", str(e))

def finding_abrv_compare_insert(db, player_id, matchup_data, logging):
    try:
        # Initialize recent matchups list
        recent_matchups = []
        home_team_abbr = matchup_data['HOME_TEAM_ABBREVIATION']
        visitor_team_abbr = matchup_data['VISITOR_TEAM_ABBREVIATION']

        print(player_id, home_team_abbr, visitor_team_abbr)

        player_logs = db.playersgamelog.find({"player_id": player_id}, sort=[("GAME_DATE", DESCENDING)])
        for log in player_logs:
                matchup = log['MATCHUP']
            # Check if the matchup contains both team abbreviations
                if home_team_abbr in matchup and visitor_team_abbr in matchup:
                    print(matchup)
                    if len(recent_matchups) < 3:  # Limit to the last 3 matchups
                        recent_matchups.append(log)
                    else:
                        break  # Break the loop if 3 matchups are appended
        print(player_id, recent_matchups)
        # Insert or overwrite the matchup information into the playersmatchuplog collection
        db.playersmatchuplog.update_one(
            {"player_id": player_id},
            {"$set": {
                "num_games": len(recent_matchups),
                "recent_matchups": recent_matchups if recent_matchups else None
            }},
            upsert=True  # Insert a new document if it doesn't exist
        )

        if recent_matchups is None:
            logging.info(f"Next game Matchup data for player is set to none for {player_id}")
            logging.info(f"Upcoming game found but no games in DB that match the matchup game for {player_id}")
        else:
            logging.info(f"Next game Matchup data for player is updated for {player_id}")

    #    print(player_id, player_logs)
            
    except Exception as e:
        logging.error(f"Error finding_abrv_and_compare from DB: {str(e)}")
        print("Error:", str(e))

# Load environment variables from .env file
load_dotenv()

# Retrieve the MongoDB Atlas URI from the environment
uri = os.getenv("MONGODB_URI")
print(uri)

# Create a MongoClient instance
client = MongoClient(uri, tlsCAFile=certifi.where())
print(client)

# Create loggers
player_next_game_logger = setup_logger('player_next_game', 'player_next_game.log')
player_game_data_logger = setup_logger('player_game_data', 'player_game_data.log')
active_players_logger = setup_logger('active_players', 'active_players.log')

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
     # Connect to MongoDB
    db = client['nba']

    #nba_update_active_players(db, active_players_logger)
    # print("NBA PLAYER NAME and ID DATA UPDATED")

    nba_update_player_game_data(db, player_game_data_logger)
    print("NBA PLAYER GAME DATA UPDATED")

    #nba_update_player_next_game_matchup(db, player_next_game_logger)
   # print("NBA PLAYER MATCHUP LOG UPDATED")

    client.close()

except Exception as e:
    print(e)















