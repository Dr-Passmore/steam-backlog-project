import sqlalchemy
from sqlalchemy import text
import secrets_store
import pandas as pd

class WriteData:
    def __init__(self):
        sql_user = secrets_store.mysqlUser
        sql_pass = secrets_store.mysqlPassword
        self.engine = sqlalchemy.create_engine(f'mysql+pymysql://{sql_user}:{sql_pass}@127.0.0.1:3307/steamdata')

    def writeData(self, df, table_name):
        
        df.to_sql(table_name, self.engine, if_exists='replace', index=False, index_label='Game ID')
       
        return True

    def writeGameInfo(self, df):
        table_name = 'gameinfo'
        df.to_sql(table_name, self.engine, if_exists='append', index=False, index_label='Game ID')
        return True
    
    def updateOwnedGameStatus(self, df):
        table_name = 'owned_games'
        df.to_sql(table_name, self.engine, if_exists='replace', index=False, index_label='Game ID')
        return True
    
    def addNewGame(self, df):
        table_name = 'owned_games'
        df.to_sql(table_name, self.engine, if_exists='append', index=False, index_label='Game ID')
        return True
    
    def altervalue(self, table_name, condition_column, condition_value, game_id):
        query = text(f'''
            UPDATE {table_name}
            SET `{condition_column}` = {condition_value}
            WHERE `Game ID` = {game_id}
        ''')
        print(query)
        with self.engine.begin() as connection:
            connection.execute(query)

        return True
        
   