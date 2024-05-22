import requests
import datetime as datetime
import json
import os
import certifi
from pymongo import MongoClient, DESCENDING
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import pandas as pd
import itertools

import random

# def get_dk_player_props_and_odds(db):
#     # An api key is emailed to you when you sign up to a plan
#     # Get a free API key at https://api.the-odds-api.com/
#     API_KEY = '41427f459bc4c67745a3bc720220292d'

#     SPORT = 'basketball_nba'  # Specify the sport as basketball_nba for NBA games
#     REGIONS = 'us'             # Specify the region as us
#     ODDS_FORMAT = 'american'    # Specify the odds format as decimal

#     # Markets for NBA player props
#     MARKETS = ['player_points', 'player_rebounds', 'player_assists', 'player_threes', 'player_blocks', 'player_steals']

#     # Get today's date
#     today_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
#     collection = db["dailyschedule"]
    
#     # Query the document
#     schedule_doc = collection.find_one()

#     # Check if the document exists and has the 'Schedule' field
#     if schedule_doc and 'Schedule' in schedule_doc:
#         # Get the length of the 'Schedule' array
#         schedule_length = len(schedule_doc['Schedule'])
#         print("Number of games today:", schedule_length)
#     else:
#         print("Schedule document not found or does not contain 'Schedule' field.")

#     # Make a request to fetch NBA basketball events for today
#     events_response = requests.get(
#         f'https://api.the-odds-api.com/v4/sports/{SPORT}/events',
#         params={
#             'apiKey': API_KEY,
#             'regions': REGIONS,
#             'oddsFormat': ODDS_FORMAT,
#             'date': today_date  # Specify the date as today's date
#         }
#     )

#     if events_response.status_code != 200:
#         print(f'Failed to get NBA events: status_code {events_response.status_code}, response body {events_response.text}')
#     else:
#         events_json = events_response.json()
#         print(events_json)
#         event_ids = []  # Initialize an empty list to store event IDs

#         # Iterate over the events and extract the event IDs
#         for event in events_json:
#             event_ids.append(event['id'])

#         print('Event IDs for today:', event_ids)

#         # Now fetch player prop odds for each event and market
#         event_id = event_ids[0]
        
#         # Initialize an empty list to store DraftKings outcomes
#         draftkings_outcomes = []
        
#         # Fetch data for the first two events
#         for event_id in event_ids[:schedule_length]:
#             # Fetch player prop odds for each market
#             for market in MARKETS:
#                 odds_response = requests.get(
#                     f'https://api.the-odds-api.com/v4/sports/{SPORT}/events/{event_id}/odds',
#                     params={
#                         'apiKey': API_KEY,
#                         'regions': REGIONS,
#                         'markets': market,
#                         'bookmaker': 'draftkings', 
#                         'oddsFormat': ODDS_FORMAT,
#                     }
#                 )

#                 if odds_response.status_code != 200:
#                     print(f'Failed to get {market} odds for event {event_id}: status_code {odds_response.status_code}, response body {odds_response.text}')
#                 else:
#                     # Extract JSON content from the response
#                     data = odds_response.json()

#                     # Check if data is not empty and contains bookmakers
#                     if data and 'bookmakers' in data:
#                         # Iterate over each bookmaker
#                         for bookmaker in data['bookmakers']:
#                             # Check if the bookmaker is DraftKings
#                             if bookmaker['key'] == 'draftkings':
#                                 # Extract outcomes from DraftKings
#                                 draftkings_outcomes.append(bookmaker.get('markets', []))
#                                 break

#         # Print DraftKings outcomes for the first two events
#         return draftkings_outcomes

# def add_player_ids(db, daily_player_odds):
#     # Connect to the MongoDB collection
#     dailyplayers_collection = db["dailyplayers"]
    
