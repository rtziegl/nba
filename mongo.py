from pymongo import MongoClient, DESCENDING
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.endpoints import PlayerNextNGames, PlayerGameLog, CommonPlayerInfo
from nba_api.stats.endpoints import LeagueGameLog
from nba_api.stats.library.parameters import SeasonAll
from nba_api.stats.endpoints import AllTimeLeadersGrids
from nba_api.stats.endpoints import LeagueGameFinder
from nba_api.stats.endpoints.teamestimatedmetrics import TeamEstimatedMetrics
from nba_api.stats.endpoints import TeamGameLogs
from nba_api.stats.endpoints.leagueleaders import LeagueLeaders
import datetime
from datetime import datetime


from flask import Flask, jsonify, request, render_template

import json
import os
import certifi
import requests
import pandas as pd
import logging

# Scraping and Regex
from bs4 import BeautifulSoup
import re



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
        # Fetch the single document from the dailyplayers collection
        daily_players_doc = db.dailyplayers.find_one()

        # Check if the document exists
        if not daily_players_doc:
            logging.error("No document found in the dailyplayers collection.")
            return json.dumps({'message': 'No document found in the dailyplayers collection.'}), 404, {'Content-Type': 'application/json'}

        # Get the players array from the document
        players = daily_players_doc['players']

        # Iterate over each player in the players array
        for player in players:
            player_id = player['player_id']
            full_name = player['player_name']
            
            print("fetching game data for", full_name)

            # Fetch game data for the player from the API
            player_game_data = fetch_player_game_data(player_id, logging)
            player_playoff_game_data = fetch_playoff_game_data(player_id, logging)

            # Convert the data to dictionaries
            game_data_from_api_regular = player_game_data.to_dict(orient='records')
            game_data_from_api_playoff = player_playoff_game_data.to_dict(orient='records')

            game_data_from_api = game_data_from_api_regular + game_data_from_api_playoff

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

        date_format = "%b %d, %Y"

        # Convert the 'GAME_DATE' column to datetime using the specified format
        player_stats['GAME_DATE'] = pd.to_datetime(player_stats['GAME_DATE'], format=date_format)

        # Sort the data by game date in descending order (most recent first)
        player_stats = player_stats.sort_values(by='GAME_DATE', ascending=False)

        logging.info(f"Fetched game data for player {player_id}")

        return player_stats

    except Exception as e:
        # Send error response
        logging.error(f"Error fetching game data for player {player_id}: {str(e)}")
        error_message = {'error': str(e)}
        return json.dumps(error_message), 500, {'Content-Type': 'application/json'}

def fetch_playoff_game_data(player_id, logging):
    try:

        # Retrieve playoff game logs
        playoff_logs = playergamelog.PlayerGameLog(player_id=player_id, season=SeasonAll.current_season, season_type_all_star='Playoffs').get_data_frames()[0]
        date_format = "%b %d, %Y"

        # Convert the 'GAME_DATE' column to datetime using the specified format
        playoff_logs['GAME_DATE'] = pd.to_datetime(playoff_logs['GAME_DATE'], format=date_format)

        # Sort the data by game date in descending order (most recent first)
        playoff_logs = playoff_logs.sort_values(by='GAME_DATE', ascending=False)
       
        logging.info(f"Fetched game data for player {player_id}")

        return playoff_logs

    except Exception as e:
        print(f"Error fetching game data: {e}")
        return None



def finding_abrv_compare_insert(db, player_id, matchup_data, logging):
    try:
        # Initialize recent matchups list
        recent_matchups = []
        home_team_abbr = matchup_data['HOME_TEAM_ABBREVIATION']
        visitor_team_abbr = matchup_data['VISITOR_TEAM_ABBREVIATION']

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
        
