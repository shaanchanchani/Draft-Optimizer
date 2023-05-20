import requests 
from bs4 import BeautifulSoup
import re 
import os
import csv


def get_draft_urls(base_url):
    url_tups = []

    response = requests.get(base_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    table = soup.find('table', {'id': 'draftListTable'})
    tbody = table.find('tbody')
    rows = tbody.find_all('tr')
    
    for row in rows:
        date = row.find_all('td')[0].text
        scoring = row.find_all('td')[1].text
        roster_settings = row.find_all('td')[2].text
        teams = row.find_all('td')[3].text
        rounds = row.find_all('td')[4].text

        # check for 12 teams and PPR scoring
        if "12" in teams and "PPR" in scoring and 'Default' in roster_settings and '15' in rounds:
            url_tups.append(("https://draftwizard.fantasypros.com" + row.find_all('td')[6].find('a')['href'],row.find_all('td')[6].find('a')['href']))
    
    return url_tups

def scrape_draft_picks(draft_url):
    response = requests.get(draft_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    draft_picks = []

    for picked_player in soup.find_all('div', {'class': 'PickedPlayer'}):
        title = picked_player.get('title', '')
        link = picked_player.find('a', href=True)['href']
        rank_div = picked_player.find('div', {'class': 'Rank'})
        if rank_div is not None:
            rank = rank_div.text.strip()
            draft_picks.append({'title': title, 'rank': rank})
    
    return draft_picks


def save_to_csv(filename, data):
    folder = 'data'
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    keys = data[0].keys()
    file_path = os.path.join(folder, filename)
    
    with open(file_path, 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)


def process_csv_files(directory_path):
    # Iterate through all files in the directory
    for filename in os.listdir(directory_path):
        # Create a temporary list to hold cleaned rows
        cleaned_rows = []

        # Open the CSV file
        with open(os.path.join(directory_path, filename), 'r') as file:
            # Create a CSV reader object
            csv_reader = csv.reader(file)

            # Skip the header row
            next(csv_reader)

            # Iterate through each row in the CSV file
            for row in csv_reader:
                # Assuming each row is a single string, you can access the string directly
                row_string = row[0]

                # Use regular expressions to extract the desired information
                match = re.match(r'Pick #(\d+) by (.*?): (.*?) \((.*?) - (.*?)\)', row_string)

                if match:
                    pick_order = match.group(1)
                    team_name = match.group(2)
                    player_name = match.group(3)
                    player_team = match.group(4)
                    player_position = match.group(5)

                    # Create the cleaned row
                    cleaned_row = [pick_order, team_name, player_name, player_team, player_position]
                    cleaned_rows.append(cleaned_row)
        
        # Write cleaned rows back to the CSV file
        if cleaned_rows:
            with open(os.path.join(directory_path, filename), 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(cleaned_rows)


def main():
    #url_tups = get_draft_urls('https://draftwizard.fantasypros.com/football/mock-drafts-directory/')


    # test_data = scrape_draft_picks('https://draftwizard.fantasypros.com/nfl/mock-draft/nJWflp1g')
    # save_to_csv('test', test_data)
    process_csv_files('./data')


    # for tup in url_tups:
    #     link = tup[0]
    #     filename = tup[1]
    #     filename = input_string.split('/')
    #     filename = 'draft_' + parts[-1]

    #     draft_picks = scrape_draft_picks(link)

    #     save_to_csv(filename, draft_picks)
















if __name__ == "__main__":
    main()