import requests
import datetime as datetime
import json
import os
import certifi
from pymongo import MongoClient, DESCENDING
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import pandas as pd



def get_dk_player_props_and_odds(db):
    # An api key is emailed to you when you sign up to a plan
    # Get a free API key at https://api.the-odds-api.com/
    API_KEY = '41427f459bc4c67745a3bc720220292d'

    SPORT = 'basketball_nba'  # Specify the sport as basketball_nba for NBA games
    REGIONS = 'us'             # Specify the region as us
    ODDS_FORMAT = 'american'    # Specify the odds format as decimal

    # Markets for NBA player props
    MARKETS = ['player_points', 'player_rebounds', 'player_assists', 'player_threes', 'player_blocks', 'player_steals']

    # Get today's date
    today_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    collection = db["dailyschedule"]
    
    # Query the document
    schedule_doc = collection.find_one()

    # Check if the document exists and has the 'Schedule' field
    if schedule_doc and 'Schedule' in schedule_doc:
        # Get the length of the 'Schedule' array
        schedule_length = len(schedule_doc['Schedule'])
        print("Number of games today:", schedule_length)
    else:
        print("Schedule document not found or does not contain 'Schedule' field.")

    # Make a request to fetch NBA basketball events for today
    events_response = requests.get(
        f'https://api.the-odds-api.com/v4/sports/{SPORT}/events',
        params={
            'apiKey': API_KEY,
            'regions': REGIONS,
            'oddsFormat': ODDS_FORMAT,
            'date': today_date  # Specify the date as today's date
        }
    )

    if events_response.status_code != 200:
        print(f'Failed to get NBA events: status_code {events_response.status_code}, response body {events_response.text}')
    else:
        events_json = events_response.json()
        print(events_json)
        event_ids = []  # Initialize an empty list to store event IDs

        # Iterate over the events and extract the event IDs
        for event in events_json:
            event_ids.append(event['id'])

        print('Event IDs for today:', event_ids)

        # Now fetch player prop odds for each event and market
        event_id = event_ids[0]
        
        # Initialize an empty list to store DraftKings outcomes
        draftkings_outcomes = []
        
        # Fetch data for the first two events
        for event_id in event_ids[:schedule_length]:
            # Fetch player prop odds for each market
            for market in MARKETS:
                odds_response = requests.get(
                    f'https://api.the-odds-api.com/v4/sports/{SPORT}/events/{event_id}/odds',
                    params={
                        'apiKey': API_KEY,
                        'regions': REGIONS,
                        'markets': market,
                        'bookmaker': 'draftkings', 
                        'oddsFormat': ODDS_FORMAT,
                    }
                )

                if odds_response.status_code != 200:
                    print(f'Failed to get {market} odds for event {event_id}: status_code {odds_response.status_code}, response body {odds_response.text}')
                else:
                    # Extract JSON content from the response
                    data = odds_response.json()

                    # Check if data is not empty and contains bookmakers
                    if data and 'bookmakers' in data:
                        # Iterate over each bookmaker
                        for bookmaker in data['bookmakers']:
                            # Check if the bookmaker is DraftKings
                            if bookmaker['key'] == 'draftkings':
                                # Extract outcomes from DraftKings
                                draftkings_outcomes.append(bookmaker.get('markets', []))
                                break

        # Print DraftKings outcomes for the first two events
        return draftkings_outcomes

def organize_response(dk_outcomes):
    # Define a dictionary to map market types to stat abbreviations
    market_stat_abrv = {
        'player_points': 'PTS',
        'player_rebounds': 'REB',
        'player_assists': 'AST',
        'player_threes': 'FG3M',
        'player_blocks': 'BLK',
        'player_steals': 'STL'
    }
    
    # Initialize an empty dictionary to store the overall organized data
    overall_organized_data = {}
    
    # Iterate over each list of outcomes
    for outcomes_list in dk_outcomes:
        # Iterate over each market type in the outcomes list
        for market_data in outcomes_list:
            market_type = market_data['key']  # Get the market type
            stat_abrv = market_stat_abrv.get(market_type, '')  # Get the stat abbreviation
            
            # Initialize a dictionary for the market type
            organized_data = {}
            
            # Iterate over outcomes for each player in the market type
            for outcome in market_data['outcomes']:
                player_name = outcome['description']
                over_under = outcome['name']
                price = outcome['price']
                point = outcome['point']
                
                # Initialize a dictionary for the player if not already present
                if player_name not in organized_data:
                    organized_data[player_name] = {'stat_abrv': stat_abrv}
                
                # Store over/under prices and points for the player
                organized_data[player_name][over_under] = {'price': price, 'point': point}
            
            # Store the organized data for the market type in the overall dictionary
            overall_organized_data.setdefault(market_type, {}).update(organized_data)

    # Return the overall organized data
    return overall_organized_data



