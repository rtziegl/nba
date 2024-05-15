import json
from requests_html import HTMLSession
from bs4 import BeautifulSoup
import os
import certifi
from pymongo import MongoClient, DESCENDING
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import pandas as pd

def initialize_player_category(player_data, player_name, category):
    if player_name not in player_data:
        player_data[player_name] = {}
    if category not in player_data[player_name]:
        player_data[player_name][category] = {'Hardline': {}, 'X+': {}, 'Altline': []}

def clean_player_name(name):
    return name.split(' Alt ')[0].split(' O/U')[0].strip() 

def scrape_draftkings_main(url, player_data, category):
    session = HTMLSession()
    response = session.get(url)
    
    response.html.render(timeout=20)
    soup = BeautifulSoup(response.html.html, 'html.parser')
    event_sections = soup.find_all('div', class_='sportsbook-event-accordion__wrapper')
    
    for event in event_sections:
        date_element = event.find('span', class_='sportsbook-event-accordion__date')
        if date_element and date_element.find('span', string='Today'):
            player_odds_table = event.find('table', class_='sportsbook-table')
            if player_odds_table:
                rows = player_odds_table.find('tbody', class_='sportsbook-table__body').find_all('tr')
                for row in rows:
                    try:
                        player_name_element = row.find('span', class_='sportsbook-row-name')
                        player_name = player_name_element.text.strip() if player_name_element else None
                        if not player_name:
                            continue
                        
                        player_name = clean_player_name(player_name)
                        
                        over_cell = row.find_all('td')[0]
                        over_value_element = over_cell.find('span', class_='sportsbook-outcome-cell__line')
                        over_value = over_value_element.text.strip() if over_value_element else None
                        over_odds_element = over_cell.find('span', class_='sportsbook-odds')
                        over_odds = over_odds_element.text.strip() if over_odds_element else None
                        
                        under_cell = row.find_all('td')[1]
                        under_value_element = under_cell.find('span', class_='sportsbook-outcome-cell__line')
                        under_value = under_value_element.text.strip() if under_value_element else None
                        under_odds_element = under_cell.find('span', class_='sportsbook-odds')
                        under_odds = under_odds_element.text.strip() if under_odds_element else None

                        hardline_points = {
                            'over_value': over_value,
                            'over_odds': over_odds,
                            'under_value': under_value,
                            'under_odds': under_odds
                        }

                        initialize_player_category(player_data, player_name, category)
                        player_data[player_name][category]['Hardline'] = hardline_points
                    except Exception as e:
                        print(f"An error occurred: {e}")
                        continue
    return player_data

def scrape_draftkings_x_plus(url, player_data, category):
    session = HTMLSession()
    response = session.get(url)
    
    response.html.render(timeout=20)
    soup = BeautifulSoup(response.html.html, 'html.parser')
    event_sections = soup.find_all('div', class_='sportsbook-event-accordion__wrapper')
    
    for event in event_sections:
        date_element = event.find('span', class_='sportsbook-event-accordion__date')
        if date_element and date_element.find('span', string='Today'):
            player_sections = event.find_all('div', class_='sportsbook-event-accordion__children-wrapper')
            for section in player_sections:
                try:
                    player_lists = section.find_all('div', class_='component-29')
                    for player_list in player_lists:
                        player_name_element = player_list.find('p', class_='participants')
                        player_name = player_name_element.text.strip() if player_name_element else None
                        if not player_name:
                            continue
                        
                        player_name = clean_player_name(player_name)
                        
                        
                        x_plus_data = {}
                        outcomes = player_list.find_all('li', class_='component-29__cell')
                        for outcome in outcomes:
                            label_element = outcome.find('span', class_='sportsbook-outcome-cell__label')
                            value = label_element.text.strip() if label_element else None
                            odds_element = outcome.find('span', class_='sportsbook-odds')
                            odds = odds_element.text.strip() if odds_element else None

                            if value and odds:
                                x_plus_data[value] = odds
                        
                        initialize_player_category(player_data, player_name, category)
                        player_data[player_name][category]['X+'] = x_plus_data
                except Exception as e:
                    print(f"An error occurred: {e}")
                    continue
    return player_data

