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
                df_completed = pd.read_csv(r'gameStatus\completedgames.csv') 
                df_broken = pd.read_csv(r'gameStatus\brokengames.csv')
                df_endless = pd.read_csv(r'gameStatus\endless.csv')
                df_selected = pd.read_csv(r'gameStatus\selectedgames.csv')
                for game in games:
                    appid = game['appid']
                    name = game.get('name', 'N/A')
                    playtime_2weeks = game.get('playtime_2weeks', 0)
                    playtime_forever = game.get('playtime_forever', 0)
                    img_icon_url = game.get('img_icon_url')
                    completed_game = dataSetUp.get_flag_value(appid, df_completed)
                    broken_game = dataSetUp.get_flag_value(appid, df_broken)
                    endless_game = dataSetUp.get_flag_value(appid, df_endless)
                    selected_game = dataSetUp.get_flag_value(appid, df_selected)
                    

                    # Append game data to the list
                    game_data.append({
                        'Game ID': appid,
                        'Name': name,
                        'Playtime (2 weeks)': playtime_2weeks,
                        'Playtime (forever)': playtime_forever,
                        'Icon URL': f"http://media.steampowered.com/steamcommunity/public/images/apps/{appid}/{img_icon_url}.jpg",
                        'Completed': completed_game,
                        'Broken': broken_game,
                        'Endless': endless_game,
                        'selected': selected_game
                       
                    })

                # Create a DataFrame from the list of game data
                df = pd.DataFrame(game_data)

                return df
            else:
                print("No games found in the library.")
        else:
            print(f"Error: {response.status_code}, {response.text}")
    
    def get_flag_value(game_id, df):
        """
        Get the flag value based on the Game ID
        """
        if game_id in df['Game ID'].values:
            return 1
        else:
            return 0
        
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