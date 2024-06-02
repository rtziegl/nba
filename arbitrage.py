import requests
from datetime import datetime, timezone

# An API key is emailed to you when you sign up for a plan
API_KEY = '41427f459bc4c67745a3bc720220292d'

SPORT = 'upcoming'  # Use the sport_key from the /sports endpoint below, or use 'upcoming' to see the next 8 games across all sports
REGIONS = 'us,uk,eu,au'  # uk | us | eu | au. Multiple can be specified if comma delimited
MARKETS = 'h2h,spreads,totals'  # h2h | spreads | totals. Multiple can be specified if comma delimited
ODDS_FORMAT = 'decimal'  # decimal | american
DATE_FORMAT = 'iso'  # iso | unix

DESIRED_BOOKMAKERS = [
    'betonlineag', 'bovada', 'draftkings', 'fanduel', 
    'betmgm', 'mybookieag', 'betus', 'espnbet'
]

# Get a list of in-season sports
sports_response = requests.get(
    'https://api.the-odds-api.com/v4/sports',
    params={
        'api_key': API_KEY
    }
)

if sports_response.status_code != 200:
    print(f'Failed to get sports: status_code {sports_response.status_code}, response body {sports_response.text}')
else:
    print('List of in-season sports:', sports_response.json())

# Get a list of live & upcoming games for the sport you want, along with odds for different bookmakers
odds_response = requests.get(
    f'https://api.the-odds-api.com/v4/sports/{SPORT}/odds',
    params={
        'api_key': API_KEY,
        'regions': REGIONS,
        'markets': MARKETS,
        'oddsFormat': ODDS_FORMAT,
        'dateFormat': DATE_FORMAT,
    }
)

if odds_response.status_code != 200:
    print(f'Failed to get odds: status_code {odds_response.status_code}, response body {odds_response.text}')
else:
    odds_json = odds_response.json()
    print('Number of events:', len(odds_json))

    # Function to find arbitrage opportunities
    def find_arbitrage_opportunity(odds_dict):
        outcomes = list(odds_dict.keys())
        if len(outcomes) < 2:
            return False, 0, [], []

        implied_probabilities = []
        for outcome in outcomes:
            best_odds = max(odds_dict[outcome], key=lambda x: x[1])
            implied_probabilities.append(1 / best_odds[1])

        total_implied_probability = sum(implied_probabilities)

        if total_implied_probability < 1:
            stakes = [(total_investment * implied_prob) / total_implied_probability for implied_prob in implied_probabilities]
            profit_margin = 1 - total_implied_probability
            return True, profit_margin, outcomes, stakes
        else:
            return False, 0, [], []

    arbitrage_opportunities = []
    total_investment = 100  # You can change the total investment amount

    current_time = datetime.now(timezone.utc)

    # Iterate through events and bookmakers to find arbitrage opportunities
    for event in odds_json:
        commence_time = datetime.fromisoformat(event['commence_time'].replace('Z', '+00:00'))
        if commence_time < current_time:
            continue

        sport_title = event.get('sport_title', 'Unknown Sport')
        event_name = f"{event['home_team']} vs {event['away_team']}"

        for market_type in ['h2h', 'totals', 'spreads']:
            odds_dict = {}
            for bookmaker in event['bookmakers']:
                if bookmaker['key'] not in DESIRED_BOOKMAKERS:
                    continue
                for market in bookmaker['markets']:
                    if market['key'] == market_type:
                        for outcome in market['outcomes']:
                            outcome_name = outcome['name']
                            odds_price = outcome['price']
                            points = outcome.get('point', None)  # Get points if available
                            if outcome_name not in odds_dict:
                                odds_dict[outcome_name] = []
                            odds_dict[outcome_name].append((bookmaker['title'], odds_price, points))

            is_arbitrage, profit_margin, outcomes, stakes = find_arbitrage_opportunity(odds_dict)
            if is_arbitrage:
                opportunity = {
                    'sport': sport_title,
                    'event_name': event_name,
                    'market_type': market_type,
                    'profit_margin': profit_margin,
                    'details': []
                }
                for i, outcome in enumerate(outcomes):
                    best_odds = max(odds_dict[outcome], key=lambda x: x[1])
                    return_value = stakes[i] * best_odds[1]
                    profit = return_value - total_investment
                    opportunity['details'].append({
                        'bookmaker': best_odds[0],
                        'outcome': outcome,
                        'odds': best_odds[1],
                        'stake': stakes[i],
                        'profit': profit,
                        'points': best_odds[2]  # Include points if available
                    })
                arbitrage_opportunities.append(opportunity)

    # Sort the arbitrage opportunities by profit margin in descending order
    arbitrage_opportunities.sort(key=lambda x: x['profit_margin'], reverse=True)

    # Print the top 5 arbitrage opportunities
    top_arbitrages = arbitrage_opportunities[:5]

    for opportunity in top_arbitrages:
        print(f"\nArbitrage opportunity found for event {opportunity['event_name']} in market {opportunity['market_type']} ({opportunity['sport']})!")
        print(f"Profit margin: {opportunity['profit_margin']*100:.2f}%")
        for detail in opportunity['details']:
            print(f"Bookmaker: {detail['bookmaker']}")
            if detail['points'] is not None:
                print(f"{detail['outcome']} at {detail['points']}: {detail['odds']}, Stake: {detail['stake']:.2f}, Profit if {detail['outcome']} wins: {detail['profit']:.2f}")
            else:
                print(f"{detail['outcome']}: {detail['odds']}, Stake: {detail['stake']:.2f}, Profit if {detail['outcome']} wins: {detail['profit']:.2f}")

    if not top_arbitrages:
        print("\nNo arbitrage opportunities found.")

    # Check the usage quota
    print('Remaining requests', odds_response.headers['x-requests-remaining'])
    print('Used requests', odds_response.headers['x-requests-used'])