#     # Iterate over each market type
#     for market_type, players in daily_player_odds.items():
#         # Iterate over each player in the market type
#         for player_name in players:
#             print(player_name)
#             # Search for the player in the dailyplayers collection
#             player_record = dailyplayers_collection.find_one({"players.player_name": player_name})
#             if player_record:
#                 # Get the player ID from the record and add it to the organized data
#                 player_id = next(item["player_id"] for item in player_record["players"] if item["player_name"] == player_name)
#                 players[player_name]["player_id"] = player_id
# def organize_response(dk_outcomes):
#     # Define a dictionary to map market types to stat abbreviations
#     market_stat_abrv = {
#         'player_points': 'PTS',
#         'player_rebounds': 'REB',
#         'player_assists': 'AST',
#         'player_threes': 'FG3M',
#         'player_blocks': 'BLK',
#         'player_steals': 'STL'
#     }
    
#     # Initialize an empty dictionary to store the overall organized data
#     overall_organized_data = {}
    
#     # Iterate over each list of outcomes
#     for outcomes_list in dk_outcomes:
#         # Iterate over each market type in the outcomes list
#         for market_data in outcomes_list:
#             market_type = market_data['key']  # Get the market type
#             stat_abrv = market_stat_abrv.get(market_type, '')  # Get the stat abbreviation
            
#             # Initialize a dictionary for the market type
#             organized_data = {}
            
#             # Iterate over outcomes for each player in the market type
#             for outcome in market_data['outcomes']:
#                 player_name = outcome['description']
#                 over_under = outcome['name']
#                 price = outcome['price']
#                 point = outcome['point']
                
#                 # Initialize a dictionary for the player if not already present
#                 if player_name not in organized_data:
#                     organized_data[player_name] = {'stat_abrv': stat_abrv}
                
#                 # Store over/under prices and points for the player
#                 organized_data[player_name][over_under] = {'price': price, 'point': point}
            
#             # Store the organized data for the market type in the overall dictionary
#             overall_organized_data.setdefault(market_type, {}).update(organized_data)

#     # Return the overall organized data
#     return overall_organized_data



def fetch_daily_player_odds(collection):
    player_data = {}

    try:
        # Fetch all documents from the collection
        cursor = collection.find()

        # Iterate over the cursor and store data in the dictionary
        for document in cursor:
            player_name = document['player']
            categories = document['categories']
            player_data[player_name] = categories
        
        # # Debugging: Print the fetched data
        # print(f"Fetched player data: {player_data}")

    except Exception as e:
        print(f"An error occurred while fetching data from MongoDB: {e}")

    return player_data

def add_player_ids_and_stat_abrv(db, player_data):
    dailyplayers_collection = db["dailyplayers"]
    # Fetch the single document containing all player records
    player_record = dailyplayers_collection.find_one()
    
    # Check if the player_record exists
    if not player_record or 'players' not in player_record:
        print("No player records found in the dailyplayers collection.")
        return
    
    # Create a mapping of player names to their IDs
    player_id_map = {player['player_name']: player['player_id'] for player in player_record['players']}
    
    # Define the stat abbreviation mapping
    stat_abbreviations = {
        "Points": "PTS",
        "Assists": "AST",
        "Blocks": "BLK",
        "Rebounds": "REB",
        "3-Pointers": "FG3M",
        "Steals": "STL"
    }
    
    # Iterate over each player in the player_data and add the player ID and stat abbreviations
    for player_name in player_data.keys():
        print(f"Processing player: {player_name}")
        if player_name in player_id_map:
            player_id = player_id_map[player_name]
            player_data[player_name]['player_id'] = player_id
            for category in player_data[player_name]:
                if category in stat_abbreviations:
                    player_data[player_name][category]['abbreviation'] = stat_abbreviations[category]
        else:
            print(f"Player ID not found for: {player_name}")
                
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

