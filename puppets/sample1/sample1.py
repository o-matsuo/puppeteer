# -*- coding: utf-8 -*-
# ==========================================
# サンプル Puppet (websocket)
# ==========================================
import datetime

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

        # websocketを使う時には、この引数は取得しなくて良い。
        self._logger.info("<<<<<<<<<<<<<<< running >>>>>>>>>>>>>>>")
        self._logger.info(
            "ticker {}, orderbook {}, position {}, balance {}, candle {}".format(
                ticker, orderbook, position, balance, candle
            )
        )

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
        # quotes
        # ------------------------------------------------------
        quote = self._ws.quotes()
        self._logger.info("quote: {}".format(quote))

        # ------------------------------------------------------
        # trades
        # ------------------------------------------------------
        trade = self._ws.trades()
        self._logger.info("trade: {}".format(trade))

        # ------------------------------------------------------
        # executions
        # ------------------------------------------------------
        execution = self._ws.executions()
        self._logger.info("execution: {}".format(execution))

        # ------------------------------------------------------
        # ticker
        # ------------------------------------------------------
        tick = self._ws.ticker()
        self._logger.info("tick: {}".format(tick))

        # ------------------------------------------------------
        # orderbookから最新のbid/askを取得する
        # ------------------------------------------------------
        orderbook = self._ws.orderbook()
        bid = orderbook["bids"][0]["price"]
        ask = orderbook["asks"][0]["price"]
        # 値チェック
        if bid == 0 or ask == 0 or bid == None or ask == None:
            self._logger.error("orderbook error: bid={}, ask={}".format(bid, ask))
            return
        self._logger.info("bid {}, ask {}".format(bid, ask))

        # ------------------------------------------------------
        # ポジションサイズ、参入価格
        # ------------------------------------------------------
        position = self._ws.position()
        if position is not {}:
            pos_qty = (
                position["currentQty"] if position["currentQty"] is not None else 0
            )
            avg_price = (
                position["avgEntryPrice"]
                if position["avgEntryPrice"] is not None
                else 0
            )
            self._logger.info("pos {}, avg {}".format(pos_qty, avg_price))

        # ------------------------------------------------------
        # オープンオーダー
        # ------------------------------------------------------
        self._logger.info("open orders = {}".format(self._ws.open_orders()))

        # ------------------------------------------------------
        # 資産
        # ------------------------------------------------------
        self._logger.info("balance {}".format(self._ws.funds()))

        # ------------------------------------------------------
        # ローソク足
        # ------------------------------------------------------
        candle = self._ws.candle(1)
        df = pd.DataFrame(
            candle,
            columns=[
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "buy",
                "sell",
            ],
        )
        df["timestamp"] = pd.to_datetime(
            df["timestamp"], unit="s", infer_datetime_format=True
        )
        df = df.set_index("timestamp")
        df.index = df.index.tz_localize(None)
        self._logger.info((df.tail(10)))
