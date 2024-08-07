from nba_api.stats.endpoints import PlayerNextNGames, PlayerGameLog, CommonPlayerInfo
from nba_api.stats.library.parameters import SeasonAll
from nba_api.stats.endpoints import commonallplayers
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import playergamelog

from datetime import datetime, timezone
from flask import Flask, jsonify, request, render_template, session
from flask_cors import CORS
from flask_session import Session 
from pymongo import MongoClient, DESCENDING
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from bcrypt import hashpw, gensalt, checkpw
from flask_mail import Mail, Message
import pandas as pd
import json
import os
import certifi
import requests
import html
import string
import secrets
from datetime import datetime, timedelta, timezone 
from apscheduler.schedulers.background import BackgroundScheduler
from bson.json_util import dumps 

app = Flask(__name__)
CORS(app)

app.secret_key = 'your_secret_key'  
# Configure session to use filesystem (instead of signed cookies)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

@app.route('/')
def index():
    return render_template('index.html')



API_KEY = os.getenv("ODDS_API_KEY")

REGIONS = 'us,uk,eu,au'
MARKETS = 'h2h,spreads,totals'
ALTERNATE_MARKETS = 'alternate_spreads,alternate_totals'
ODDS_FORMAT = 'decimal'
DATE_FORMAT = 'iso'

DESIRED_BOOKMAKERS = [
    'betonlineag', 'bovada', 'draftkings', 'fanduel', 
    'betmgm', 'mybookieag', 'betus', 'espnbet', 'betparx', 'hardrockbet',
    'betrivers', 'pointsbetus', 'pinnacle', 'bet365'
]





#----------- SCHEDULED JOBS -------------#

# def scheduled_job():
#     print("This job runs periodically")

# # Initialize the scheduler only once
# scheduler = BackgroundScheduler()

# # Add the job only if it's not already registered
# if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
#     scheduler.add_job(scheduled_job, 'interval', minutes=1)
#     scheduler.start()
#     print("Scheduler started.")





# ------------------------ USER SIGN IN / SIGN UP --------------------------
# Flask-Mail configuration (UPDATE FOR ACTUAL PRODUCTION using our domain smtp!!)
app.config['MAIL_SERVER'] = 'smtp.ethereal.email'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'candelario51@ethereal.email'
app.config['MAIL_PASSWORD'] = '9S62KdZPVwZS8h27Bb'

mail = Mail(app)

def send_verification_email(email, token):
    msg = Message('Email Verification', sender='candelario51@ethereal.email', recipients=[email])
    msg.html = f"""\
    <html>
      <body>
        <p>Click the link below to verify your email address:</p>
        <a href="https://nbadev-562335df253a.herokuapp.com/verify_email?token={token}">Verify Email</a>
      </body>
    </html>
    """
    mail.send(msg)

# Function to generate unique token
def generate_token():
    return os.urandom(24).hex()

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get('email').lower()
    password = data.get('password')

    # Check if the user already exists or is pending
    existing_users = db.users.find({'email': email})

    # Iterate over all matching users
    for existing_user in existing_users:
        if existing_user['status'] == 'active':
            # If an active user with the same email exists, return an error response
            return jsonify({'error': 'User already exists'}), 400
        elif existing_user['status'] == 'pending':
            # If a pending user with the same email exists, you may handle it differently
            # For example, you can allow multiple pending accounts until verification is completed
            pass

    # Generate verification token
    token = generate_token()

    # Store user data and verification token in the database with pending status
    user_data = {'email': email, 'password': hashpw(password.encode('utf-8'), gensalt()), 'verification_token': token, 'status': 'pending'}
    db.users.insert_one(user_data)

    # Send verification email
    send_verification_email(email, token)

    return jsonify({'message': 'User signed up successfully. Check your email for verification instructions.'}), 201

@app.route('/verify_email', methods=['GET'])
def verify_email():
    token = request.args.get('token')

    # Find the user with the provided token
    user = db.users.find_one({'verification_token': token})

    if not user:
        return "Invalid or expired token. Please request a new verification email."

    # Check if the token has already been used
    if user.get('status') == 'active':
        return "Email already verified. You can log in to your account."

    # Mark the token as used to prevent multiple uses
    db.users.update_one({'_id': user['_id']}, {'$set': {'status': 'active', 'verification_token': None}})

    return "Email verified successfully. You can now log in to your account."


