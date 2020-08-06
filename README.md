# 環境構築
- tweepy
    ```
    $ conda install -c conda-forge tweepy
    ```
- mojimoji
    ```
    $ pip install mojimoji
    ```

- emoji
    ```
    $ pip install emoji
    ```

- neologn
    ```
    $ pip install neologdn
    ```

- MeCab neologd
    1. Homebrewがインストールされているか確認する  
        ```
        $ brew --version
        Homebrew 2.4.9
        Homebrew/homebrew-core (git revision a619dad; last commit 2020-08-03)
        ```
        インストールされていない場合、
        ```
        $ /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
        ```
    2.  mecabとmecab辞書をインストールする
        ```
        $ brew install mecab mecab-ipadic
        ```
    3. mecabが動作するか確認する
        ```
        $ mecab
        安倍晋三内閣総理大臣
        ...
        [^] + Cで終了
        ```
    4. neologd辞書をインストールする
        ```
        $ git clone --depth 1 https://github.com/neologd/mecab-ipadic-neologd.git
        ```
    5. ビルド
        ```
        $ cd mecab-ipadic-neologd
        $ ./bin/install-mecab-ipadic-neologd -n -a
        ```
        途中で
        ```
        [install-mecab-ipadic-NEologd] : Do you want to install mecab-ipadic-NEologd? Type yes or no.
        ```
        と表示されるため、
        ```
        yes
        ```
        と入力する
    6. 辞書にneologdを設定する
        usr/local/etc/mecabrcを編集する  
        before
        ```
        ; $Id: mecabrc.in,v 1.3 2006/05/29 15:36:08 taku-ku Exp $;
        ;

        ;dicdir =  /usr/local/lib/mecab/dic/ipadic
        ```

        after
        ```
        ; $Id: mecabrc.in,v 1.3 2006/05/29 15:36:08 taku-ku Exp $;
        ;
        dicdir =  /usr/local/lib/mecab/dic/mecab-ipadic-neologd
        ;dicdir =  /usr/local/lib/mecab/dic/ipadic
        ```
        保存して、閉じた後、ターミナルを再起動する
    7. 動作確認
        ```
        $ mecab
        安倍晋三内閣総理大臣
        ...
        [^] + Cで終了
        ```
        先ほどと分かち書きのされ方が変更されていれば成功である
    8. notebook上での動作確認
        ```
        import MeCab

        mecab = MeCab.Tagger()
        print(mecab.parse ("安倍晋三内閣総理大臣"))
        ```

- merge test