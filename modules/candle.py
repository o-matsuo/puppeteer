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

    __DIFF_TIME = 5     # 5秒

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

        # -------------------------------------------------------
        # timezone
        # -------------------------------------------------------
        self._tz = tz.utc

        # -------------------------------------------------------
        # 最大ロープ時間
        # period = {'1m': 1 * 60, '5m': 5 * 60, '1h': 60 * 60, '1d': 24 * 60 * 60}
        # -------------------------------------------------------
        self.__max_loop_time = 24 * 60 * 60     # MAX

        # -------------------------------------------------------
        # マルチタイムフレーム で定義されたローソク足に基準ローソク足が設定されていなかったら　1m, 5m, 1h, 1d　を設定する
        # -------------------------------------------------------
        # 1d
        if '1d' in self._config['MULTI_TIMEFRAME_CANDLE_SPAN_LIST']:
            self.__max_loop_time = 24 * 60 * 60  # 24時間
        # 1h
        for h in ['2h', '3h', '4h', '6h', '12h']:
            if '1h' not in self._config['MULTI_TIMEFRAME_CANDLE_SPAN_LIST'] and h in self._config['MULTI_TIMEFRAME_CANDLE_SPAN_LIST']:
                # 2h, 3h, 4h, 6h, 12hが定義されていて、1hが未定義
                self._config['MULTI_TIMEFRAME_CANDLE_SPAN_LIST'].insert(0, '1h')
                self.__max_loop_time = 1 * 60 * 60  # 1時間
                break
        if '1h' in self._config['MULTI_TIMEFRAME_CANDLE_SPAN_LIST']:
            self.__max_loop_time = 1 * 60 * 60  # 1時間
        # 5m
        for m5 in ['10m', '15m', '30m']:
            if '5m' not in self._config['MULTI_TIMEFRAME_CANDLE_SPAN_LIST'] and m5 in self._config['MULTI_TIMEFRAME_CANDLE_SPAN_LIST']:
                # 10m, 15m, 30mが定義されていて、5mが未定義
                self._config['MULTI_TIMEFRAME_CANDLE_SPAN_LIST'].insert(0, '5m')
                self.__max_loop_time = 5 * 60  # 5分
                break
        if '5m' in self._config['MULTI_TIMEFRAME_CANDLE_SPAN_LIST']:
            self.__max_loop_time = 5 * 60  # 5分
        # 1m
        for m1 in ['3m']:
            if '1m' not in self._config['MULTI_TIMEFRAME_CANDLE_SPAN_LIST'] and m1 in self._config['MULTI_TIMEFRAME_CANDLE_SPAN_LIST']:
                # 3mが定義されていて、1mが未定義
                self._config['MULTI_TIMEFRAME_CANDLE_SPAN_LIST'].insert(0, '1m')
                self.__max_loop_time = 1 * 60  # 1分
                break
        if '1m' in self._config['MULTI_TIMEFRAME_CANDLE_SPAN_LIST']:
            self.__max_loop_time = 1 * 60  # 1分

        # for DEBUG
        # print(self._config['MULTI_TIMEFRAME_CANDLE_SPAN_LIST'])

        # -------------------------------------------------------
        # Threadのロック用オブジェクト
        # -------------------------------------------------------
        self._lock = threading.Lock()

        # -------------------------------------------------------
        # マルチタイムフレーム ローソク足
        # タイムフレーム（設定可能: 1m, 3m, 5m, 10m, 15m, 30m, 1h, 2h, 3h, 4h, 6h, 12h, 1d）
        # -------------------------------------------------------
        self._candle = {}
        for span in self._config['MULTI_TIMEFRAME_CANDLE_SPAN_LIST']:
            self._candle[span] = None

        # -------------------------------------------------------
        # 起動時に初回ロード
        # -------------------------------------------------------
        self.__get_candle()

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

    # ===========================================================
    # candle
    # ===========================================================
    def candle(self, span):
        self.__thread_lock()
        _candle = self._candle[span][:]   # コピー
        self.__thread_unlock()

        return _candle

    # ===========================================================
    # Lock取得
    # ===========================================================
    def __thread_lock(self):
        _count = 0
        while self._lock.acquire(blocking=True, timeout=1) == False :
            _count += 1
            if _count > 3:
                self._logger.error('lock acquire: timeout')
                return False
        return True

    # ===========================================================
    # Lock解放
    # ===========================================================
    def __thread_unlock(self):
        try:
            self._lock.release()
        except Exception as e:
            self._logger.error('lock release: {}'.format(e))
            return False
        return True

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
                since=self._config['CANDLE']['SINCE'],              # データ取得開始時刻(Unix Timeミリ秒)
                limit=self._config['CANDLE']['LIMIT'],              # 取得件数(未指定:100、MAX:500)
                params={
                    'reverse': self._config['CANDLE']['REVERSE'],   # True(New->Old)、False(Old->New)　未指定時はFlase (注意：sineceを指定せずに、このフラグをTrueにすると最古のデータは2016年頃のデータが取れる)
                    'partial': self._config['CANDLE']['PARTIAL']    # True(最新の未確定足を含む)、False(含まない)　未指定はTrue　（注意：まだバグっているのか、Falseでも最新足が含まれる）
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
    # get candle
    # ==========================================================
    def __get_candle(self):
        # 1m, 3m, 5m, 10m, 15m, 30m, 1h, 2h, 3h, 4h, 6h, 12h, 1d
        for resolution in self._config['MULTI_TIMEFRAME_CANDLE_SPAN_LIST']:
            if resolution in ['1m', '5m', '1h', '1d']:
                self._candle[resolution] = self.__fetch_candle(resolution)
            elif resolution in ['3m']:
                self._candle[resolution] = self.__change_candleDF(self._candle['1m'], resolution)
            elif resolution in ['10m', '15m', '30m']:
                self._candle[resolution] = self.__change_candleDF(self._candle['5m'], resolution)
            elif resolution in ['2h', '3h', '4h', '6h', '12h']:
                self._candle[resolution] = self.__change_candleDF(self._candle['1h'], resolution)
            time.sleep(0.1)
            # for DEBUG
            # print(self._candle[resolution].tail(3))

    # ==========================================================
    # get_wait_time
    #   待ち時間を計算する
    #   params:
    #       timeframe: 1分、5分、1時間、1日
    #       diff:      あまりに使う時間（5秒前には処理に入ることにする）
    # ==========================================================
    def get_wait_time(self, timeframe=60, diff=5):
        now_dt = dt.now(self._tz)
        now_sec = now_dt.second
        now_min = now_dt.minute
        now_hour = now_dt.hour

        # for DEBUG
        # print('{}:{}:{}'.format(now_hour, now_min, now_sec))

        if timeframe == 1 * 60:
            # 1分
            if now_sec >= (timeframe - diff):
                return 0
            else:
                return timeframe - diff - now_sec
        elif timeframe == 5 * 60:
            # 5分
            if now_sec >= ((5 - now_min % 5) * 60 - diff):
                return 0
            else:
                return (5 - now_min % 5) * 60 - diff - now_sec
        elif timeframe == 1 * 60 * 60:
            # 1時間
            if now_sec >= ((60 - now_min) * 60 - diff):
                return 0
            else:
                return (60 - now_min) * 60 - diff - now_sec
        elif timeframe == 24 * 60 * 60:
            # 1日
            if now_sec >= ((24 - now_hour) * 60 * 60 - now_min * 60 - diff):
                return 0
            else:
                return (24 - now_hour) * 60 * 60 - now_min * 60 - diff - now_sec

    # ==========================================================
    # run
    # ==========================================================
    def __run(self, args):

        # -------------------------------------------------------
        # 毎時毎分0秒の5秒前までスリープしていることにする
        # -------------------------------------------------------
        sec = self.get_wait_time(self.__max_loop_time, Candle.__DIFF_TIME)
        if sec > 0:
            time.sleep(sec)

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

            # Lock
            self.__thread_lock()

            try:
                # ローソク足取得
                self.__get_candle()
            except Exception as e:
                self._logger.error('multi timeframe candle thread Exception {}'.format(e))
            finally:
                pass

            # unLock
            self.__thread_unlock()

            time.sleep(3)

            # 終了
            end = time.time()
            elapsed_time = end - start

            # ---------------------------------------------------
            # 時間調整
            # ---------------------------------------------------
            if elapsed_time >= self.__max_loop_time:
                # それほど時間を消費することはないと思うが、念のため
                self._logger.warning('multi timeframe candle thread: use time {}'.format(elapsed_time))
            else:
                # 毎時毎分0秒の5秒前までスリープしていることにする
                sec = self.get_wait_time(self.__max_loop_time, Candle.__DIFF_TIME)
                if sec > 0:
                    time.sleep(sec)

