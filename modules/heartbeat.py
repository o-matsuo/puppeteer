# -*- coding: utf-8 -*-
# ==========================================
# Discord
# ==========================================
import time
from datetime import datetime, timedelta, timezone
# thred操作
import threading

#from puppeteer import Puppeteer

# ==============================================================
# Heartbeat クラス
#   param:
#       puppeteer: Puppeteerオブジェクト
# ==============================================================
class Heartbeat:

    # ==========================================================
    # 初期化
    #   param:
    #       puppeteer: Puppeteerオブジェクト
    # ==========================================================
    def __init__(self, Puppeteer):
        self._exchange = Puppeteer._exchange    # 取引所オブジェクト(ccxt.bitmex)
        self._logger = Puppeteer._logger        # logger
        self._config = Puppeteer._config        # 定義ファイル
        self._ws = Puppeteer._ws                # websocket
        self._bitmex = Puppeteer._bitmex        # ccxt.bimexラッパーオブジェクト
        self._discord = Puppeteer._discord      # discord
        self._puppeteer = Puppeteer             # puppeteer

        # websocketが無効
        if not self._config['USE_WEBSOCKET']:
            self._logger.warning('heartbeat check is None. because [not websocket]')

        # -------------------------------------------------------
        # 開始時刻のタイムスタンプ
        # -------------------------------------------------------
        self._tz = timezone.utc
        self._ts = datetime.now(self._tz).timestamp()

        # -------------------------------------------------------
        # 資産状況通知スレッド
        # -------------------------------------------------------
        self._check_heart_beat_thread = threading.Thread(target=self.__run, args=('check_heart_beat',))
        self._check_heart_beat_thread.daemon = True
        self._check_heart_beat_thread.start()
        self._logger.debug("Started check heart beat thread")

    # ===========================================================
    # デストラクタ
    # ===========================================================
    def __del__(self):
        self._check_heart_beat_thread.join(timeout=3) # この値が妥当かどうか検討する

    # ==========================================================
    # run
    # ==========================================================
    def __run(self, args):
        while True:

            # 開始
            start = time.time()

            self._ts = datetime.now(self._tz).timestamp()
            # ---------------------------------------------------
            # メイン処理
            # ---------------------------------------------------
            try:
                # -----------------------------------------------
                # Puppeteer動作heart beat
                # -----------------------------------------------
                self._logger.warning('puppeteer ts:{}, diff:{}'.format(self._puppeteer._ts, self._ts - self._puppeteer._ts))
                # -----------------------------------------------
                # websocke動作heart beat
                # -----------------------------------------------
                self._logger.warning('websocket ts:{}, diff:{}, status:{}'.format(self._ws._ts, self._ts - self._ws._ts, self._ws._ws_status))
            except Exception as e:
                self._logger.error('check heart beat thread: Exception: {}'.format(e))
            
            # 終了
            end = time.time()
            elapsed_time = end - start

            # ---------------------------------------------------
            # 時間調整
            # ---------------------------------------------------
            if elapsed_time >= 60:
                # それほど時間を消費することはないと思うが、念のため
                self._logger.warning('check heart beat thread: use time {}'.format(elapsed_time))
            else:
                # 毎時毎分0秒の5秒前までスリープしていることにする
                now_sec = datetime.now(self._tz).second
                if now_sec >= 55:
                    pass
                else:
                    time.sleep(55 - now_sec)

