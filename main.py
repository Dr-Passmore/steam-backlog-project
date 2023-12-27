#!D:/Creative projects/Coding/Python/steam backlog project/myenv/Scripts/python.exe


import secrets
import requests
import loadData
import pandas as pd

api_key = secrets.steamKey
steam_id = secrets.userID

loadData.dataSetUp(api_key, steam_id)

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
            img_logo_url = game.get('img_logo_url')

            print(f"Game ID: {appid}, Name: {name}, Playtime (2 weeks): {playtime_2weeks} minutes, Playtime (forever): {playtime_forever} minutes")
            #print(f"Icon URL: {img_icon_url}, Logo URL: {img_logo_url}\n")
    else:
        print("No games played recently.")
else:
    print(f"Error: {response.status_code}, {response.text}")

