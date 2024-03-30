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

# Predict win probabilities for each team using the logistic regression model
def predict_win_probabilities(model, X):
    return model.predict_proba(X)[:, 1]  # Predict probabilities for class 1 (win)

def get_team_game_stats(team_id, db):
    """
    Fetches regular season game statistics for a given team ID from the database.
    Returns a dictionary containing game statistics keyed by game ID.
    """
    game_ids = get_regular_season_data_per_team(team_id)
    game_stats = {}

    # Fetch team ranking data from the database
    team_ranks_data = {}
    for rank_data in db.teamsranks.find():
        team_ranks_data[rank_data["TEAM_ID"]] = {
            "W_PCT": rank_data["W_PCT"],
            "E_OFF_RATING": rank_data["E_OFF_RATING"],
            "E_DEF_RATING": rank_data["E_DEF_RATING"],
            "E_NET_RATING": rank_data["E_NET_RATING"],
            "E_AST_RATIO": rank_data["E_AST_RATIO"],
            "E_OREB_PCT": rank_data["E_OREB_PCT"],
            "E_DREB_PCT": rank_data["E_DREB_PCT"],
            "E_REB_PCT": rank_data["E_REB_PCT"],
            "E_TM_TOV_PCT": rank_data["E_TM_TOV_PCT"],
            "E_PACE": rank_data["E_PACE"]
        }

    # Process data for the team
    for game_id in game_ids:
        game_data = db.games.find_one({"game_id": game_id})
        if game_data:
            # Extract team statistics from the game data
            team_stats = {}
            for team_info in game_data['teams']:
                team_id = team_info['team_id']
                team_stats[team_id] = team_info['statistics']

            # Merge team statistics with team ranking data
            for team_id, stats in team_stats.items():
                # Check if ranking data is available for the team
                if team_id in team_ranks_data:
                    # Merge statistics with ranking data
                    stats.update(team_ranks_data[team_id])

            # Add the game stats to the dictionary
            game_stats[game_id] = team_stats
        else:
            print(f"No data found for game ID: {game_id}")

    return game_stats


def prepare_matchup_data(team1_game_stats, team1_id):
    flattened_rows = []

    # Iterate over each game in the dictionary
    for game_id, game_data in team1_game_stats.items():
        team1_stats = None
        opponent_stats = None
        # Iterate over each team in the game
        for team_id, team_stats in game_data.items():
            if team_id == team1_id:
                team1_stats = team_stats
            else:
                opponent_stats = team_stats
        
        if team1_stats is not None and opponent_stats is not None:
            # Subtract opponent stats from team1 stats
            for key, value in opponent_stats.items():
                if isinstance(value, (int, float)):
                    team1_stats[key] -= value

            # Modify WL and HOMEORAWAY values
            if team1_stats['WL'] == -1:
                team1_stats['WL'] = 0
            if team1_stats['HOMEORAWAY'] == -1:
                team1_stats['HOMEORAWAY'] = 0
            
            
            # Create a new dictionary for the flattened row
            flattened_row = {'game_id': game_id, 'team_id': team1_id}
            # Update the dictionary with team1 statistics
            flattened_row.update(team1_stats)
            # Append the flattened row to the list
            flattened_rows.append(flattened_row)

    # Convert the list of dictionaries into a DataFrame
    team1_vs_opponent_df = pd.DataFrame(flattened_rows)

    return team1_vs_opponent_df


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
todays_team_ids = get_todays_team_ids(matchups)
print(todays_team_ids)

todays_team_ids = todays_team_ids
print(todays_team_ids)

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix


# Initialize a dictionary to store regular season data for each team
all_regular_season_data_dict = {}
# Define your features
features = ["TEAM1_TEAM_NAME", "TEAM1_TEAM_ABBREVIATION", "TEAM1_WL", "TEAM1_HOMEORAWAY", 
            "TEAM1_FGM", "TEAM1_FGA", "TEAM1_FG_PCT", "TEAM1_FG3M", "TEAM1_FG3A",
            "TEAM1_FG3_PCT", "TEAM1_FTM", "TEAM1_FTA", "TEAM1_FT_PCT", "TEAM1_OREB", 
            "TEAM1_DREB", "TEAM1_REB", "TEAM1_AST", "TEAM1_STL", "TEAM1_BLK", "TEAM1_TOV",
            "TEAM1_PF", "TEAM1_PLUS_MINUS", "TEAM2_TEAM_NAME", "TEAM2_TEAM_ABBREVIATION", 
            "TEAM2_WL", "TEAM2_HOMEORAWAY", "TEAM2_FGM", "TEAM2_FGA", "TEAM2_FG_PCT", 
            "TEAM2_FG3M", "TEAM2_FG3A", "TEAM2_FG3_PCT", "TEAM2_FTM", "TEAM2_FTA", 
            "TEAM2_FT_PCT", "TEAM2_OREB", "TEAM2_DREB", "TEAM2_REB", "TEAM2_AST", 
            "TEAM2_STL", "TEAM2_BLK", "TEAM2_TOV", "TEAM2_PF", "TEAM2_PLUS_MINUS", 
            "TARGET"]

