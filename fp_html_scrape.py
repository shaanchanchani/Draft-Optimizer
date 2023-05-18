import requests 
from bs4 import BeautifulSoup
import os

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
        else:
            rank = ''         
        draft_picks.append((title, link, rank))
    
    save_to_csv('.data/draft_data.csv', draft_picks)

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