def update_players_last_played_game(db, logging):
    try:
        # Get all players from the players collection
        players = db.players.find()

        for player in players:
            player_id = player['id']
            full_name = player['full_name']

            # Find the most recent game for the player
            most_recent_game = db.playersgamelog.find_one({'player_id': player_id}, sort=[('GAME_DATE', DESCENDING)])

            if most_recent_game:
                # Extract the most recent game date
                most_recent_game_date = most_recent_game['GAME_DATE']

                # Update or create the lastgame field in the player document
                db.players.update_one(
                    {'_id': player['_id']},
                    {'$set': {'last_game': most_recent_game_date}},
                    upsert=True
                )

                logging.info(f"Updated lastgame for player: {player_id}, Full Name: {full_name}, Last Game Date: {most_recent_game_date}")
            else:
                logging.warning(f"No game data found for player: {player_id}, Full Name: {full_name}")

        return True

    except Exception as e:
        logging.error(f"Error updating players' last game: {str(e)}")
        return False



def update_team_game_data(db, logging):
    features = ['FGM', 'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT', 
                'FTM', 'FTA', 'FT_PCT', 'OREB', 'DREB', 'REB', 'AST', 'STL', 
                'BLK', 'TOV', 'PF', 'PLUS_MINUS']

    try:
        # Define parameters for regular season game search
        regular_season_params = {
            "counter": 0,  # Counter parameter is required
            "direction": "ASC",  # Sorting direction (ascending)
            "league_id": '00',  # NBA league ID
            "player_or_team_abbreviation": "T",  # T for team
            "season": "2023-24",  # Season ID (e.g., "2019-20")
            "season_type_all_star": "Regular Season",  # Regular season games
            "sorter": "DATE",  # Sort by date
            "date_from_nullable": None,  # Nullable parameter: Start date
            "date_to_nullable": None  # Nullable parameter: End date
        }

        # Define parameters for playoff game search
        playoff_params = {
            "counter": 0,  # Counter parameter is required
            "direction": "ASC",  # Sorting direction (ascending)
            "league_id": '00',  # NBA league ID
            "player_or_team_abbreviation": "T",  # T for team
            "season": "2023-24",  # Season ID (e.g., "2019-20")
            "season_type_all_star": "Playoffs",  # Playoff games
            "sorter": "DATE",  # Sort by date
            "date_from_nullable": None,  # Nullable parameter: Start date
            "date_to_nullable": None  # Nullable parameter: End date
        }

        # Create LeagueGameLog instance with regular season parameters
        regular_season_lgl = LeagueGameLog(**regular_season_params)
        regular_season_team_game_data = regular_season_lgl.get_data_frames()[0]
        
        # Create LeagueGameLog instance with playoff parameters
        playoff_lgl = LeagueGameLog(**playoff_params)
        playoff_team_game_data = playoff_lgl.get_data_frames()[0]
        
        team_game_data = pd.concat([regular_season_team_game_data, playoff_team_game_data])

        # Combine regular season and playoff game data
        # Filter out games from the offseason (October to April)
        # team_game_data = team_game_data[
        #     (team_game_data['GAME_DATE'] >= '2023-10-01') & 
        #     (team_game_data['GAME_DATE'] <= '2024-05-30')
        # ]

        # Map WL column to 1 for W (win) and 0 for L (loss)
        team_game_data['WL'] = team_game_data['WL'].map({'W': 1, 'L': 0})

        # Add a new column 'HomeOrAway' based on the 'MATCHUP' column
        team_game_data['HOMEORAWAY'] = team_game_data['MATCHUP'].apply(lambda x: 1 if 'vs.' in x else 0)

        # Group the DataFrame by game ID
        grouped_data = team_game_data.groupby('GAME_ID')

        collection = db['games']  # Replace 'your_collection' with your actual collection name

        existing_game_ids = set(collection.distinct("game_id"))

        new_games_added = False

        for game_id, group in grouped_data:
            if game_id not in existing_game_ids:
                game_info = {
                    "game_id": game_id,
                    "date": group['GAME_DATE'].iloc[0],
                    "teams": []
                }

                for index, row in group.iterrows():
                    team_data = {
                        "team_id": row['TEAM_ID'],
                        "statistics": {
                            "TEAM_NAME": row['TEAM_NAME'],
                            "TEAM_ABBREVIATION": row['TEAM_ABBREVIATION'],
                            "WL": row['WL'],
                            "HOMEORAWAY": row['HOMEORAWAY'],
                            **{feature: row[feature] for feature in features}
                        }
                    }
                    game_info["teams"].append(team_data)

                collection.insert_one(game_info)
                
                logging.info(f"New game added - Game ID: {game_id}, Date: {game_info['date']}")
                
                new_games_added = True
        
        if not new_games_added:
            print("No new games added.")
            logging.info("No new games added already up to date ")

        logging.info("Game data update completed.")

    except Exception as e:
        logging.error(f"Error updating game data: {str(e)}")


