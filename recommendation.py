import sqlalchemy
from sqlalchemy import text
import pandas as pd
import secrets_store
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from bs4 import BeautifulSoup 
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np 
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

from wordcloud import WordCloud
import matplotlib.pyplot as plt

class GameSelection:
    def __init__(self) -> None:
        sql_user = secrets_store.mysqlUser
        sql_pass = secrets_store.mysqlPassword
        self.engine = sqlalchemy.create_engine(f'mysql+pymysql://{sql_user}:{sql_pass}@127.0.0.1:3307/steamdata')
        custom_stopwords = ['game', 
                            'games', 
                            'play', 
                            'playing', 
                            'player', 
                            'players', 
                            'steam', 
                            'like', 
                            'new', 
                            'world', 
                            's', 
                            'experience', 
                            'gameplay', 
                            'mode', 
                            'feature', 
                            'including', 
                            'featuring', 
                            'steampowered',
                            'app',
                            'com',
                            'store',
                            'total',
                            'unique',
                            'weapon',
                            'battle']
        self.stopwords = set(ENGLISH_STOP_WORDS).union(custom_stopwords)
        self.stopwords = list(self.stopwords)
    def query_data(self, query):
        with self.engine.connect() as connection:
            result = connection.execute(text(query))
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
    
    def neverPlayedSelection(self):
        df = self.uncompletedgames()
        df_details = self.gamedetails()
        df = pd.merge(df, df_details, on='Game ID', how='left')
        zero_minutes_games = df[df['Playtime (forever)'] == 0] 
        if not zero_minutes_games.empty:
            # Randomly pick one game with zero minutes played
            random_game = zero_minutes_games.sample()
        else:
            # Pick the game with the lowest minutes played
            random_game = df.loc[df['Playtime (forever)'].idxmin()]
        return random_game
    
    def clean_html_tags(self, text):
        if isinstance(text, str):  # Check if the value is a string
            soup = BeautifulSoup(text, 'html.parser')
            return soup.get_text(separator=' ')
        else:
            return ''
                             
    def recommendBasedOnPlaytime(self):
        df = self.allgames()
        uncompleted_games_df = self.uncompletedgames()

        top_10_percent_count = int(len(df) * 0.1)
        df_details = self.gamedetails()
        merged_df = pd.merge(df.nlargest(top_10_percent_count, 'Playtime (forever)'), df_details, on='Game ID', how='left')
        uncompleted_games_df = pd.merge(uncompleted_games_df, df_details, on='Game ID', how='left')
        
        merged_df['Detailed Description'] = merged_df['Detailed Description'].apply(self.clean_html_tags)
        uncompleted_games_df['Detailed Description'] = uncompleted_games_df['Detailed Description'].apply(self.clean_html_tags)

        top_10_descriptions = merged_df['Detailed Description'].fillna('')
        uncompleted_descriptions = uncompleted_games_df['Detailed Description'].fillna('')
        # Generate a word cloud image
        
        wordcloud = WordCloud(stopwords=self.stopwords, background_color="white").generate(' '.join(top_10_descriptions))

        # Display the generated image
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")
        plt.show()
        tfidf_vectorizer = TfidfVectorizer(stop_words=self.stopwords, max_df=0.8, min_df=0.1, ngram_range=(1, 2))

        # Fit and transform on top 10% of games
        top_10_tfidf_matrix = tfidf_vectorizer.fit_transform(top_10_descriptions)

        # Transform uncompleted games using the same vectorizer
        uncompleted_tfidf_matrix = tfidf_vectorizer.transform(uncompleted_descriptions)

        # Compute cosine similarity matrix
        similarity_matrix = cosine_similarity(uncompleted_tfidf_matrix, top_10_tfidf_matrix)

        recommendations = []

        for index, game_row in uncompleted_games_df.iterrows():
            # Find the indices with the highest cosine similarity
            top_similar_game_indices = similarity_matrix[index].argsort()[::-1]
            
            top_10_percent = int(len(top_similar_game_indices) * 0.1)
            top_similar_game_indices = top_similar_game_indices[:top_10_percent]
            # Get the top 5 most accurate recommendations
            game_recommendations = merged_df['Game ID'].iloc[top_similar_game_indices][:5].tolist()
            mean_score = np.mean(similarity_matrix[index, top_similar_game_indices])
            # Print similarity scores for debugging
            similarity_scores = similarity_matrix[index, top_similar_game_indices]
            
            sorted_recommendations = sorted(recommendations, key=lambda x: x['Mean Similarity Score'], reverse=True)
            recommendations.append({
                'Uncompleted Game ID': game_row['Game ID'],
                'Recommendations': game_recommendations,
                'Mean Similarity Score': mean_score
            })
        sorted_recommendations = sorted(recommendations, key=lambda x: x['Mean Similarity Score'], reverse=True)

        # Get the top 5 recommendations
        top_5_recommendations = sorted_recommendations[:10]

        return top_5_recommendations

        
        
    
    def recommendBasedOnCompleted(self):
        completed_df = self.completedgames()
        uncompleted_games_df = self.uncompletedgames()

        df_details = self.gamedetails()
        uncompleted_games_df = pd.merge(uncompleted_games_df, df_details, on='Game ID', how='left')
        merged_df = pd.merge(completed_df, df_details, on='Game ID', how='left')
        merged_df['Detailed Description'] = merged_df['Detailed Description'].apply(self.clean_html_tags)
        uncompleted_games_df['Detailed Description'] = uncompleted_games_df['Detailed Description'].apply(self.clean_html_tags)

        completed_descriptions = merged_df['Detailed Description'].fillna('')
        uncompleted_descriptions = uncompleted_games_df['Detailed Description'].fillna('')
        
        # Generate a word cloud image
        wordcloud = WordCloud(stopwords=self.stopwords, background_color="white").generate(' '.join(completed_descriptions))

        # Display the generated image
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")
        plt.show()

        # Use TF-IDF Vectorizer with adjusted parameters
        tfidf_vectorizer = TfidfVectorizer(stop_words=self.stopwords, max_df=0.5, min_df=0.05, ngram_range=(1, 2))

        # Fit and transform on completed games
        completed_tfidf_matrix = tfidf_vectorizer.fit_transform(completed_descriptions)

        # Transform uncompleted games using the same vectorizer
        uncompleted_tfidf_matrix = tfidf_vectorizer.transform(uncompleted_descriptions)

        # Compute cosine similarity matrix
        similarity_matrix = cosine_similarity(uncompleted_tfidf_matrix, completed_tfidf_matrix)

        recommendations = []

        for index, game_row in uncompleted_games_df.iterrows():
            # Find the indices with the highest cosine similarity
            
            top_similar_game_indices = similarity_matrix[index].argsort()[::-1]
            
            top_10_percent = int(len(top_similar_game_indices) * 0.1)
            top_similar_game_indices = top_similar_game_indices[:top_10_percent]
            # Get the top 5 most accurate recommendations
            game_recommendations = merged_df['Game ID'].iloc[top_similar_game_indices][:5].tolist()
            mean_score = np.mean(similarity_matrix[index, top_similar_game_indices])
            # Print similarity scores for debugging
            similarity_scores = similarity_matrix[index, top_similar_game_indices]
            
            sorted_recommendations = sorted(recommendations, key=lambda x: x['Mean Similarity Score'], reverse=True)
            recommendations.append({
                'Uncompleted Game ID': game_row['Game ID'],
                'Recommendations': game_recommendations,
                'Mean Similarity Score': mean_score
            })
        sorted_recommendations = sorted(recommendations, key=lambda x: x['Mean Similarity Score'], reverse=True)

        # Get the top 5 recommendations
        top_5_recommendations = sorted_recommendations[:10]

        return top_5_recommendations
        #return recommendations
        




GameSelection = GameSelection()
print("Recommendations based on playtime:")

print(GameSelection.recommendBasedOnPlaytime())
print(GameSelection.neverPlayedSelection())
print(GameSelection.recommendBasedOnCompleted())