def process_hardline_data(organized_data, player_game_collection):
    # Mapping dictionary for abbreviation codes to full words
    stat_abrv_mapping = {
        'PTS': 'Points',
        'AST': 'Assists',
        'REB': 'Rebounds',
        'BLK': 'Blocks',
        'STL': 'Steals',
        'FG3M': '3-Pointers'
    }
    
    # Initialize a list to store results for each player
    results = []
    
    # Query player matchups from DB
    player_matchup_collection = get_data_from_db('playersmatchuplog')
    
    # Iterate over each player and their categories
    for player_name, categories in organized_data.items():
        player_id = categories.get('player_id', None)
        
        if player_id is None:
            print(f"Warning: Missing player ID for {player_name}")
            continue
        
        # Iterate over each category (e.g., 'Points', 'Rebounds', etc.)
        for category_name, category_data in categories.items():
            if category_name == 'player_id':
                continue  # Skip player_id
            
            # Get the stat abbreviation for the current category
            stat_abrv = [k for k, v in stat_abrv_mapping.items() if v == category_name]
            if not stat_abrv:
                print(f"Warning: No stat abbreviation found for {category_name}")
                continue
            stat_abrv = stat_abrv[0]
            
            # Extract Hardline data
            hardline_data = category_data.get('Hardline', {})
            over_value = float(hardline_data.get('over_value', None))
            under_value = float(hardline_data.get('under_value', None))
            over_odds = hardline_data.get('over_odds', None)
            under_odds = hardline_data.get('under_odds', None)
            
            # Check if all necessary information is available
            if over_value is not None and under_value is not None:
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
                
                # Construct the final player result
                final_player_result['player_name'] = player_name
                final_player_result['stat'] = full_stat_name
                final_player_result['Over'] = {
                    'over_value': over_value,
                    'over_odds': over_odds,
                    'consistency_score_over': consistency_score_over
                }
                final_player_result['Under'] = {
                    'under_value': under_value,
                    'under_odds': under_odds,
                    'consistency_score_under': consistency_score_under
                }
                
                # Append the result to the list of results
                results.append(final_player_result)
            else:
                # Print a warning if any necessary information is missing
                print(f"Warning: Missing Hardline data for {player_name} in {category_name} category")
    
    return results


def process_daily_player_odds(dailyplayerodds):
    # Mapping dictionary for abbreviation codes to full words
    stat_abrv_mapping = {
        'PTS': 'Points',
        'AST': 'Assists',
        'REB': 'Rebounds',
        'BLK': 'Blocks',
        'STL': 'Steals',
        'FG3M': '3-Pointers'
    }
    
    # Initialize a list to store results for each player
    results = []
    
    # Query player matchups from DB
    player_matchup_collection = get_data_from_db('playersmatchuplog')
    player_game_collection = get_data_from_db('playersgamelog')
    # Iterate over each player and their categories
    for player_name, categories in dailyplayerodds.items():
        player_id = categories.get('player_id', None)
        
        if player_id is None:
            print(f"Warning: Missing player ID for {player_name}")
            continue
        
        # Iterate over each category (e.g., 'Points', 'Rebounds', etc.)
        for category_name, category_data in categories.items():
            if category_name == 'player_id':
                continue  # Skip player_id
            
            # Get the stat abbreviation for the current category
            stat_abrv = category_data.get('abbreviation', None)
            if not stat_abrv:
                print(f"Warning: No stat abbreviation found for {category_name}")
                continue
            
            # Process Hardline data
            hardline_data = category_data.get('Hardline', {})
            if hardline_data:
                process_category_data(player_name, player_id, category_name, stat_abrv, hardline_data, player_game_collection, player_matchup_collection, results)
            
            # Process X+ data
            x_plus_data = category_data.get('X+', {})
            if x_plus_data:
                process_x_plus_data(player_name, player_id, category_name, stat_abrv, x_plus_data, player_game_collection, player_matchup_collection, results)
            
            # Process Altline data
            altline_data = category_data.get('Altline', [])
            if altline_data:
                process_altline_data(player_name, player_id, category_name, stat_abrv, altline_data, player_game_collection, player_matchup_collection, results)
    
    return results