def update_team_ranks_data(db,logging):
    try:
     # Create an instance of the TeamEstimatedMetrics class with the parameters
        metrics_params = {
            "league_id": "00",
            "season": "2023-24",
            "season_type": "Regular Season"
        }
        team_estimated_metrics = TeamEstimatedMetrics(**metrics_params)

        # Call the API and get the response
        metrics_data = team_estimated_metrics.get_data_frames()[0]
        
        desired_columns = ['TEAM_NAME', 'TEAM_ID', 'W_PCT', 'E_OFF_RATING', 'E_DEF_RATING', 'E_NET_RATING', 
                   'E_AST_RATIO', 'E_OREB_PCT', 'E_DREB_PCT', 'E_REB_PCT', 'E_TM_TOV_PCT', 'E_PACE']
        
        team_stats = metrics_data[desired_columns]
        
        collection = db['teamsranks']  # Replace 'your_collection' with your actual collection name
        
        # Clear the collection
        collection.delete_many({})
        
        # Create a list to hold team data
        team_data_list = []

        for index, row in team_stats.iterrows():
            team_data = {
                "TEAM_NAME": row["TEAM_NAME"],
                "TEAM_ID": row["TEAM_ID"],
                "W_PCT": row["W_PCT"],
                "E_OFF_RATING": row["E_OFF_RATING"],
                "E_DEF_RATING": row["E_DEF_RATING"],
                "E_NET_RATING": row["E_NET_RATING"],
                "E_AST_RATIO": row["E_AST_RATIO"],
                "E_OREB_PCT": row["E_OREB_PCT"],
                "E_DREB_PCT": row["E_DREB_PCT"],
                "E_REB_PCT": row["E_REB_PCT"],
                "E_TM_TOV_PCT": row["E_TM_TOV_PCT"],
                "E_PACE": row["E_PACE"]
            }
            # Append the team data to the list
            team_data_list.append(team_data)
            # Log the updated game data
            logging.info("Team ranks updated: %s", row['TEAM_ID'])

        # Insert all team data into the collection
        collection.insert_many(team_data_list)
         # Log success message
        logging.info("All team ranks updated")
            
    except Exception as e:
        logging.error(f"Error updating team rank data: {str(e)}")
  
