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
        #print(query)
        with self.engine.begin() as connection:
            connection.execute(query)
        return True

    def updateReleaseToDateFormat (self):
        query = text(f'''UPDATE game_details
            SET parsed_released = 
                COALESCE(
                    STR_TO_DATE(released, '%d %b, %Y'),  -- e.g. 23 Jan, 2025
                    STR_TO_DATE(released, '%d %b %Y'),   -- e.g. 8 Nov 1998
                    STR_TO_DATE(CONCAT('1 ', released), '%d %b %Y'), -- e.g. Dec 2010
                    STR_TO_DATE(released, '%Y-%m-%d')    -- e.g. 1999-04-01
                )
            WHERE parsed_released IS NULL
            AND released IS NOT NULL
            AND released <> '';
        ''')
        with self.engine.begin() as connection:
            connection.execute(query)
        return True
        
writing = WriteData()
print(writing.updateReleaseToDateFormat())