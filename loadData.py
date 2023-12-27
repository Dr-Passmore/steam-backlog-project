import secrets_store
import requests
import pandas as pd

class dataSetUp:
    def __init__(self) -> None:
        self.api_key = secrets_store.steamKey
        self.steam_id = secrets_store.userID
    
    def getOwnedGames(self):
        url = f'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={self.api_key}&steamid={self.steam_id}&include_appinfo=1&include_played_free_games=1&format=json'
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if 'response' in data and 'games' in data['response']:
                games = data['response']['games']
                game_data = []

                for game in games:
                    appid = game['appid']
                    name = game.get('name', 'N/A')
                    playtime_2weeks = game.get('playtime_2weeks', 0)
                    playtime_forever = game.get('playtime_forever', 0)
                    img_icon_url = game.get('img_icon_url')
                    

                    # Append game data to the list
                    game_data.append({
                        'Game ID': appid,
                        'Name': name,
                        'Playtime (2 weeks)': playtime_2weeks,
                        'Playtime (forever)': playtime_forever,
                        'Icon URL': f"http://media.steampowered.com/steamcommunity/public/images/apps/{appid}/{img_icon_url}.jpg",
                       
                    })

                # Create a DataFrame from the list of game data
                df = pd.DataFrame(game_data)

                return df
            else:
                print("No games found in the library.")
        else:
            print(f"Error: {response.status_code}, {response.text}")
            
    def getgameInfo(self, appid):
        #url = f'http://api.steampowered.com/ISteamUserStats/GetSchemaForGame/v2/?key={self.api_key}&appid={appid}&format=json'
        url = f'http://api.steampowered.com/ISteamUserStats/GetSchemaForGame/v2/?key={self.api_key}&appid={221640}&format=json'
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if 'game' in data:
                game = data['game']
                game_data = []

                name = game.get('gameName', 'N/A')
                game_data.append({
                    'Game ID': appid,
                    'Name': name,
                })

                # Create a DataFrame from the list of game data
                df = pd.DataFrame(game_data)

                return df
            else:
                print("No games found in the library.")
        else:
            print(f"Error: {response.status_code}, {response.text}")