import MeCab
from tqdm.notebook import tqdm
from collections import deque
import tweepy
import datetime

class GetDescriptionNetwork:
    """
    入力されたユーザが設定しているディスクリプションの単語を含むフォロワーのみのネットワークを取得する
    ネットワークの枝の向きは、情報の伝播の向きである。つまり、AのフォロワーがBであると、「A -> B」となる
    
    Attributes
    ----------
    api : 
        Twitter API
    max_depth : int
        rootユーザからの最大探索する深さ
    max_followers : int
        フォロワーが多すぎるとネットワークが膨大になってしまうため、最大値に閾値を設ける
    min_listed_count : int
        リストに登録しているユーザ数の閾値
    cleansing : function
        テキスト(str)をクレンジングする関数
    tokenizer : function
        テキストを分かち書きする関数
    network_keywords : list of str
        root nodeのディスクリプションの単語リスト
    history : dict
        user1 -> user2 -> user3 : {'user3': [user1, user2], 'user2' : [user1]}
    network : dict
        {user : [user's followers]}
    users_info : dict
        ユーザの情報が格納されている
        {
        screen_name1 : {
        'id': user id,
        'screen_name': screen_name,
        'location': ユーザが登録している位置情報,
        'url': ユーザが登録しているurl情報,
        'description': 自己紹介文,
        'description_clean': クレジング済み自己紹介文,
        'followers_count': フォロワー数,
        'friends_count': フォロー数,
        'listed_count': リスト登録数,
        'favourites_count': お気に入り数,
        'statuses_count': 総ツイート数,
        'created_at': 作成日,
        'elapsed_date': 作成からの経過日数
        },
        screen_name2 : {...},
        ...
        }
    probability : list of float
        [低伝播確率, 中伝播確率, 高伝播確率]
    favorite_thres : list of float
        [閾値1, 閾値2]
        閾値1以下のユーザ : ノンアクティブユーザ
        閾値1以上、閾値2以下 : ノーマルユーザ
        閾値2以上 : アクティブユーザ
    tweet_thres : list of float
        [閾値1, 閾値2]
        閾値1以下のユーザ : ノンアクティブユーザ
        閾値1以上、閾値2以下 : ノーマルユーザ
        閾値2以上 : アクティブユーザ
    """
    def __init__(self, cleansing, tokenizer, 
                 max_depth=3, max_followers=1000, min_listed_count=0, 
                 probability=[0.3, 0.8, 1.0], favorite_thres=[0.2, 2.0], tweet_thres=[0.3, 4.4]):
        """
        Parameters
        ----------
        max_depth : int
            rootユーザからの最大探索する深さ
        max_followers : int
            フォロワーが多すぎるとネットワークが膨大になってしまうため、最大値に閾値を設ける(枝かりに使用)
        min_listed_count : int
            リストに登録しているユーザ数の閾値(枝かりに使用)
        cleansing : function
            テキスト(str)をクレンジングする関数
        tokenizer : function
            テキストを分かち書きする関数
        favorite_thres : list
            [閾値1, 閾値2]
            閾値1以下のユーザ : インアクティブユーザ
            閾値1以上、閾値2以下 : ノーマルユーザ
            閾値2以上 : アクティブユーザ
        tweet_thres : list
            [閾値1, 閾値2]
            閾値1以下のユーザ : インアクティブユーザ
            閾値1以上、閾値2以下 : ノーマルユーザ
            閾値2以上 : アクティブユーザ
        """
        # keys_and_tokensにtwitterAPIのkeyとtokenが格納してある
        # keys_and_tokens.pyを編集して、API情報を記入する必要がある
        import twitter.keys_and_tokens as config
        auth = tweepy.OAuthHandler(config.CONSUMER_KEY, config.CONSUMER_SECRET)
        auth.set_access_token(config.ACCESS_TOKEN, config.ACCESS_TOKEN_SECRET)
        self.api = tweepy.API(auth, wait_on_rate_limit=True, retry_count=5)
        
        self.max_depth = max_depth
        self.max_followers = max_followers
        self.min_listed_count = min_listed_count
        self.tokenizer = tokenizer
        self.cleansing = cleansing
        self.favorite_thres = favorite_thres
        self.tweet_thres = tweet_thres
        self.probability = probability

        
    def get_user_info(self, screen_name):
        """
        ユーザー情報を取得する
        
        Parameters
        ----------
        screen_name : str
            twitterでの「@user」
        
        Returns
        -------
        user_info : dict
            {
            'id': user id,
            'screen_name': screen_name,
            'location': ユーザが登録している位置情報,
            'url': ユーザが登録しているurl情報,
            'description': 自己紹介文,
            'description_clean': クレジング済み自己紹介文,
            'followers_count': フォロワー数,
            'friends_count': フォロー数,
            'listed_count': リスト登録数,
            'favourites_count': お気に入り数,
            'statuses_count': 総ツイート数,
            'created_at': 作成日,
            'elapsed_date': 作成からの経過日数
            'favorite_per_day': 一日あたりのお気に入り数
            'tweet_per_day': 一日あたりのツイート数
            }
        """
        try:
            res = self.api.get_user(screen_name)
            elapsed_date = (datetime.datetime.now() - res.created_at).days
            user_info = {
                'id': res.id,
                'screen_name': res.screen_name,
                'location': res.location,
                'url': res.url,
                'description': res.description,
                'description_clean': self.cleansing(res.description),
                'followers_count': res.followers_count,
                'friends_count': res.friends_count,
                'listed_count': res.listed_count,
                'favourites_count': res.favourites_count,
                'statuses_count': res.statuses_count,
                'created_at': res.created_at,
                'elapsed_date': elapsed_date,
                'favorite_per_day': res.favourites_count / elapsed_date,
                'tweet_per_day': res.statuses_count / elapsed_date
                }
        except tweepy.error.TweepError as e:
            print(e.reason)

        return user_info
    
    
    def get_follower_ids(self, screen_name):
        """
        フォロワーのidのリストを取得する
        
        Parameters
        ----------
        screen_name : str
            twitterでの「@user」
        
        Returns
        -------
        follower_id_list : list
            フォロワーのidのリスト
        """
        try:
            #Cursorを使ってフォロワーのidを逐次的に取得
            follower_ids = tweepy.Cursor(self.api.followers_ids, screen_name=screen_name, cursor=-1).items()
            follower_id_list = [followers_id for followers_id in follower_ids]
            return follower_id_list
            
        except tweepy.error.TweepError as e:
            print(e.reason)
            return []

           
    

    def get_follower_info(self, screen_name):
        """
        フォロワーの情報を取得する
        
        Parameters
        ----------
        screen_name : str
            twitterでの「@user」
            
        Returns
        -------
        user_info_list : list
            入力されたフォロワーのユーザー情報が格納されたlistを返す
        
        """
        # フォロワーのid情報を取得する
        follower_ids = self.get_follower_ids(screen_name)
        
        # id情報からユーザの情報を取得する
        user_info_list = [self.get_user_info(user_id) for user_id in tqdm(follower_ids, leave=False)]

        return user_info_list
    
    def cut_followers(self, followers_info):
        """
        探索キューに入れるフォロワーを枝刈りする
        
        Parameters
        ----------
        follwers_info : dict
            ユーザの情報が格納されている
        """
        live_followers = []
        for follower_info in followers_info:
            follower_description_tokenize = self.tokenizer(follower_infor['description_clean'])

            # 積集合が空じゃないかつフォロワーが閾値以上なら残す
            if len((set(follower_description_tokenize) & set(self.network_keywords))) > 0  and \
            (follower_info['followers_count'] <= self.max_followers) and \
            (follower_info['listed_count'] >= self.min_listed_count):
                live_followers_info.append(follower_info)

        return live_followers_info
    
    def convert_probability(self, state):
        """
        アクティブ状態を確率に変換する
        
        Parameters
        ----------
        state : str
            'active' or 'nomal' or 'inactive'
        
        Returns
        -------
        ret : float
            状態に応じた確率
        """
        if state == 'inactive':
            return self.probability[0]
        elif state == 'nomal':
            return self.probability[1]
        else:
            return self.probability[2]
    
    def set_probability(self, from_node, to_node):
        """
        ノード間の伝播確率を設定する
        
        Parameters
        ----------
        from_node : str
            screen_name
        to_node : str
            screen_name
        
        Returns
        -------
        ret : float
            ノード間の伝播確率
        """
        if self.users_info[from_node]['tweet_per_day'] >= self.tweet_thres[1]:
            from_node_state = 'active'
        elif self.users_info[from_node]['tweet_per_day'] <= self.tweet_thres[0]:
            from_node_state = 'inactive'
        else:
            from_node_state = 'nomal'
        
        if self.users_info[to_node]['favorite_per_day'] >= self.favorite_thres[1]:
            to_node_state = 'active'
        elif self.users_info[to_node]['favorite_per_day'] <= self.favorite_thres[0]:
            to_node_state = 'inactive'
        else:
            to_node_state = 'nomal'
            
        to_node_look_prob = 1 / self.users_info[to_node]['friends_count']
        return to_node_look_prob * self.convert_probability(from_node_state) * self.convert_probability(to_node_state)
        
    def get_network(self, root_user):
        """
        Parameters
        ----------
        root_user : str
            screen name 「@(user)」
            ネットワークのルートとするユーザ
        
        Returns
        -------
        users_info : dict
            {screen_name : user_info(twitterから得られる情報), ...}
        adj_list : list of list
            [
            [from_node1(str), to_node1(str), prob1(float)], 
            [from_node1, to_node2, prob2], 
            [from_node2, to_node2, prob3]
            ]
            隣接リスト
        """
        
        # ルートユーザの情報を取得し、ディスクリプションを単語ごとに分ける
        root_user_info = self.get_user_info(root_user)
        self.network_keywords = self.tokenizer(root_user_info['description_clean'])
        self.history = {root_user : []}
        self.network = {}
        
        self.users_info = {root_user: root_user_info}
        adj_list = []
        
        # 幅優先探索
        queue = deque([root_user])
        while queue:
            user_pointed = queue.popleft()
            print(f'\rcurrent user : {user_pointed}', end='')
            
            try:
                followers_info = self.get_follower_info(user_pointed)
                self.network[user_pointed] = [follower_info['screen_name'] for follower_info in followers_info]
                
                for follower_info in followers_info:
                    if follower_info['screen_name'] not in self.users_info:
                        follower_description_tokenize = self.tokenizer(follower_info['description_clean'])
                        self.users_info[follower_info['screen_name']] = follower_info
                        self.history[follower_info['screen_name']] = self.history[user_pointed] + [user_pointed]
                        
                        # 枝かり
                        if len((set(follower_description_tokenize) & set(self.network_keywords))) > 0  and \
                        (follower_info['listed_count'] >= self.min_listed_count) and \
                        (len(self.history[follower_info['screen_name']]) < self.max_depth):
                            # フォロワーが多すぎるため、枝かりをする(情報として、取っておきたい)
                            if follower_info['followers_count'] <= self.max_followers:
                                queue.append(follower_info['screen_name'])
                            else:
                                self.network[follower_info['screen_name']] = follower_info['followers_count']
                
                adj_list += [[user_pointed, to_node, self.set_probability(user_pointed, to_node)]
                             for to_node in self.network[user_pointed]]
            except Exception as e:
                print('error')
                print(e)
        
        return adj_list, self.users_info