@app.route('/signin', methods=['POST'])
def signin():
    data = request.json
    email = data.get('email').lower()
    password = data.get('password')

    # Find all users with the provided email
    users = db.users.find({'email': email})

    # Initialize a variable to track if a user with active status is found
    active_user_found = False

    # Iterate over all users with the provided email
    for user in users:
        # Check if the user's status is active
        if user.get('status') == 'active':
            # Retrieve the hashed password from the user data
            hashed_password = user.get('password')

            # Check if the provided password matches the hashed password
            if checkpw(password.encode('utf-8'), hashed_password):
                active_user_found = True
                break  # Exit the loop if an active user with matching password is found

    # If no active user with matching password is found, return an error
    if not active_user_found:
        return jsonify({'error': 'Invalid email or password'}), 401

    # If an active user with matching password is found, return a success message
    return jsonify({'message': 'Sign in successful'}), 200

@app.route('/changepassword', methods=['POST'])
def changepassword():
    data = request.json
    email = data.get('email').lower()
    old_password = data.get('old_password')
    new_password = data.get('new_password')

    # Find all users with the provided email and active status
    users = db.users.find({'email': email, 'status': 'active'})

    # Initialize a variable to track if a user with matching email and old password is found
    user_found = False

    # Iterate over all users with the provided email and active status
    for user in users:
        # Retrieve the hashed password from the user data
        hashed_password = user.get('password')

        # Compare the hashed old password with the hashed password stored in the database
        if checkpw(old_password.encode('utf-8'), hashed_password):
            # Hash the new password
            hashed_new_password = hashpw(new_password.encode('utf-8'), gensalt())

            # Update the password in the database
            db.users.update_one({'_id': user['_id']}, {'$set': {'password': hashed_new_password}})
            user_found = True
            print("Password updated successfully")
            break  # Exit the loop if a matching user is found and password is updated

    # If no user with matching email and old password is found, return an error
    if not user_found:
        return jsonify({'error': 'Invalid email or old password'}), 401

    return jsonify({'message': 'Password changed successfully'}), 200


   
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


def get_players_by_ids(player_ids):
    players_collection = get_data_from_db('players')


    # Extract player data
    player_data = []
    for player in players_collection:
        player_data.append({
            'player_id': player['id'],
            'player_name': player['full_name'],
            'last_game': player['last_game']
        })

    return player_data

   
# -------------------- GET ACTIVE PLAYERS --------------------------
@app.route('/nba_get_active_players', methods=['GET'])
def nba_get_active_players():
    try:
        # Get player data from the dailyplayers collection
        daily_players_cursor = get_data_from_collection('dailyplayers')
        
        # Access the 'players' key directly and iterate over the list of players
        players_data = daily_players_cursor[0].get('players', [])  # Assuming only one document in the cursor
        
        sanitized_players = []
        for player in players_data:
            player_name = player.get('player_name', '')
            player_id = player.get('player_id', '')
            if player_name and player_id:
                sanitized_player = {
                    'full_name': sanitize_string(player_name),
                    'id': sanitize_string(player_id),
                }
                sanitized_players.append(sanitized_player)

        # Convert the sanitized data to JSON format
        return jsonify(sanitized_players), 200

    except Exception as e:
        # Send error response
        error_message = {'error': str(e)}
        return jsonify(error_message), 500

# -------------------- GET PLAYER GAME DATA --------------------------
def getting_player_over_under_values(player_game_collection, player_id, stat_abbreviation, prop_value):
    # Filter player game data based on player ID
    player_game_data = [game for game in player_game_collection if game['player_id'] == player_id]
    
    # Convert int64 GAME_DATE to datetime.datetime if needed 
    # (This is bizarre) Random new game different date format fix
    for game in player_game_data:
        if isinstance(game['GAME_DATE'], pd._libs.tslibs.timestamps.Timestamp):
            game['GAME_DATE'] = game['GAME_DATE'].to_pydatetime()
        elif isinstance(game['GAME_DATE'], int):
            game['GAME_DATE'] = datetime.utcfromtimestamp(game['GAME_DATE'] / 1000.0)  # Assuming Unix timestamp is in milliseconds
    
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

