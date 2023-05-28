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

        # check for 12 teams and PPR scoring
        if num_teams in teams and scoring_format in scoring and 'Default' in roster_settings and num_rounds in rounds:
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


def process_csv_files(folder):
    # Iterate through all files in the directory
    for filename in os.listdir(folder):
        # Create a temporary list to hold cleaned rows
        cleaned_rows = []
        # Open the CSV file
        with open(os.path.join(folder, filename), 'r') as file:
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
                    cleaned_row = [pick_order, team_name, player_name, player_team, player_position]
                    cleaned_rows.append(cleaned_row)
        if cleaned_rows:
            with open(os.path.join(folder, filename), 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(cleaned_rows)


def main():

    folder =  './dataset2'

    while True:
        try:
            num_teams = int(input("Enter number of teams: "))
            break  
        except ValueError:
            print("Invalid input. Please enter an integer.")

    while True:
        scoring_format = input("Enter 'P' for PPR or 'S' for Standard: ")
        if scoring_format == 'P' or scoring_format == 'S':
            break
        else:
            print("Invalid input. Enter 'P' or 'S'.")
    
    while True:
        try:
            num_rounds = int(input("Enter number of rounds in draft: "))
            break  
        except ValueError:
            print("Invalid input. Please enter an integer.")
    
    links = []

    while True:
        link = input("Enter a link or '0' to finish: ")
        
        if link == '0':
            break
        
        links.append(link)

    for link in links:
        url_tups = get_draft_urls(link,num_teams,scoring_format,num_rounds)

        for tup in url_tups:
            link = tup[0]
            filename = tup[1]
            filename = filename.split('/')
            filename = 'draft_' + filename[-1]

            draft_picks = scrape_draft_picks(link)
            save_to_csv(folder,filename,draft_picks)

        process_csv_files(folder)


    


if __name__ == "__main__":
    main()