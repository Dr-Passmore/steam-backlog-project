import sqlalchemy
import secrets_store
import pandas as pd

class WriteData:
    def __init__(self):
        sql_user = secrets_store.mysqlUser
        sql_pass = secrets_store.mysqlPassword
        self.engine = sqlalchemy.create_engine(f'mysql+pymysql://{sql_user}:{sql_pass}@localhost:3306/steamdata')

    def writeData(self, df, table_name):
        
        df.to_sql(table_name, self.engine, if_exists='replace', index=False, index_label='Game ID')
       
        return True

   