# Grab the counts of over unders for the matchup
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

# Generates the consistency response
def get_consistency_response(combined_response, consistency_score, over_under):
    # Extract relevant data from combined_response based on over_under
    if over_under == "Over":
        hits_season = f"{combined_response.get('over_count', 0)} / {combined_response.get('total_games', 1)}"
        hits_five = f"{combined_response.get('over_count_recent_5', 0)} / 5"
        fouls = combined_response.get('avg_fouls', 0)
        minutes = combined_response.get('avg_minutes_over', 0)
    elif over_under == "Under":
        hits_season = f"{combined_response.get('under_count', 0)} / {combined_response.get('total_games', 1)}"
        hits_five = f"{combined_response.get('under_count_recent_5', 0)} / 5"
        fouls = combined_response.get('avg_fouls', 0)
        minutes = combined_response.get('avg_minutes_under', 0)
    else:
        raise ValueError("Invalid over_under value")
    
    # Determine consistency rating and color class
    consistency_rating = ''
    if over_under == 'Over':
        if consistency_score >= 6.5:
            if fouls <= 2.5:
                consistency_rating = 'CONSISTENT'
            else:
                consistency_rating = 'NEUTRAL'
        else:
            consistency_rating = 'INCONSISTENT'
    elif over_under == 'Under':
        if consistency_score >= 6.5:
            consistency_rating = 'CONSISTENT'
        else:
            consistency_rating = 'INCONSISTENT'
    
    # Create JSON response
    response = {
        "overall_score": consistency_score,
        "consistency_rating": consistency_rating,
        'avg_fouls': fouls,
        "minutes": minutes,
        "hits_season": hits_season,
        "hits_five": hits_five
    }
    
    return response
      
@app.route('/nba_get_player_game_data', methods=['GET'])
def nba_get_player_game_data():
    try:
        player_game_data = []
        # Extract player ID from the query parameters
        player_id = int(request.args.get('playerId'))
        stat = request.args.get('stat')
        prop_value = int(request.args.get('propValue'))
        over_under = request.args.get('overUnder')
        
        # Define a dictionary to map stat values to their abbreviations
        stat_abbreviations = {
            'Points': 'PTS',
            'Assists': 'AST',
            '3 Pointers': 'FG3M',
            'Rebounds': 'REB',
            'Blocks': 'BLK',
            'Steals': 'STL'
        }
        
        # Convert the incoming stat to its abbreviation using the dictionary
        if stat in stat_abbreviations:
            stat_abbreviation = stat_abbreviations[stat]
        else:
            raise ValueError(f"Invalid stat: {stat}")
        
         # Query player games from DB
        player_game_collection = get_data_from_db('playersgamelog')

        # Call the function to get player values
        response_data = getting_player_over_under_values(player_game_collection, player_id, stat_abbreviation, prop_value)
        
        # Query player matchups from DB
        player_matchup_collection = get_data_from_db('playersmatchuplog')
        
        response_matchup_data = getting_player_matchup_values(player_id, stat_abbreviation, prop_value, player_matchup_collection)

        # Merge the two response dictionaries
        combined_response = {**response_data, **response_matchup_data}
        
        consistency_score = get_consistency_score(combined_response, over_under)
        
        consistency_response = get_consistency_response(combined_response, consistency_score, over_under)
        
        return jsonify(consistency_response), 200
    except Exception as e:
        # Send error response
        error_message = {'error': str(e)}
        return jsonify(error_message), 500

@app.route('/get_game_times', methods=['GET'])
def get_game_times():
    try:
        # Query game times from the 'dailyschedule' collection
        game_times = db.dailyschedule.distinct("Schedule.game_time")
        
        # Convert the game times to a list
        game_times_list = list(game_times)
        
        # Serialize the game times to JSON
        game_times_json = json.dumps({"game_times": game_times_list})
        
        return game_times_json, 200
    except Exception as e:
        # Send error response
        error_message = {'error': str(e)}
        return jsonify(error_message), 500