def find_and_update_daily_players(db, logging):
    
    # Watch this some possible wrong team mappings
    try:
        team_mapping = {
            "atlanta": "atlanta hawks",
            "boston": "boston celtics",
            "brooklyn": "brooklyn nets",
            "charlotte": "charlotte hornets",
            "chicago": "chicago bulls",
            "cleveland": "cleveland cavaliers",
            "dallas": "dallas mavericks",
            "denver": "denver nuggets",
            "detroit": "detroit pistons",
            "golden state": "golden state warriors",
            "houston": "houston rockets",
            "indiana": "indiana pacers",
            "la": "la clippers",
            "los angeles": "los angeles lakers",
            "memphis": "memphis grizzlies",
            "miami": "miami heat",
            "milwaukee": "milwaukee bucks",
            "minnesota": "minnesota timberwolves",
            "new orleans": "new orleans pelicans",
            "new york": "new york knicks",
            "oklahoma city": "oklahoma city thunder",
            "orlando": "orlando magic",
            "philadelphia": "philadelphia 76ers",
            "phoenix": "phoenix suns",
            "portland": "portland trail blazers",
            "sacramento": "sacramento kings",
            "san antonio": "san antonio spurs",
            "toronto": "toronto raptors",
            "utah": "utah jazz",
            "washington": "washington wizards"
        }

        daily_schedule = db["dailyschedule"].find_one({}, {"Schedule": 1})
        if daily_schedule:
            # Extract team names from daily schedule
            all_players_data = []
            for entry in daily_schedule["Schedule"]:
                team1_abbr = entry["team1"]
                team2_abbr = entry["team2"]
                matchup1 = entry["matchup1"]
                matchup2 = entry["matchup2"]
                
                # Map abbreviated team names to full team names
                team1_full = team_mapping.get(team1_abbr)
                team2_full = team_mapping.get(team2_abbr)

                # Query players collection for each team
                if team1_full:
                    players_team1 = db["teamrosters"].find_one({"team_name": team1_full}, {"players": 1})
                    if players_team1 and "players" in players_team1:
                        for player_name in players_team1["players"]:
                            player = db["players"].find_one({"full_name": player_name})
                            if player:
                                player_id = player["id"]
                                player_data = {"player_name": player_name, "player_id": player_id, "matchup": matchup1}
                                all_players_data.append(player_data)
                
                if team2_full:
                    players_team2 = db["teamrosters"].find_one({"team_name": team2_full}, {"players": 1})
                    if players_team2 and "players" in players_team2:
                        for player_name in players_team2["players"]:
                            player = db["players"].find_one({"full_name": player_name})
                            if player:
                                player_id = player["id"]
                                player_data = {"player_name": player_name, "player_id": player_id, "matchup": matchup2}
                                all_players_data.append(player_data)

            # Replace the entire collection with the new data
            db["dailyplayers"].replace_one({}, {"players": all_players_data}, upsert=True)
            
            print("Daily players added to the collection.")
        else:
            print("Daily schedule not found.")
            
    except Exception as e:
        logging.error(f"Error updating team rank data: {str(e)}")

def find_and_insert_player_stats(db, logging):
    try:
        # Get all players from the dailyplayers collection
        daily_players = db["dailyplayers"].find_one({}, {"players": 1})
        if daily_players and "players" in daily_players:
            for player_data in daily_players["players"]:
                player_id = player_data["player_id"]
                matchup = player_data["matchup"]
                player_name = player_data["player_name"]
                
                print(f"Processing player: {player_name}, Matchup: {matchup}")
                
                # Split the matchup string
                teams = matchup.split(" @ ") if "@" in matchup else matchup.split(" vs. ")
                home_team = teams[0]
                away_team = teams[1]
                
                print(f"Home Team: {home_team}, Away Team: {away_team}")
                
                # Query game logs for both scenarios
                player_game_logs = db["playersgamelog"].find({
                    "player_id": player_id,
                    "$or": [
                        {"MATCHUP": f"{away_team} @ {home_team}"},
                        {"MATCHUP": f"{away_team} vs. {home_team}"},
                        {"MATCHUP": f"{home_team} vs. {away_team}"},
                        {"MATCHUP": f"{home_team} @ {away_team}"}
                    ]
                }).sort([("GAME_DATE", -1)]).limit(3)  # Sort by GAME_DATE descending and limit to 3
                
                # Insert player logs into playersmatchuplog collection
                player_logs = list(player_game_logs)  # Convert cursor to list for counting num_games
                num_games = len(player_logs)
                recent_matchups = [{"GAME_STATS": log} for log in player_logs]
                
                # Insert or update player log in playersmatchuplog collection
                db["playersmatchuplog"].update_one(
                    {"player_id": player_id},
                    {"$set": {"num_games": num_games, "recent_matchups": recent_matchups}},
                    upsert=True
                    )
                
                print("Inserted player logs into playersmatchuplog collection.")
                print(f"Number of games: {num_games}")
                print("Recent matchups:")
                for matchup in recent_matchups:
                    print(matchup)
                
                print("\n")  # Add a new line between players
        else:
            print("No daily players found.")
            
    except Exception as e:
        logging.error(f"Error finding and inserting player stats: {type(e).__name__}: {str(e)}")












  
