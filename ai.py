from nba_api.stats.endpoints.teamestimatedmetrics import TeamEstimatedMetrics
from nba_api.stats.endpoints import LeagueGameFinder
import pandas as pd
from sklearn.linear_model import LinearRegression
from nba_api.stats.endpoints import ScoreboardV2
from datetime import datetime

from pymongo import MongoClient, DESCENDING
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

import json
import json
import os
import certifi
import requests
import pandas as pd
import logging

############# DATA PREPROCESSING FUNCTIONS #################

# Grabs matchups and organizes them into a structure
def get_todays_matchups():
    try:
        # Get today's date
        today = datetime.today().strftime('%Y-%m-%d')

        # Define the parameters
        params = {
            'day_offset': 0,
            'game_date': today,
            'league_id': '00'  # NBA league ID
        }

        # Create an instance of the ScoreboardV2 class with the parameters
        scoreboard = ScoreboardV2(**params)

        # Call the API and get the response
        response = scoreboard.get_json()

        # Parse the JSON response
        data = json.loads(response)

        # Extract relevant data
        game_header_data = data['resultSets'][0]['rowSet']
        game_header_columns = data['resultSets'][0]['headers']
        game_header_df = pd.DataFrame(game_header_data, columns=game_header_columns)

        line_score_data = data['resultSets'][1]['rowSet']
        line_score_columns = data['resultSets'][1]['headers']
        line_score_df = pd.DataFrame(line_score_data, columns=line_score_columns)

        # Get unique game IDs
        unique_game_ids = line_score_df['GAME_ID'].unique()

        # Initialize a list to store matchup information
        matchups = []

        # Loop through each unique game ID
        for game_id in unique_game_ids:
            # Get the rows corresponding to the current game ID
            game_rows = line_score_df[line_score_df['GAME_ID'] == game_id]

            # Extract team information for the current game
            team_info = game_rows[['TEAM_ID', 'TEAM_NAME']].values.tolist()

            # Get home and away team IDs from GameHeader
            game_header_info = game_header_df[game_header_df['GAME_ID'] == game_id]
            home_team_id = game_header_info['HOME_TEAM_ID'].values[0]
            visitor_team_id = game_header_info['VISITOR_TEAM_ID'].values[0]

            # Determine home and away teams and mark them as Home or Away
            for team in team_info:
                if team[0] == home_team_id:
                    team.append(1)
                elif team[0] == visitor_team_id:
                    team.append(0)

            # Append matchup information to the list
            matchups.append((game_id, team_info))
            
            
        return matchups
        
    except Exception as e:
        print("Error:", e)

# Creates and returns a mapping from team_id to whether they are home or away 
def create_team_home_away_map(matchup_data):
    team_home_away_map = {}
    for matchup in matchup_data:
        team1_id = matchup[1][0][0]
        team1_home_away = matchup[1][0][2]
        team2_id = matchup[1][1][0]
        team2_home_away = matchup[1][1][2]
        team_home_away_map[team1_id] = team1_home_away
        team_home_away_map[team2_id] = team2_home_away
    return team_home_away_map

# Gets all the game ids from todays matchup and returns as tupled by matchup list
def get_todays_team_ids(matchups):
    # Initialize an empty list to store team IDs
    team_ids = []

    for matchup in matchups:
        print(matchup[1])
        # Extract team IDs from the matchup tuple
        team1_id = matchup[1][0][0]
        print("TEAM ID 1" ,team1_id)
        team2_id = matchup[1][1][0]
        print("TEAM ID 2" ,team2_id)
        
        # Append the team IDs as a tuple to the team_ids list
        team_ids.append((team1_id, team2_id))

    return team_ids

# Gets regular season data based on team id and returns
def get_regular_season_data_per_team(team_id):
    try:
        # Define parameters for game search
        params = {
            "team_id_nullable": team_id,
            "player_or_team_abbreviation": "T",  # T for team
        }

        # Create LeagueGameFinder instance with parameters
        lgf = LeagueGameFinder(**params)

        # Retrieve data
        team_game_data = lgf.get_data_frames()[0]

        # Filter data for the regular season (assuming season ID is 22023)
        regular_season_data = team_game_data[team_game_data['SEASON_ID'] == '22023']

        # Filter out games from the offseason (October to April)
        regular_season_data = regular_season_data[
            (regular_season_data['GAME_DATE'] >= '2023-10-01') & 
            (regular_season_data['GAME_DATE'] <= '2024-04-30')
        ]

        team_id_and_game_ids = []
        # Extract game IDs
        game_ids = regular_season_data['GAME_ID'].tolist()
        return game_ids

    except Exception as e:
        print("Error:", e)
        return None, None

