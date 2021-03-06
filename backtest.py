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
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler
from os.path import splitext, basename

# fetch_ohlcv改良
from datetime import datetime, timedelta, timezone
import calendar

# bitmexラッパー
from exchanges.ccxt.bitmex import BitMEX

# websocket
from exchanges.websocket.inmemorydb_bitmex_websocket import BitMEXWebsocket

# ==========================================
# BackTest モジュール
# ==========================================
from modules.discord import Discord  # Discordクラス
from modules.balance import Balance  # Balanceクラス
from modules.heartbeat import Heartbeat  # Heartbeatクラス
from modules.candle import Candle  # Candleクラス

# ==========================================
# python pupeteer <実行ファイルのフルパス> <実行定義JSONファイルのフルパス>
# ==========================================
args = sys.argv


# ==========================================
# 傀儡師
# ==========================================
class BackTest:

    # ======================================
    # 初期化
    #   param:
    #       args: BackTest起動時の引数
    # ======================================
    def __init__(self, args):
        # ----------------------------------
        # timezone,timestamp
        # ----------------------------------
        self._tz = timezone.utc
        self._ts = datetime.now(self._tz).timestamp()
        # ----------------------------------
        # loggerの設定
        # ----------------------------------
        # logファイル名を抜き出す
        base, ext = splitext(basename(args[1]))  # 引数チェックをする前に引数を使っているけど、Loggerを先に作りたい。
        # loggerオブジェクトの宣言
        logger = getLogger("backtest")
        # loggerのログレベル設定(ハンドラに渡すエラーメッセージのレベル)
        logger.setLevel(logging.INFO)  # ※ここはConfigで設定可能にする
        # Formatterの生成
        formatter = Formatter(
            fmt="%(asctime)s, %(levelname)-8s, %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        # console handlerの生成・追加
        stream_handler = StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        # file handlerの生成・追加
        timedrotating_handler = TimedRotatingFileHandler(
            filename="logs/{}.log".format(base),  # logファイル名
            when="D",  # 1日を指定
            interval=1,  # 間隔
            backupCount=7,  # 7日間保持
            encoding="UTF-8",  # UTF-8
        )
        timedrotating_handler.setFormatter(formatter)
        logger.addHandler(timedrotating_handler)
        self._logger = logger
        # ----------------------------------
        # 資産状況通知loggerの設定
        # ----------------------------------
        self._balanceLogName = base + "-balance"  # ログ名称
        # balance格納用ログ
        # loggerオブジェクトの宣言
        balanceLogger = getLogger("balanceLogger")
        # loggerのログレベル設定(ハンドラに渡すエラーメッセージのレベル)
        balanceLogger.setLevel(logging.DEBUG)  # 絶対にログを出すので
        # Formatterの生成
        formatter = Formatter(fmt="%(message)s")
        # file handlerの生成・追加
        rotating_handler = RotatingFileHandler(
            filename="logs/" + self._balanceLogName + ".log",  # logファイル名
            maxBytes=100 * 1000 * 1000,  # 100MBを指定
            backupCount=7,  # 7個保持
            encoding="UTF-8",  # UTF-8
        )
        rotating_handler.setFormatter(formatter)
        balanceLogger.addHandler(rotating_handler)
        self._balanceLogger = balanceLogger  # balanceデータ格納ロガー
        # ----------------------------------
        # 引数チェック
        # ----------------------------------
        if len(args) != 3:
            self._logger.error("argument length != 3")
            exit()
        # ----------------------------------
        # 定義ファイルのロード
        # ----------------------------------
        with open(args[2], "r") as f:
            jsonData = json.load(f)
            # print(json.dumps(jsonData, sort_keys = True, indent = 4))
            self._config = jsonData
        # ----------------------------------
        # ログレベルの設定（デフォルトはINFO）
        # ----------------------------------
        if "LOG_LEVEL" in self._config:
            if self._config["LOG_LEVEL"] in [
                "CRITICAL",
                "ERROR",
                "WARNING",
                "INFO",
                "DEBUG",
            ]:
                self._logger.setLevel(eval("logging." + self._config["LOG_LEVEL"]))
        # ------------------------------
        # websocketを使うか
        # ------------------------------
        if "USE_WEBSOCKET" not in self._config:
            self._config["USE_WEBSOCKET"] = False
        # ------------------------------
        # bitmexラッパー
        # ------------------------------
        self._bitmex = BitMEX(
            symbol=self._config["SYMBOL"],  # BTC/USD   注意：XBTUSDではない
            apiKey=self._config["APIKEY"],
            secret=self._config["SECRET"],
            logger=self._logger,
            use_testnet=self._config["USE_TESTNET"],
        )
        # ------------------------------
        # 取引所オブジェクト(ccxt.bitmex)
        # ------------------------------
        self._exchange = self._bitmex._exchange
        # ----------------------------------
        # websocket
        # ----------------------------------
        self._ws = (
            BitMEXWebsocket(
                endpoint="wss://www.bitmex.com/realtime"
                if self._config["USE_TESTNET"] is False
                else "wss://testnet.bitmex.com/realtime",
                symbol=self._config["INFO_SYMBOL"],  # XBTUSD
                api_key=self._config["APIKEY"],
                api_secret=self._config["SECRET"],
                logger=self._logger,
                use_timemark=False,
            )
            if self._config["USE_WEBSOCKET"] == True
            else None
        )
        # instrumentメソッドを一度呼び出さないとエラーを吐くので追加(内部的にtickerがこの情報を使用するため)
        # if self._config['USE_WEBSOCKET'] == True:
        #    self._ws.instrument()
        # ----------------------------------
        # Discord生成
        # ----------------------------------
        self._discord = Discord(self._config["DISCORD_WEBHOOK_URL"])
        # ------------------------------
        # 資産状況通知を使うか
        # ------------------------------
        if "USE_SEND_BALANCE" not in self._config:
            self._config["USE_SEND_BALANCE"] = False
        # ------------------------------
        # マルチタイムフレームを使うかどうか
        # ------------------------------
        if "MULTI_TIMEFRAME_CANDLE_SPAN_LIST" not in self._config:
            self._config["MULTI_TIMEFRAME_CANDLE_SPAN_LIST"] = []

        # ------------------------------
        # マルチタイムフレーム ローソク足オブジェクト
        # ------------------------------
        self._candle = (
            Candle(self)
            if len(self._config["MULTI_TIMEFRAME_CANDLE_SPAN_LIST"]) != 0
            else None
        )

        # ----------------------------------
        # ストラテジのロードと生成
        # ----------------------------------
        module = machinery.SourceFileLoader("Puppet", args[1]).load_module()
        self._Puppet = module.Puppet(self)
        # ----------------------------------
        # 起動メッセージ
        # ----------------------------------
        message = "[傀儡師] 起動しました。Puppet={}, Config={}, 対象通貨ペア={}, RUN周期={}(秒)".format(
            args[1], args[2], self._config["SYMBOL"], self._config["INTERVAL"]
        )
        self._logger.info(message)
        self._discord.send(message)


# ==========================================
# メイン
# ==========================================
if __name__ == "__main__":
    # ======================================
    # 起動
    # ======================================
    def start():
        backtest = BackTest(args=args)
        # 資産状況通知
        balance = Balance(backtest) if backtest._config["USE_SEND_BALANCE"] else None
        heartbeat = Heartbeat(backtest) if backtest._config["USE_WEBSOCKET"] else None
        while True:
            try:
                run(BackTest=backtest)
            except KeyboardInterrupt:
                backtest._logger.info("[傀儡師] Ctrl-C検出: 処理を終了します")
                backtest._discord.send("[傀儡師] Ctrl-C検出: 処理を終了します")
                exit()
            except Exception as e:
                backtest._logger.error("[傀儡師] 例外発生[{}]: 処理を再起動します".format(e))
                backtest._discord.send("[傀儡師] 例外発生[{}]: 処理を再起動します".format(e))
                # websocket再接続
                if backtest._config["USE_WEBSOCKET"]:
                    backtest._ws.reconnect()
                time.sleep(5)

    # ======================================
    # メインループ
    # ======================================
    def run(BackTest):
        while True:
            # ----------------------------------
            # timestamp更新
            # ----------------------------------
            BackTest._ts = datetime.now(BackTest._tz).timestamp()
            # ----------------------------------
            # 引数の初期化
            # ----------------------------------
            ticker, orderbook, position, balance, candle = None, None, None, None, None
            # ----------------------------------
            # 処理開始
            # ----------------------------------
            start = time.time()
            try:
                # ------------------------------
                # ローソク足情報取得
                #  ローカル関数を使用
                # ------------------------------
                candle = (
                    BackTest._bitmex.ohlcv(
                        symbol=BackTest._config["SYMBOL"],  # シンボル
                        timeframe=BackTest._config["CANDLE"][
                            "TIMEFRAME"
                        ],  # timeframe= 1m 5m 1h 1d
                        since=BackTest._config["CANDLE"][
                            "SINCE"
                        ],  # データ取得開始時刻(Unix Timeミリ秒)
                        limit=BackTest._config["CANDLE"][
                            "LIMIT"
                        ],  # 取得件数(未指定:100、MAX:500)
                        params={
                            "reverse": BackTest._config["CANDLE"][
                                "REVERSE"
                            ],  # True(New->Old)、False(Old->New)　未指定時はFlase (注意：sineceを指定せずに、このフラグをTrueにすると最古のデータは2016年頃のデータが取れる)
                            "partial": BackTest._config["CANDLE"][
                                "PARTIAL"
                            ],  # True(最新の未確定足を含む)、False(含まない)　未指定はTrue　（注意：まだバグっているのか、Falseでも最新足が含まれる）
                        },
                    )
                    if BackTest._config["USE"]["CANDLE"] == True
                    else None
                )
                # ------------------------------
                # 資産状況の取得
                # ------------------------------
                balance = (
                    BackTest._bitmex.balance()
                    if BackTest._config["USE"]["BALANCE"] == True
                    else None
                )
                # print('BTC={}'.format(balance['BTC']['total']))
                # ------------------------------
                # ポジション取得
                # ------------------------------
                position = (
                    BackTest._bitmex.position()
                    if BackTest._config["USE"]["POSITION"] == True
                    else None
                )
                # print('position={}, avgPrice={}'.format(position[0]['currentQty'], position[0]['avgEntryPrice']))
                # ------------------------------
                # ticker取得
                # ------------------------------
                ticker = (
                    BackTest._bitmex.ticker(symbol=BackTest._config["SYMBOL"])  # シンボル
                    if BackTest._config["USE"]["TICKER"] == True
                    else None
                )
                # print('last={}'.format(ticker['last']))
                # ------------------------------
                # 板情報取得
                # ------------------------------
                orderbook = (
                    BackTest._bitmex.orderbook(
                        symbol=BackTest._config["SYMBOL"],  # シンボル
                        limit=BackTest._config["ORDERBOOK"][
                            "LIMIT"
                        ],  # 取得件数(未指定:100、MAX:500)
                    )
                    if BackTest._config["USE"]["ORDERBOOK"] == True
                    else None
                )
                # print('bid={}, ask={}'.format(orderbook['bids'][0][0], orderbook['asks'][0][0]))
            except Exception as e:
                # bitmexオブジェクトの実行で例外が発生したが、再起動はしないで処理を継続する
                BackTest._logger.error(
                    "BackTest.run() bitmex Exception: {}".format(e)
                )
                # 処理時間がINTERVALよりも長かったらワーニングを出す
                elapsed_time = time.time() - start
                if elapsed_time > BackTest._config["INTERVAL"]:
                    BackTest._logger.warning(
                        "elapsed_time={} over interval time={}".format(
                            elapsed_time, BackTest._config["INTERVAL"]
                        )
                    )
                # 処理をすぐに継続する
                continue
            # ----------------------------------
            # websocketを使っていた場合、force_exitフラグのチェック
            # ----------------------------------
            if BackTest._config["USE_WEBSOCKET"] and BackTest._ws.is_force_exit():
                raise Exception("websocket force exit")
            # ----------------------------------
            # ストラテジ呼び出し
            # ----------------------------------
            BackTest._Puppet.run(ticker, orderbook, position, balance, candle)
            # ----------------------------------
            # 処理終了
            # ----------------------------------
            elapsed_time = time.time() - start
            # ----------------------------------
            # 上記までで消費された秒数だけ差し引いてスリープする
            # ----------------------------------
            interval = BackTest._config["INTERVAL"]
            if interval - elapsed_time > 0:
                time.sleep(interval - elapsed_time)
            else:
                time.sleep(1)  # RUN時間が想定よりも長くかかってしまったため、すぐに次の処理に繊維する。
                BackTest._logger.warning(
                    "elapsed_time={} over interval time={}".format(
                        elapsed_time, interval
                    )
                )

    # ======================================
    # 実行開始
    # ======================================
    start()