# -------------------- GET MONEYLINEDATA --------------------------
@app.route('/nba_get_moneylines', methods=['GET'])
def nba_get_moneylines():
    try:
        # Query moneylines from DB
        moneyline_collection = get_data_from_db('moneylines')
        
        # Serialize MongoDB documents to JSON
        moneylines_json = dumps(moneyline_collection)
        
        return moneylines_json, 200
    except Exception as e:
        # Send error response
        error_message = {'error': str(e)}
        return jsonify(error_message), 500

@app.route('/hardline9', methods=['GET'])
def get_hardline9():
    hardline9 = get_data_from_db_general('hardline9')
    return jsonify(hardline9)

@app.route('/less_legs', methods=['GET'])
def get_less_legs():
    less_legs = get_data_from_db_general('lesslegs')
    return jsonify(less_legs)

@app.route('/more_legs', methods=['GET'])
def get_more_legs():
    more_legs = get_data_from_db_general('morelegs')
    return jsonify(more_legs)

@app.route('/golden_goose', methods=['GET'])
def get_golden_goose():
    golden_goose  = get_data_from_db_general('goldengoose')
    return jsonify(golden_goose)





        
        
#-------- ARBITRAGE ----------
@app.route('/get_arbitrage', methods=['GET'])
def get_arbitrage():
    arbitrage  = get_data_from_db_general('arbitrage')
    return jsonify(arbitrage)


def get_in_season_sports():
    try:
        sports_response = requests.get(
            'https://api.the-odds-api.com/v4/sports/',
            params={
                'apiKey': API_KEY
            }
        )

        sports_response.raise_for_status()  # Raise an HTTPError for bad responses

        sports_json = sports_response.json()
        sports = [
            sport['key'] for sport in sports_json
            if 'football' not in sport['key'] and not sport['key'].endswith('_winner')
        ]
        return sports

    except Exception as e:
        print(f'An error occurred: {e}')
        return None

def fetch_odds_for_sports(sports):
    all_events = []
    for sport in sports:
        try:
            odds_response = requests.get(
                f'https://api.the-odds-api.com/v4/sports/{sport}/odds',
                params={
                    'api_key': API_KEY,
                    'regions': REGIONS,
                    'markets': MARKETS,
                    'oddsFormat': ODDS_FORMAT,
                    'dateFormat': DATE_FORMAT,
                }
            )

            if odds_response.status_code != 200:
                print(f'Failed to get odds for {sport}: status_code {odds_response.status_code}, response body {odds_response.text}')
                continue

            odds_json = odds_response.json()
            for event in odds_json:
                event_id = event['id']
                sport_key = event['sport_key']
                home_team = event['home_team']
                away_team = event['away_team']
                commence_time = datetime.fromisoformat(event['commence_time'][:-1]).replace(tzinfo=timezone.utc)

                # Filter out events that have already commenced
                if commence_time < datetime.now(timezone.utc):
                    continue

                event_data = {
                    'event_id': event_id,
                    'sport_key': sport_key,
                    'home_team': home_team,
                    'away_team': away_team,
                    'odds': {}
                }

                for bookmaker in event['bookmakers']:
                    if bookmaker['key'] in DESIRED_BOOKMAKERS:
                        event_data['odds'][bookmaker['title']] = bookmaker['markets']

                # Fetch alternate markets
                # alternate_markets = fetch_alternate_markets(event_id, sport)
                # if alternate_markets:
                #     for bookmaker in alternate_markets['bookmakers']:
                #         if bookmaker['key'] in DESIRED_BOOKMAKERS:
                #             if bookmaker['title'] in event_data['odds']:
                #                 event_data['odds'][bookmaker['title']].extend(bookmaker['markets'])
                #             else:
                #                 event_data['odds'][bookmaker['title']] = bookmaker['markets']

                all_events.append(event_data)

        except Exception as e:
            print(f'An error occurred while processing sport {sport}: {e}')

    return all_events, odds_response.headers.get('x-requests-remaining', 'N/A'), odds_response.headers.get('x-requests-used', 'N/A')