# Fetches regular season game statistics for a given team ID from the database
# and returns a dictionary containing game statistics keyed by game ID
def get_team_game_stats(team_id, db):
    game_ids = get_regular_season_data_per_team(team_id)
    game_stats = {}

    # Fetch team ranking data from the database
    # team_ranks_data = {}
    # for rank_data in db.teamsranks.find():
    #     team_ranks_data[rank_data["TEAM_ID"]] = {
    #         "W_PCT": rank_data["W_PCT"],
    #         "E_OFF_RATING": rank_data["E_OFF_RATING"],
    #         "E_DEF_RATING": rank_data["E_DEF_RATING"],
    #         "E_NET_RATING": rank_data["E_NET_RATING"],
    #         "E_AST_RATIO": rank_data["E_AST_RATIO"],
    #         "E_OREB_PCT": rank_data["E_OREB_PCT"],
    #         "E_DREB_PCT": rank_data["E_DREB_PCT"],
    #         "E_REB_PCT": rank_data["E_REB_PCT"],
    #         "E_TM_TOV_PCT": rank_data["E_TM_TOV_PCT"],
    #         "E_PACE": rank_data["E_PACE"]
    #     }

    # Process data for the team
    for game_id in game_ids:
        game_data = db.games.find_one({"game_id": game_id})
        if game_data:
            # Extract team statistics from the game data
            team_stats = {}
            for team_info in game_data['teams']:
                team_id = team_info['team_id']
                team_stats[team_id] = team_info['statistics']

            # # Merge team statistics with team ranking data
            # for team_id, stats in team_stats.items():
            #     # Check if ranking data is available for the team
            #     if team_id in team_ranks_data:
            #         # Merge statistics with ranking data
            #         stats.update(team_ranks_data[team_id])

            # Add the game stats to the dictionary
            game_stats[game_id] = team_stats
        else:
            print(f"No data found for game ID: {game_id}")

    return game_stats

# Organizes matchup data for each team and returns a df, each row is a game with matchup stats
def prepare_matchup_data(team_game_stats, team_id):
    flattened_rows = []

    # Iterate over each game in the dictionary
    for game_id, game_data in team_game_stats.items():
        # Extract team1 and team2 data
        team1_stats = game_data[team_id]
        opponent_id = [t_id for t_id in game_data if t_id != team_id][0]
        team2_stats = game_data[opponent_id]

        # Create row for the matchup
        matchup_row = {'game_id': game_id}
        
        # Add team 1 stats with '_team' suffix
        for key, value in team1_stats.items():
            matchup_row[key + '_team'] = value

        # Add team 2 stats with '_opp' suffix
        for key, value in team2_stats.items():
            matchup_row[key + '_opp'] = value
        
        flattened_rows.append(matchup_row)

    # Convert the list of dictionaries into a DataFrame
    matchup_df = pd.DataFrame(flattened_rows)
    
    return matchup_df

# Renames columns for input data for the model
def rename_columns(team_mean_stats, team_number):
    # Convert Series to DataFrame
    team_mean_stats_df = team_mean_stats.to_frame().T
    
    # Define column name mappings
    column_mappings = {
        'WL_team': f'team{team_number}_WL',
        'HOMEORAWAY_team': f'team{team_number}_HOMEORAWAY',
        'FGM_team': f'team{team_number}_FGM',
        'FGA_team': f'team{team_number}_FGA',
        'FG_PCT_team': f'team{team_number}_FG_PCT',
        'FG3M_team': f'team{team_number}_FG3M',
        'FG3A_team': f'team{team_number}_FG3A',
        'FG3_PCT_team': f'team{team_number}_FG3_PCT',
        'FTM_team': f'team{team_number}_FTM',
        'FTA_team': f'team{team_number}_FTA',
        'FT_PCT_team': f'team{team_number}_FT_PCT',
        'OREB_team': f'team{team_number}_OREB',
        'DREB_team': f'team{team_number}_DREB',
        'REB_team': f'team{team_number}_REB',
        'AST_team': f'team{team_number}_AST',
        'STL_team': f'team{team_number}_STL',
        'BLK_team': f'team{team_number}_BLK',
        'TOV_team': f'team{team_number}_TOV',
        'PF_team': f'team{team_number}_PF',
        'PLUS_MINUS_team': f'team{team_number}_PLUS_MINUS'
    }
    
    # Rename columns
    team_mean_stats_df.rename(columns=column_mappings, inplace=True)
    
    return team_mean_stats_df

# returns a df of all the nba_matchups this season from db
def get_all_season_matchups_into_df(db):
    collection = db['games']
    
    cursor = collection.find({})

    # Iterate over the cursor to access each document
    # Initialize lists to store data
    team1_data = []
    team2_data = []

