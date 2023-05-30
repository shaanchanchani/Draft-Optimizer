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
        if str(num_teams) in teams and (str(scoring_format) in scoring and 'Half' not in scoring) and 'Default' in roster_settings and str(num_rounds) in rounds:
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
    
    if len(error_files) > 0:
        print(f"Wrong number of teams in {len(error_files)} of {len(os.listdir(folder))} files checked")

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

    if len(error_files) > 0:
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

    folder =  './dataset3_12_PPR_15'
    num_teams,scoring_format,num_rounds = specify_draft_type()
    # get_raw_data(folder,num_teams,scoring_format,num_rounds)

    links = ['https://draftwizard.fantasypros.com/football/mock-drafts-directory/',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=VrV-uzSGYbq4WX5PpKsxHnUxm1qN5DUeib4cSYqinFwYBBXkte-nrDLHjSo2DKb7',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=e6mgk4GiKm6Mp-q-eTuhgL8-4Sv0QcDf2AWFhk6YWSZgBbv42_YDzSjKr1J6voCt',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=L983Zsk1QO8fNSG2LYv3hKnv1CeJSO-3KP3PPR0foavlwJ4vUnNggN_oBVW9ixMc',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=KZP3y0EA-YsHgMS9MmCyLgS9QTtj1DbXOaUBW4Krs4Oe-u2IeNYiF6qTx7X8GuAU',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=Jms5h-YPOlTp27ORFJ1tbrxd8JJl5yJOQ3-jqS3aC8xe0ltv3F7t2flhRCnUA2tK',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=lg3Tj5XsloTjO3kBwic1fQ7fddYvexbMa6HcPnEf-GOfm2rhsEq5TpErk9yCQ9AH',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=apU3JfQ-BuOWjuDvO3kOEZEwds7SDCm_CVFAjfuKdz9AOACLLBTQtXjzGS5PLBBB',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=JTp_ONIfY7xI9DdJ637OM5OUA7EZNxM32gQFrA27Oyzrkm4sORKzetBCm8pPL17o',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=rlooacoWCszh-4-6Psak9sloJbCkEftAAba5F1hyeAg_NG6c84uIokgjNfbAcekp',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=x6OVhGdKKQIJRDT1XvyOHAOZKyOypIqkwbzxZutNY7as-lx8m1iowyTZ5rFc5dRo',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=PCV0Ylo9L9M690a73FLIYZYmVDVfd3cLY01RnsD80F3n1i5gc6P0rS6z_FcOzL8I',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=gA9TPYwxGKTL-ip8La3ue_FGRcT7lMVJXLvu4dc6ceOd2V7ytxS3yJOPl85ocmeu',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=GokRm_dYnUyTLgfUFRkYuxMRBHcId1CiFw0S05XcBwopaNYeUGERmjx6Ck7TUAN9',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=sA0QQSLDq4-dAS48qFCiQapG5AZQkyLj4dmkSeRH-BCA8zDeGZzpoC1QL80bTixw',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=ocVv6g5FrVpDmkaZiXxRKDMIj1PsKwcraEIAqVxyoHM6XbvrKPgoHXgGeWFBFTZv',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=QXfHVsiYPMOPK21HDsJsTbqZKwU4S0wPIZmyS5dJIznWkPk3_Pg6FJN0oGdZ0RuN',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=mnKZ9Tg0AKFslK7nnVcqdK5YC-yyi0LK1Oi4-Rj6H194fQ6S_5Chzl8vy1Ikr5E6',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=85cmqTE6b95cTekEmQ8G01Y5lPqWKQtHqE_ZlOH3BHSBLx3hUZSgMI_7nKKjhTJI',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=Jbek7LiX0yKCkLOgLXTLZBd1sb-9JROcQwDN4IK4B-Dw02GRTTRMToIg-YXay-2N',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=k0xIbhsd8TQDiMX6FfpuihDXaaSH9EMFaQxyenfhN7MdUzCAzJ5a3kaPDm6lWaeP',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=CWezIopdPdCJIPfTDzxT0hhGpXjpo-jLTjpZVuf-gyOTqhumZyBfthyqPmBbT1tr',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=gEYdREViqtbhNJXnd7wmVUpjHcNAM3FDTyxa001nJeMP0BEw_FhHxxD-FKq28pso',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=zCFzex_JiiNVrbc7lq6VJt0BBVDrIL6Pt-v7kezzCW3aK4ybQllKevolEBf22seW',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=awrRk-KEO-DRoiPtaWH3f4RDy_y3V0aX1DHGO39J-dHD04o7KybNi3FjMK_UB27g',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=FDNsA--7osGJag2TaluEUNxEiagVBjURR6ex0EwC9-B-XPedOo_rjgQQGSD34tv6',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=xvPO-dEpE3JdopiWMvEC3QHBhtG1zQFeA5xrKLbmYqZgfcY40WyaPOFdePYprR-g',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=suG4qH0BJq-hL9Qcd5I1-xATD3E2Fhse5im4neP2V_7LaworswoQO7_TeiYwyjaV',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=Cis41N-morz_1k6ozai1RDN7ZV-SCBuQ4DLfhoSP5IG6fWi3kweXYxOCrcPgF7us',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=dcLWz8e5cGSXvVVmJQNCnMtPVFdve0c5sPmgHXfkFjWhIdQ33PPZZv2pseZxZN2l',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=Et8mzP7wIfJLPM0ew0--iK0fEH3_0ao-ysBJeLP3pBrI_WDRCu-dYfIJ3CCpmSrY',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=D3DBm2hhcEEhrAMYayNoBAvWgjSXQjhEUPqMCo8TiyVNzNgxKFwFIvacxeZ7Z0bM',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=1Rw3CFj-LWWjdoA6PzNRM_NTLxkxuCjkOZ3Dpf-l6dz_j1fR2G_2w8naUk3k5V3a',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=GCdEp0SoJKnXoLG72yMcb7xf9rbHzEr7XgCMtDUP1XMv96H5LNvBWj7yUsWMMNbF',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=MuvD__IuZCyg2rF5pCz5hGDNMDG5mg3BIpixuEXm8UjNR00Rs8rbWGcae0O47WuB',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=i30bNAVdChZTDMsGxGJbxZSJZiW7sopX0b6y120MBv23bsA5d5X0JbuBfdxlgJLS',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=HTyJGH6T3Fx9ZwwEG77_fGCCs3svs59w6Ss7yMyeYIx76rDLGVW_8Wr331PTMQgq',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=vxtMYg1S8pHKL3OWhdZnQfzshHjMNO8wcdEHQa1NizQbOGiEyMNT6cGTPKSFCEIn',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=lC1UlC3c6ygHeprx0PZka1p4uXjDYAwPm_TC9X14Am0hMLqLAxmQIE9hHhlw1hjU',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=9yAq_tCn1mnly0ULGtQ0Mx0LXeJ8fytciDvGcF8DThjv5uGbN5VwxtRs4-LYW0Xh',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=eQransVR-6g79qy5cs9PuMf2ZJe8PJnfhPKduRUd1tNHmuR8tWgoJIW-ebhnelV4',
    'https://draftwizard.fantasypros.com/football/mock-drafts-directory/?start=DsRbyOIeYYka8J3s7szaudD0RwmzeKnBAfFUPD7nsNGtZq0JCYe8gC2FImabRyqT']
    
    for link in links:
            url_tups = get_draft_urls(link,num_teams,scoring_format,num_rounds)

            for tup in url_tups:
                link = tup[0]
                filename = tup[1]
                filename = filename.split('/')
                filename = 'draft_' + filename[-1]

                draft_picks = scrape_draft_picks(link)
                save_to_csv(folder,filename,draft_picks)


    clean_data(folder,scoring_format)
    add_headers(folder)
    check_num_teams(folder,num_teams)
    encode_team_names(folder)
    check_pick_order(folder, num_teams, num_rounds)



if __name__ == "__main__":
    main()