#---- SCRAPING ----#
def scrapeForRosters(db, logging):
    try:
        collection = db["teamrosters"]
        # List of URLs for team rosters
        urls = [
            "https://www.espn.com/nba/team/roster/_/name/bos/boston-celtics",
            "https://www.espn.com/nba/team/roster/_/name/bkn/brooklyn-nets",
            "https://www.espn.com/nba/team/roster/_/name/ny/new-york-knicks",
            "https://www.espn.com/nba/team/roster/_/name/phi/philadelphia-76ers",
            "https://www.espn.com/nba/team/roster/_/name/tor/toronto-raptors",
            "https://www.espn.com/nba/team/roster/_/name/gs/golden-state-warriors",
            "https://www.espn.com/nba/team/roster/_/name/lac/la-clippers",
            "https://www.espn.com/nba/team/roster/_/name/lal/los-angeles-lakers",
            "https://www.espn.com/nba/team/roster/_/name/phx/phoenix-suns",
            "https://www.espn.com/nba/team/roster/_/name/sac/sacramento-kings",
            "https://www.espn.com/nba/team/roster/_/name/chi/chicago-bulls",
            "https://www.espn.com/nba/team/roster/_/name/cle/cleveland-cavaliers",
            "https://www.espn.com/nba/team/roster/_/name/det/detroit-pistons",
            "https://www.espn.com/nba/team/roster/_/name/ind/indiana-pacers",
            "https://www.espn.com/nba/team/roster/_/name/mil/milwaukee-bucks",
            "https://www.espn.com/nba/team/roster/_/name/dal/dallas-mavericks",
            "https://www.espn.com/nba/team/roster/_/name/hou/houston-rockets",
            "https://www.espn.com/nba/team/roster/_/name/mem/memphis-grizzlies",
            "https://www.espn.com/nba/team/roster/_/name/no/new-orleans-pelicans",
            "https://www.espn.com/nba/team/roster/_/name/sa/san-antonio-spurs",
            "https://www.espn.com/nba/team/roster/_/name/den/denver-nuggets",
            "https://www.espn.com/nba/team/roster/_/name/min/minnesota-timberwolves",
            "https://www.espn.com/nba/team/roster/_/name/okc/oklahoma-city-thunder",
            "https://www.espn.com/nba/team/roster/_/name/por/portland-trail-blazers",
            "https://www.espn.com/nba/team/roster/_/name/utah/utah-jazz",
            "https://www.espn.com/nba/team/roster/_/name/atl/atlanta-hawks",
            "https://www.espn.com/nba/team/roster/_/name/cha/charlotte-hornets",
            "https://www.espn.com/nba/team/roster/_/name/mia/miami-heat",
            "https://www.espn.com/nba/team/roster/_/name/orl/orlando-magic",
            "https://www.espn.com/nba/team/roster/_/name/wsh/washington-wizards"
        ]

        # Define headers to mimic a browser request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }

        # Dictionary to store team rosters
        team_rosters = {}

        # Iterate over each URL
        for url in urls:
            # Extract team name from the URL
            team_name = url.split("/")[-1].replace("-", " ").title()

            # Send a GET request to the URL with headers
            response = requests.get(url, headers=headers)

            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                # Parse the HTML content using BeautifulSoup
                soup = BeautifulSoup(response.content, "html.parser")

                # Find the section with class "Roster"
                roster_section = soup.find("section", class_="Roster")

                # Check if the roster section was found
                if roster_section:
                    # Find the table inside the roster section
                    roster_table = roster_section.find("table")

                    # Check if the roster table was found
                    if roster_table:
                        players = []  # List to store player names

                        # Now you can iterate over rows and cells to extract the data
                        rows = roster_table.find_all("tr")
                        for row in rows:
                            cells = row.find_all("td")
                            if len(cells) > 1:
                                player_name = re.sub(r'\d+', '', cells[1].text.strip())
                                players.append(player_name.strip()) 

                         # Store team roster in dictionary
                        # Normalize the team name extracted from the URL
                        team_name_normalized = team_name.lower()

                        # Store team roster in dictionary
                        team_roster_data = {
                            "team_name": team_name_normalized,
                            "players": players
                        }

                        # Replace existing entry or insert a new one
                        collection.replace_one({"team_name": team_name_normalized}, team_roster_data, upsert=True)
                    else:
                        print(f"Roster table not found for {url}.")
                else:
                    print(f"Roster section not found for {url}.")
            else:
                print(f"Failed to retrieve data from {url}. Status code: {response.status_code}")
                
    except Exception as e:
        logging.error(f"Error updating team rank data: {str(e)}")
       
