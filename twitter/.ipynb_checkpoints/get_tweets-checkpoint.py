import tweepy
import pandas as pd

class GetTweet:
    """
    tweepyを使用して、ツイートを取得する
    
    Attributes
    ----------
    api : 
        twitter API情報
    """
    
    def __init__(self):
        """
        keys_and_tokensにtwitterAPIのkeyとtokenが格納してある
        keys_and_tokens.pyを編集して、API情報を記入する必要がある
        """
        import twitter.keys_and_tokens as config

        auth = tweepy.OAuthHandler(config.CONSUMER_KEY, config.CONSUMER_SECRET)
        auth.set_access_token(config.ACCESS_TOKEN, config.ACCESS_TOKEN_SECRET)
        
        self.api = tweepy.API(auth, wait_on_rate_limit = True, retry_count=5)
    
    def get_tweets_target(self, target):
        """
        ユーザーを指定してツイートを取得する
        
        Parameters
        ----------
        target : str
            screen_name(@.+?)
            
        Returns
        -------
        ret : DataFrame
            {"tweet_id": , "created_at": , "text": , "favorite_count": , "retweet_count": }
        """
        tweets = {"tweet_id": [], "created_at": [], "text": [], "favorite_count": [], "retweet_count": []}
        for tweet in tweepy.Cursor(self.api.user_timeline, screen_name = target, exclude_replies = True).items():
            tweets["tweet_id"].append(tweet.id)
            tweets["created_at"].append(tweet.created_at)
            tweets["text"].append(tweet.text)
            tweets["favorite_count"].append(tweet.favorite_count)
            tweets["retweet_count"].append(tweet.retweet_count)
            
        return pd.DataFrame(tweets)
    
    def get_tweets_keyword(self, keyword):
        """
        キーワードを検索する
        
        Parameters
        ----------
        keywork : str
            検索するキーワード
        
        Returns
        -------
        ret : DataFrame
            {
            "tweet_id": , 
            "created_at": , 
            "screen_name": , 
            "user_name": , 
            "user_description": ,
            "followers_count": ,
            "following_count": ,
            "text": , 
            "favorite_count": , 
            "retweet_count": 
            }
        """
        tweets = {
            "tweet_id": [], 
            "created_at": [], 
            "screen_name": [], 
            "user_name": [], 
            "user_description": [],
            "followers_count": [],
            "following_count": [],
            "text": [], 
            "favorite_count": [], 
            "retweet_count": []
        }
        for tweet in tweepy.Cursor(self.api.search, q=keyword, include_entities=True, tweet_mode='extended', lang='ja').items():
            tweets["tweet_id"].append(tweet.id)
            tweets["created_at"].append(tweet.created_at)
            tweets["screen_name"].append(tweet.user.screen_name)
            tweets["user_name"].append(tweet.user.name)
            tweets["user_description"].append(tweet.user.description)
            tweets["followers_count"].append(tweet.user.followers_count)
            tweets["following_count"].append(tweet.user.friends_count)
            tweets["text"].append(tweet.full_text)
            tweets["favorite_count"].append(tweet.favorite_count)
            tweets["retweet_count"].append(tweet.retweet_count)
            
        return pd.DataFrame(tweets)