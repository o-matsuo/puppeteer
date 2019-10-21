# -*- coding: utf-8 -*-
# ==========================================
# バックテストデータ収集 Puppet (websocket)
# ==========================================
#from datetime import datetime, timedelta, timezone
import dateutil.parser
import time

import pandas as pd

from puppeteer import Puppeteer


# ==========================================
# Puppet(傀儡) クラス
# ==========================================
class Puppet:

    # ==========================================================
    # 初期化
    #   param:
    #       puppeteer: Puppeteerオブジェクト
    # ==========================================================
    def __init__(self, Puppeteer):
        self._exchange = Puppeteer._exchange  # 取引所オブジェクト(ccxt.bitmex)
        self._logger = Puppeteer._logger  # logger
        self._config = Puppeteer._config  # 定義ファイル
        self._ws = Puppeteer._ws  # websocket
        self._bitmex = Puppeteer._bitmex  # ccxt.bimexラッパーオブジェクト
        self._discord = Puppeteer._discord  # discord
        self._candle = Puppeteer._candle  # Candleクラス

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

        # Socketの接続が活きている and 強制終了フラグがOFF の限り処理を続ける
        if (
            not self._ws.ws.sock
            and not self._ws.ws.sock.connected
            and self._ws.is_force_exit()
        ):
            self._logger.warning("websocket not running / force exit")
            return

        # --------------------------
        # ここに処理を記述します
        # --------------------------

        # ------------------------------------------------------
        # 処理時間計測開始
        # ------------------------------------------------------
        start = time.time()

        # ------------------------------------------------------
        # trades
        # ------------------------------------------------------
        trade = self._ws.trades()
        self._logger.info("trade: {}".format(trade[-1]))
        ts = round(dateutil.parser.parse(trade[-1]["timestamp"]).timestamp())
        print(f"timestamp: {ts}")

        """
        {
            'timestamp': '2019-10-21T10:49:07.804Z', 
            'symbol': 'XBTUSD', 
            'side': 'Sell', 
            'size': 38, 
            'price': 8274.5, 
            'tickDirection': 'ZeroMinusTick', 
            'trdMatchID': '11f2fa4d-4c89-bef3-3cf2-ea047540792d', 
            'grossValue': 459230, 
            'homeNotional': 0.0045923, 
            'foreignNotional': 38
        }
        """

        # ------------------------------------------------------
        # ローソク足
        # ------------------------------------------------------
        df = self._candle.candle("1m")
        self._logger.info(df.tail(5))

        # ------------------------------------------------------
        # 処理時間計測終了
        # ------------------------------------------------------
        end = time.time()
        elapsed_time = end - start
        self._logger.debug("elapsed_time: {}".format(elapsed_time))
        # for DEBUG
        # print('経過時間 {}'.format(round(elapsed_time,3)))

        # ------------------------------------------------------
        # 次回までの待ち時間を計算して、想定の半分以上を使っていたら警告を出す
        # ------------------------------------------------------
        if (self._config["INTERVAL"] / 2) < elapsed_time:
            self._logger.warning("time use {}[sec]".format(elapsed_time))

    # ==========================================================
    # DB初期化
    # ==========================================================
    def _init_db(self):
        pass

    # ==========================================================
    # DB挿入 (Replace)
    # ==========================================================
    def _replace_db(self, data):
        pass