# Iterate over the cursor to access each document
    for document in cursor:
        team1 = document['teams'][0]['statistics']
        team2 = document['teams'][1]['statistics']
        
        # Append team data to respective lists
        team1_data.append(team1)
        team2_data.append(team2)

    # Create DataFrames for each team's data
    team1_df = pd.DataFrame(team1_data)
    team2_df = pd.DataFrame(team2_data)

    # Combine the DataFrames into a single DataFrame representing game matchups
    game_matchups_df = pd.concat([team1_df, team2_df], axis=1)

    # Rename columns to differentiate between teams
    team1_cols = [f"team1_{col}" for col in team1_df.columns]
    team2_cols = [f"team2_{col}" for col in team2_df.columns]
    game_matchups_df.columns = team1_cols + team2_cols
    
    game_matchups_df.drop(columns=['team1_TEAM_NAME', 'team2_TEAM_NAME', 'team1_TEAM_ABBREVIATION', 'team2_TEAM_ABBREVIATION'], inplace=True)
    
    return game_matchups_df

# returns a readied input df to be fed into the Log reg model
def get_input_data_ready(team1_df, team2_df, team1_home_or_away, team2_home_or_away):
    # Drop unnecessary columns from team dataframes
    team1_df.drop(columns=['game_id', 'TEAM_NAME_team', 'TEAM_ABBREVIATION_team', 'TEAM_NAME_opp', 'TEAM_ABBREVIATION_opp'], inplace=True)
    team2_df.drop(columns=['game_id', 'TEAM_NAME_team', 'TEAM_ABBREVIATION_team', 'TEAM_NAME_opp', 'TEAM_ABBREVIATION_opp'], inplace=True)

    # Calculate the mean of the last 10 game stats for each team
    # Calculate mean performance metrics for each time frame
    team1_last_5_games_mean = team1_df.filter(regex='_team$').tail(5).mean()
    team1_last_10_games_mean = team1_df.filter(regex='_team$').tail(10).mean()
    team1_last_20_games_mean = team1_df.filter(regex='_team$').tail(20).mean()

    team2_last_5_games_mean = team2_df.filter(regex='_team$').tail(5).mean()
    team2_last_10_games_mean = team2_df.filter(regex='_team$').tail(10).mean()
    team2_last_20_games_mean = team2_df.filter(regex='_team$').tail(20).mean()

    # Calculate recent, medium-term, and long-term averages
    team1_mean_stats = (team1_last_5_games_mean + team1_last_10_games_mean + team1_last_20_games_mean) / 3
    team2_mean_stats = (team2_last_5_games_mean + team2_last_10_games_mean + team2_last_20_games_mean) / 3
    
    # Usage
    team1_mean_stats = rename_columns(team1_mean_stats, 1)
    team2_mean_stats = rename_columns(team2_mean_stats, 2)
    
    # Concatenate team1_mean_stats and team2_mean_stats
    input_data = pd.concat([team1_mean_stats, team2_mean_stats], axis=1)
    
    # Update team home/away indicators
    input_data['team1_HOMEORAWAY'] = team1_home_or_away
    input_data['team2_HOMEORAWAY'] = team2_home_or_away

    # Drop unnecessary columns from input data
    # Drop unnecessary columns from input data
    input_data.drop(columns=['team1_WL', 'team2_WL', 'team1_PLUS_MINUS', 'team2_PLUS_MINUS' ], inplace=True)
    
    return input_data

############### TESTING LOG REGRESSION MODEL FUNCTIONS ##################

# Evaluates feature coefficients 
def evaluate_features(X, model):
    # Get feature names
    feature_names = X.columns

    # Get coefficients
    coefficients = model.coef_[0]

    # Pair feature names with coefficients
    feature_coefficients = pd.DataFrame({'Feature': feature_names, 'Coefficient': coefficients})

    # Sort feature coefficients by absolute coefficient values
    feature_coefficients['Absolute Coefficient'] = feature_coefficients['Coefficient'].abs()
    feature_coefficients = feature_coefficients.sort_values(by='Absolute Coefficient', ascending=False)

    # Print feature coefficients
    print("Feature Coefficients:")
    print(feature_coefficients)

# Gets cross validation scores
def get_cv_scores(X_train_scaled, y_train, model):
    # Step 7: Perform cross-validation
    cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=10, scoring='accuracy')

    # Print cross-validation scores
    print("Cross-validation scores:", cv_scores)
    print("Mean accuracy:", cv_scores.mean())