def scrape_draftkings_alt(url, player_data, category):
    session = HTMLSession()
    response = session.get(url)
    
    response.html.render(timeout=20)
    soup = BeautifulSoup(response.html.html, 'html.parser')
    event_sections = soup.find_all('div', class_='sportsbook-event-accordion__wrapper')
    
    for event in event_sections:
        date_element = event.find('span', class_='sportsbook-event-accordion__date')
        if date_element and date_element.find('span', string='Today'):
            player_sections = event.find_all('div', class_='sportsbook-event-accordion__children-wrapper')
            for section in player_sections:
                try:
                    player_lists = section.find_all('div', class_='component-29')
                    for player_list in player_lists:
                        player_name_element = player_list.find('p', class_='participants')
                        player_name = player_name_element.text.strip() if player_name_element else None
                        if not player_name:
                            continue
                        
                        player_name = clean_player_name(player_name)
                        
                        alt_data = []
                        outcomes = player_list.find_all('li', class_='component-29__cell')
                        for outcome in outcomes:
                            label_element = outcome.find('span', class_='sportsbook-outcome-cell__label')
                            value = label_element.text.strip() if label_element else None
                            line_element = outcome.find('span', class_='sportsbook-outcome-cell__line')
                            line = line_element.text.strip() if line_element else None
                            odds_element = outcome.find('span', class_='sportsbook-odds')
                            odds = odds_element.text.strip() if odds_element else None

                            if value and line and odds:
                                alt_data.append({'value': value, 'line': line, 'odds': odds})
                        
                        initialize_player_category(player_data, player_name, category)
                        player_data[player_name][category]['Altline'] = alt_data
                except Exception as e:
                    print(f"An error occurred: {e}")
                    continue
    return player_data

def insert_into_mongodb(player_data):
    # Load environment variables from .env file
    load_dotenv()

    # Retrieve the MongoDB Atlas URI from the environment
    uri = os.getenv("MONGODB_URI")

    # Create a MongoClient instance
    client = MongoClient(uri, tlsCAFile=certifi.where())

    db = client["nba"]
    collection = db['dailyplayerodds']
    collection.delete_many({})

    for player, data in player_data.items():
        document = {
            'player': player,
            'categories': data
        }
        collection.replace_one({'player': player}, document, upsert=True)
        


player_data = {}

main_stat_urls = {
    'Points': 'https://sportsbook.draftkings.com/leagues/basketball/nba?category=player-points&subcategory=points',
    'Assists': 'https://sportsbook.draftkings.com/leagues/basketball/nba?category=player-assists&subcategory=assists',
    'Rebounds': 'https://sportsbook.draftkings.com/leagues/basketball/nba?category=player-rebounds&subcategory=rebounds',
    '3-Pointers': 'https://sportsbook.draftkings.com/leagues/basketball/nba?category=player-threes&subcategory=threes',
    'Steals': 'https://sportsbook.draftkings.com/leagues/basketball/nba?category=player-defense&subcategory=steals',
    'Blocks': 'https://sportsbook.draftkings.com/leagues/basketball/nba?category=player-defense&subcategory=blocks'
}

for stat_type, url in main_stat_urls.items():
    player_data = scrape_draftkings_main(url, player_data, stat_type)
    
print('Main stats complete')

x_plus_stat_urls = {
    'Points': 'https://sportsbook.draftkings.com/leagues/basketball/nba?category=player-points&subcategory=x%2B-points',
    'Assists': 'https://sportsbook.draftkings.com/leagues/basketball/nba?category=player-assists&subcategory=x%2B-assists',
    'Rebounds': 'https://sportsbook.draftkings.com/leagues/basketball/nba?category=player-rebounds&subcategory=x%2B-rebounds',
    '3-Pointers': 'https://sportsbook.draftkings.com/leagues/basketball/nba?category=player-threes&subcategory=x%2B-threes',
    'Steals': 'https://sportsbook.draftkings.com/leagues/basketball/nba?category=player-defense&subcategory=alt-steals',
    'Blocks': 'https://sportsbook.draftkings.com/leagues/basketball/nba?category=player-defense&subcategory=alt-blocks'
}

for stat_type, url in x_plus_stat_urls.items():
    player_data = scrape_draftkings_x_plus(url, player_data, stat_type)
    
print('X+ stats complete')

altline_stat_urls = {
    'Points': 'https://sportsbook.draftkings.com/leagues/basketball/nba?category=player-points&subcategory=alt-points',
    'Assists': 'https://sportsbook.draftkings.com/leagues/basketball/nba?category=player-assists&subcategory=alt-assists',
    'Rebounds': 'https://sportsbook.draftkings.com/leagues/basketball/nba?category=player-rebounds&subcategory=alt-rebounds',
}

for stat_type, url in altline_stat_urls.items():
    player_data = scrape_draftkings_alt(url, player_data, stat_type)
    
print('Altline stats complete')

insert_into_mongodb(player_data)

# def print_player_data(player_data):
#     for player, categories in player_data.items():
#         print(f"Player: {player}")
#         for category, details in categories.items():
#             print(f"  Category: {category}")
#             for stat_type, values in details.items():
#                 print(f"    {stat_type}:")
#                 if stat_type == 'Altline':
#                     for value in values:
#                         print(f"      Value: {value['value']}, Line: {value['line']}, Odds: {value['odds']}")
#                 else:
#                     for key, val in values.items():
#                         print(f"      {key}: {val}")
#         print("\n")

# print_player_data(player_data)
