# -*- coding: utf-8 -*-
# ==========================================
# システムモジュール
# ==========================================
import sys
import ccxt
import time
from importlib import machinery
import json
import pprint
# ログのライブラリ
import logging
from logging import getLogger, StreamHandler, Formatter
from logging.handlers import TimedRotatingFileHandler
from os.path import splitext, basename
# fetch_ohlcv改良
from datetime import datetime
import calendar
# bitmexラッパー
from exchanges.ccxt.bitmex import BitMEX
# websocket
from exchanges.websocket.inmemorydb_bitmex_websocket import BitMEXWebsocket

# ==========================================
# Puppeteer モジュール
# ==========================================
from modules.discord import Discord           # Discordクラス

# ==========================================
# python pupeteer <実行ファイルのフルパス> <実行定義JSONファイルのフルパス>
# ==========================================
args = sys.argv

# ==========================================
# 傀儡師
# ==========================================
class Puppeteer:
    _exchange = None            # 取引所オブジェクト(ccxt.bitmex)
    _Puppet = None              # ストラテジ(ユーザが作成)
    _config = None              # 定義情報(JSON)
    _logger = None              # logger設定
    _discord = None             # discordオブジェクト
    _bitmex = None              # ccxt.bitmexラッパー
    _ws = None                  # websocket

    # ======================================
    # 初期化
    #   param:
    #       args: Puppeteer起動時の引数
    # ======================================
    def __init__(self, args):
        # ----------------------------------
        # loggerの設定
        # ----------------------------------
        # logファイル名を抜き出す
        base, ext = splitext(basename(args[1]))     # 引数チェックをする前に引数を使っているけど、Loggerを先に作りたい。
        # loggerオブジェクトの宣言
        logger = getLogger("puppeteer")
        # loggerのログレベル設定(ハンドラに渡すエラーメッセージのレベル)
        logger.setLevel(logging.INFO)              # ※ここはConfigで設定可能にする
        # Formatterの生成
        formatter = Formatter(
                fmt='%(asctime)s, %(levelname)-8s, %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        # console handlerの生成・追加
        stream_handler = StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        # file handlerの生成・追加
        timedrotating_handler = TimedRotatingFileHandler(
            filename='logs/{}.log'.format(base),    # logファイル名
            when='D',                               # 1日を指定
            interval=1,                             # 間隔
            backupCount=7,                          # 7日間保持
            encoding='UTF-8'                        # UTF-8
            )
        timedrotating_handler.setFormatter(formatter)
        logger.addHandler(timedrotating_handler)
        self._logger = logger
        # ----------------------------------
        # 引数チェック
        # ----------------------------------
        if len(args) != 3:
            self._logger.error('argument length != 3')
            exit()
        # ----------------------------------
        # 定義ファイルのロード
        # ----------------------------------
        with open(args[2], 'r') as f:
            jsonData = json.load(f)
            # print(json.dumps(jsonData, sort_keys = True, indent = 4))
            self._config = jsonData
        # ------------------------------
        # bitmexラッパー
        # ------------------------------
        self._bitmex = BitMEX(
            symbol=self._config['SYMBOL'],          # BTC/USD   注意：XBTUSDではない 
            apiKey=self._config['APIKEY'],
            secret=self._config['SECRET'],
            logger=self._logger,
            use_testnet=self._config['USE_TESTNET']
        )
        # ------------------------------
        # 取引所オブジェクト(ccxt.bitmex)
        # ------------------------------
        self._exchange = self._bitmex._exchange
        # ----------------------------------
        # websocket
        # ----------------------------------
        self._ws = BitMEXWebsocket(
                endpoint='wss://www.bitmex.com/realtime' if self._config['USE_TESTNET'] is False else 'wss://testnet.bitmex.com/realtime', 
                symbol=self._config['INFO_SYMBOL'],     # XBTUSD
                api_key=self._config['APIKEY'], 
                api_secret=self._config['SECRET'],
                logger=self._logger,
                use_timemark=False
            )
        # instrumentメソッドを一度呼び出さないとエラーを吐くので追加(内部的にtickerがこの情報を使用するため)
        self._ws.instrument()
        # ----------------------------------
        # Discord生成
        # ----------------------------------
        self._discord = Discord(self._config['DISCORD_WEBHOOK_URL'])
        # ----------------------------------
        # ストラテジのロードと生成
        # ----------------------------------
        module = machinery.SourceFileLoader('Puppet', args[1]).load_module()
        self._Puppet =  module.Puppet(self)
        # ----------------------------------
        # 起動メッセージ
        # ----------------------------------
        message = '[傀儡師] 起動しました。Puppet={}, Config={}, 対象通貨ペア={}, RUN周期={}(秒)'.format(
                args[1], 
                args[2],
                self._config['SYMBOL'],
                self._config['INTERVAL']
            )
        self._logger.info(message)
        self._discord.send(message)

# ==========================================
# メイン
# ==========================================
if __name__ == '__main__':
    # ======================================
    # 起動
    # ======================================
    def start():
        puppeteer = Puppeteer(args=args)
        while True:
            try:
                run(Puppeteer=puppeteer)
            except KeyboardInterrupt:
                puppeteer._logger.info('[傀儡師] Ctrl-C検出: 処理を終了します')
                puppeteer._discord.send('[傀儡師] Ctrl-C検出: 処理を終了します')
                exit()
            except Exception as e:
                puppeteer._logger.error('[傀儡師] 例外発生[{}]: 処理を再起動します'.format(e))
                puppeteer._discord.send('[傀儡師] 例外発生[{}]: 処理を再起動します'.format(e))
                time.sleep(1)
    
    # ======================================
    # メインループ
    # ======================================
    def run(Puppeteer):
        while True:
            # ----------------------------------
            # 処理開始
            # ----------------------------------
            start = time.time()
            # ----------------------------------
            # ローソク足情報取得
            #  ローカル関数を使用
            # ----------------------------------
            candle = fetch_ohlcv(
                    bitmex=Puppeteer._exchange,                              # ccxt.bitmex
                    symbol=Puppeteer._config['SYMBOL'],                      # シンボル
                    timeframe=Puppeteer._config['CANDLE']['TIMEFRAME'],      # timeframe= 1m 5m 1h 1d
                    since=Puppeteer._config['CANDLE']['SINCE'],              # データ取得開始時刻(Unix Timeミリ秒)
                    limit=Puppeteer._config['CANDLE']['LIMIT'],              # 取得件数(未指定:100、MAX:500)
                    params={
                        'reverse': Puppeteer._config['CANDLE']['REVERSE'],   # True(New->Old)、False(Old->New)　未指定時はFlase (注意：sineceを指定せずに、このフラグをTrueにすると最古のデータは2016年頃のデータが取れる)
                        'partial': Puppeteer._config['CANDLE']['PARTIAL']    # True(最新の未確定足を含む)、False(含まない)　未指定はTrue　（注意：まだバグっているのか、Falseでも最新足が含まれる）
                    }
                ) if Puppeteer._config['USE']['CANDLE'] == True else None
            # ----------------------------------
            # 資産状況の取得
            # ----------------------------------
            balance = Puppeteer._exchange.fetch_balance() if Puppeteer._config['USE']['BALANCE'] == True else None
            # print('BTC={}'.format(balance['BTC']['total']))
            # ----------------------------------
            # ポジション取得
            # ----------------------------------
            position = Puppeteer._exchange.private_get_position() if Puppeteer._config['USE']['POSITION'] == True else None
            # print('position={}, avgPrice={}'.format(position[0]['currentQty'], position[0]['avgEntryPrice']))
            # ----------------------------------
            # ticker取得
            # ----------------------------------
            ticker = Puppeteer._exchange.fetch_ticker(
                    symbol=Puppeteer._config['SYMBOL']                      # シンボル
                ) if Puppeteer._config['USE']['TICKER'] == True else None
            # print('last={}'.format(ticker['last']))
            # ----------------------------------
            # 板情報取得
            # ----------------------------------
            orderbook = Puppeteer._exchange.fetch_order_book(
                    symbol=Puppeteer._config['SYMBOL'],                     # シンボル
                    limit=Puppeteer._config['ORDERBOOK']['LIMIT']           # 取得件数(未指定:100、MAX:500)
                ) if Puppeteer._config['USE']['ORDERBOOK'] == True else None
            # print('bid={}, ask={}'.format(orderbook['bids'][0][0], orderbook['asks'][0][0]))
            # ----------------------------------
            # ストラテジ呼び出し
            # ----------------------------------
            Puppeteer._Puppet.run(ticker, orderbook, position, balance, candle)
            # ----------------------------------
            # 処理終了
            # ----------------------------------
            elapsed_time = time.time() - start
            # ----------------------------------
            # 上記までで消費された秒数だけ差し引いてスリープする
            # ----------------------------------
            interval = Puppeteer._config['INTERVAL']
            if interval - elapsed_time > 0:
                time.sleep(interval - elapsed_time)
            else:
                time.sleep(1)   # RUN時間が想定よりも長くかかってしまったため、すぐに次の処理に繊維する。
                Puppeteer._logger.warning('elapsed_time={} over interval time={}'.format(elapsed_time, interval))

    # ======================================
    # ccxtのfetch_ohlcv問題に対応するローカル関数
    #  partial問題については、
    #   https://note.mu/nagi7692/n/n5a52e0fa8c28
    #  の記事を参考にした
    #  また、結構な確率でOHLCデータがNoneになってくることがある。
    # ======================================
    def fetch_ohlcv(bitmex, symbol, timeframe='1m', since=None, limit=None, params={}):
        # timeframe1期間あたりの秒数
        period = {'1m': 1 * 60, '5m': 5 * 60, '1h': 60 * 60, '1d': 24 * 60 * 60}
    
        if bitmex is None:
            return None
        if timeframe not in period.keys():
            return None
    
        # 未確定の最新時間足のtimestampを取得(ミリ秒)
        now = datetime.utcnow()
        unixtime = calendar.timegm(now.utctimetuple())
        current_timestamp = (unixtime - (unixtime % period[timeframe]) + period[timeframe]) * 1000

        # for DEBUG
        # print('current_timestamp={} : {}'.format(current_timestamp, datetime.fromtimestamp(current_timestamp / 1000)))
    
        # partialフラグ
        is_partial = True
        if 'partial' in params.keys():
            is_partial = params['partial']
    
        # reverseフラグ
        is_reverse = False
        if 'reverse' in params.keys():
            is_reverse = params['reverse']
    
        # 取得件数(未指定は100件)
        fetch_count = 100 if limit is None else limit
        count = fetch_count
    
        # 取得後に最新足を除外するため、1件多く取得
        if is_partial == False:
            count += 1
        # 取得件数が足りないため、1件多く取得
        if is_reverse == False:
            count += 1
        # 1page最大500件のため、オーバーしている場合、500件に調整
        if count > 500:
            count = 500
    
        # OHLCVデータ取得
        ohlcvs = bitmex.fetch_ohlcv(symbol, timeframe, since, count, params)

        # for DEBUG
        # print('ohlcvs={}'.format(datetime.fromtimestamp(ohlcvs[-1][0] / 1000)))
    
        # partial=Falseの場合、未確定の最新足を除去する
        if is_partial == False:
            if is_reverse == True:
                # 先頭行のtimestampが最新足と一致したら除去
                if ohlcvs[0][0] == current_timestamp:
                    # True(New->Old)なので、最初データを削除する
                    ohlcvs = ohlcvs[1:]
            else:
                # 最終行のtimestampが最新足と一致したら除去
                if ohlcvs[-1][0] == current_timestamp:
                    # False(Old->New)なので、最後データを削除する
                    ohlcvs = ohlcvs[:-1]
    
        # 取得件数をlimit以下になるように調整
        while len(ohlcvs) > fetch_count:
            if is_reverse == True:
                # True(New->Old)なので、最後データから削除する, sinceが設定されているときは逆
                ohlcvs = ohlcvs[:-1] if since is None else ohlcvs[1:]
            else:
                # False(Old->New)なので、最初データから削除する, sinceが設定されているときは逆
                ohlcvs = ohlcvs[1:] if since is None else ohlcvs[:-1]
    
        return ohlcvs

    # ======================================
    # 実行開始
    # ======================================
    start()
