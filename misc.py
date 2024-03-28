






# def get_player_stats(game_id):
#     # Get boxscore traditional data for the given game ID
#     boxscore = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
#     boxscore_data = boxscore.get_dict()

#     # Extract player statistics
#     player_stats = boxscore_data['resultSets'][0]['rowSet']

#     # Extract relevant columns (player ID, player name, and statistics)
#     player_data = []
#     for player_stat in player_stats:
#         player_id = player_stat[4]
#         player_name = player_stat[5]
#         player_stats = player_stat[6:]
#         player_data.append({
#             'player_id': player_id,
#             'player_name': player_name,
#             'player_stats': player_stats
#         })

#     return player_data

# # Example usage
# game_id = '0022300930'  # Example game ID
# player_data = get_player_stats(game_id)

# import tabula

# # URL of the PDF file
# pdf_url = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2024-03-20_11AM.pdf"

# # Read tables directly from the PDF URL
# tables = tabula.read_pdf(pdf_url, pages='all', multiple_tables=True)

# # Print the extracted tables
# for table in tables:
#     print(table)







#    # Get the current season
#     current_year = datetime.datetime.now().year
#     current_season = f"{current_year - 1}-{str(current_year)[-2:]}"
#     print(current_season)

#     # Define the required parameters
#     league_id = "00"  # NBA league ID
#     per_mode = "Totals"  # Per mode (e.g., totals)
#     scope = "S"  # Scope (e.g., S for regular season)
#     season = current_season  # Current season
#     season_type = "Regular Season"  # Season type

#     league_leaders_fg_pct = LeagueLeaders(
#     league_id=league_id,
#     per_mode48=per_mode,
#     scope=scope,
#     season=season,
#     season_type_all_star=season_type,
#     stat_category_abbreviation="FG_PCT"
# )

# # Get the data
#     league_leaders_fg_pct_data = league_leaders_fg_pct.get_data_frames()[0]  # Get the first DataFrame
# # Get the top player for field goal percentage
#     top_10_fg_pct_players = league_leaders_fg_pct_data.head(25)

# # Display the top player for field goal percentage
#     print("Top 25 players for FG_PCT:")
#     for index, player in top_10_fg_pct_players.iterrows():
#         print(f"{player['PLAYER']} - {player['FG_PCT']}")
    
#     # db.players.update_many({}, {'$rename': {'lastgame': 'last_game'}})





# from nba_api.stats.endpoints.homepagev2 import HomePageV2

# # Define the parameters
# params = {
#     'game_scope_detailed': 'Season',
#     'league_id': '00',
#     'player_or_team': 'Team',
#     'player_scope': 'All Players',
#     'season': '2023-24',
#     'season_type_playoffs': 'Regular Season',
#     'stat_type': 'Traditional'
# }

# # Create an instance of HomePageV2 with the parameters
# homepage = HomePageV2(**params)

# # Retrieve the data as pandas DataFrame objects
# data_frames = homepage.get_data_frames()
# print(data_frames)


# from nba_api.stats.endpoints.teamestimatedmetrics import TeamEstimatedMetrics

# # Define the parameters
# params = {
#     "league_id": "00",
#     "season": "2023-24",
#     "season_type": "Regular Season"
# }

# try:
#     # Create an instance of the TeamEstimatedMetrics class with the parameters
#     team_estimated_metrics = TeamEstimatedMetrics(**params)

#     # Call the API and get the response
#     data = team_estimated_metrics.get_data_frames()[0]
    
#     # Print all column names
#     print("Column Names:")
#     print(data.columns)

#     # Sort the data frame by the 'E_OFF_RATING' column in descending order
#     sorted_data = data.sort_values(by='E_OFF_RATING', ascending=False)

#     # Print the sorted response
#     print(sorted_data)

# except Exception as e:
#     print("Error:", e)