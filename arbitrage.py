import requests
from datetime import datetime, timezone

API_KEY = 'df3dbd3a796505a6f11173c2d787a6ca'

REGIONS = 'us,uk,eu,au'
MARKETS = 'h2h,spreads,totals'
ALTERNATE_MARKETS = 'alternate_spreads,alternate_totals'
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

def fetch_alternate_markets(event_id, sport):
    try:
        odds_response = requests.get(
            f'https://api.the-odds-api.com/v4/sports/{sport}/events/{event_id}/odds',
            params={
                'api_key': API_KEY,
                'regions': REGIONS,
                'markets': ALTERNATE_MARKETS,
                'oddsFormat': ODDS_FORMAT,
                'dateFormat': DATE_FORMAT,
            }
        )

        if odds_response.status_code != 200:
            print(f'Failed to get alternate odds for event {event_id}: status_code {odds_response.status_code}, response body {odds_response.text}')
            return None

        return odds_response.json()

    except Exception as e:
        print(f'An error occurred while fetching alternate markets for event {event_id}: {e}')
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

        # # Check for arbitrage in spreads and totals, including alternate markets
        # for market_key in ['spreads', 'totals', 'alternate_spreads', 'alternate_totals']:
        #     market_odds = {}
        #     for bookmaker, markets in event['odds'].items():
        #         for market in markets:
        #             if market['key'] == market_key:
        #                 for outcome in market['outcomes']:
        #                     point = outcome.get('point', None)
        #                     if point is not None:
        #                         if point not in market_odds:
        #                             market_odds[point] = {'over': None, 'under': None}
        #                         if outcome['name'].lower() == 'over':
        #                             if market_odds[point]['over'] is None or outcome['price'] > market_odds[point]['over']:
        #                                 market_odds[point]['over'] = outcome['price']
        #                         elif outcome['name'].lower() == 'under':
        #                             if market_odds[point]['under'] is None or outcome['price'] > market_odds[point]['under']:
        #                                 market_odds[point]['under'] = outcome['price']

        #     for point, odds in market_odds.items():
        #         if odds['over'] is not None and odds['under'] is not None:
        #             sum_inverses = (1 / odds['over']) + (1 / odds['under'])
        #             if sum_inverses < 1:
        #                 # Calculate stakes
        #                 total_stake = 10000
        #                 over_stake = total_stake / odds['over'] / sum_inverses
        #                 under_stake = total_stake / odds['under'] / sum_inverses
        #                 profit = total_stake * (1 - sum_inverses)
        #                 arbitrage_opportunities.append({
        #                     'event_id': event['event_id'],
        #                     'sport_key': event['sport_key'],
        #                     'home_team': event['home_team'],
        #                     'away_team': event['away_team'],
        #                     'market': market_key,
        #                     'point': point,
        #                     'best_odds': odds,
        #                     'sum_inverses': sum_inverses,
        #                     'over_stake': over_stake,
        #                     'under_stake': under_stake,
        #                     'profit': profit
        #                 })

    # Sort by profit in descending order and take the top 5
    arbitrage_opportunities = sorted(arbitrage_opportunities, key=lambda x: x['profit'], reverse=True)[:5]

    return arbitrage_opportunities

def print_arbitrage_opportunities(arbitrage_opportunities):
    for arb in arbitrage_opportunities:
        print(f"Arbitrage Opportunity in Event ID: {arb['event_id']}")
        print(f"Sport: {arb['sport_key']}")
        print(f"Home Team: {arb['home_team']}, Best Odds: {arb['best_odds']['home']} (Bookmaker: {arb['best_bookmakers']['home']})")
        print(f"Away Team: {arb['away_team']}, Best Odds: {arb['best_odds']['away']} (Bookmaker: {arb['best_bookmakers']['away']})")
        if arb['best_odds']['draw'] is not None:
            print(f"Draw, Best Odds: {arb['best_odds']['draw']} (Bookmaker: {arb['best_bookmakers']['draw']})")
            print(f"Bet on Draw: ${arb['draw_stake']:.2f}")
        print(f"Sum of Inverses: {arb['sum_inverses']:.6f}")
        print(f"Bet on Home Team: ${arb['home_stake']:.2f}")
        print(f"Bet on Away Team: ${arb['away_stake']:.2f}")
        print(f"Guaranteed Profit: ${arb['profit']:.2f}")
        print("\n")

in_season_sports = get_in_season_sports()

if in_season_sports:
    print(f"In-season sports: {in_season_sports}")
    filtered_events, remaining_rq, used_rq = fetch_odds_for_sports(in_season_sports)
    print("remaining:", remaining_rq)
    print("used:", used_rq)

    arbitrage_opportunities = find_arbitrage_opportunities(filtered_events)
    print_arbitrage_opportunities(arbitrage_opportunities)
else:
    print("Failed to retrieve in-season sports.")
