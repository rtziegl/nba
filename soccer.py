import requests
from datetime import datetime, timezone

API_KEY = 'df3dbd3a796505a6f11173c2d787a6ca'

REGIONS = 'us,uk,eu,au'
PLAYER_MARKETS = [
    'player_points', 'player_power_play_points', 'player_assists',
    'player_blocked_shots', 'player_shots_on_goal', 'player_goals',
    'player_total_saves'
]
ODDS_FORMAT = 'decimal'
DATE_FORMAT = 'iso'

DESIRED_BOOKMAKERS = [
    'betonlineag', 'bovada', 'draftkings', 'fanduel', 
    'betmgm', 'mybookieag', 'betus', 'espnbet', 'betparx', 'hardrockbet',
    'betrivers', 'pointsbetus'
]

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

def fetch_player_prop_markets(event_id, sport):
    try:
        odds_response = requests.get(
            f'https://api.the-odds-api.com/v4/sports/{sport}/events/{event_id}/odds',
            params={
                'api_key': API_KEY,
                'regions': REGIONS,
                'markets': ','.join(PLAYER_MARKETS),
                'oddsFormat': ODDS_FORMAT,
                'dateFormat': DATE_FORMAT,
            }
        )

        if odds_response.status_code != 200:
            print(f'Failed to get player prop odds for event {event_id}: status_code {odds_response.status_code}, response body {odds_response.text}')
            return None

        return odds_response.json()

    except Exception as e:
        print(f'An error occurred while fetching player prop markets for event {event_id}: {e}')
        return None

def fetch_odds_for_basketball(sports):
    all_events = []
    for sport in sports:
        if sport in ['icehockey_nhl']:
            try:
                odds_response = requests.get(
                    f'https://api.the-odds-api.com/v4/sports/{sport}/odds',
                    params={
                        'api_key': API_KEY,
                        'regions': REGIONS,
                        'markets': 'h2h',
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

                    # Fetch player prop markets
                    player_prop_markets = fetch_player_prop_markets(event_id, sport)
                    if player_prop_markets:
                        for bookmaker in player_prop_markets['bookmakers']:
                            if bookmaker['key'] in DESIRED_BOOKMAKERS:
                                if bookmaker['title'] in event_data['odds']:
                                    event_data['odds'][bookmaker['title']].extend(bookmaker['markets'])
                                else:
                                    event_data['odds'][bookmaker['title']] = bookmaker['markets']

                    all_events.append(event_data)

            except Exception as e:
                print(f'An error occurred while processing sport {sport}: {e}')

    return all_events

def find_player_prop_arbitrage_opportunities(events):
    arbitrage_opportunities = []

    for event in events:
        for market_key in PLAYER_MARKETS:
            market_odds = {}
            for bookmaker, markets in event['odds'].items():
                for market in markets:
                    if market['key'] == market_key:
                        for outcome in market['outcomes']:
                            player = outcome.get('description', None)
                            point = outcome.get('point', None)
                            if player and point:
                                if player not in market_odds:
                                    market_odds[player] = {}
                                if point not in market_odds[player]:
                                    market_odds[player][point] = {'over': None, 'under': None, 'over_bookmaker': None, 'under_bookmaker': None}
                                if outcome['name'].lower() == 'over':
                                    if market_odds[player][point]['over'] is None or outcome['price'] > market_odds[player][point]['over']:
                                        market_odds[player][point]['over'] = outcome['price']
                                        market_odds[player][point]['over_bookmaker'] = bookmaker
                                elif outcome['name'].lower() == 'under':
                                    if market_odds[player][point]['under'] is None or outcome['price'] > market_odds[player][point]['under']:
                                        market_odds[player][point]['under'] = outcome['price']
                                        market_odds[player][point]['under_bookmaker'] = bookmaker
                                        

            for player, points in market_odds.items():
                for point, odds in points.items():
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
                                'player': player,
                                'point': point,
                                'best_odds': odds,
                                'over_bookmaker': odds['over_bookmaker'],
                                'under_bookmaker': odds['under_bookmaker'],
                                'sum_inverses': sum_inverses,
                                'over_stake': over_stake,
                                'under_stake': under_stake,
                                'profit': profit
                            })

    # Sort by profit in descending order and take the top 5
    arbitrage_opportunities = sorted(arbitrage_opportunities, key=lambda x: x['profit'], reverse=True)[:5]

    return arbitrage_opportunities

def print_arbitrage_opportunities(arbitrage_opportunities):
    for arb in arbitrage_opportunities:
        print(f"Arbitrage Opportunity in Event ID: {arb['event_id']}")
        print(f"Sport: {arb['sport_key']}")
        print(f"Home Team: {arb['home_team']}, Away Team: {arb['away_team']}")
        print(f"Market: {arb['market']}, Player: {arb['player']}, Point: {arb['point']}")
        print(f"Best Odds Over: {arb['best_odds']['over']} (Bookmaker: {arb['over_bookmaker']})")
        print(f"Best Odds Under: {arb['best_odds']['under']} (Bookmaker: {arb['under_bookmaker']})")
        print(f"Sum of Inverses: {arb['sum_inverses']:.6f}")
        print(f"Bet on Over: ${arb['over_stake']:.2f}")
        print(f"Bet on Under: ${arb['under_stake']:.2f}")
        print(f"Guaranteed Profit: ${arb['profit']:.2f}")
        print("\n")

in_season_sports = get_in_season_sports()

if in_season_sports:
    print(f"In-season sports: {in_season_sports}")
    basketball_events = fetch_odds_for_basketball(in_season_sports)
    print("Number of soccer events fetched:", len(basketball_events))

    player_prop_arbitrage_opportunities = find_player_prop_arbitrage_opportunities(basketball_events)
    print_arbitrage_opportunities(player_prop_arbitrage_opportunities)
else:
    print("Failed to retrieve in-season sports.")