def find_arbitrage_opportunities(events):
    arbitrage_opportunities = []

    for event in events:
        best_odds = {'home': None, 'away': None, 'draw': None}
        best_bookmakers = {'home': '', 'away': '', 'draw': ''}

        for bookmaker, markets in event['odds'].items():
            for market in markets:
                if market['key'] == 'h2h':
                    for outcome in market['outcomes']:
                        if outcome['name'] == event['home_team']:
                            if best_odds['home'] is None or outcome['price'] > best_odds['home']:
                                best_odds['home'] = outcome['price']
                                best_bookmakers['home'] = bookmaker
                        elif outcome['name'] == event['away_team']:
                            if best_odds['away'] is None or outcome['price'] > best_odds['away']:
                                best_odds['away'] = outcome['price']
                                best_bookmakers['away'] = bookmaker
                        elif outcome['name'].lower() == 'draw':
                            if best_odds['draw'] is None or outcome['price'] > best_odds['draw']:
                                best_odds['draw'] = outcome['price']
                                best_bookmakers['draw'] = bookmaker

        if best_odds['home'] is not None and best_odds['away'] is not None:
            if best_odds['draw'] is not None:
                sum_inverses = (1 / best_odds['home']) + (1 / best_odds['away']) + (1 / best_odds['draw'])
            else:
                sum_inverses = (1 / best_odds['home']) + (1 / best_odds['away'])

            if sum_inverses < 1:
                # Calculate stakes
                total_stake = 10000
                home_stake = total_stake / best_odds['home'] / sum_inverses
                away_stake = total_stake / best_odds['away'] / sum_inverses
                if best_odds['draw'] is not None:
                    draw_stake = total_stake / best_odds['draw'] / sum_inverses
                    profit = total_stake * (1 - sum_inverses)
                    arbitrage_opportunities.append({
                        'event_id': event['event_id'],
                        'sport_key': event['sport_key'],
                        'home_team': event['home_team'],
                        'away_team': event['away_team'],
                        'best_odds': best_odds,
                        'best_bookmakers': best_bookmakers,
                        'sum_inverses': sum_inverses,
                        'home_stake': home_stake,
                        'away_stake': away_stake,
                        'draw_stake': draw_stake,
                        'profit': profit
                    })
                else:
                    profit = total_stake * (1 - sum_inverses)
                    arbitrage_opportunities.append({
                        'event_id': event['event_id'],
                        'sport_key': event['sport_key'],
                        'home_team': event['home_team'],
                        'away_team': event['away_team'],
                        'best_odds': best_odds,
                        'best_bookmakers': best_bookmakers,
                        'sum_inverses': sum_inverses,
                        'home_stake': home_stake,
                        'away_stake': away_stake,
                        'profit': profit
                    })

        # Check for arbitrage in spreads and totals, including alternate markets
        for market_key in ['spreads', 'totals']:
            market_odds = {}
            for bookmaker, markets in event['odds'].items():
                for market in markets:
                    if market['key'] == market_key:
                        for outcome in market['outcomes']:
                            point = outcome.get('point', None)
                            if point is not None:
                                if point not in market_odds:
                                    market_odds[point] = {'over': None, 'under': None}
                                if outcome['name'].lower() == 'over':
                                    if market_odds[point]['over'] is None or outcome['price'] > market_odds[point]['over']:
                                        market_odds[point]['over'] = outcome['price']
                                elif outcome['name'].lower() == 'under':
                                    if market_odds[point]['under'] is None or outcome['price'] > market_odds[point]['under']:
                                        market_odds[point]['under'] = outcome['price']
                                      

            for point, odds in market_odds.items():
                if odds['over'] is not None and odds['under'] is not None:
                    sum_inverses = (1 / odds['over']) + (1 / odds['under'])
                    if sum_inverses < 1:
                        # Calculate stakes
                        total_stake = 10000
                        over_stake = total_stake / odds['over'] / sum_inverses
                        under_stake = total_stake / odds['under'] / sum_inverses
                        profit = total_stake * (1 - sum_inverses)
                        arbitrage_opportunities.append({
                            'event_id': event['event_id'],
                            'sport_key': event['sport_key'],
                            'home_team': event['home_team'],
                            'away_team': event['away_team'],
                            'market': market_key,
                            'point': point,
                            'best_odds': odds,
                            'sum_inverses': sum_inverses,
                            'over_stake': over_stake,
                            'under_stake': under_stake,
                            'profit': profit
                        })

    # Sort by profit in descending order and take the top 5
    arbitrage_opportunities = sorted(arbitrage_opportunities, key=lambda x: x['profit'], reverse=True)[:5]

    return arbitrage_opportunities

