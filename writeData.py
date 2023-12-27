import sqlalchemy
import secrets_store

class WriteData:
    def __init__(self):
        self.engine = sqlalchemy.create_engine('mysql+pymysql://root:password@localhost:3306/steam')

    def writeData(self, df, table_name):
        df.to_sql(table_name, self.engine, if_exists='append', index=False)
        return True