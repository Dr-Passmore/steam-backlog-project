import requests
import pandas as pd
import sqlalchemy

import secrets_store

class DatabaseExtract():
    def __init__(self):
        # Load MySQL database user credentials from the secrets store
        sql_user = secrets_store.mysqlUser
        sql_pass = secrets_store.mysqlPassword

        # Set up the SQLAlchemy engine for MySQL connection using the provided credentials
        # 'mysql+pymysql://' is the dialect+driver used to communicate with MySQL
        # '127.0.0.1:3307' is the address of the MySQL server
        # 'steamdata' is the name of the database to connect to
        self.engine = sqlalchemy.create_engine(f'mysql+pymysql://{sql_user}:{sql_pass}@127.0.0.1:3307/steamdata')

    def query_data(self, query):
        with self.engine.connect() as connection:
            result = connection.execute(sqlalchemy.text(query))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
        return df
    
    def uncompletedgames(self):
        query = '''SELECT * FROM steamdata.owned_games
            WHERE Completed = 0 AND Broken = 0 AND ENDLESS = 0 AND selected = 0;'''
        return self.query_data(query)
        
    def completedgames(self):
        query = '''SELECT * FROM steamdata.owned_games
            WHERE Completed = 1 AND Broken = 0 AND ENDLESS = 0;'''
        return self.query_data(query)
    
    def allgames(self):
        query = 'SELECT * FROM steamdata.owned_games;'
        return self.query_data(query)
    
    def gamedetails(self):
        query = 'SELECT * FROM steamdata.game_details;'
        return self.query_data(query)