def process_category_data(player_name, player_id, category_name, stat_abrv, data, player_game_collection, player_matchup_collection, results):
    over_value = float(data.get('over_value', None))
    under_value = float(data.get('under_value', None))
    over_odds = data.get('over_odds', None)
    under_odds = data.get('under_odds', None)
    
    if over_value is not None and under_value is not None:
        final_player_result = {}
        
        # Call the function to get over/under values for the player and prop
        player_result = getting_player_over_under_values(player_game_collection, player_id, stat_abrv, over_value)
        player_matchup_result = getting_player_matchup_values(player_id, stat_abrv, over_value, player_matchup_collection)
        
        # Merge the two response dictionaries
        combined_response = {**player_result, **player_matchup_result}
        
        consistency_score_over = get_consistency_score(combined_response, "Over")
        consistency_score_under = get_consistency_score(combined_response, "Under")
        
        # Get the full word for the stat abbreviation
        full_stat_name = category_name
        
        # Construct the final player result
        final_player_result['player_name'] = player_name
        final_player_result['stat'] = full_stat_name
        final_player_result['category'] = 'Hardline'
        final_player_result['Over'] = {
            'over_value': over_value,
            'over_odds': over_odds,
            'consistency_score_over': consistency_score_over
        }
        final_player_result['Under'] = {
            'under_value': under_value,
            'under_odds': under_odds,
            'consistency_score_under': consistency_score_under
        }
        
        # Append the result to the list of results
        results.append(final_player_result)
    else:
        # Print a warning if any necessary information is missing
        print(f"Warning: Missing data for {player_name} in {category_name} category")

def process_x_plus_data(player_name, player_id, category_name, stat_abrv, data, player_game_collection, player_matchup_collection, results):
    for prop_value, odds in data.items():
        if odds is not None:
            final_player_result = {}
            
            # Convert prop_value to a float for further processing
            value = float(prop_value.replace('+', ''))
            
            # Call the function to get over/under values for the player and prop
            player_result = getting_player_over_under_values(player_game_collection, player_id, stat_abrv, value)
            player_matchup_result = getting_player_matchup_values(player_id, stat_abrv, value, player_matchup_collection)
            
            # Merge the two response dictionaries
            combined_response = {**player_result, **player_matchup_result}
            
            consistency_score = get_consistency_score(combined_response, "Over")  # Assuming X+ refers to over values
            
            # Get the full word for the stat abbreviation
            full_stat_name = category_name
            
            # Construct the final player result
            final_player_result['player_name'] = player_name
            final_player_result['stat'] = full_stat_name
            final_player_result['X+'] = {
                'value': value,
                'odds': odds,
                'consistency_score': consistency_score
            }
            
            # Append the result to the list of results
            results.append(final_player_result)
        else:
            print(f"Warning: Missing odds for {player_name} in {category_name} X+ category")

def process_altline_data(player_name, player_id, category_name, stat_abrv, data, player_game_collection, player_matchup_collection, results):
    for altline in data:
        value = altline.get('value', None)
        line = float(altline.get('line', None))
        odds = altline.get('odds', None)
        
        if value and line is not None and odds is not None:
            final_player_result = {}
            
            # Call the function to get over/under values for the player and prop
            player_result = getting_player_over_under_values(player_game_collection, player_id, stat_abrv, line)
            player_matchup_result = getting_player_matchup_values(player_id, stat_abrv, line, player_matchup_collection)
            
            # Merge the two response dictionaries
            combined_response = {**player_result, **player_matchup_result}
            
            consistency_score = get_consistency_score(combined_response, value)
            
            # Get the full word for the stat abbreviation
            full_stat_name = category_name
            
            # Construct the final player result
            final_player_result['player_name'] = player_name
            final_player_result['stat'] = full_stat_name
            final_player_result['Altline'] = {
                'value': value,
                'line': line,
                'odds': odds,
                'consistency_score': consistency_score
            }
            
            # Append the result to the list of results
            results.append(final_player_result)
        else:
            print(f"Warning: Missing data for {player_name} in {category_name} Altline category")

def convert_odds_to_int(odds):
    if isinstance(odds, str):
        return int(odds.replace('−', '-').replace('+', ''))
    return int(odds)

