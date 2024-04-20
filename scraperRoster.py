import requests
from bs4 import BeautifulSoup
import re
import json

# List of URLs for team rosters
urls = [
    "https://www.espn.com/nba/team/roster/_/name/bos/boston-celtics",
    "https://www.espn.com/nba/team/roster/_/name/bkn/brooklyn-nets",
    "https://www.espn.com/nba/team/roster/_/name/ny/new-york-knicks",
    "https://www.espn.com/nba/team/roster/_/name/phi/philadelphia-76ers",
    "https://www.espn.com/nba/team/roster/_/name/tor/toronto-raptors",
    "https://www.espn.com/nba/team/roster/_/name/gs/golden-state-warriors",
    "https://www.espn.com/nba/team/roster/_/name/lac/la-clippers",
    "https://www.espn.com/nba/team/roster/_/name/lal/los-angeles-lakers",
    "https://www.espn.com/nba/team/roster/_/name/phx/phoenix-suns",
    "https://www.espn.com/nba/team/roster/_/name/sac/sacramento-kings",
    "https://www.espn.com/nba/team/roster/_/name/chi/chicago-bulls",
    "https://www.espn.com/nba/team/roster/_/name/cle/cleveland-cavaliers",
    "https://www.espn.com/nba/team/roster/_/name/det/detroit-pistons",
    "https://www.espn.com/nba/team/roster/_/name/ind/indiana-pacers",
    "https://www.espn.com/nba/team/roster/_/name/mil/milwaukee-bucks",
    "https://www.espn.com/nba/team/roster/_/name/dal/dallas-mavericks",
    "https://www.espn.com/nba/team/roster/_/name/hou/houston-rockets",
    "https://www.espn.com/nba/team/roster/_/name/mem/memphis-grizzlies",
    "https://www.espn.com/nba/team/roster/_/name/no/new-orleans-pelicans",
    "https://www.espn.com/nba/team/roster/_/name/sa/san-antonio-spurs",
    "https://www.espn.com/nba/team/roster/_/name/den/denver-nuggets",
    "https://www.espn.com/nba/team/roster/_/name/min/minnesota-timberwolves",
    "https://www.espn.com/nba/team/roster/_/name/okc/oklahoma-city-thunder",
    "https://www.espn.com/nba/team/roster/_/name/por/portland-trail-blazers",
    "https://www.espn.com/nba/team/roster/_/name/utah/utah-jazz",
    "https://www.espn.com/nba/team/roster/_/name/atl/atlanta-hawks",
    "https://www.espn.com/nba/team/roster/_/name/cha/charlotte-hornets",
    "https://www.espn.com/nba/team/roster/_/name/mia/miami-heat",
    "https://www.espn.com/nba/team/roster/_/name/orl/orlando-magic",
    "https://www.espn.com/nba/team/roster/_/name/wsh/washington-wizards"
]

# Define headers to mimic a browser request
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}

# Dictionary to store team rosters
team_rosters = {}

# Iterate over each URL
for url in urls:
    # Extract team name from the URL
    team_name = url.split("/")[-1].replace("-", " ").title()

    # Send a GET request to the URL with headers
    response = requests.get(url, headers=headers)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")

        # Find the section with class "Roster"
        roster_section = soup.find("section", class_="Roster")

        # Check if the roster section was found
        if roster_section:
            # Find the table inside the roster section
            roster_table = roster_section.find("table")

            # Check if the roster table was found
            if roster_table:
                players = []  # List to store player names

                # Now you can iterate over rows and cells to extract the data
                rows = roster_table.find_all("tr")
                for row in rows:
                    cells = row.find_all("td")
                    if len(cells) > 1:
                        player_name = re.sub(r'\d+', '', cells[1].text.strip())
                        players.append(player_name.strip()) 

                # Store team roster in dictionary
                team_rosters[team_name] = players
            else:
                print(f"Roster table not found for {url}.")
        else:
            print(f"Roster section not found for {url}.")
    else:
        print(f"Failed to retrieve data from {url}. Status code: {response.status_code}")

# Print the team rosters dictionary with JSON formatting
print(json.dumps(team_rosters, indent=4))