def save_arbitrage_opportunities(arbitrage_opportunities):
    collection = db['arbitrage']

    # Delete existing documents if any
    collection.delete_many({})

    # Create document
    document = {}

    # Check if there are arbitrage opportunities
    if arbitrage_opportunities:
        document['arbitrage'] = True
        document['arbitrage_opportunities'] = arbitrage_opportunities
    else:
        document['arbitrage'] = False
        document['arbitrage_opportunities'] = []

    # Insert document
    collection.insert_one(document)
    print("Document saved successfully.")

def find_arbitrages():
    
    in_season_sports = get_in_season_sports()

    if in_season_sports:
        print(f"In-season sports: {in_season_sports}")
        filtered_events, remaining_rq, used_rq = fetch_odds_for_sports(in_season_sports)
        print("remaining:", remaining_rq)
        print("used:", used_rq)

        arbitrage_opportunities = find_arbitrage_opportunities(filtered_events)
        save_arbitrage_opportunities(arbitrage_opportunities)
    else:
        print("Failed to retrieve in-season sports.")


@app.route('/fetch_arbitrages', methods=['POST'])
def fetch_arbitrages():
    find_arbitrages()
    return jsonify({'message': 'Arbitrages fetched successfully'})

@app.route('/start_countdown', methods=['POST'])
def start_countdown():
    # Calculate the end_timer timestamp using timezone-aware datetime
    end_timer = datetime.now(timezone.utc) + timedelta(minutes=1)
    # Store the end_timer and button_used flag in the session
    session['end_timer'] = end_timer.isoformat()
    session['button_used'] = True
    
    # Return the end_timer to the client
    return jsonify({'end_timer': end_timer.isoformat(), 'button_used': False})

@app.route('/check_timer', methods=['GET'])
def check_timer():
    # Check the current state of the timer using session
    if 'button_used' in session:
        # Check if the timer has expired
        if datetime.now(timezone.utc) > datetime.fromisoformat(session['end_timer']):
            # Reset the session if the timer has expired
            session.pop('end_timer', None)
            session.pop('button_used', None)
            return jsonify({'button_used': False})
        else:
            # Return the existing end_timer and button_used state
            return jsonify({'end_timer': session['end_timer'], 'button_used': True})
    else:
        # If no timer is found in the session, return button_used as False
        return jsonify({'button_used': False})


# ------ DB STUFF ----- #    
def get_data_from_collection(collection_name):
    collection = db[collection_name]
    return collection.find()

def get_data_from_db_general(collection_name):
    collection = db[collection_name]
    data = list(collection.find())
    for entry in data:
        entry['_id'] = str(entry['_id'])
    return data


# Get DB based on collection   
def get_data_from_db(collection_name):
    collection = db[collection_name]  # corrected the string formatting
    data = collection.find()
    data_list = list(data)  # Convert cursor to list for JSON serialization
    return data_list

# Sanatize
def sanitize_string(value):
    """Sanitize string to prevent XSS attacks."""
    if isinstance(value, str):
        # Escape special characters for strings
        return html.escape(value, quote=False)
    else:
        # If value is not a string, return it as is
        return value
    
    
# Load environment variables from .env file
load_dotenv()

# Retrieve the MongoDB Atlas URI from the environment
uri = os.getenv("MONGODB_URI") # currently changed from end user for post of timestamp

# Create a MongoClient instance
client = MongoClient(uri, tlsCAFile=certifi.where())

db = client["nba"]

if __name__ == '__main__':
    app.run(debug=True, port=8000)  # Run on port 8000 instead of the default 5000
