import pandas as pd
import json
import re
import emoji
import mojimoji
import neologdn

class CleansingTweets:
    """
    ツイートをクレンジングする
    """
    def cleansing_space(self, text):
        """
        半角を全角に変換するand\sをスペースに変換する
        
        Parameters
        ----------
        text : str
            クレジングされる文字列
            
        Returns
        -------
        ret : str
            クレジング済みの文字列
        """
        return re.sub("\u3000|\s", " ", text)
    
    def cleansing_hash(self, text):
        """
        ハッシュタグの削除
        
        Parameters
        ----------
        text : str
            クレジングされる文字列
            
        Returns
        -------
        ret : str
            クレジング済みの文字列
        """
        return re.sub("#[^\s]+", "", text)
    
    def cleansing_url(self, text):
        """
        urlの削除
        
        Parameters
        ----------
        text : str
            クレジングされる文字列
            
        Returns
        -------
        ret : str
            クレジング済みの文字列
        """
        return re.sub(r"(https?|ftp)(:\/\/[-_\.!~*\'()a-zA-Z0-9;\/?:\@&=\+$,%#]+)", "" , text)
    
    def cleansing_emoji(self, text):
        """
        絵文字の削除
        
        Parameters
        ----------
        text : str
            クレジングされる文字列
            
        Returns
        -------
        ret : str
            クレジング済みの文字列
        """
        return ''.join(c for c in text if c not in emoji.UNICODE_EMOJI)
    
    def cleansing_username(self, text):
        """
        @userの削除
        
        Parameters
        ----------
        text : str
            クレジングされる文字列
            
        Returns
        -------
        ret : str
            クレジング済みの文字列
        """
        return re.sub(r"@([A-Za-z0-9_]+) ", "", text)
    
    def cleansing_picture(self, text):
        """
        画像文字列の削除
        
        Parameters
        ----------
        text : str
            クレジングされる文字列
            
        Returns
        -------
        ret : str
            クレジング済みの文字列
        """
        return re.sub(r"pic.twitter.com/[-_\.!~*\'()a-zA-Z0-9;\/?:\@&=\+$,%#]*", "" , text)
    
    def cleansing_unity(self, text):
        """
        文字統一
        
        Parameters
        ----------
        text : str
            クレジングされる文字列
            
        Returns
        -------
        ret : str
            クレジング済みの文字列
        """
        text = text.lower()
        text = mojimoji.zen_to_han(text, kana=True)
        text = mojimoji.han_to_zen(text, digit=False, ascii=False)
        text = re.sub(r'\d+', "0", text)
        return text 
    
    def cleansing_rt(self, text):
        """
        RT部分の削除
        
        Parameters
        ----------
        text : str
            クレジングされる文字列
            
        Returns
        -------
        ret : str
            クレジング済みの文字列
        """
        return re.sub(r"RT @[-_\.!~*\'()a-zA-Z0-9;\/?:\@&=\+$,%#]*?: ", "" , text)
    
    def cleansing_text(self, text):
        """
        クレンジングのパイプライン
        
        Parameters
        ----------
        text : str
            クレジングされる文字列
            
        Returns
        -------
        ret : str
            クレジング済みの文字列
        """
        text = self.cleansing_rt(text)
        text = self.cleansing_hash(text)
        text = self.cleansing_space(text)
        text = self.cleansing_url(text)
        text = self.cleansing_emoji(text)
        text = self.cleansing_username(text)
        text = self.cleansing_picture(text)
        text = self.cleansing_unity(text)
        text = neologdn.normalize(text)
        return text
    
    def cleansing_df(self, df, subset_col):
        """
        Parameters
        ----------
        df : DataFrame
            クレンジング対象
        subset_col : list of str
            ['text', ...,]
            DataFrameのsubset_colで指定された列にクレンジングを行う
        
        Returns
        -------
        ret : DataFrame
            クレンジグ済みのDataFrame
        """
        # 重複した行はリツイートの可能性が高いため、全種類削除
        df = df.drop_duplicates(subset=subset_col, keep=False)

        df_copy = df.copy()
        
        # クレンジング
        for col in subset_col:
            df_copy[col] = df[col].apply(lambda x: self.cleansing_text(x))

        # クレンジング後の重複を削除
        df_copy = df_copy.drop_duplicates(subset=subset_col, keep=False).reset_index(drop=True)

        return df_copy