def scrapeForDailySchedule(db, logging):
    try:
        collection = db["dailyschedule"]
        
        cities = [
        "Boston",
        "Brooklyn",
        "New York",
        "Philadelphia",
        "Toronto",
        "Chicago",
        "Cleveland",
        "Detroit",
        "Indiana",
        "Milwaukee",
        "Denver",
        "Minnesota",
        "Oklahoma City",
        "Portland",
        "Utah",
        "Golden State",
        "LA",
        "Los Angeles",
        "Phoenix",
        "Sacramento",
        "Atlanta",
        "Charlotte",
        "Miami",
        "Orlando",
        "Washington",
        "Dallas",
        "Houston",
        "Memphis",
        "New Orleans",
        "San Antonio"
        ]

        city_team_mapping = {
            "Atlanta": "ATL",
            "Boston": "BOS",
            "Brooklyn": "BKN",
            "Charlotte": "CHA",
            "Chicago": "CHI",
            "Cleveland": "CLE",
            "Dallas": "DAL",
            "Denver": "DEN",
            "Detroit": "DET",
            "Golden State": "GSW",
            "Houston": "HOU",
            "Indiana": "IND",
            "LA": "LAC",
            "Los Angeles": "LAL",
            "Memphis": "MEM",
            "Miami": "MIA",
            "Milwaukee": "MIL",
            "Minnesota": "MIN",
            "New Orleans": "NOP",
            "New York": "NYK",
            "Oklahoma City": "OKC",
            "Orlando": "ORL",
            "Philadelphia": "PHI",
            "Phoenix": "PHX",
            "Portland": "POR",
            "Sacramento": "SAC",
            "San Antonio": "SAS",
            "Toronto": "TOR",
            "Utah": "UTA",
            "Washington": "WAS"
        }

        # Get current date
        current_date = datetime.now().strftime("%Y%m%d")

        # URL of the webpage containing today's NBA schedule
        url = f"https://www.espn.com/nba/schedule/_/date/{current_date}"

        # Define headers to mimic a browser request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }

        # Send a GET request to the URL with headers
        response = requests.get(url, headers=headers)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Find the table with class "Table"
            schedule_table = soup.find("table", class_="Table")
            
            # Check if the schedule table was found
            if schedule_table:
                # Create an empty list to store schedule information
                schedule = []
                
                # Find all rows in the table
                rows = schedule_table.find_all("tr")
                
                # Iterate over each row
                for row in rows:
                    # Find all cells in the row
                    cells = row.find_all("td")
                    
                    # Check if the row contains schedule information
                    if len(cells) > 1:
                        # Extract team names
                        team_1 = cells[0].text.strip()
                        team_2 = cells[1].text.strip() 
                        game_time = cells[2].text.strip()
                        print(game_time)
                        
                        # Check if any city name is present in team names
                        for city in cities:
                            if city in team_1:
                                team1 = city
                            if city in team_2:
                                team2 = city
                        
                        # Generate matchup strings
                        matchup1 = f"{city_team_mapping[team1]} @ {city_team_mapping[team2]}"
                        matchup2 = f"{city_team_mapping[team2]} vs. {city_team_mapping[team1]}"
                        
                        # Add schedule information to the list
                        schedule.append({"team1": team1.lower(), "team2": team2.lower(), "matchup1": matchup1, "matchup2": matchup2, "game_time": game_time})
                
                # Create a JSON object with the schedule
                schedule_json = {"Schedule": schedule}
                # Replace existing entry or insert a new one
                collection.replace_one({}, schedule_json, upsert=True)
                # Print the JSON object
                print(json.dumps(schedule_json, indent=4))
            else:
                print("Schedule table not found.")
        else:
            print("Failed to retrieve data from", url, ". Status code:", response.status_code)

    except Exception as e:
        logging.error(f"Error updating team rank data: {str(e)}")

       
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
player_recent_game_logger = setup_logger('player_recent_game', 'player_recent_game.log')
team_game_data_logger = setup_logger('team_game_data', 'team_game_data.log')
team_rank_data_logger = setup_logger('team_rank_data', 'team_rank_data.log')

