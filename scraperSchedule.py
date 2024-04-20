import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

cities = [
    "Boston",
    "Brooklyn",
    "New York",
    "Philadelphia",
    "Toronto",
    "Chicago",
    "Cleveland",
    "Detroit",
    "Indiana",
    "Milwaukee",
    "Denver",
    "Minnesota",
    "Oklahoma City",
    "Portland",
    "Utah",
    "Golden State",
    "LA",
    "Los Angeles",
    "Phoenix",
    "Sacramento",
    "Atlanta",
    "Charlotte",
    "Miami",
    "Orlando",
    "Washington",
    "Dallas",
    "Houston",
    "Memphis",
    "New Orleans",
    "San Antonio"
]

city_team_mapping = {
    "Atlanta": "ATL",
    "Boston": "BOS",
    "Brooklyn": "BKN",
    "Charlotte": "CHA",
    "Chicago": "CHI",
    "Cleveland": "CLE",
    "Dallas": "DAL",
    "Denver": "DEN",
    "Detroit": "DET",
    "Golden State": "GSW",
    "Houston": "HOU",
    "Indiana": "IND",
    "LA": "LAC",
    "Los Angeles": "LAL",
    "Memphis": "MEM",
    "Miami": "MIA",
    "Milwaukee": "MIL",
    "Minnesota": "MIN",
    "New Orleans": "NOP",
    "New York": "NYK",
    "Oklahoma City": "OKC",
    "Orlando": "ORL",
    "Philadelphia": "PHI",
    "Phoenix": "PHX",
    "Portland": "POR",
    "Sacramento": "SAC",
    "San Antonio": "SAS",
    "Toronto": "TOR",
    "Utah": "UTA",
    "Washington": "WAS"
}

# Get current date
current_date = datetime.now().strftime("%Y%m%d")

# URL of the webpage containing today's NBA schedule
url = f"https://www.espn.com/nba/schedule/_/date/{current_date}"

# Define headers to mimic a browser request
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}

# Send a GET request to the URL with headers
response = requests.get(url, headers=headers)

# Check if the request was successful (status code 200)
if response.status_code == 200:
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Find the table with class "Table"
    schedule_table = soup.find("table", class_="Table")
    
    # Check if the schedule table was found
    if schedule_table:
        # Create an empty list to store schedule information
        schedule = []
        
        # Find all rows in the table
        rows = schedule_table.find_all("tr")
        
        # Iterate over each row
        for row in rows:
            # Find all cells in the row
            cells = row.find_all("td")
            
            # Check if the row contains schedule information
            if len(cells) > 1:
                # Extract team names
                team_1 = cells[0].text.strip()
                team_2 = cells[1].text.strip()
                
                # Check if any city name is present in team names
                for city in cities:
                    if city in team_1:
                        team1 = city
                    if city in team_2:
                        team2 = city
                
                # Generate matchup strings
                matchup1 = f"{city_team_mapping[team1]} @ {city_team_mapping[team2]}"
                matchup2 = f"{city_team_mapping[team2]} vs. {city_team_mapping[team1]}"
                
                # Add schedule information to the list
                schedule.append({"team1": team1, "team2": team2, "matchup1": matchup1, "matchup2": matchup2})
        
        # Create a JSON object with the schedule
        schedule_json = {"Schedule": schedule}
        
        # Print the JSON object
        print(json.dumps(schedule_json, indent=4))
    else:
        print("Schedule table not found.")
else:
    print("Failed to retrieve data from", url, ". Status code:", response.status_code)