def add_player_ids(db, organized_data):
    # Connect to the MongoDB collection
    dailyplayers_collection = db["dailyplayers"]
    
    # Iterate over each market type
    for market_type, players in organized_data.items():
        # Iterate over each player in the market type
        for player_name in players:
            # Search for the player in the dailyplayers collection
            player_record = dailyplayers_collection.find_one({"players.player_name": player_name})
            if player_record:
                # Get the player ID from the record and add it to the organized data
                player_id = next(item["player_id"] for item in player_record["players"] if item["player_name"] == player_name)
                players[player_name]["player_id"] = player_id
                
def get_data_from_db(collection_name):
    collection = db[collection_name]  # corrected the string formatting
    data = collection.find()
    data_list = list(data)  # Convert cursor to list for JSON serialization
    return data_list
  
  
def getting_player_over_under_values(player_game_collection, player_id, stat_abbreviation, prop_value):
    # Filter player game data based on player ID
    player_game_data = [game for game in player_game_collection if game['player_id'] == player_id]
    
    # Convert int64 GAME_DATE to datetime.datetime if needed 
    # (This is bizarre) Random new game different date format fix
    for game in player_game_data:
        if isinstance(game['GAME_DATE'], pd._libs.tslibs.timestamps.Timestamp):
            game['GAME_DATE'] = game['GAME_DATE'].to_pydatetime()
        elif isinstance(game['GAME_DATE'], int):
            game['GAME_DATE'] = datetime.datetime.fromtimestamp(game['GAME_DATE'] / 1000.0)  # Assuming Unix timestamp is in milliseconds
    
    # Sort player game data based on 'GAME_DATE' in descending order (most recent first)
    player_game_data.sort(key=lambda x: x['GAME_DATE'], reverse=True)

    
    # Initialize counters
    total_games = len(player_game_data)
    over_count = 0
    under_count = 0
    over_count_recent_3 = 0
    under_count_recent_3 = 0
    over_count_recent_5 = 0
    under_count_recent_5 = 0
    over_count_recent_7 = 0
    under_count_recent_7 = 0
    over_count_recent_11 = 0
    under_count_recent_11 = 0
    total_minutes_over = 0
    total_minutes_under = 0
    total_fouls = 0  # New counter for fouls
    
    # Iterate over player game data
    for i, game in enumerate(player_game_data):
        if game[stat_abbreviation] >= prop_value:
            over_count += 1
            total_minutes_over += game['MIN']
            if i < 3:
                over_count_recent_3 += 1
            if i < 5:
                over_count_recent_5 += 1
            if i < 7:
                over_count_recent_7 += 1
            if i < 11:
                over_count_recent_11 += 1
        else:
            under_count += 1
            total_minutes_under += game['MIN']
            if i < 3:
                under_count_recent_3 += 1
            if i < 5:
                under_count_recent_5 += 1
            if i < 7:
                under_count_recent_7 += 1
            if i < 11:
                under_count_recent_11 += 1
        
        # Add fouls to the total fouls counter
        total_fouls += game.get('PF', 0)
    
    # Calculate average minutes for over and under
    avg_minutes_over = round(total_minutes_over / over_count, 2) if over_count > 0 else 0
    avg_minutes_under = round(total_minutes_under / under_count, 2) if under_count > 0 else 0
    
    # Calculate fouls average
    avg_fouls = round(total_fouls / total_games, 2) if total_games > 0 else 0
    
    # Create response data
    response_data = {
        'total_games': total_games,
        'over_count': over_count,
        'under_count': under_count,
        'over_count_recent_3': over_count_recent_3,
        'under_count_recent_3': under_count_recent_3,
        'over_count_recent_5': over_count_recent_5,
        'under_count_recent_5': under_count_recent_5,
        'over_count_recent_7': over_count_recent_7,
        'under_count_recent_7': under_count_recent_7,
        'over_count_recent_11': over_count_recent_11,
        'under_count_recent_11': under_count_recent_11,
        'avg_minutes_over': avg_minutes_over,
        'avg_minutes_under': avg_minutes_under,
        'avg_fouls': avg_fouls  # Include fouls average in the response
    }
    
    return response_data   

