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
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')




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


   
# -------------------- GET ACTIVE PLAYERS --------------------------
@app.route('/nba_get_active_players', methods=['GET'])
def nba_get_active_players():
    try:
        # Get all active players from the database
        active_players = get_data_from_db('players')
        
        if not active_players:
            print("active_players is empty")


        # Sanitize player data
        sanitized_players = []
        for player in active_players:
            try:
                sanitized_player = {
                    'full_name': sanitize_string(player.get('full_name', '')),
                    'id': sanitize_string(player.get('id', '')),
                    'last_game': sanitize_string(player.get('last_game', ''))
                }
                sanitized_players.append(sanitized_player)
            except Exception as e:
                print(f"Error sanitizing player: {e}")

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
        
        # Get the most recent 7 games
        recent_games = player_game_data[:5]
        
        # Initialize counters for all games and recent 7 games
        total_games = len(player_game_data)
        recent_over_count = 0
        recent_under_count = 0
        over_count = 0
        under_count = 0
        
        # Check over/under condition for all games
        for game in player_game_data:
            if over_under == 'Over':
                if game[stat_abbreviation] >= prop_value:
                    over_count += 1
            elif over_under == 'Under':
                if game[stat_abbreviation] < prop_value:
                    under_count += 1
        
        # Check over/under condition for recent 7 games
        for game in recent_games:
            if over_under == 'Over':
                if game[stat_abbreviation] >= prop_value:
                    recent_over_count += 1
            elif over_under == 'Under':
                if game[stat_abbreviation] < prop_value:
                    recent_under_count += 1
        
        # Create response data
        response_data = {
            'total_games': total_games,
            'over_count': over_count,
            'under_count': under_count,
            'recent_over_count': recent_over_count,
            'recent_under_count': recent_under_count
        }
        
        return jsonify(response_data), 200
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
    if isinstance(value, str):
        # Escape special characters for strings
        return html.escape(value, quote=False)
    else:
        # If value is not a string, return it as is
        return value
    
    
# Load environment variables from .env file
load_dotenv()

# Retrieve the MongoDB Atlas URI from the environment
uri = os.getenv("MONGODB_URI_ENDUSER")

# Create a MongoClient instance
client = MongoClient(uri, tlsCAFile=certifi.where())

db = client["nba"]

if __name__ == '__main__':
    app.run(debug=True)