# New
update_daily_players_logger =  setup_logger('update_daily_players', 'update_daily_players.log')
update_players_recent_matchups_logger =  setup_logger('update_players_recent_matchups', 'update_players_recent_matchups.log')
player_game_playoff_data_logger = setup_logger('player_game_playoff_data', 'player_game_playoff_data.log')

# Scraping Loggers
scraping_roster_logger = setup_logger('scraping_roster', 'scraping_roster.log')
scraping_daily_schedule_logger = setup_logger('scraping_daily_schedule', 'scraping_daily_schedule.log')

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
    
    # Connect to MongoDB
    db = client['nba']

    try:
        scrapeForRosters(db, scraping_roster_logger)
        print("TEAM ROSTERS UPDATED")
    except Exception as e:
        print(f"Error updating team rosters: {e}")

    try:
        scrapeForDailySchedule(db, scraping_daily_schedule_logger)
        print("DAILY SCHEDULE UPDATED")
    except Exception as e:
        print(f"Error updating daily schedule: {e}")

    try:
        find_and_update_daily_players(db, update_daily_players_logger)
        print("UPDATED TODAY'S PLAYERS")
    except Exception as e:
        print(f"Error updating today's players: {e}")

    try:
        nba_update_player_game_data(db, player_game_data_logger)
        print("NBA PLAYER GAME DATA UPDATED")
    except Exception as e:
        print(f"Error updating NBA player game data: {e}")

    # try:
    #     nba_update_active_players(db, active_players_logger)
    #     print("NBA PLAYER NAME and ID DATA UPDATED")
    # except Exception as e:
    #     print(f"Error updating NBA active players: {e}")

    try:
        update_players_last_played_game(db, player_recent_game_logger)
        print("UPDATED PLAYERS' MOST RECENT GAME")
    except Exception as e:
        print(f"Error updating players' most recent game: {e}")

    try:
        find_and_insert_player_stats(db, update_players_recent_matchups_logger)
        print("UPDATED TODAY'S PLAYERS STATS")
    except Exception as e:
        print(f"Error updating today's players stats: {e}")

    try:
        update_team_game_data(db, team_game_data_logger)
        print("UPDATED TEAM GAME DATA")
    except Exception as e:
        print(f"Error updating team game data: {e}")

    # Uncomment this block if you want to update team rank data
    # try:
    #     update_team_ranks_data(db, team_rank_data_logger)
    #     print("UPDATED TEAM RANK DATA")
    # except Exception as e:
    #     print(f"Error updating team rank data: {e}")

    client.close()

except Exception as e:
    print(f"Critical error: {e}")
    