# Create an empty DataFrame with the specified features
prepared_data = pd.DataFrame(columns=features)

# Print the empty DataFrame
print(prepared_data)

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
    # Connect to MongoDB
    db = client['nba']
    
    for team1_id, team2_id in todays_team_ids:
        print("Team 1 ID:", team1_id)
        print("Team 2 ID:", team2_id)

        # Get regular season game stats for team 1
        team1_game_stats = get_team_game_stats(team1_id, db)
        
        # Prepare team1 df
        team1_df = prepare_matchup_data(team1_game_stats, team1_id)
        
        # Get regular season game stats for team 2
        team2_game_stats = get_team_game_stats(team2_id, db)
        # Prepare team2 df
        team2_df = prepare_matchup_data(team2_game_stats, team2_id)
        
        # Add is_team1 column for team1_df
        team1_df['is_team1'] = 1

        # Add is_team1 column for team2_df
        team2_df['is_team1'] = 0

        # Concatenate team1_df and team2_df
        combined_df = pd.concat([team1_df, team2_df], ignore_index=True)
        
        # Get the team names
        team1_name = combined_df.loc[combined_df['is_team1'] == 1, 'TEAM_NAME'].iloc[0]
        team2_name = combined_df.loc[combined_df['is_team1'] == 0, 'TEAM_NAME'].iloc[0]

        from sklearn.preprocessing import MinMaxScaler

        # Drop unnecessary columns
        columns_to_drop = ['team_id', 'TEAM_NAME', 'TEAM_ABBREVIATION', 'game_id']  # Adjust this list as needed
        combined_df.drop(columns=columns_to_drop, inplace=True)
        
        # Scale numerical features
        scaler = MinMaxScaler()
        numerical_columns = ['HOMEORAWAY', 'FGM', 'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT', 'FTM', 'FTA', 'FT_PCT',
                            'OREB', 'DREB', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PLUS_MINUS', 'W_PCT',
                            'E_OFF_RATING', 'E_DEF_RATING', 'E_NET_RATING', 'E_AST_RATIO', 'E_OREB_PCT', 'E_DREB_PCT',
                            'E_REB_PCT', 'E_TM_TOV_PCT', 'E_PACE']
        combined_df[numerical_columns] = scaler.fit_transform(combined_df[numerical_columns])
        
        print(combined_df)
        
        from sklearn.model_selection import train_test_split
        from sklearn.linear_model import LogisticRegression

        # Split data into features (X) and target variable (y)
        X = combined_df.drop(columns=['WL'])  # Drop 'WL' column to get features
        y = combined_df['WL']  # Target variable

        # Split data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Train the model
        model = LogisticRegression()  # Example: Logistic Regression
        model.fit(X_train, y_train)
        
         # Step 3: Make predictions on the testing data
        y_pred = model.predict(X_test)

        # Step 4: Calculate evaluation metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        conf_matrix = confusion_matrix(y_test, y_pred)

        # Step 5: Display evaluation metrics
        print("Accuracy:", accuracy)
        print("Precision:", precision)
        print("Recall:", recall)
        print("F1 Score:", f1)
        print("Confusion Matrix:")
        print(conf_matrix)
        
        # Predict the outcome for the combined data
        predicted_probabilities = model.predict_proba(X)[:, 1]

        # Display the predicted probabilities for each team
        predicted_probability_team1 = predicted_probabilities[combined_df['is_team1'] == 1].mean()
        predicted_probability_team2 = 1 - predicted_probability_team1

        print("Predicted Probability of", team1_name, "Winning:", "{:.2f}".format(predicted_probability_team1))
        print("Predicted Probability of", team2_name, "Winning:", "{:.2f}".format(predicted_probability_team2))
        
        import pandas as pd
        from sklearn.linear_model import LinearRegression

        # Separate features (X) and target variable (y)
        X = combined_df.drop(columns=['WL'])  # Features
        y = combined_df[['FGM', 'FG3M', 'FTM']]  # Target variables to predict

        # Train a linear regression model
        model = LinearRegression()
        model.fit(X, y)

        # Predict the stat differentials for both team_1 and team_2
        predicted_diff = model.predict(X)
        
        # Convert the NumPy array to a pandas DataFrame
        predicted_diff_df = pd.DataFrame(predicted_diff, columns=['FGM', 'FG3M', 'FTM'])

        # Print the column names of the predicted_diff DataFrame
        print(predicted_diff_df.columns)

        # # Split the predicted differentials for team_1 and team_2
        # predicted_diff_team1 = predicted_diff[combined_df['is_team1'] == 1].mean()
        # predicted_diff_team2 = predicted_diff[combined_df['is_team1'] == 0].mean()

        # Split the predicted differentials for team_1 and team_2
        predicted_diff_team1 = predicted_diff[combined_df['is_team1'] == 1].mean(axis=0)

        # Print the mean of each column separately for predicted_diff_team1
        print("Mean of Predicted Differentials for Team 1:")
        for col_index, mean_value in enumerate(predicted_diff_team1):
            col_name = combined_df.columns[col_index]
            print(col_name + ":", mean_value)
                                
    client.close()

except Exception as e:
    print("An error occurred:", e)
