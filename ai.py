from nba_api.stats.endpoints.teamestimatedmetrics import TeamEstimatedMetrics
from nba_api.stats.endpoints import LeagueGameFinder
import pandas as pd
from sklearn.linear_model import LinearRegression
from nba_api.stats.endpoints import ScoreboardV2
from datetime import datetime
import json

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

    # Extract team IDs from matchups and populate team_ids list
    for _, teams_info in matchups:
        for team_info in teams_info:
            team_id = team_info[0]
            team_ids.append(team_id)

    # Remove duplicates by converting to set and back to list
    team_ids = list(set(team_ids))

    return team_ids

def get_regular_season_data_per_team(team_id):
    # Define the features you want to use for training the model
    features = ['FGM', 'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT', 
            'FTM', 'FTA', 'FT_PCT', 'OREB', 'DREB', 'REB', 'AST', 'STL', 
            'BLK', 'TOV', 'PF', 'PLUS_MINUS']
    try:
        # Define parameters for game search
        params = {
            "player_or_team_abbreviation": "T",  # T for team
            "league_id_nullable": '00' 
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

        # Map WL column to 1 for W (win) and 0 for L (loss)
        regular_season_data['WL'] = regular_season_data['WL'].map({'W': 1, 'L': 0})

        # Add a new column 'HomeOrAway' based on the 'Matchup' column
        regular_season_data['HOMEORAWAY'] = regular_season_data['MATCHUP'].apply(lambda x: 1 if 'vs.' in x else 0)
        
        print(regular_season_data)
        
        # Group the DataFrame by game ID
        grouped_data = regular_season_data.groupby('GAME_ID')

        # Initialize an empty list to store game information
        all_games_info = []

        # Iterate over each group and construct the JSON structure
        for game_id, group in grouped_data:
            game_info = {
                "game_id": game_id,
                "date": group['GAME_DATE'].iloc[0],
                "teams": []
            }
            
            # Iterate over each row in the group
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
            
            # Append the game information to the list
            all_games_info.append(game_info)

        # Convert the list of game information to JSON format
        all_games_json = json.dumps(all_games_info, indent=4)

        # Print the JSON structure
        print(all_games_json)
        
        # Define the parameters for estimated metrics
        metrics_params = {
            "league_id": "00",
            "season": "2023-24",
            "season_type": "Regular Season"
        }

        # Create an instance of the TeamEstimatedMetrics class with the parameters
        team_estimated_metrics = TeamEstimatedMetrics(**metrics_params)

        # Call the API and get the response
        metrics_data = team_estimated_metrics.get_data_frames()[0]

        # Filter data for the desired team ID
        team_metrics_data = metrics_data[metrics_data['TEAM_ID'] == team_id]

        # Extract relevant metrics
        team_metrics = team_metrics_data.iloc[0]  # Assuming only one row per team

        # Extract desired estimated metrics
        regular_season_data['E_OFF_RATING'] = team_metrics['E_OFF_RATING']
        regular_season_data['E_DEF_RATING'] = team_metrics['E_DEF_RATING']
        regular_season_data['E_NET_RATING'] = team_metrics['E_NET_RATING']
        regular_season_data['E_PACE'] = team_metrics['E_PACE']
        regular_season_data['E_AST_RATIO'] = team_metrics['E_AST_RATIO']
        regular_season_data['E_OREB_PCT'] = team_metrics['E_OREB_PCT']
        regular_season_data['E_DREB_PCT'] = team_metrics['E_DREB_PCT']
        regular_season_data['E_REB_PCT'] = team_metrics['E_REB_PCT']
        regular_season_data['E_TM_TOV_PCT'] = team_metrics['E_TM_TOV_PCT']
        

        return regular_season_data

    except Exception as e:
        print("Error:", e)

# Predict win probabilities for each team using the logistic regression model
def predict_win_probabilities(model, X):
    return model.predict_proba(X)[:, 1]  # Predict probabilities for class 1 (win)


# Get todays matchups
matchups = get_todays_matchups()
todays_team_ids = get_todays_team_ids(matchups)
print(matchups)
print(todays_team_ids)

from sklearn.linear_model import LogisticRegression

# Initialize a dictionary to store regular season data for each team
all_regular_season_data_dict = {}

# Loop through each team ID in team_ids
for team_id in todays_team_ids:
    # Get regular season data for the current team ID
    regular_season_data = get_regular_season_data_per_team(team_id)
    
    # Store the regular season data in the dictionary
    all_regular_season_data_dict[team_id] = regular_season_data


# Define the features you want to use for training the model
features = ['MIN', 'FGM', 'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT', 
            'FTM', 'FTA', 'FT_PCT', 'OREB', 'DREB', 'REB', 'AST', 'STL', 
            'BLK', 'TOV', 'PF', 'PLUS_MINUS']

continuous_ratings = ['E_OFF_RATING', 'E_DEF_RATING', 'E_NET_RATING', 'E_PACE', 
                      'E_AST_RATIO', 'E_OREB_PCT', 'E_DREB_PCT', 'E_REB_PCT', 'E_TM_TOV_PCT']


from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import numpy as np

# Initialize lists to store features and labels
X_train = []
y_train = []

# Loop through each matchup
for game_id, teams_info in matchups:
    home_team_info = teams_info[0] if teams_info[0][2] == 1 else teams_info[1]
    away_team_info = teams_info[0] if teams_info[0][2] == 0 else teams_info[1]
    
    home_team_id, _, _ = home_team_info
    away_team_id, _, _ = away_team_info

    # Get historical game data for home and away teams
    home_team_games = all_regular_season_data_dict[home_team_id]
    away_team_games = all_regular_season_data_dict[away_team_id]

    # Calculate mean performance for home and away teams
    home_team_avg = home_team_games[features].mean(axis=0)
    away_team_avg = away_team_games[features].mean(axis=0)

    # Calculate mean continuous ratings for home and away teams
    home_team_ratings = home_team_games[continuous_ratings].mean(axis=0)
    away_team_ratings = away_team_games[continuous_ratings].mean(axis=0)

    # Calculate rating differences ensuring correct alignment
    rating_diffs = np.where(home_team_ratings > away_team_ratings, home_team_ratings - away_team_ratings, away_team_ratings - home_team_ratings)

    # Combine home and away team data as features along with rating differences
    combined_features = np.concatenate((home_team_avg, away_team_avg, rating_diffs))

    # Determine label based on the outcome of historical matchups
    # If the home team won more games, label = 1, else label = 0
    home_team_wins = (home_team_games['WL'] == 1).sum()
    away_team_wins = (away_team_games['WL'] == 1).sum()
    

    # Determine label based on the average performance of home and away teams
    weight_avg = 0.7  # Weight for average performance
    weight_ratings = 0.3  # Weight for ratings

    home_team_score = np.mean(home_team_avg) * weight_avg + np.mean(home_team_ratings) * weight_ratings
    away_team_score = np.mean(away_team_avg) * weight_avg + np.mean(away_team_ratings) * weight_ratings

    if home_team_score > away_team_score:
        # Home team has higher weighted score
        X_train.append(np.concatenate((home_team_avg, away_team_avg, rating_diffs)))
        y_train.append(1)  # Assign label 1 for home team win
    else:
        # Away team has higher or equal weighted score
        X_train.append(np.concatenate((home_team_avg, away_team_avg, rating_diffs)))
        y_train.append(0)  # Assign label 0 for home team loss or tie
    
    
# Convert lists to arrays
X_train = np.array(X_train)
y_train = np.array(y_train)

# Normalize features
scaler = MinMaxScaler()
X_train_normalized = scaler.fit_transform(X_train)

# Initialize Logistic Regression with default hyperparameters
logistic_model = LogisticRegression()

# Fit the model to the entire normalized dataset
logistic_model.fit(X_train_normalized, y_train)

# Predict probabilities for the normalized data
y_pred_proba = logistic_model.predict_proba(X_train_normalized)

# Extract probability of home team winning
home_win_probabilities = y_pred_proba[:, 1]

# Calculate probability of away team winning
away_win_probabilities = y_pred_proba[:, 0]

total_win_probability = 0
num_predicted_wins = 0

# Loop through each matchup
for idx, (game_id, teams_info) in enumerate(matchups):
    home_team_info = teams_info[0] if teams_info[0][2] == 1 else teams_info[1]
    away_team_info = teams_info[0] if teams_info[0][2] == 0 else teams_info[1]

    home_win_probability = home_win_probabilities[idx]
    away_win_probability = away_win_probabilities[idx]
    
    home_team_name = home_team_info[1]
    away_team_name = away_team_info[1]


    # Print game ID and win probabilities
    print(f"Game ID: {game_id}")
    print(f"{home_team_name} Win Probability (Logistic Regression): {home_win_probability:.2f}")
    print(f"{away_team_name} Win Probability (Logistic Regression): {away_win_probability:.2f}")

    # Check if either home or away team is predicted to win
    if home_win_probability > 0.5:
        total_win_probability += home_win_probability
        num_predicted_wins += 1
    elif away_win_probability > 0.5:
        total_win_probability += away_win_probability
        num_predicted_wins += 1

# Calculate the average win probability of the predicted winning teams
if num_predicted_wins > 0:
    average_win_probability = total_win_probability / num_predicted_wins
    print(f"\nAverage Win Probability of Predicted Winning Teams: {average_win_probability:.2f}")
else:
    print("\nNo teams are predicted to win with probability greater than 0.5.")


# Evaluate the model using metrics
accuracy = accuracy_score(y_train, logistic_model.predict(X_train_normalized))
precision = precision_score(y_train, logistic_model.predict(X_train_normalized))
recall = recall_score(y_train, logistic_model.predict(X_train_normalized))
f1 = f1_score(y_train, logistic_model.predict(X_train_normalized))
roc_auc = roc_auc_score(y_train, home_win_probabilities)

# Print evaluation metrics
print('Evaluation Metrics (Logistic Regression):')
print(f'Accuracy: {accuracy:.2f}')
print(f'Precision: {precision:.2f}')
print(f'Recall: {recall:.2f}')
print(f'F1 Score: {f1:.2f}')
print(f'ROC AUC: {roc_auc:.2f}')

# Get the coefficients of the logistic regression model
coefficients = logistic_model.coef_[0]

# Get the feature names
feature_names = ['Home Team Avg ' + str(i) for i in range(len(home_team_avg))] + ['Away Team Avg ' + str(i) for i in range(len(away_team_avg))] + ['Rating Difference ' + str(i) for i in range(len(rating_diffs))]

# Print the feature names and their corresponding coefficients
print("Feature Importance (Logistic Regression):")
for feature_name, coef in zip(feature_names, coefficients):
    print(f"{feature_name}: {coef:.2f}")










# X_points_train = []
# y_points_train = []

# # Extract features and target for predicting total points for each team
# for game_id, teams_info in matchups:
#     home_team_id, away_team_id = teams_info[0][0], teams_info[1][0]
    
#     home_team_data = all_regular_season_data_dict[home_team_id][features].mean().values
#     away_team_data = all_regular_season_data_dict[away_team_id][features].mean().values
    
#     home_team_ratings = all_regular_season_data_dict[home_team_id][continuous_ratings].mean().values
#     away_team_ratings = all_regular_season_data_dict[away_team_id][continuous_ratings].mean().values
    
#     home_rating_diffs = home_team_ratings - away_team_ratings
#     away_rating_diffs = away_team_ratings - home_team_ratings
    
#     # Combine features for both home and away teams along with rating differences
#     combined_features_home = np.concatenate((home_team_data, away_team_data, home_rating_diffs))
#     combined_features_away = np.concatenate((away_team_data, home_team_data, away_rating_diffs))
    
#     X_points_train.append(combined_features_home)  # For home team
#     X_points_train.append(combined_features_away)  # For away team
    
#     # Calculate average points for the home and away teams
#     home_points = all_regular_season_data_dict[home_team_id]['PTS'].mean()
#     away_points = all_regular_season_data_dict[away_team_id]['PTS'].mean()
    
#     y_points_train.append(home_points)
#     y_points_train.append(away_points)

# # Train the Linear Regression Model for Total Points Prediction
# points_model = LinearRegression()
# points_model.fit(X_points_train, y_points_train)

# # Step 3: Make Predictions
# matchup_predictions = []

# for game_id, teams_info in matchups:
#     # Extract home and away team information
#     home_team_info = None
#     away_team_info = None
    
#     for team_info in teams_info:
#         team_id, team_name, is_home = team_info

#         if is_home == 1:
#             home_team_info = {"id": team_id, "name": team_name}
#         else:
#             away_team_info = {"id": team_id, "name": team_name}

#     # Prepare data for the home team
#     home_team_id = home_team_info["id"]
#     home_team_data = all_regular_season_data_dict[home_team_id][features].mean().values
#     home_team_ratings = all_regular_season_data_dict[home_team_id][continuous_ratings].mean().values

#     # Prepare data for the away team
#     away_team_id = away_team_info["id"]
#     away_team_data = all_regular_season_data_dict[away_team_id][features].mean().values
#     away_team_ratings = all_regular_season_data_dict[away_team_id][continuous_ratings].mean().values

#     # Calculate rating differences after obtaining both teams' ratings
#     home_rating_diffs = home_team_ratings - away_team_ratings
#     away_rating_diffs = away_team_ratings - home_team_ratings

#     # Combine features and rating differences for the home team
#     home_combined_features = np.concatenate((home_team_data, away_team_data, home_rating_diffs)).reshape(1, -1)

#     # Combine features and rating differences for the away team
#     away_combined_features = np.concatenate((away_team_data, home_team_data, away_rating_diffs)).reshape(1, -1)

#      # Ensure that the input data has 65 features
#     assert home_combined_features.shape[1] == 65
#     assert away_combined_features.shape[1] == 65
#     # Predict points for the home and away teams
#     home_team_predicted_points = points_model.predict(home_combined_features)[0]
#     away_team_predicted_points = points_model.predict(away_combined_features)[0]

#     # Calculate spread
#     spread = abs(home_team_predicted_points - away_team_predicted_points)
    
#     # Predict win probabilities for the home and away teams
#     home_win_probability = predict_win_probabilities(model, home_combined_features)[0]
#     away_win_probability = predict_win_probabilities(model, away_combined_features)[0]

#     # Append predictions to the list
#      # Append predictions to the list
#     matchup_predictions.append({
#         "Game ID": game_id,
#         "Home Team ID": home_team_info["id"],
#         "Home Team Name": home_team_info["name"],
#         "Away Team ID": away_team_info["id"],
#         "Away Team Name": away_team_info["name"],
#         "Home Team Predicted Points": home_team_predicted_points,
#         "Away Team Predicted Points": away_team_predicted_points,
#         "Home Team Win Probability": home_win_probability,
#         "Away Team Win Probability": away_win_probability,
#         "Spread": spread
#     })

# # Print matchup predictions
# for prediction in matchup_predictions:
#     print("Game ID:", prediction["Game ID"])
#     print("-----------------------------------------------------------------")
#     print("Home Team Name:", prediction["Home Team Name"])
#     print("Home Team Predicted Points:", round(prediction["Home Team Predicted Points"], 2))
#     print("Home Team Win Probability:", round(prediction["Home Team Win Probability"] * 100, 2), "%")
#     print("---------------------------------------------------------------")
#     print("Away Team Name:", prediction["Away Team Name"])
#     print("Away Team Predicted Points:", round(prediction["Away Team Predicted Points"], 2))
#     print("Away Team Win Probability:", round(prediction["Away Team Win Probability"] * 100, 2), "%")
#     print("---------------------------------------------------------------")
#     print("Spread:", round(prediction["Spread"], 2))
#     print()






######## TESTING MODEL ACCURACY ##########

# from sklearn.metrics import accuracy_score, mean_squared_error, mean_absolute_error

# # Evaluation of the models' performance
# # Initialize lists to store actual and predicted outcomes for evaluation
# actual_outcomes = []
# predicted_outcomes = []

# # Initialize lists to store actual and predicted total points for evaluation
# actual_total_points = []
# predicted_total_points = []

# print("Team IDs in all_regular_season_data_dict:", list(all_regular_season_data_dict.keys()))

# # Make predictions and evaluate performance for each matchup
# for prediction in matchup_predictions:
#     # Extract actual outcome (whether the home team won or not)
#     actual_outcome = int(all_regular_season_data_dict[prediction["Home Team ID"]]['WL'].mean() > 0.5)
#     actual_outcomes.append(actual_outcome)

#     # Predicted win probabilities for the home team
#     predicted_home_win_probability = prediction["Home Team Win Probability"]

#     # Predicted outcome (1 if predicted win probability is greater than 0.5, else 0)
#     predicted_outcome = int(predicted_home_win_probability > 0.5)
#     predicted_outcomes.append(predicted_outcome)

#     # Actual and predicted total points
#     actual_total_points.append(all_regular_season_data_dict[prediction["Home Team ID"]]['PTS'].mean())
#     actual_total_points.append(all_regular_season_data_dict[prediction["Away Team ID"]]['PTS'].mean())
#     predicted_total_points.append(prediction["Home Team Predicted Points"])
#     predicted_total_points.append(prediction["Away Team Predicted Points"])

# # Evaluate logistic regression model performance
# logistic_regression_accuracy = accuracy_score(actual_outcomes, predicted_outcomes)
# print("Logistic Regression Model Performance:")
# print("Accuracy:", logistic_regression_accuracy)

# # Evaluate linear regression model performance
# linear_regression_mse = mean_squared_error(actual_total_points, predicted_total_points)
# linear_regression_mae = mean_absolute_error(actual_total_points, predicted_total_points)
# print("Linear Regression Model Performance:")
# print("Mean Squared Error:", linear_regression_mse)
# print("Mean Absolute Error:", linear_regression_mae)


# # Retrieve coefficients for logistic regression
# logistic_regression_coefficients = model.coef_[0]  # Assuming model is your logistic regression model

# # Retrieve coefficients for linear regression
# linear_regression_coefficients = points_model.coef_  # Assuming points_model is your linear regression model

# # Print coefficients for logistic regression
# print("Logistic Regression Coefficients:")
# for feature, coef in zip(features, logistic_regression_coefficients):
#     print(f"{feature}: {coef}")

# # Print coefficients for linear regression
# print("\nLinear Regression Coefficients:")
# for feature, coef in zip(features, linear_regression_coefficients):
#     print(f"{feature}: {coef}")