# Evaluates accuracy, precision, etc.
def evaluate_model(X_test_scaled, y_test, model):
    # Step 10: Evaluate the model
    y_pred = model.predict(X_test_scaled)
    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]

    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    confusion_mat = confusion_matrix(y_test, y_pred)

    # Print metrics
    print("Accuracy:", accuracy)
    print("Precision:", precision)
    print("Recall:", recall)
    print("ROC AUC:", roc_auc)
    print("Confusion Matrix:")
    print(confusion_mat)


# Load environment variables from .env file
load_dotenv()

# Retrieve the MongoDB Atlas URI from the environment
uri = os.getenv("MONGODB_URI")
print(uri)

# Create a MongoClient instance
client = MongoClient(uri, tlsCAFile=certifi.where())
print(client)

# Get todays matchups
matchups = get_todays_matchups()
print(matchups)
todays_team_ids = get_todays_team_ids(matchups)
print(todays_team_ids)

todays_team_ids = todays_team_ids
print(todays_team_ids)

print(matchups)
team_home_away_map = create_team_home_away_map(matchups)

print(team_home_away_map)

# Initialize a dictionary to store regular season data for each team
all_regular_season_data_dict = {}

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
    # Connect to MongoDB
    db = client['nba']
    
    game_matchups_df = get_all_season_matchups_into_df(db)
    
    
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.preprocessing import MinMaxScaler
    from sklearn.linear_model import LogisticRegression
    import pandas as pd
    from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score, confusion_matrix

    # Delete previous moneyline entries
    db.moneylines.delete_many({})
    
    for team1_id, team2_id in todays_team_ids:

        # Get regular season game stats for team 1
        team1_game_stats = get_team_game_stats(team1_id, db)
        # Prepare team1 df
        team1_df = prepare_matchup_data(team1_game_stats, team1_id)
        
        team1_name = team1_df['TEAM_NAME_team'].iloc[0]
        team1_home_or_away = team_home_away_map.get(team1_id)

        # Get regular season game stats for team 2
        team2_game_stats = get_team_game_stats(team2_id, db)
        # Prepare team2 df
        team2_df = prepare_matchup_data(team2_game_stats, team2_id)
        
        team2_name = team2_df['TEAM_NAME_team'].iloc[0]
        team2_home_or_away = team_home_away_map.get(team2_id)
        
        input_data = get_input_data_ready(team1_df, team2_df, team1_home_or_away, team2_home_or_away)
        
        input_data.fillna(input_data.mean(), inplace=True)
        # input_data.to_csv('input_data.csv', index=False)

        # Step 3: Split the data into features (X) and target (y)
        X = game_matchups_df.drop(columns=['team1_WL' , 'team2_WL' , 'team1_PLUS_MINUS', 'team2_PLUS_MINUS'])
        y = game_matchups_df['team1_WL']
        
        # Fill NaN values in X
        X.fillna(X.mean(), inplace=True)

        # Step 4: Split the data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Step 5: Scale the input data
        scaler = MinMaxScaler()

        # Fit scaler on X_train
        scaler.fit(X_train)

        # Scale X_train and X_test
        X_train_scaled = scaler.transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Step 6: Train the model
        model = LogisticRegression()  # You can replace this with any other algorithm
        model.fit(X_train_scaled, y_train)

        # Step 8: Prepare input data for prediction
        input_data_scaled = scaler.transform(input_data)

        # Step 9: Make predictions
        predicted_probabilities = model.predict_proba(input_data_scaled)

        print("=========================")

        # Print team names and predicted probabilities
        team1_win_prob = predicted_probabilities[:, 1].mean()  # Mean probability of team 1 winning
        team2_win_prob = predicted_probabilities[:, 0].mean()  # Mean probability of team 2 winning
        
        winning_team = ""

        print(f"{team1_name}: {team1_win_prob}")
        print(f"{team2_name}: {team2_win_prob}")
        
        if team1_win_prob > team2_win_prob:
            print(f"{team1_name}: will win!")
            winning_team = team1_name
        else:
            print(f"{team2_name}: will win!")
            winning_team = team2_name
        
        team1_win_prob_formatted = f"{round(team1_win_prob * 100, 2)}%"
        team2_win_prob_formatted = f"{round(team2_win_prob * 100, 2)}%"

        # Prepare the data to insert into the "moneylines" collection
        moneyline_data = {
            'team1_name': team1_name,
            'team1_win_prob': team1_win_prob_formatted,
            'team2_name': team2_name,
            'team2_win_prob': team2_win_prob_formatted,
            'winning_team': winning_team
        }

        # Insert the data into the "moneylines" collection
        db.moneylines.insert_one(moneyline_data)

        # # Call evaluation functions
        # evaluate_model(X_test_scaled, y_test, model)
        # get_cv_scores(X_train_scaled, y_train, model)
        # evaluate_features(X, model)




        


    client.close()

except Exception as e:
    print("An error occurred:", e)