def get_top_consistent_scores(results, top_n=50):
    # List to store all scores with necessary information
    all_scores = []

    # Iterate over each player's result
    for player_result in results:
        player_name = player_result['player_name']
        stat = player_result['stat']

        # Process each type of bet: Over, Under, X+, Altline
        for bet_type in ['Over', 'Under']:
            if bet_type in player_result:
                score_key = f'consistency_score_{bet_type.lower()}'
                if score_key in player_result[bet_type]:
                    odds = convert_odds_to_int(player_result[bet_type][f'{bet_type.lower()}_odds'])
                    if odds >= -600:
                        all_scores.append({
                            'player_name': player_name,
                            'stat': stat,
                            'category': 'Hardline',
                            'value': bet_type,
                            'line': player_result[bet_type][f'{bet_type.lower()}_value'],
                            'odds': player_result[bet_type][f'{bet_type.lower()}_odds'],
                            'consistency_score': player_result[bet_type][score_key]
                        })
        
        if 'X+' in player_result:
            odds = convert_odds_to_int(player_result['X+']['odds'])
            if odds >= -600:
                all_scores.append({
                    'player_name': player_name,
                    'stat': stat,
                    'category': 'X+',
                    'value': 'Over',
                    'line': player_result['X+']['value'],
                    'odds': player_result['X+']['odds'],
                    'consistency_score': player_result['X+']['consistency_score']
                })
        
        if 'Altline' in player_result:
            odds = convert_odds_to_int(player_result['Altline']['odds'])
            if odds >= -600:
                all_scores.append({
                    'player_name': player_name,
                    'stat': stat,
                    'category': 'Altline',
                    'value': player_result['Altline']['value'],
                    'line': player_result['Altline']['line'],
                    'odds': player_result['Altline']['odds'],
                    'consistency_score': player_result['Altline']['consistency_score']
                })
    
    # Sort all scores by consistency_score in descending order
    all_scores.sort(key=lambda x: x['consistency_score'], reverse=True)

    # Get the top N scores
    top_scores = all_scores[:top_n]

    return top_scores


def get_top_consistent_jackpot_scores(results, top_n=50):
    # List to store all scores with necessary information
    all_scores = []

    # Iterate over each player's result
    for player_result in results:
        player_name = player_result['player_name']
        stat = player_result['stat']

        # Process each type of bet: Over, Under, X+, Altline
        for bet_type in ['Over', 'Under']:
            if bet_type in player_result:
                score_key = f'consistency_score_{bet_type.lower()}'
                if score_key in player_result[bet_type]:
                    odds = convert_odds_to_int(player_result[bet_type][f'{bet_type.lower()}_odds'])
                    if odds >= 100:
                        all_scores.append({
                            'player_name': player_name,
                            'stat': stat,
                            'category': 'Hardline',
                            'value': bet_type,
                            'line': player_result[bet_type][f'{bet_type.lower()}_value'],
                            'odds': player_result[bet_type][f'{bet_type.lower()}_odds'],
                            'consistency_score': player_result[bet_type][score_key]
                        })
        
        if 'X+' in player_result:
            odds = convert_odds_to_int(player_result['X+']['odds'])
            if odds >= 100:
                all_scores.append({
                    'player_name': player_name,
                    'stat': stat,
                    'category': 'X+',
                    'value': 'Over',
                    'line': player_result['X+']['value'],
                    'odds': player_result['X+']['odds'],
                    'consistency_score': player_result['X+']['consistency_score']
                })
        
        if 'Altline' in player_result:
            odds = convert_odds_to_int(player_result['Altline']['odds'])
            if odds >= 100:
                all_scores.append({
                    'player_name': player_name,
                    'stat': stat,
                    'category': 'Altline',
                    'value': player_result['Altline']['value'],
                    'line': player_result['Altline']['line'],
                    'odds': player_result['Altline']['odds'],
                    'consistency_score': player_result['Altline']['consistency_score']
                })
    
    # Sort all scores by consistency_score in descending order
    all_scores.sort(key=lambda x: x['consistency_score'], reverse=True)

    # Get the top N scores
    top_scores = all_scores[:top_n]

    return top_scores
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
    # Initialize dictionaries to store the top scores for each category
    top_scores = {
        'Points': [],
        'Rebounds': [],
        '3-Pointers': [],
        'Assists': [],
        'Blocks': [],
        'Steals': []
    }

    # Iterate over each player's result
    for player_result in results:
        player_name = player_result['player_name']
        stat = player_result['stat']

        # Check if the stat is in the categories of interest
        if stat in top_scores:
            # Iterate over 'Over' and 'Under' to find the highest consistency scores with price >= -400
            for bet_type in ['Over', 'Under']:
                consistency_score_key = 'consistency_score_' + bet_type.lower()
                price_key = bet_type.lower() + '_odds'
                
                consistency_score = player_result[bet_type][consistency_score_key]
                price = player_result[bet_type][price_key]
                prop_value = player_result[bet_type][bet_type.lower() + '_value']

                # Convert price to an integer for comparison
                price_int = int(price.replace('−', '-'))

                # Check if the price is greater than or equal to -400
                if price_int >= -400:
                    # Append the relevant data to the appropriate category
                    top_scores[stat].append({
                        'player_name': player_name,
                        'stat': stat,
                        'prop_value': prop_value,
                        'bet_type': bet_type,
                        'consistency_score': consistency_score,
                        'odds': price
                    })

    # Sort each category based on consistency score in descending order
    for stat, scores in top_scores.items():
        scores.sort(key=lambda x: x['consistency_score'], reverse=True)

    # Get the top scores for each category
    top_9_players = []
    for stat in ['Points', 'Rebounds', '3-Pointers', 'Assists', 'Blocks', 'Steals']:
        top_9_players.extend(top_scores[stat][:2] if stat in ['Points', 'Rebounds', '3-Pointers'] else top_scores[stat][:1])
    

    return top_9_players


