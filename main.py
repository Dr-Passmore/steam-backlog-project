
import secrets_store
import requests
import loadData
import pandas as pd
import json

api_key = secrets_store.steamKey
steam_id = secrets_store.userID

data_setup = loadData.dataSetUp()

'''
url = f'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={api_key}&steamid={steam_id}&include_appinfo=1&include_played_free_games=1&format=json'

response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    if 'response' in data and 'games' in data['response']:
        games = data['response']['games']
        for game in games:
            appid = game['appid']
            name = game.get('name', 'N/A')
            playtime_2weeks = game.get('playtime_2weeks', 0)
            playtime_forever = game.get('playtime_forever', 0)
            img_icon_url = game.get('img_icon_url')
            img_logo_url = game.get('img_logo_url')

            print(f"Game ID: {appid}, Name: {name}, Playtime (2 weeks): {playtime_2weeks} minutes, Playtime (forever): {playtime_forever} minutes")
            print(f"Icon URL: {img_icon_url}, Logo URL: {img_logo_url}\n")
    else:
        print("No games found in the library.")
else:
    print(f"Error: {response.status_code}, {response.text}")
'''
url = f'http://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/?key={api_key}&steamid={steam_id}&format=json'
response = requests.get(url)
if response.status_code == 200:
    data = response.json()
    if 'response' in data and 'games' in data['response']:
        games = data['response']['games']
        for game in games:
            appid = game['appid']
            name = game.get('name', 'N/A')
            playtime_2weeks = game.get('playtime_2weeks', 0)
            playtime_forever = game.get('playtime_forever', 0)
            img_icon_url = game.get('img_icon_url')

            print(f"Game ID: {appid}, Name: {name}, Playtime (2 weeks): {playtime_2weeks} minutes, Playtime (forever): {playtime_forever} minutes")
            
    else:
        print("No games played recently.")
else:
    print(f"Error: {response.status_code}, {response.text}")



df = data_setup.getOwnedGames()
print(df)

csv_filename = 'owned_games.csv'  # Specify the desired filename
df.to_csv(csv_filename, index=False)

zero_playtime_count = df['Playtime (forever)'] == 0
zero_playtime_games = df[zero_playtime_count]

print(f"Number of games with zero playtime: {len(zero_playtime_games)}")


#url = f'http://api.steampowered.com/ISteamApps/GetAppList/v2/?key={api_key}&format=json'
url = f'https://store.steampowered.com/api/appdetails/?appids={1150440}&key={api_key}'

app_id = 1150440
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    print(data)
    with open('aliens_app_list.json', 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)
    # Find the game information using the app ID
    '''
    game_info = next((game for game in data['applist']['apps'] if game['appid'] == app_id), None)

    if game_info:
        # Print the information for the specific game
        print(f"Game Information for app ID {app_id}:")
        print(f"Game Name: {game_info.get('name', 'N/A')}")
        print(f"Game Tags: {game_info.get('tags', [])}")
        # Add more fields as needed
    else:
        print(f"No information found for the game with app ID {app_id}")
else:
    print(f"Error: {response.status_code}, {response.text}")
'''

url_current_players = f'https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?key={api_key}&appid={app_id}'
url_peak_players = f'https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/?key={api_key}&appid={app_id}&steamid=0'

try:
    response_current_players = requests.get(url_current_players)
    response_current_players.raise_for_status()  # Raise an HTTPError for bad responses
    data_current_players = response_current_players.json()
    with open('aliens_app_current_players.json', 'w', encoding='utf-8') as json_file:
        json.dump(data_current_players, json_file, ensure_ascii=False, indent=4)
    current_players = data_current_players['response']['player_count']
    print(f'Current Players: {current_players}')

    

except requests.exceptions.HTTPError as errh:
    print(f"HTTP Error: {errh}")
except requests.exceptions.RequestException as err:
    print(f"Request Error: {err}")
except Exception as e:
    print(f"An error occurred: {e}")
    

url_global_stats = f'http://api.steampowered.com/ISteamUserStats/GetGlobalStatsForGame/v0001/?key={api_key}&appid={app_id}&count=1'
response_global_stats = requests.get(url_global_stats)

try:
    response_global_stats.raise_for_status()  # Check for HTTP errors

    data_global_stats = response_global_stats.json()

    # Check if the request was successful
    if data_global_stats.get('response', {}).get('result') == 1:
        # Save the response to a JSON file
        with open('aliens_app_user_stats.json', 'w', encoding='utf-8') as json_file:
            json.dump(data_global_stats, json_file, ensure_ascii=False, indent=4)
        
        # Extract and print global statistics
        for stat_name, stat_value in data_global_stats['response']['globalstats']['stats'].items():
            print(f'{stat_name}: {stat_value}')
    else:
        print(f"Error: {data_global_stats.get('response', {}).get('error')}")
except requests.exceptions.HTTPError as http_err:
    print(f"HTTP Error: {http_err}")
except ValueError as json_err:
    print(f"JSON Decode Error: {json_err}")
    print(f"Response Content: {response_global_stats.content}")
except Exception as err:
    print(f"An unexpected error occurred: {err}")