def getting_player_matchup_values(player_id, stat_abbreviation, prop_value, player_matchup_collection):
    over_count = 0
    under_count = 0
    num_games = 0

    for matchup_doc in player_matchup_collection:
        if matchup_doc['player_id'] == player_id:
            num_games = matchup_doc.get('num_games', 0)
            recent_matchups = matchup_doc.get('recent_matchups', [])
            for matchup in recent_matchups:
                game_stats = matchup.get('GAME_STATS', {})
                if game_stats.get(stat_abbreviation, 0) >= prop_value:
                    over_count += 1
                else:
                    under_count += 1

    response_data = {
        'num_games_matchups': num_games,
        'over_count_matchups': over_count,
        'under_count_matchups': under_count
    }
    
    return response_data

def process_organized_data(organized_data, player_game_collection):
    
    # Mapping dictionary for abbreviation codes to full words
    stat_abrv_mapping = {
        'PTS': 'Points',
        'AST': 'Assists',
        'REB': 'Rebounds',
        'BLK': 'Blocks',
        'STL': 'Steals',
        'FG3M': '3 Pointers'
    }
    
    # Initialize a list to store results for each player
    results = []
    
    # Query player matchups from DB
    player_matchup_collection = get_data_from_db('playersmatchuplog')
    
    # Iterate over each market type (e.g., 'player_points', 'player_rebounds', etc.)
    for market_type, players in organized_data.items():
        # Iterate over each player and their props in the current market type
        for player_name, props in players.items():
            # Get the player ID, stat abbreviation, and over/under values from the props
            player_id = props.get('player_id', None)
            stat_abrv = props.get('stat_abrv', None)
            over_value = props.get('Over', {}).get('point', None)  # Use 'Over' point as prop value
            under_value = props.get('Under', {}).get('point', None)
            over_price = props.get('Over', {}).get('price', None)
            under_price = props.get('Under', {}).get('price', None)
            
            # Check if all necessary information is available
            if player_id is not None and stat_abrv is not None and over_value is not None and under_value is not None:
                
                final_player_result = {}
                # Call the function to get over/under values for the player and prop
                player_result = getting_player_over_under_values(player_game_collection, player_id, stat_abrv, over_value)
                player_matchup_result = getting_player_matchup_values(player_id, stat_abrv, over_value, player_matchup_collection)
                
                # Merge the two response dictionaries
                combined_response = {**player_result, **player_matchup_result}

                consistency_score_over = get_consistency_score(combined_response, "Over")
                consistency_score_under = get_consistency_score(combined_response, "Under")
                
                 # Get the full word for the stat abbreviation
                full_stat_name = stat_abrv_mapping.get(stat_abrv, stat_abrv)
                
                
                # Add the player's name and prop values to the result
                # Construct the final player result
                final_player_result['player_name'] = player_name
                final_player_result['stat'] = full_stat_name
                final_player_result['Over'] = {
                    'over_value': over_value,
                    'over_price': over_price,
                    'consistency_score_over': consistency_score_over
                }
                final_player_result['Under'] = {
                    'under_value': under_value,
                    'under_price': under_price,
                    'consistency_score_under': consistency_score_under
                }
                # Append the result to the list of results
                results.append(final_player_result)
            else:
                # Print a warning if any necessary information is missing
                print(f"Warning: Missing data for {player_name} in {market_type} market")
    
    return results

