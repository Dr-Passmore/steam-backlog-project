# Standard library imports
import time

# Third-party library imports
import requests
import pandas as pd
import sqlalchemy

# Local application imports
import secrets_store
import recommendation
import writeData

class dataSetUp:
    def __init__(self) -> None:
        '''
        Initialisation of the dataSetUp class.
        
        This method initialises the dataSetUp class by setting up necessary configurations 
        such as API keys, Steam user ID, and database connection. It also initializes a 
        writeData object for recording data.
        '''
        # Load API key for Steam from the secrets store
        self.api_key = secrets_store.steamKey

        # Load Steam user ID from the secrets store
        self.steam_id = secrets_store.userID

        # Load MySQL database user credentials from the secrets store
        sql_user = secrets_store.mysqlUser
        sql_pass = secrets_store.mysqlPassword

        # Set up the SQLAlchemy engine for MySQL connection using the provided credentials
        # 'mysql+pymysql://' is the dialect+driver used to communicate with MySQL
        # '127.0.0.1:3307' is the address of the MySQL server
        # 'steamdata' is the name of the database to connect to
        self.engine = sqlalchemy.create_engine(f'mysql+pymysql://{sql_user}:{sql_pass}@127.0.0.1:3307/steamdata')
        
        # Initialise a writeData object to handle data writing operations
        self.record_data = writeData.WriteData()
    
    def getOwnedGames(self):
        '''
        Fetch owned games from the Steam API and compile the information into a DataFrame.
        
        This method sends a request to the Steam API to get the list of owned games for the user. 
        It processes the response to extract relevant information and combines it with additional 
        data from local CSV files indicating game status (completed, broken, endless, selected). 
        The method returns a DataFrame containing the compiled game information.
        
        Returns:
            DataFrame: A DataFrame containing details of owned games.
        '''
        # Construct the URL for the Steam API request to get owned games
        url = f'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={self.api_key}&steamid={self.steam_id}&include_appinfo=1&include_played_free_games=1&format=json'
        
        # Send the GET request to the Steam API
        response = requests.get(url)

        # Check if the response from the API is successful (status code 200)
        if response.status_code == 200:

            # Parse the JSON response
            data = response.json() 

            # Check if the response contains game information
            if 'response' in data and 'games' in data['response']:
                # Extract the list of games
                games = data['response']['games']
                game_data = []
                
                # Load additional game status information from local CSV files
                df_completed = pd.read_csv(r'gameStatus/completedgames.csv') 
                df_broken = pd.read_csv(r'gameStatus/brokengames.csv')
                df_endless = pd.read_csv(r'gameStatus/endless.csv')
                df_selected = pd.read_csv(r'gameStatus/selectedgames.csv')

                # Iterate through each game in the list
                for game in games:
                    # Extract the game ID
                    appid = game['appid']

                    # Extract the game name, default to 'N/A' if not available
                    name = game.get('name', 'N/A')

                    # Extract playtime in the last 2 weeks, default to 0
                    playtime_2weeks = game.get('playtime_2weeks', 0)

                    # Extract total playtime, default to 0
                    playtime_forever = game.get('playtime_forever', 0)

                    # Extract the icon URL
                    img_icon_url = game.get('img_icon_url')

                    # Get the game status flags from the corresponding CSV files
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
                # Print a message if no games are found
                print("No games found in the library.")
        else:
            # Print an error message if the API request fails
            print(f"Error: {response.status_code}, {response.text}")
    
    def updateOwnedGamesInfo(self, df):
        '''
        Update the owned games table with the latest information.
        
        This method updates the owned games information in the database by comparing the 
        existing stored data with the newly fetched data. It identifies new games to be added 
        and existing games that need their information updated.
        
        Parameters:
            df (DataFrame): DataFrame containing the latest information about owned games.
        '''
        # Fetch the existing stored games data using the recommendation module
        stored_df = recommendation.GameSelection().allgames()
        
         # Merge the existing data with the new data on 'Game ID'
        # 'how' = 'outer' ensures all records are included
        # 'suffixes' differentiate between existing and new data columns
        # 'indicator' = True adds a column '_merge' to indicate the source of each row
        merged_data = pd.merge(stored_df, df, on='Game ID', how='outer', suffixes=('_existing', '_new'), indicator=True)
        
        # Print the merged data for debugging purposes
        print(merged_data)

        # Identify new rows (games that are in the new data but not in the existing data)
        new_rows = merged_data[merged_data['_merge'] == 'right_only']

        # Print the new rows for debugging purposes
        print(new_rows)

        # Iterate through each new row and add the new game to the database
        for index, row in new_rows.iterrows():
            # Extract the Game ID of the new game
            new_game = row['Game ID']

            # Get the new game's information from the new data DataFrame
            new_game_info = df.loc[df['Game ID'] == new_game]

            # Add the new game information to the database
            write_data = self.record_data.addNewGame(new_game_info)

            if write_data == True:
                # Print success message if the write operation is successful
                print(f"write successful: {new_game_info}")
            else:
                # Print failure message if the write operation fails
                print(f"write failed: {new_game_info}")

        # Identify rows that exist in both the existing and new data
        update_rows = merged_data[merged_data['_merge'] == 'both']

        # Iterate through each row that exists in both data sets and update fields where there are differences
        for index, row in update_rows.iterrows():
            # Check and update the 'Name' field if there is a difference
            if row['Name_existing'] != row['Name_new']:
                print(f"Updating Name for Game ID {row['Game ID']}")
                self.record_data.altervalue('owned_games', 'Name', row['Name_new'], row['Game ID']) 

            # Check and update the 'Playtime (2 weeks)' field if there is a difference    
            if row['Playtime (2 weeks)_existing'] != row['Playtime (2 weeks)_new']:
                print(f"Updating Playtime (2 weeks) for Game ID {row['Game ID']}")
                self.record_data.altervalue('owned_games', 'Playtime (2 weeks)', row['Playtime (2 weeks)_new'], row['Game ID']) 

            # Check and update the 'Playtime (forever)' field if there is a difference    
            if row['Playtime (forever)_existing'] != row['Playtime (forever)_new']:
                print(f"Updating Playtime (forever) for Game ID {row['Game ID']}")
                self.record_data.altervalue('owned_games', 'Playtime (forever)', row['Playtime (forever)_new'], row['Game ID']) 
            
            # Check and update the 'Completed' field if there is a difference
            if row['Completed_existing'] != row['Completed_new']:
                print(f"Updating Completed for Game ID {row['Game ID']}")
                self.record_data.altervalue('owned_games', 'Completed', row['Completed_new'], row['Game ID'])
                
            # Check and update the 'Broken' field if there is a difference
            if row['Broken_existing'] != row['Broken_new']:
                print(f"Updating Broken for Game ID {row['Game ID']}")
                self.record_data.altervalue('owned_games', 'Broken', row['Broken_new'], row['Game ID'])
            
            # Check and update the 'Endless' field if there is a difference
            if row['Endless_existing'] != row['Endless_new']:
                print(f"Updating Endless for Game ID {row['Game ID']}")
                self.record_data.altervalue('owned_games', 'Endless', row['Endless_new'], row['Game ID'])
            
            # Check and update the 'selected' field if there is a difference
            if row['selected_existing'] != row['selected_new']:
                print(f"Updating selected for Game ID {row['Game ID']}")
                self.record_data.altervalue('owned_games', 'selected', row['selected_new'], row['Game ID'])
            
        # Iterate through rows with differences and accumulate the differences
        #for index, row in merged_data.iterrows():
            #print(row['Game ID'])
            
                
    def get_flag_value(game_id, df):
        '''
        Helper method to get the flag value for a game from a DataFrame.
        
        This method checks if a given game ID (appid) is present in a provided DataFrame.
        If present, it returns 1 (true); otherwise, it returns 0 (false).
        
        Parameters:
            appid (int): The ID of the game to check.
            df (DataFrame): The DataFrame to check against.
        
        Returns:
            int: 1 if the game ID is present in the DataFrame, 0 otherwise.
        '''
        # Check if the provided list is empty
        if game_id in df['Game ID'].values:
            return 1
        
        # Return the original list if it is not empty
        else:
            return 0
    
    def updateGameDetails(self, df):
        '''
        Update the game details table with the latest information.
    
        This method updates the game details information in the database by fetching new game details
        for games that are owned but not yet in the game details table. It also handles error logging
        for game IDs that fail to fetch details.
        
        Parameters:
            df (DataFrame): DataFrame containing the owned games information.
        '''
        owned_games = df

        # Query to select all existing game details from the database
        query = '''
            SELECT * FROM steamdata.game_details;
        '''
        
        # Execute the query and store the result in a DataFrame
        df_gamedetails = pd.read_sql(query, self.engine)

        # Print the existing game details for debugging purposes
        print(df_gamedetails)

        # Get a list of existing game IDs from the game details DataFrame
        gamedetails_game_ids = df_gamedetails['Game ID'].tolist()

        # Filter out games that are already in the game details table from the owned games DataFrame
        owned_games_filtered = owned_games[~owned_games['Game ID'].isin(gamedetails_game_ids)]

        # Load the list of erroring game IDs from erroring.csv if it exists
        try:
            erroring_games = pd.read_csv('erroring.csv')
            erroring_game_ids = erroring_games['Game ID'].tolist()
        except FileNotFoundError:
            # Initialise with an empty list if the file does not exist
            erroring_game_ids = []
        
        # Initialise an empty list to store new errors
        new_errors = []
        
        # Iterate through the filtered list of owned game IDs
        for app_id in owned_games_filtered['Game ID']:
            # Skip game IDs that have previously errored
            if app_id in erroring_game_ids:
                print(f"Skipping Game ID {app_id} due to previous errors")
                continue
            
            # Fetch game details for the current game ID
            df_game_details = self.getgameInfo(app_id)

            # Check if the game details DataFrame is not empty
            if not df_game_details.empty:
                # Append the game details to the existing table in the database
                df_game_details.to_sql('game_details', self.engine, if_exists='append', index=False)
            else:
                # Log an error message and add the game ID to the new errors list
                print(f"Error getting details for Game ID {app_id}")
                new_errors.append({'Game ID': app_id})

        # If there are new errors, update the erroring.csv file
        if new_errors:
            # Convert the new errors list to a DataFrame
            df_new_errors = pd.DataFrame(new_errors)

            try:
                # Load existing errors from erroring.csv
                df_existing_errors = pd.read_csv('erroring.csv')
                # Combine the new errors with the existing errors
                df_combined_errors = pd.concat([df_existing_errors, df_new_errors], ignore_index=True)
            except FileNotFoundError:
                # If erroring.csv does not exist, use only the new errors
                df_combined_errors = df_new_errors
            
            # Write the combined errors back to erroring.csv
            df_combined_errors.to_csv('erroring.csv', index=False)

    def checkforemptylist(self, dataCheck):
        '''
        Check for an empty list.
        
        This method checks if the provided list (dataCheck) is empty. If the list is empty,
        it returns None. Otherwise, it returns the original list.
        
        Parameters:
            dataCheck (list): The list to check.
        
        Returns:
            list or None: Returns None if the list is empty, otherwise returns the original list.
        '''
        # Check if the provided list is empty
        if not dataCheck:
            return None
        # Return the original list if it is not empty
        return dataCheck
    
    def getgameInfo(self, app_id):
        '''
        Fetches detailed information for a given game from the Steam Store API and returns it as a DataFrame.

        Parameters:
            app_id (int): The ID of the game for which information is to be fetched.

        Returns:
            DataFrame: A DataFrame containing detailed game information if the API call is successful,
                    otherwise returns an empty DataFrame.
        '''
        # Construct the URL for the Steam Store API request
        url = f'https://store.steampowered.com/api/appdetails/?appids={app_id}&key={self.api_key}'

        # Send the GET request to the API
        response = requests.get(url)
        
        # Check if the request was successful
        if response.status_code == 200:
            try:
                # Parse the JSON response
                json_data = response.json()

                # Extract various pieces of game information, using helper method to handle empty lists
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
                
                # Extract the release date if available
                if release_date is not None:
                    released = self.checkforemptylist(release_date.get('date'))
                else:
                    released = None

                appid = app_id

                # Prepare genre list if available
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

                # Extract platform information if available
                if not platforms:
                    windows = None
                    mac = None
                    linux = None
                else:
                    windows = self.checkforemptylist(platforms.get('windows'))
                    mac = self.checkforemptylist(platforms.get('mac'))
                    linux = self.checkforemptylist(platforms.get('linux'))
                
                # Extract Metacritic information if available
                try:
                    metacritic_score = metacritic.get('score')
                    metacritic_url = metacritic.get('url')
                except AttributeError:
                    metacritic_score = None
                    metacritic_url = None

                # Print extracted information for debugging purposes
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
                
                # Create a DataFrame with the extracted game information
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
                
                # Pause to avoid hitting API rate limits
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