# Converts American odds to decimal odds
def convert_odds_to_decimal(odds):
    odds = int(odds.replace('−', '-').replace('+', ''))
    if odds > 0:
        return (odds / 100) + 1
    else:
        return (100 / abs(odds)) + 1

# Calculates the combined decimal odds for a parlay
def calculate_combined_odds(parlay):
    combined_odds = 1.0
    for leg in parlay:
        combined_odds *= convert_odds_to_decimal(leg['odds'])
    return combined_odds

# Converts decimal odds back to American odds
def convert_decimal_to_american(odds):
    if odds >= 2:
        return f"+{int((odds - 1) * 100)}"
    else:
        return f"-{int(100 / (odds - 1))}"

# Calculates the implied probability of the parlay hitting based on decimal odds
def calculate_implied_probability(decimal_odds):
    return 1 / decimal_odds

# Checks if a parlay is valid based on the rules specified (e.g., no conflicting bets)
def is_valid_parlay(parlay):
    player_stat_over = {}
    player_stat_under = {}

    for leg in parlay:
        player_stat = (leg['player_name'], leg['stat'])
        value = float(leg.get('line', leg.get('value')))

        if "Over" in leg['value']:
            if player_stat in player_stat_over:
                return False
            player_stat_over[player_stat] = value
        elif "Under" in leg['value']:
            if player_stat in player_stat_under:
                return False
            player_stat_under[player_stat] = value

        if player_stat in player_stat_over and player_stat in player_stat_under:
            if player_stat_over[player_stat] >= player_stat_under[player_stat]:
                return False

    return True

# Attempts to create a valid parlay within the specified odds range
def get_legs_for_parlay(available_legs, min_odds, max_odds):
    # Define the priority of stats
    high_priority_stats = ['Points', '3-Pointers', 'Rebounds']
    medium_priority_stats = ['Assists']
    low_priority_stats = ['Blocks', 'Steals']

    # Separate the legs into high, medium, and low priority lists
    high_priority_legs = [leg for leg in available_legs if leg['stat'] in high_priority_stats]
    medium_priority_legs = [leg for leg in available_legs if leg['stat'] in medium_priority_stats]
    low_priority_legs = [leg for leg in available_legs if leg['stat'] in low_priority_stats]

    # Sort each list by consistency_score
    high_priority_legs = sorted(high_priority_legs, key=lambda x: x['consistency_score'], reverse=True)
    medium_priority_legs = sorted(medium_priority_legs, key=lambda x: x['consistency_score'], reverse=True)
    low_priority_legs = sorted(low_priority_legs, key=lambda x: x['consistency_score'], reverse=True)

    # Combine the lists, giving priority to high_priority_legs first, then medium, then low
    sorted_legs = high_priority_legs + medium_priority_legs + low_priority_legs

    # Try to create parlays with the least number of legs first
    for num_legs in range(2, 5):  # 2, 3, 4 legs
        for combination in itertools.combinations(sorted_legs, num_legs):
            parlay = list(combination)
            if is_valid_parlay(parlay):
                combined_odds = calculate_combined_odds(parlay)
                american_odds = convert_decimal_to_american(combined_odds)
                # Check if american_odds is within the specified range and is positive
                if min_odds <= int(american_odds.replace('-', '').replace('+', '')) < max_odds and int(american_odds) > 0:
                    return parlay

    return None