# Calculates the consistency score
def get_consistency_score(combined_response, over_under):
    allGamesCalc = 0.0
    recent3GamesCalc = 0.0
    recent7GamesCalc = 0.0
    recent11GamesCalc = 0.0
    matchupGamesCalc = 0.0
    allGamesPercent = 0.25
    recent11GamesPercent = 0.30
    matchupGamesPercent = 0.15
    recent3GamesPercent = 0.10
    recent7GamesPercent = 0.20
    
    # Calculate consistency scores for "Over" case
    if over_under == "Over":
        allGamesOverCount = combined_response.get('over_count', 0)
        total_games = combined_response.get('total_games', 1)  # Avoid division by zero
        recent3GamesOverCount = combined_response.get('over_count_recent_3', 0)
        recent7GamesOverCount = combined_response.get('over_count_recent_7', 0)
        recent11GamesOverCount = combined_response.get('over_count_recent_11', 0)
        num_games_matchups = combined_response.get('num_games_matchups', 0)
        matchupGamesOverCount = combined_response.get('over_count_matchups', 0)
        
        allGamesCalc = allGamesOverCount / total_games
        allGamesCalc *= allGamesPercent
        
        recent3GamesCalc = recent3GamesOverCount / 3
        recent3GamesCalc *= recent3GamesPercent
        
        recent7GamesCalc = recent7GamesOverCount / 7
        recent7GamesCalc *= recent7GamesPercent
        
        recent11GamesCalc = recent11GamesOverCount / 11
        recent11GamesCalc *= recent11GamesPercent
        
        if num_games_matchups == 0:
            matchupGamesCalc = recent3GamesOverCount / 3
            matchupGamesCalc *= matchupGamesPercent
        else:
            matchupGamesCalc = matchupGamesOverCount / num_games_matchups
            matchupGamesCalc *= matchupGamesPercent
    
    # Calculate consistency scores for "Under" case
    elif over_under == "Under":
        allGamesUnderCount = combined_response.get('under_count', 0)
        total_games = combined_response.get('total_games', 1)  # Avoid division by zero
        recent3GamesUnderCount = combined_response.get('under_count_recent_3', 0)
        recent7GamesUnderCount = combined_response.get('under_count_recent_7', 0)
        recent11GamesUnderCount = combined_response.get('under_count_recent_11', 0)
        num_games_matchups = combined_response.get('num_games_matchups', 0)
        matchupGamesUnderCount = combined_response.get('under_count_matchups', 0)
        
        allGamesCalc = allGamesUnderCount / total_games
        allGamesCalc *= allGamesPercent
        
        recent3GamesCalc = recent3GamesUnderCount / 3
        recent3GamesCalc *= recent3GamesPercent
        
        recent7GamesCalc = recent7GamesUnderCount / 7
        recent7GamesCalc *= recent7GamesPercent
        
        recent11GamesCalc = recent11GamesUnderCount / 11
        recent11GamesCalc *= recent11GamesPercent
        
        if num_games_matchups == 0:
            matchupGamesCalc = recent3GamesUnderCount / 3
            matchupGamesCalc *= matchupGamesPercent
        else:
            matchupGamesCalc = matchupGamesUnderCount / num_games_matchups
            matchupGamesCalc *= matchupGamesPercent
    
    tallyUpCalc = allGamesCalc + recent11GamesCalc + matchupGamesCalc + recent3GamesCalc + recent7GamesCalc
    
    tallyUpCalc *= 10
    
    tallyUpCalc = round(tallyUpCalc , 2)
    
    return tallyUpCalc

def get_top_consistent_players(results):
    # Initialize a list to store the top consistent players
    top_players = []

    # Iterate over each player's result
    for player_result in results:
        player_name = player_result['player_name']
        stat = player_result['stat']

        # Iterate over 'Over' and 'Under' to find the highest consistency scores with price >= -400
        for bet_type in ['Over', 'Under']:
            consistency_score = player_result[bet_type]['consistency_score_' + bet_type.lower()]
            price = player_result[bet_type]['{}_price'.format(bet_type.lower())]
            prop_value = player_result[bet_type]['{}_value'.format(bet_type.lower())] 

            # Check if the price is greater than or equal to -400
            if price >= -400:
                top_players.append({
                    'player_name': player_name,
                    'stat': stat,
                    'prop_value': prop_value,
                    'bet_type': bet_type,
                    'consistency_score': consistency_score,
                    'price': price
                })

    # Sort the top players based on consistency score in descending order
    top_players.sort(key=lambda x: x['consistency_score'], reverse=True)

    # Get the top 9 players
    top_9_players = top_players[:9]

    return top_9_players
# Load environment variables from .env file
load_dotenv()

# Retrieve the MongoDB Atlas URI from the environment
uri = os.getenv("MONGODB_URI")

# Create a MongoClient instance
client = MongoClient(uri, tlsCAFile=certifi.where())

db = client["nba"]

dk_outcomes = get_dk_player_props_and_odds(db)
organized_response = organize_response(dk_outcomes)
add_player_ids(db, organized_response)

# Query player games from DB
player_game_collection = get_data_from_db('playersgamelog')
results = process_organized_data(organized_response, player_game_collection)
top_9_scores = get_top_consistent_players(results)

collection = db["hardlinedailyprops"]
# Clear existing data from the collection
collection.delete_many({})
# Insert the new data into the collection
collection.insert_many(top_9_scores)


                