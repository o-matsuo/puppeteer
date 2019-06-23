# -*- coding: utf-8 -*-
# ==========================================
# Candle
# ==========================================
import time
from datetime import datetime as dt, timezone as tz, timedelta as delta
# thred操作
import threading
# csv reader として利用
import pandas as pd

#from .. import Puppeteer

# ==============================================================
# Candle クラス
#   param:
#       puppeteer: Puppeteerオブジェクト
# ==============================================================
class Candle:

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

        # for DEBUG
        self._config['MULTI_TIMEFRAME_CANDLE_SPAN_LIST'] = ['5m', '15m']

        # -------------------------------------------------------
        # timezone
        # -------------------------------------------------------
        self._tz = tz.utc

        # -------------------------------------------------------
        # マルチタイムフレーム ローソク足
        # -------------------------------------------------------
        self._candle = {}
        for span in self._config['MULTI_TIMEFRAME_CANDLE_SPAN_LIST']:
            self._candle[span] = None

        # -------------------------------------------------------
        # マルチタイムフレーム ローソク足 スレッド
        # -------------------------------------------------------
        self._candle_thread = threading.Thread(target=self.__run, args=('collect_candle',))
        self._candle_thread.daemon = True
        self._candle_thread.start()
        self._logger.debug("Started multi timeframe candle thread")

    # ===========================================================
    # デストラクタ
    # ===========================================================
    def __del__(self):
        self._candle_thread.join(timeout=3) # この値が妥当かどうか検討する

    # ==========================================================
    # ローソク足取得(ccxt)
    # ==========================================================
    def __fetch_candle(self, resolution='1m'):
        # 引数チェック
        if resolution not in ['1m', '5m', '1h', '1d']:
            return None

        # -----------------------------------------------
        # 1分ローソク足情報取得
        # -----------------------------------------------
        candle = self._bitmex.ohlcv(
                symbol=self._config['SYMBOL'],  # シンボル
                timeframe=resolution,           # timeframe= 1m 5m 1h 1d
                since=None,                     # データ取得開始時刻(Unix Timeミリ秒)
                limit=499,                      # 取得件数(未指定:100、MAX:500)
                params={
                    'reverse': False,           # True(New->Old)、False(Old->New)　未指定時はFlase (注意：sineceを指定せずに、このフラグをTrueにすると最古のデータは2016年頃のデータが取れる)
                    'partial': False            # True(最新の未確定足を含む)、False(含まない)　未指定はTrue　（注意：まだバグっているのか、Falseでも最新足が含まれる）
                }
            )
        # -----------------------------------------------
        # Pandasのデータフレームに
        # -----------------------------------------------
        df = pd.DataFrame(candle,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        # -----------------------------------------------
        # 日時データをDataFrameのインデックスにする
        # -----------------------------------------------
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True, infer_datetime_format=True) # UNIX時間(ミリ秒)を変換, UTC=TrueでタイムゾーンがUTCに設定される, infer_datetime_format=Trueは高速化に寄与するとのこと。
        df = df.set_index('timestamp')

        return df

    # ==========================================================
    # ローソク足の足幅変換
    #   params:
    #       ohlcv: DataFrame (pandas)
    #       resolution: 刻み幅(1m, 3m, 5m, 15m, 30m, 1h, 2h, 3h, 4h, 6h, 12h, 1d, 3d, 1w, 2w, 1M)
    # ==========================================================
    def __change_candleDF(self, ohlcv, resolution='1m'):
        # 参考にしたサイト https://docs.pyq.jp/python/pydata/pandas/resample.html
        """
        -------+------+------
        引数    単位    区切り
        -------+------+------
        AS	    年      年初
        A	    年	    年末
        MS	    月	    月初
        M	    月	    月末
        W	    週	    日曜
        D	    日	    0時
        H	    時	    0分
        T,min	分	    0秒
        S	    秒
        L,ms    ミリ秒
        U,us    マイクロ秒
        N,ns    ナノ秒
        """
        
        """
        -------+------+------
        関数    説明
        -------+------+------
        min	    最小
        max	    最大
        sum	    合計
        mean	平均
        first	最初の値
        last    最後の値
        interpolate	補間        
        """

        period = {
            '1m' : '1T', 
            '3m' : '3T', 
            '5m' : '5T', 
            '15m' : '15T', 
            '30m' : '30T', 
            '1h' : '1H', 
            '2h' : '2H', 
            '3h' : '3H', 
            '4h' : '4H', 
            '6h' : '6H', 
            '12h' : '12H', 
            '1d' : '1D', 
            '3d' : '3D', 
            '1w' : '1W', 
            '2w' : '2W', 
            '1M' : '1M'
        }

        if resolution not in period.keys():
            return None

        # 他の分刻みに直す
        df = ohlcv[['open', 'high', 'low', 'close', 'volume']].resample(period[resolution], label='left', closed='left').agg({
                'open': 'first', 
                'high': 'max', 
                'low': 'min', 
                'close': 'last',
                'volume': 'sum'
            })
            # ohlcを再度ohlcに集計するにはaggメソッド
        
        return df

    # ==========================================================
    # run
    # ==========================================================
    def __run(self, args):

        # -------------------------------------------------------
        # 毎時毎分0秒の5秒前までスリープしていることにする
        # -------------------------------------------------------
        now_sec = dt.now(self._tz).second
        if now_sec >= 55:
            pass
        else:
            time.sleep(55 - now_sec)

        # -------------------------------------------------------
        # 処理ループ（exit用のフラグを儲けるか？）
        # -------------------------------------------------------
        while True:

            # ---------------------------------------------------
            # 時刻が0秒をすぎたら実行する
            # ---------------------------------------------------
            while dt.now(self._tz).second not in [0,1,2]:
                time.sleep(1)

            # 開始
            start = time.time()

            try:
                # 1m, 3m, 5m, 10m, 15m, 30m, 1h, 2h, 3h, 4h, 6h, 12h
                for resolution in self._config['MULTI_TIMEFRAME_CANDLE_SPAN_LIST']:
                    if resolution in ['1m', '5m', '1h']:
                        self._candle[resolution] = self.__fetch_candle(resolution)
                    elif resolution in ['3m']:
                        self._candle[resolution] = self.__change_candleDF(self._candle['1m'], resolution)
                    elif resolution in ['10m', '15m', '30m']:
                        self._candle[resolution] = self.__change_candleDF(self._candle['5m'], resolution)
                    elif resolution in ['2h', '3h', '4h', '6h', '12h']:
                        self._candle[resolution] = self.__change_candleDF(self._candle['1h'], resolution)
                    time.sleep(0.1)
                    # for DEBUG
                    print(self._candle[resolution].tail(3))

            except Exception as e:
                self._logger.error('multi timeframe candle thread Exception {}'.format(e))
            finally:
                pass

            time.sleep(3)

            # 終了
            end = time.time()
            elapsed_time = end - start

            # ---------------------------------------------------
            # 時間調整
            # ---------------------------------------------------
            if elapsed_time >= 60:
                # それほど時間を消費することはないと思うが、念のため
                self._logger.warning('multi timeframe candle thread: use time {}'.format(elapsed_time))
            else:
                # 毎時毎分0秒の5秒前までスリープしていることにする
                now_sec = dt.now(self._tz).second
                if now_sec >= 55:
                    pass
                else:
                    time.sleep(55 - now_sec)