# Creates parlays that fit within the specified odds ranges and uses the most consistent scores
def create_parlays(top_scores):
    parlays = []
    used_legs = set()
    
    odds_ranges = [
        {'min': 100, 'max': 200},
        {'min': 200, 'max': 300},
        {'min': 300, 'max': 400}
    ]
    
    for odds_range in odds_ranges:
        available_legs = [leg for leg in top_scores if leg['id'] not in used_legs]
        parlay = get_legs_for_parlay(available_legs, odds_range['min'], odds_range['max'])
        if parlay:
            combined_odds = calculate_combined_odds(parlay)
            implied_probability = calculate_implied_probability(combined_odds)
            parlays.append({
                'parlay': parlay,
                'odds': convert_decimal_to_american(combined_odds),
                'implied_probability': implied_probability
            })
            used_legs.update(leg['id'] for leg in parlay)

    return parlays

# Attempts to create a valid parlay with exactly 4 legs within the specified odds range
def get_more_legs_for_parlay(available_legs, min_odds, max_odds):
    # Define the priority of stats
    high_priority_stats = ['Points', '3-Pointers', 'Rebounds']
    medium_priority_stats = ['Assists']
    low_priority_stats = ['Blocks', 'Steals']

    # Separate the legs into high, medium, and low priority lists
    high_priority_legs = [leg for leg in available_legs if leg['stat'] in high_priority_stats]
    medium_priority_legs = [leg for leg in available_legs if leg['stat'] in medium_priority_stats]
    low_priority_legs = [leg for leg in available_legs if leg['stat'] in low_priority_stats]

    # Sort each list by consistency_score
    high_priority_legs = sorted(high_priority_legs, key=lambda x: x['consistency_score'], reverse=True)
    medium_priority_legs = sorted(medium_priority_legs, key=lambda x: x['consistency_score'], reverse=True)
    low_priority_legs = sorted(low_priority_legs, key=lambda x: x['consistency_score'], reverse=True)

    # Combine the lists, giving priority to high_priority_legs first, then medium, then low
    sorted_legs = high_priority_legs + medium_priority_legs + low_priority_legs

    # Try to create parlays with exactly 4 legs
    for combination in itertools.combinations(sorted_legs, 4):
        parlay = list(combination)
        if is_valid_parlay(parlay):
            combined_odds = calculate_combined_odds(parlay)
            american_odds = convert_decimal_to_american(combined_odds)
            # Check if american_odds is within the specified range and is positive
            if min_odds <= int(american_odds.replace('-', '').replace('+', '')) < max_odds and int(american_odds) > 0:
                return parlay

    return None

def create_more_parlays(top_scores):
    parlays = []
    used_legs = set()
    
    odds_ranges = [
        {'min': 100, 'max': 200},
        {'min': 200, 'max': 300},
        {'min': 300, 'max': 400}
    ]
    
    for odds_range in odds_ranges:
        available_legs = [leg for leg in top_scores if leg['id'] not in used_legs]
        parlay = get_more_legs_for_parlay(available_legs, odds_range['min'], odds_range['max'])
        if parlay:
            combined_odds = calculate_combined_odds(parlay)
            implied_probability = calculate_implied_probability(combined_odds)
            parlays.append({
                'parlay': parlay,
                'odds': convert_decimal_to_american(combined_odds),
                'implied_probability': implied_probability
            })
            used_legs.update(leg['id'] for leg in parlay)

    return parlays


