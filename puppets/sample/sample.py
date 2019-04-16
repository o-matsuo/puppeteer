# -*- coding: utf-8 -*-
# ==========================================
# サンプル Puppet
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
        # --------------------------
        # ここに処理を記述します
        # --------------------------
        # ------------------------------------------------------
        # orderbookから最新のbid/askを取得する
        # ------------------------------------------------------
        bid = orderbook['bids'][0][0]
        ask = orderbook['asks'][0][0]
        # 値チェック
        if bid == 0 or ask == 0 or bid == None or ask == None :
            self._logger.error('orderbook error: bid={}, ask={}'.format(bid, ask))
            return

        # ------------------------------------------------------
        # ポジションサイズ、参入価格
        # ------------------------------------------------------
        pos_qty = position[0]['currentQty'] if position[0]['currentQty'] is not None else 0
        avg_price = position[0]['avgEntryPrice'] if position[0]['avgEntryPrice'] is not None else 0

        # ------------------------------------------------------
        # LOT取得
        # ------------------------------------------------------
        lot = self._config['LOT_SIZE']
        