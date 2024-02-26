from nba_api.stats.endpoints import PlayerNextNGames, PlayerGameLog, CommonPlayerInfo
from nba_api.stats.library.parameters import SeasonAll

def get_recent_games_stats(player_id, opponent_team_abbr):
    try:
        # Get player's game logs for the current season
        player_logs = PlayerGameLog(player_id=player_id, season=SeasonAll.current_season)
        player_logs_df = player_logs.get_data_frames()[0]

        # Filter logs to games against the opponent team
        opponent_logs = player_logs_df[player_logs_df['MATCHUP'].str.contains(opponent_team_abbr)]

        # Take the most recent 3 games against the opponent team in the current season
        recent_games = opponent_logs.head(3)

        return recent_games, len(opponent_logs)
    except Exception as e:
        print(f"Error retrieving recent games stats: {e}")
        return None, 0


def get_opponent_team(player_team_abbr):
    try:
        # Get the next game for the player
        next_games = PlayerNextNGames(player_id=player_id)
        next_games_data = next_games.get_normalized_dict()["NextNGames"]

        # Check if there are any upcoming games
        if next_games_data:
            # Retrieve details of the next game
            next_game = next_games_data[0]
            
            # Extract the team abbreviations
            home_team_abbr = next_game['HOME_TEAM_ABBREVIATION']
            visitor_team_abbr = next_game['VISITOR_TEAM_ABBREVIATION']

            # Determine the opponent team abbreviation
            opponent_team_abbr = home_team_abbr if player_team_abbr != home_team_abbr else visitor_team_abbr

            return opponent_team_abbr
        else:
            print("No upcoming games found for the player.")
            return None
    except Exception as e:
        print(f"Error retrieving opponent team: {e}")
        return None


def get_player_team_abbreviation(player_id):
    try:
        # Retrieve player information
        player_info = CommonPlayerInfo(player_id=player_id)
        player_info = player_info.get_data_frames()[0]

        # Extract the team abbreviation
        team_abbreviation = player_info['TEAM_ABBREVIATION'].iloc[0]
        return team_abbreviation
    except Exception as e:
        print(f"Error retrieving player team abbreviation: {e}")
        return None


# Example usage:
player_id = 201939  # Example player ID (Stephen Curry)

# Get the player's team abbreviation
player_team_abbreviation = get_player_team_abbreviation(player_id)
if player_team_abbreviation:
    print("Player's Team Abbreviation:", player_team_abbreviation)
    
    # Get the opponent team abbreviation
    opponent_team_abbreviation = get_opponent_team(player_team_abbreviation)
    if opponent_team_abbreviation:
        print("Opponent Team Abbreviation:", opponent_team_abbreviation)
        
        # Retrieve recent games stats
        opponent_games, num_games = get_recent_games_stats(player_id, opponent_team_abbreviation)
        if opponent_games is not None:
            print("Recent Games Against Opponent Team:")
            print(opponent_games)
            print(f"Number of Games Played Against {opponent_team_abbreviation}: {num_games}")
        else:
            print("Error retrieving recent games stats.")
    else:
        print("Error retrieving opponent team abbreviation.")
else:
    print("Error retrieving player team abbreviation.")
