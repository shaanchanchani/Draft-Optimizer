import requests 
from bs4 import BeautifulSoup
import re 
import os
import csv
import numpy as np 
import pandas as pd 

def get_draft_urls(base_url,num_teams,scoring_format,num_rounds):
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
        if str(num_teams) in teams and str(scoring_format) in scoring and 'Default' in roster_settings and str(num_rounds) in rounds:
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

def save_to_csv(folder,filename, data):
    if not os.path.exists(folder):
        os.makedirs(folder)
    keys = data[0].keys()
    file_path = os.path.join(folder, filename)  
    with open(file_path, 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)

def clean_data(folder,scoring_format):
    adp_df_path = f'./{scoring_format}.csv'
    
    df = pd.read_csv(adp_df_path)
    df = df[['Player','AVG']]
    df = df.rename(columns={'AVG': 'ADP', 'Player' : 'player'})
    df = df.dropna(how = 'all')
    default_adp = df['ADP'].max() + 10

    adp_dict = df.set_index('player')['ADP'].to_dict()
    
    for filename in os.listdir(folder):
        cleaned_rows = []
        with open(os.path.join(folder, filename), 'r') as file:
            csv_reader = csv.reader(file)
            next(csv_reader)
            for row in csv_reader:
                row_string = row[0]
                match = re.match(r'Pick #(\d+) by (.*?): (.*?) \((.*?) - (.*?)\)', row_string)
                if match:
                    pick_order = match.group(1)
                    team_name = match.group(2)
                    player_name = match.group(3)
                    player_team = match.group(4)
                    player_position = match.group(5)

                    if player_name in adp_dict.keys():
                        adp = adp_dict[player_name]
                    else:
                        adp = default_adp #Do not have ADP values for Kickers and DST 
                        #print(f'Assigned Default ADP to: {player_name}')
                    cleaned_row = [pick_order, team_name, player_name, player_team, player_position,adp]
                    cleaned_rows.append(cleaned_row)
        if cleaned_rows:
            with open(os.path.join(folder, filename), 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(cleaned_rows)

def add_headers(folder):
    header = ['pick_num', 'team_name', 'player', 'player_team', 'player_pos','ADP']
    for filename in os.listdir(folder):
        if not os.path.isdir(os.path.join(folder, filename)): 
            file_path = os.path.join(folder, filename)
            with open(file_path, 'r') as file:
                lines = file.readlines()
            lines.insert(0, ','.join(header) + '\n')
            with open(file_path, 'w') as file:
                file.writelines(lines)

def check_num_teams(folder, num_teams):
    error_files = []

    for filename in os.listdir(folder):
        if not os.path.isdir(os.path.join(folder, filename)):
            file_path = os.path.join(folder, filename)
            df = pd.read_csv(file_path)  
            teams = df['team_name'].unique()
            if len(teams) != num_teams:
                error_files.append(filename)

    print(f"Wrong number of teams in {len(error_files)}/{len(os.listdir(folder))} files checked")

    for filename in error_files:
        file_path = os.path.join(folder,filename)
        df = pd.read_csv(file_path)
        teams = df['team_name'].unique()
        print(f"File '{filename}': Number of unique teams is {len(teams)}, expected {num_teams}.")

        confirmation = input('Delete file? (Y/N):')
        if confirmation.upper() == 'Y':
            try:
                os.remove(file_path)
                print(f"File '{file_path}' successfully deleted.")
            except OSError as e:
                print(f'Error occurred while deleting file: {e}')
        else:
            print(f"File '{file_path}' will not be deleted.")
 
def encode_team_names(folder):
    for filename in os.listdir(folder):
        if not os.path.isdir(os.path.join(folder,filename)):
            file_path = os.path.join(folder,filename)
            df = pd.read_csv(file_path)
            teams = df['team_name'].unique()
            team_mapping = {team: f'Team{i+1}' for i, team in enumerate(teams)}
            df['team_name'] = df['team_name'].map(team_mapping)
            df.to_csv(file_path,index = False)

def check_pick_order(folder, num_teams, num_rounds):
    error_files = []

    for filename in os.listdir(folder):
        if not os.path.isdir(os.path.join(folder,filename)):
            file_path = os.path.join(folder,filename)
            df = pd.read_csv(file_path)
            expected_draft_order = (list(range(1,(num_teams+1))) + list(range(num_teams,0,-1)))*num_rounds
            expected_draft_order = expected_draft_order[:int(len(expected_draft_order)/2)]
            draft_order_in_file = [int(''.join(filter(str.isdigit, element))) for element in df['team_name']]

            if expected_draft_order != draft_order_in_file:
                error_files.append(filename)

    print(f"Draft order doesn't match expected draft order in {len(error_files)}/{len(os.listdir(folder))} files checked")

    for filename in error_files:
        print(f"File '{filename}': Draft order incorrect")
        file_path = os.path.join(folder,filename)
        confirmation = input('Delete file? (Y/N):')
        if confirmation.upper() == 'Y':
            try:
                os.remove(file_path)
                print(f"File '{file_path}' successfully deleted.")
            except OSError as e:
                print(f'Error occurred while deleting file: {e}')
        else:
            print(f"File '{file_path}' will not be deleted.")

def specify_draft_type():
    while True:
        try:
            num_teams = int(input("Enter number of teams: "))
            break  
        except ValueError:
            print("Invalid input. Please enter an integer.")

    while True:
        scoring_format = input("Enter 'PPR' for PPR or 'STD' for Standard: ")
        if scoring_format == 'PPR' or scoring_format == 'STD':
            break
        else:
            print("Invalid input. Enter 'PPR' for PPR or 'STD' for Standard: ")
    
    while True:
        try:
            num_rounds = int(input("Enter number of rounds in draft: "))
            break  
        except ValueError:
            print("Invalid input. Please enter an integer.")
    
    #print(f"Scraping data for {num_teams} team {scoring_format} {num_rounds} round drafts (default roster settings)")

    return num_teams,scoring_format,num_rounds

def get_raw_data(folder,num_teams,scoring_format,num_rounds):
    links = []
    while True:
        link = input("Enter a mock draft directory link or '0' to finish: ")
        
        if link == '0':
            break
        
        links.append(link)

    if len(links) != 0:
        for link in links:
            url_tups = get_draft_urls(link,num_teams,scoring_format,num_rounds)

            for tup in url_tups:
                link = tup[0]
                filename = tup[1]
                filename = filename.split('/')
                filename = 'draft_' + filename[-1]

                draft_picks = scrape_draft_picks(link)
                save_to_csv(folder,filename,draft_picks)



def main():
    folder =  './dataset3'
    num_teams,scoring_format,num_rounds = specify_draft_type()
    get_raw_data(folder,num_teams,scoring_format,num_rounds)
    clean_data(folder,scoring_format)
    add_headers(folder)
    check_num_teams(folder,num_teams)
    encode_team_names(folder)
    check_pick_order(folder, num_teams, num_rounds)


    


if __name__ == "__main__":
    main()