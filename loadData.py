import secrets_store
import requests
import pandas as pd
import sqlalchemy
import time

#import recommendation
import writeData

class dataSetUp:
    def __init__(self) -> None:
        self.api_key = secrets_store.steamKey
        self.steam_id = secrets_store.userID
        sql_user = secrets_store.mysqlUser
        sql_pass = secrets_store.mysqlPassword
        self.engine = sqlalchemy.create_engine(f'mysql+pymysql://{sql_user}:{sql_pass}@127.0.0.1:3307/steamdata')
        self.record_data = writeData.WriteData()
    
    def getOwnedGames(self):
        url = f'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={self.api_key}&steamid={self.steam_id}&include_appinfo=1&include_played_free_games=1&format=json'
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if 'response' in data and 'games' in data['response']:
                games = data['response']['games']
                game_data = []
                df_completed = pd.read_csv(r'gameStatus/completedgames.csv') 
                df_broken = pd.read_csv(r'gameStatus/brokengames.csv')
                df_endless = pd.read_csv(r'gameStatus/endless.csv')
                df_selected = pd.read_csv(r'gameStatus/selectedgames.csv')
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
    
    def updateOwnedGamesInfo(self, df):
        """
        Update the owned games table with the latest information
        """
        stored_df = recommendation.GameSelection().allgames()
        
        merged_data = pd.merge(stored_df, df, on='Game ID', how='outer', suffixes=('_existing', '_new'), indicator=True)
        print(merged_data)
        new_rows = merged_data[merged_data['_merge'] == 'right_only']
        print(new_rows)
        for index, row in new_rows.iterrows():
            new_game = row['Game ID']
            new_game_info = df.loc[df['Game ID'] == new_game]
            write_data = self.record_data.addNewGame(new_game_info)
            if write_data == True:
                print(f"write successful: {new_game_info}")
            else:
                print(f"write failed: {new_game_info}")
        update_rows = merged_data[merged_data['_merge'] == 'both']
        for index, row in update_rows.iterrows():
            # Iterate through rows with differences and alter values
            if row['Name_existing'] != row['Name_new']:
                print(f"Updating Name for Game ID {row['Game ID']}")
                self.record_data.altervalue('owned_games', 'Name', row['Name_new'], row['Game ID']) 
                
            if row['Playtime (2 weeks)_existing'] != row['Playtime (2 weeks)_new']:
                print(f"Updating Playtime (2 weeks) for Game ID {row['Game ID']}")
                self.record_data.altervalue('owned_games', 'Playtime (2 weeks)', row['Playtime (2 weeks)_new'], row['Game ID']) 
                
            if row['Playtime (forever)_existing'] != row['Playtime (forever)_new']:
                print(f"Updating Playtime (forever) for Game ID {row['Game ID']}")
                self.record_data.altervalue('owned_games', 'Playtime (forever)', row['Playtime (forever)_new'], row['Game ID']) 
            
            if row['Completed_existing'] != row['Completed_new']:
                print(f"Updating Completed for Game ID {row['Game ID']}")
                self.record_data.altervalue('owned_games', 'Completed', row['Completed_new'], row['Game ID'])
                
            if row['Broken_existing'] != row['Broken_new']:
                print(f"Updating Broken for Game ID {row['Game ID']}")
                self.record_data.altervalue('owned_games', 'Broken', row['Broken_new'], row['Game ID'])
            
            if row['Endless_existing'] != row['Endless_new']:
                print(f"Updating Endless for Game ID {row['Game ID']}")
                self.record_data.altervalue('owned_games', 'Endless', row['Endless_new'], row['Game ID'])
            
            if row['selected_existing'] != row['selected_new']:
                print(f"Updating selected for Game ID {row['Game ID']}")
                self.record_data.altervalue('owned_games', 'selected', row['selected_new'], row['Game ID'])
            
        # Iterate through rows with differences and accumulate the differences
        #for index, row in merged_data.iterrows():
            #print(row['Game ID'])
            
                
    def get_flag_value(game_id, df):
        """
        Get the flag value based on the Game ID
        """
        if game_id in df['Game ID'].values:
            return 1
        else:
            return 0
    
    def updateGameDetails(self, df):
        owned_games = df
        query = '''
            SELECT * FROM steamdata.game_details;
        '''
        
        df_gamedetails = pd.read_sql(query, self.engine)
        print(df_gamedetails)
        gamedetails_game_ids = df_gamedetails['Game ID'].tolist()

        # Drop rows in df_gamedetails that have a 'Game ID' in owned_games
        owned_games_filtered = owned_games[~owned_games['Game ID'].isin(gamedetails_game_ids)]

        # Load the list of erroring game IDs from erroring.csv if it exists
        try:
            erroring_games = pd.read_csv('erroring.csv')
            erroring_game_ids = erroring_games['Game ID'].tolist()
        except FileNotFoundError:
            erroring_game_ids = []

        new_errors = []
        
        for app_id in owned_games_filtered['Game ID']:
            if app_id in erroring_game_ids:
                print(f"Skipping Game ID {app_id} due to previous errors")
                continue
            #print(app_id)
            #print(type(app_id))
            df_game_details = self.getgameInfo(app_id)

            # Check if the game details DataFrame is not empty
            if not df_game_details.empty:
                # Append the game details to the existing table
                df_game_details.to_sql('game_details', self.engine, if_exists='append', index=False)
            else:
                print(f"Error getting details for Game ID {app_id}")
                new_errors.append({'Game ID': app_id})
        if new_errors:
            df_new_errors = pd.DataFrame(new_errors)
            try:
                df_existing_errors = pd.read_csv('erroring.csv')
                df_combined_errors = pd.concat([df_existing_errors, df_new_errors], ignore_index=True)
            except FileNotFoundError:
                df_combined_errors = df_new_errors

            df_combined_errors.to_csv('erroring.csv', index=False)

    def checkforemptylist(self, dataCheck):
        if not dataCheck:
            return None
        
        return dataCheck
    
    def getgameInfo(self, app_id):
        url = f'https://store.steampowered.com/api/appdetails/?appids={app_id}&key={self.api_key}'
        response = requests.get(url)
        
        if response.status_code == 200:
            try:
                json_data = response.json()
                genres = self.checkforemptylist(json_data.get(f'{app_id}', {}).get('data', {}).get('genres', []))
                platforms = self.checkforemptylist(json_data.get(f'{app_id}', {}).get('data', {}).get('platforms', []))
                name = self.checkforemptylist(json_data.get(f'{app_id}', {}).get('data', {}).get('name', []))
                metacritic = self.checkforemptylist(json_data.get(f'{app_id}', {}).get('data', {}).get('metacritic', []))
                controller_support = self.checkforemptylist(json_data.get(f'{app_id}', {}).get('data', {}).get('controller_support', []))
                is_free = json_data.get(f'{app_id}', {}).get('data', {}).get('is_free', [])
                release_date = self.checkforemptylist(json_data.get(f'{app_id}', {}).get('data', {}).get('release_date', []))
                detailed_description = self.checkforemptylist(json_data.get(f'{app_id}', {}).get('data', {}).get('detailed_description', []))
                about_the_game = self.checkforemptylist(json_data.get(f'{app_id}', {}).get('data', {}).get('about_the_game', []))
                short_description = self.checkforemptylist(json_data.get(f'{app_id}', {}).get('data', {}).get('short_description', []))
                reviews = self.checkforemptylist(json_data.get(f'{app_id}', {}).get('data', {}).get('reviews', []))
                header_image = self.checkforemptylist(json_data.get(f'{app_id}', {}).get('data', {}).get('header_image', []))
                capsule_image = self.checkforemptylist(json_data.get(f'{app_id}', {}).get('data', {}).get('capsule_image', []))
                capsule_imagev5 = self.checkforemptylist(json_data.get(f'{app_id}', {}).get('data', {}).get('capsule_imagev5', [])) 
                website = self.checkforemptylist(json_data.get(f'{app_id}', {}).get('data', {}).get('website', [])) 
                
                if release_date is not None:
                    released = self.checkforemptylist(release_date.get('date'))
                else:
                    released = None
                appid = app_id
                genre_list = []
                if genres is not None:
                    
                    for genre in genres:
                        genre_id = genre.get('id')
                        description = genre.get('description')
                        genre_list.append(description)
                        print(f"Genre ID: {genre_id}, Description: {description}")

                    genres_str = ', '.join(genre_list)
                else:
                    genres_str = None

                genres_str = ', '.join(genre_list)
                if not platforms:
                    windows = None
                    mac = None
                    linux = None
                else:
                    windows = self.checkforemptylist(platforms.get('windows'))
                    mac = self.checkforemptylist(platforms.get('mac'))
                    linux = self.checkforemptylist(platforms.get('linux'))

                try:
                    metacritic_score = metacritic.get('score')
                    metacritic_url = metacritic.get('url')
                except AttributeError:
                    metacritic_score = None
                    metacritic_url = None
                print(f"Game ID: {appid}")
                print(f"Name: {name}")
                print(f"Genre: {genres_str}")
                print(f"Controller Support: {controller_support}")
                print(f"Is Free: {is_free}")
                print(f"Released: {released}")
                print(f"Windows: {windows}")
                print(f"Mac: {mac}")
                print(f"Linux: {linux}")
                print(f"Metacritic Score: {metacritic_score}")
                print(f"Metacritic Url: {metacritic_url}")
                print(f"Reviews: {reviews}")
                print(f"Short Description: {short_description}")
                print(f"About the Game: {about_the_game}")
                print(f"Detailed Description: {detailed_description}")
                print(f"Header Image: {header_image}")
                print(f"Capsule Image: {capsule_image}")
                print(f"Capsule Imagev5: {capsule_imagev5}")
                print(f"Website: {website}")
                df = pd.DataFrame({
                    'Game ID': appid,
                    'Name': name,
                    'Genre': genres_str,
                    'Controller Support': controller_support,
                    'Is Free': is_free,
                    'Released': released,
                    'Windows': windows,
                    'Mac': mac,
                    'Linux': linux,
                    'Metacritic Score': metacritic_score,
                    'Metacritic Url': metacritic_url,
                    'Reviews': reviews,
                    'Short Description': short_description,
                    'About the Game': about_the_game,
                    'Detailed Description': detailed_description,
                    'header_image': header_image,
                    'capsule_image': capsule_image,
                    'capsule_imagev5': capsule_imagev5,
                    'website': website
                }, index=[0])
                time.sleep(3)
                return df
            except:
                return pd.DataFrame()
        else:
            print(f"Error: {response.status_code}, {response.text}")
'''
datatest = dataSetUp()
game_id = '205930'
print(datatest.getgameInfo(game_id))

'''