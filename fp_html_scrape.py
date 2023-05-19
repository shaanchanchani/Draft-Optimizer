import requests 
from bs4 import BeautifulSoup
import os


def get_draft_urls(base_url):
    urls = []

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
            urls.append(("https://draftwizard.fantasypros.com" + row.find_all('td')[6].find('a')['href'],row.find_all('td')[6].find('a')['href']))
    
    return urls

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
    keys = data[0].keys()
    with open(filename, 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)
        
def main():
    os.makedirs('data', exist_ok=True)
    scrape_draft_picks('https://draftwizard.fantasypros.com/nfl/mock-draft/U9ibVw7r')




if __name__ == "__main__":
    main()