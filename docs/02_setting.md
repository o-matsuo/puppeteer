### 設定

- puppeteer本体の動作定義も、ユーザ様が作った独自ストラテジ(以降、Puppet(傀儡)と呼称)の動作定義も一つのファイルで行います。

- Puppetは次のように「pythoファイル」と「jsonファイル」の２つから構成されます。   
この2つのファイルを一つのフォルダに格納し、そのフォルダを「puppets」フォルダの下に配置します。

```
 - puppets/
   - sample/
     - sample.py
     - sample.json
```

- 説明
  - sample.py : 独自ロジックを書くpythonファイルです。
  - sample.json : puppeteer本体の動作と、独自ロジックの動作を定義するJSONファイルです。

- 独自ロジック（pythonファイル）

  - 多くの場合、次の雛形を拡張して開発します。   
Puppetには一つの「Puppetクラス」と、そのクラスに固有の「runメソッド」を持ちます。

```python
# -*- coding: utf-8 -*-
# ==========================================
# サンプル・ストラテジ
# ==========================================
import datetime

from puppeteer import Puppeteer

# ==========================================
# Puppet(傀儡) クラス
#   param:
#       puppeteer: Puppeteerオブジェクト
# ==========================================
class Puppet(Puppeteer):
    _exchange = None    # 取引所オブジェクト(ccxt.bitmex)
    _logger = None      # logger
    _config = None      # 定義ファイル

    # ==========================================================
    # 初期化
    #   param:
    #       puppeteer: Puppeteerオブジェクト
    # ==========================================================
    def __init__(self, Puppeteer):
        self._exchange = Puppeteer._exchange
        self._logger = Puppeteer._logger
        self._config = Puppeteer._config
        
    # ==========================================================
    # 売買実行
    #   param:
    #       ticker: Tick情報
    #       orderbook: 板情報
    #       position: ポジション情報
    #       balance: 資産情報
    #       candle: ローソク足
    # ==========================================================
    def run(self, ticker, orderbook, position, balance, candle):
        """
        self._logger.debug('last={}'.format(ticker['last']))
        self._logger.debug('bid={}, ask={}'.format(orderbook['bids'][0][0], orderbook['asks'][0][0]))
        self._logger.debug('position={}, avgPrice={}'.format(position[0]['currentQty'], position[0]['avgEntryPrice']))
        self._logger.debug('balance[walletBalance]={}'.format(balance['info'][0]['walletBalance'] * 0.00000001))
        """
```

- Puppetのrunメソッドの中に、独自ロジックを実装していくことになります。   
Puppetはクラス生成時に、引数としてPuppeteer本体オブジェクトが渡されます。   
そのオブジェクトから以下のものが渡されます。（今後拡張されます）
  - 取引所オブジェクト(ccxt.bitmex)
  - ロガーオブジェクト
  - コンフィギュレーション情報


- 動作定義ファイル(JSONファイル)

  - このファイルも多くの場合、sample.jsonをベースにして拡張されます。

```json
{
    "//" : "===============================================",
    "//" : " システムで利用",
    "//" : "===============================================",
    "//" : "取引所のapiKey, secretを設定します",
    "APIKEY" : "YOUR_APIKEY",
    "SECRET" : "YOUR_SECRET",

    "//" : "bitmex取引所で対応する通貨ペア等を記述",
    "SYMBOL" : "BTC/USD",
    "INFO_SYMBOL" : "XBTUSD",
    "COIN_BASE" : "BTC",
    "COIN_QUOTE" : "USD",
    "//" : "bitmex取引所の価格の最小幅(0.5ドル)",
    "PRICE_UNIT" : 0.5,

    "//" : "TestNetを使うか？(使う: true, 使わない: false)",
    "USE_TESTNET" : true,

    "//" : "ticker, orderbook, position, balance, candle のどれを利用するかを指定する。Falseを指定した場合はそのデータは取得しない",
    "USE" : {
        "TICKER" : true,
        "ORDERBOOK" : true,
        "POSITION" : true,
        "BALANCE" : true,
        "CANDLE" : true
    },

    "//" : "ローソク足の収集定義。",
    "CANDLE" : {
        "//" : "ローソク足の足幅を設定する。設定値= 1m, 5m, 1h, 1d",
        "TIMEFRAME" : "1m",
        "//" : "データ取得開始時刻(UNIXTIME：1ミリ秒)、使用しない場合 もしくは自動の場合は null(None) を指定",
        "SINCE" : null,
        "//" : "取得件数(未指定:100、MAX:500)",
        "LIMIT" : null,
        "//" : "True(New->Old)、False(Old->New)　未指定時はFlase",
        "REVERSE" : false,
        "//" : "True(最新の未確定足を含む)、False(含まない)　未指定はTrue",
        "PARTIAL" : false
    },

    "//" : "板情報の収集定義。",
    "ORDERBOOK" : {
        "//" : "取得件数(未指定:25、MAX:取引所による？)",
        "LIMIT" : null
    },

    "//" : "インターバル（botの実行周期）を秒で設定",
    "INTERVAL" :30,

    "//" : "discord通知用URL",
    "DISCORD_WEBHOOK_URL" : "",

    "//" : "===============================================",
    "//" : " ユーザで自由に定義",
    "//" : "===============================================",
    "//" : "売買するサイズ",
    "LOT_SIZE" :50
}
```

- 定義情報

  - APIKEY : 取引所のapiKeyを設定します。
  - SECRET : 取引所のsecretを設定します。

  - SYMBOL : 変更しないでください。
  - INFO_SYMBOL : 変更しないでください。
  - COIN_BASE : 変更しないでください。
  - COIN_QUOTE : 変更しないでください。
  - PRICE_UNIT : 変更しないでください。

  - USE_TESTNET : TestNetを使用するときはtrueを、使用しないときはfalseを設定します。

  - USE : 各種のデータを取得するかどうかを指定します。   
  取得できるデータは、TICKER, ORDERBOOK, POSITION, BALANCE, CANDLE の5つです。

  - CANDLE : ローソク足情報を取得する設定です。   
  TIMEFRAMEの設定は 1m, 5m, 1h, 1dの4つです。

  - ORDERBOOK : 板情報を取得する設定です。

  - USE_WEBSOCKET : websocketを使用するかどうかを設定します。

  - LOG_LEVEL : 'CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'

  - INTERVAL : botの実行周期を秒で設定します。

  - DISCORD_WEBHOOK_URL : discord通知を使用するときに、discordのwebhook urlを設定します。
  
