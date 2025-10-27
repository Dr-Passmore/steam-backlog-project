import requests
import json
import logging

import secrets_store
import loadData
import dataQuery
import writeData





class SteamRecommendation():
    def __init__(self):
        logging.info("Starting SteamRecommendation")
        self.data_setup = loadData.dataSetUp()
        self.record_data = writeData.WriteData()
        self.database_extract = dataQuery.DatabaseExtract()
        data = self.dataProcessing()
        check = self.record_data.updateReleaseToDateFormat()
        #print(data)

    def dataProcessing (self):
        df = self.data_setup.getOwnedGames()
        current_owned = self.database_extract.allgames()
        #print (current_owned)
        updated = self.data_setup.updateOwnedGamesInfo(df, current_owned)
        self.record_data.updateReleaseToDateFormat()
        print(updated)
        return df
        

if __name__ == "__main__":
    SteamRecommendation()
