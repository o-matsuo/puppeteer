### 事前準備（インストール先）

- インストール先は AWS cloud9 を想定します。   
その他の環境では動作検証しておりませんので、不具合等は[note](https://note.mu/o_matsuo/n/n88ca529043a5)にご連絡いただきますよう、お願いいたします。   
対応可能であれば、後日ご連絡いたします。

- puppeteerはpython3で動作します。検証で使用した環境は、python version 3.6.8 です。   
aws cloud9のpython3環境構築については、[ここ](https://qiita.com/acecrc/items/fb34a12b265122816d4b)等を参考にして構築してください。

### インストール

- Puppeteer本体をgitlabからcloneします。   

```
git clone https://gitlab.com/o-matsuo/puppeteer.git
```

- 上記のコマンドを実行すると、Puppeteer本体がgitlabからダウンロードされ、「puppeteer」というフォルダが作成されます。   
フォルダ構成は以下のようになっています。

```
 - puppeteer/
   - docs/
   - exchanges/
   - indicators/
   - logs/
   - modules/
   - puppets/
   - CHANGELOG.md
   - LICENSE.txt
   - MEMO.md
   - puppeteer.py
   - README.md
```

- xxxx/ と 最後が「/」（スラッシュ）終わっているのはフォルダです。   
その他はルートに置かれたファイルになります。

### 必要なモジュールのインストール

- ccxtを導入します。   
[ccxt](https://github.com/ccxt/ccxt)は多くの仮想通貨自動取引botで利用されている有名なモジュールです。

```shell script
sudo pip install -r requirements.txt
```

または

```python
sudo pip install ccxt
sudo pip install matplotlib
sudo pip install pandas
sudo pip install websocket-client==0.47
```