# Get the top 4 consistent scores and create a valid parlay
def get_golden_goose_parlay(top_scores):
    # Define the priority of stats
    high_priority_stats = ['Points', '3-Pointers', 'Rebounds']
    low_priority_stats = ['Assists', 'Blocks', 'Steals']

    # Separate the scores into high and low priority lists
    high_priority_legs = [leg for leg in top_scores if leg['stat'] in high_priority_stats]
    low_priority_legs = [leg for leg in top_scores if leg['stat'] in low_priority_stats]

    # Sort each list by consistency_score
    high_priority_legs = sorted(high_priority_legs, key=lambda x: x['consistency_score'], reverse=True)
    low_priority_legs = sorted(low_priority_legs, key=lambda x: x['consistency_score'], reverse=True)

    # Combine the lists, giving priority to high_priority_legs
    sorted_legs = high_priority_legs + low_priority_legs

    # Try to create a valid parlay with exactly 4 legs
    for combination in itertools.combinations(sorted_legs, 4):
        parlay = list(combination)
        if is_valid_parlay(parlay):
            combined_odds = calculate_combined_odds(parlay)
            american_odds = convert_decimal_to_american(combined_odds)
            implied_probability = calculate_implied_probability(combined_odds)
            return {
                'parlay': parlay,
                'odds': american_odds,
                'implied_probability': implied_probability
            }

    return None


def insert_to_db(collection, data):
    collection.delete_many({})
    document = {
        "data": data
    }
    collection.insert_one(document)

# Function to replace Unicode minus sign with ASCII hyphen
def fix_odds(data):
    for item in data:
        item['odds'] = item['odds'].replace('−', '-')
    return data

def fix_unicode_minus(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = value.replace('−', '-')
            elif isinstance(value, (dict, list)):
                fix_unicode_minus(value)
    elif isinstance(data, list):
        for item in data:
            fix_unicode_minus(item)
    return data


# Load environment variables from .env file
load_dotenv()

# Retrieve the MongoDB Atlas URI from the environment
uri = os.getenv("MONGODB_URI")

# Create a MongoClient instance
client = MongoClient(uri, tlsCAFile=certifi.where())

db = client["nba"]
collection = db['dailyplayerodds']

hardline9_collection = db['hardline9']
lesslegs_collection = db['lesslegs']
morelegs_collection = db['morelegs']
goldengoose_collection = db['goldengoose']


daily_player_odds = fetch_daily_player_odds(collection)
add_player_ids_and_stat_abrv(db, daily_player_odds)

player_game_collection = get_data_from_db('playersgamelog')

hardline_results = process_hardline_data(daily_player_odds, player_game_collection)
top_9_scores = get_top_consistent_players(hardline_results)

top_9_scores = fix_odds(top_9_scores)

insert_to_db(hardline9_collection, top_9_scores)

print(top_9_scores)

# # Query player games from DB
results = process_daily_player_odds(daily_player_odds)


top_50_consistent_scores = get_top_consistent_scores(results, top_n=50)

for idx, leg in enumerate(top_50_consistent_scores):
    leg['id'] = idx

less_legs_parlays = create_parlays(top_50_consistent_scores)
less_legs_parlays = fix_unicode_minus(less_legs_parlays)
insert_to_db(lesslegs_collection, less_legs_parlays)
for parlay in less_legs_parlays:
    print(parlay)
    print(f"Parlay Odds: {parlay['odds']}, Implied Probability: {parlay['implied_probability']:.2%}")
    for leg in parlay['parlay']:
        print(leg)


more_legs_parlays = create_more_parlays(top_50_consistent_scores)
more_legs_parlays = fix_unicode_minus(more_legs_parlays)
insert_to_db(morelegs_collection, more_legs_parlays)
for parlay in more_legs_parlays:
    print(f"Parlay Odds: {parlay['odds']}, Implied Probability: {parlay['implied_probability']:.2%}")
    for leg in parlay['parlay']:
        print(leg)

top_50_jackpot_scores = get_top_consistent_jackpot_scores(results, top_n=50)

top_4_parlay = get_golden_goose_parlay(top_50_jackpot_scores)
insert_to_db(goldengoose_collection, top_4_parlay)

if top_4_parlay:
    print(f"Parlay Odds: {top_4_parlay['odds']}, Implied Probability: {top_4_parlay['implied_probability']:.2%}")
    for leg in top_4_parlay['parlay']:
        print(leg)
else:
    print("No valid parlay found with 4 legs.")


# collection = db["hardlinedailyprops"]
# # Clear existing data from the collection
# collection.delete_many({})
# # Insert the new data into the collection
# collection.insert_many(top_9_scores)


                