#!/usr/bin/python3

# sudo pip install websocket-client==0.47
# version指定
import websocket
# thred操作
import threading
# for datetime,time関連
from datetime import datetime, timedelta, timezone
import dateutil.parser
import time
# json操作
import json
# for logging
import logging
import traceback
# import urllibだけだとエラーになる
import urllib.parse
# for instrument
import math
# for signature
import hmac, hashlib
# sqlite
import sqlite3
# for logging
import logging
from logging import getLogger, StreamHandler, Formatter
# listのコピー
import copy

# サポートクラス
# 板情報
from exchanges.websocket.orderbook import OrderBook
# 注文情報
from exchanges.websocket.order import Order

# ###############################################################
# Naive implementation of connecting to BitMEX websocket for streaming realtime data.
# The Marketmaker still interacts with this as if it were a REST Endpoint, but now it can get
# much more realtime data without polling the hell out of the API.
#
# The Websocket offers a bunch of data as raw properties right on the object.
# On connect, it synchronously asks for a push of all this data then returns.
# Right after, the MM can start using its data. It will be updated in realtime, so the MM can
# poll really often if it wants.
# ###############################################################
class BitMEXWebsocket:

    # Don't grow a table larger than this amount. Helps cap memory usage.
    MAX_TABLE_LEN = 1000
    # order bookの最大保持数
    MAX_ORDERBOOK_LEN = 100
    # ローソク足の刻み幅
    CANDLE_RANGE = 5
    MAX_CANDLE_LEN = int(3600 / CANDLE_RANGE)    # 1h分

    # ===========================================================
    # コンストラクタ
    # ===========================================================
    def __init__(self, endpoint, symbol='XBTUSD', api_key=None, api_secret=None, logger=None, use_timemark=False):
        '''Connect to the websocket and initialize data stores.'''
        # -------------------------------------------------------
        # logger
        # -------------------------------------------------------
        self.logger = logger if logger is not None else logging.getLogger(__name__)
        self.logger.info("BitMEXWebsocket constructor")

        # -------------------------------------------------------
        # endpoint, symbol
        # -------------------------------------------------------
        self.endpoint = endpoint
        self.symbol = symbol

        # -------------------------------------------------------
        # apikey,secret
        # -------------------------------------------------------
        if api_key is not None and api_secret is None:
            raise ValueError('api_secret is required if api_key is provided')
        if api_key is None and api_secret is not None:
            raise ValueError('api_key is required if api_secret is provided')

        self.api_key = api_key
        self.api_secret = api_secret

        # -------------------------------------------------------
        # 時間計測するかどうか
        # -------------------------------------------------------
        self._use_timemark = use_timemark

        # -------------------------------------------------------
        # Threadのロック用オブジェクト
        # -------------------------------------------------------
        self._lock = threading.Lock()

        # -------------------------------------------------------
        # ローカル変数 設定
        # -------------------------------------------------------
        self.__initialize_params()

        # -------------------------------------------------------
        # websocket初期化、スレッド生成
        # -------------------------------------------------------
        # We can subscribe right in the connection querystring, so let's build that.
        # Subscribe to all pertinent endpoints
        wsURL = self.__get_url()
        self.logger.info("Connecting to %s" % wsURL)
        self.__connect(wsURL, symbol)
        self.logger.info('Connected to WS.')

        # -------------------------------------------------------
        # 各メッセージの「partial」が到着するまで待機
        # -------------------------------------------------------
        # apikeyが必要無いもの
        # -------------------------------------------------------
        self.__wait_for_symbol(symbol)
        # -------------------------------------------------------
        # tickerがinstrumentの情報を使用するため
        # -------------------------------------------------------
        time.sleep(0.1)
        self.instrument()
        # -------------------------------------------------------
        # apikeyを持つもの
        # -------------------------------------------------------
        if api_key:
            self.__wait_for_account()
        self.logger.info('Got all market data. Starting.')

    # ===========================================================
    # デストラクタ
    # ===========================================================
    def __del__(self):
        self.logger.info('BitMEXWebsocket destructor')
        if not self.exited:
            # クロースずる
            self.exit()

    # ###########################################################
    # public methods
    # ###########################################################
    def reconnect(self):

        # -------------------------------------------------------
        # 終了処理が未実施だったら終了処理を実行
        # -------------------------------------------------------
        if not self.exited:
            self.exit()

        # -------------------------------------------------------
        # ローカル変数 再設定開始
        # -------------------------------------------------------
        self.__initialize_params()

        # -------------------------------------------------------
        # websocket初期化、スレッド生成
        # -------------------------------------------------------
        try:
            # We can subscribe right in the connection querystring, so let's build that.
            # Subscribe to all pertinent endpoints
            wsURL = self.__get_url()
            self.logger.info("Connecting to %s" % wsURL)
            self.__connect(wsURL, self.symbol)
            self.logger.info('Connected to WS.')
        except Exception as e:
            self.logger.error('websocket reconnect() : __connect() error = {}'.format(e))

        # -------------------------------------------------------
        # 各メッセージの「partial」が到着するまで待機
        # -------------------------------------------------------
        try:
            # ---------------------------------------------------
            # apikeyが必要無いもの
            # ---------------------------------------------------
            self.__wait_for_symbol(self.symbol)
            # ---------------------------------------------------
            # tickerがinstrumentの情報を使用するため
            # ---------------------------------------------------
            time.sleep(0.1)
            self.instrument()
            # ---------------------------------------------------
            # apikeyを持つもの
            # ---------------------------------------------------
            if self.api_key:
                self.__wait_for_account()
            self.logger.info('Got all market data. Starting.')
        except Exception as e:
            self.logger.error('websocket reconnect() : __wait_for_xx() error = {}'.format(e))

    # ===========================================================
    # 終了
    # ===========================================================
    def exit(self):
        '''Call this to exit - will close websocket.'''
        self.exited = True
        # for DEBUG
        time.sleep(1)

        # -------------------------------------------------------
        # check candle スレッドの終了
        # -------------------------------------------------------
        try:
            # スレッド終了
            self.__check_candle_thread_exit()
        except Exception as e:
            self.logger.error('websocket exit() check candle thread exit : error = {}'.format(e))
        finally:
            #self._check_candle_thread = None   # reconnect の再帰に備えてクリアしない
            pass

        # -------------------------------------------------------
        # websocketのクローズ
        # -------------------------------------------------------
        try:
            # websokectクローズ
            if self.ws:
                self.ws.keep_running = False # 永遠に実行中をやめる
                # ソケットクローズ
                if self.ws.sock or self.ws.sock.connected:
                    self.ws.close()
                    self.logger.info('websocket exit() socket closed')
                    time.sleep(1)
        except Exception as e:
            self.logger.error('websocket exit() socket close: error = {}'.format(e))
        finally:
            #self.ws = None
            pass

        # -------------------------------------------------------
        # websocket スレッドの終了
        # -------------------------------------------------------
        try:
            # スレッド終了
            self.__wst_thread_exit()
        except Exception as e:
            self.logger.error('websocket exit() websocket thread exit : error = {}'.format(e))
        finally:
            #self.wst = None     # reconnect の再帰に備えてクリアしない
            self.ws = None

        # -------------------------------------------------------
        # DBクローズ
        # -------------------------------------------------------
        try:
            # db close
            self._db.close()
            # db用オブジェクトの削除
            del self._orderbook
            del self._order
        except Exception as e:
            self.logger.error('websocket exit() db close : error = {}'.format(e))
        finally:
            self._db = None
            self._orderbook = None
            self._order = None

    # ===========================================================
    # quote, trade, execution は追記型
    # ===========================================================
    # quotes
    # ===========================================================
    def quotes(self):
        '''Get recent quotes.'''
        return self.data['quote']

    # ===========================================================
    # trades
    # ===========================================================
    def trades(self):
        '''Get recent trades.'''
        return self.data['trade']

    # ===========================================================
    # executions
    # ===========================================================
    def executions(self):
        '''Get recent executions.'''
        return self.data['execution']

    # ===========================================================
    # margin(funds), position, instrument は更新型
    # ===========================================================
    # funds (margin)
    # ===========================================================
    def funds(self):
        '''Get your margin details.'''
        return self.data['margin']

    # ===========================================================
    # position
    # ===========================================================
    def position(self):
        ''' Get your position details.'''
        return self.data['position']

    # ===========================================================
    # instrument
    # ===========================================================
    def instrument(self):
        '''Get the raw instrument data for this symbol.'''
        # Turn the 'tickSize' into 'tickLog' for use in rounding
        instrument = self.data['instrument']
        instrument['tickLog'] = int(math.fabs(math.log10(instrument['tickSize'])))
        return instrument

    # ===========================================================
    # tickerはquote,trade,instrumentから作成された合成型
    # ===========================================================
    # ticker
    # ===========================================================
    def ticker(self):
        '''Return a ticker object. Generated from quote and trade.'''
        lastQuote = self.data['quote'][-1]
        lastTrade = self.data['trade'][-1]
        ticker = {
            "last": lastTrade['price'],
            "bid": lastQuote['bidPrice'],
            "ask": lastQuote['askPrice'],
            "mid": (float(lastQuote['bidPrice'] or 0) + float(lastQuote['askPrice'] or 0)) / 2
        }

        # The instrument has a tickSize. Use it to round values.
        instrument = self.data['instrument']
        return {k: round(float(v or 0), instrument['tickLog']) for k, v in ticker.items()}

    # ===========================================================
    # orders, orderbook はDB型(partial, insert, update, delete)
    # ===========================================================
    # open orders
    # ===========================================================
    def open_orders(self, clOrdIDPrefix=None):
        '''Get all your open orders.'''
        self.__thread_lock()
        # orders = self.data['order']
        orders = self._order.get_orders()
        self.__thread_unlock()
        if clOrdIDPrefix is None:
            # Filter to only open orders (leavesQty > 0) and those that we actually placed
            return [o for o in orders if o['leavesQty'] > 0]
        else:
            # Filter to only open orders (leavesQty > 0) and those that we actually placed
            return [o for o in orders if str(o['clOrdID']).startswith(clOrdIDPrefix) and o['leavesQty'] > 0]

    # ===========================================================
    # market depth (orderbook)
    # ===========================================================
    def orderbook(self):
        '''Get market depth (orderbook). Returns all levels.'''
        # return self.data['orderBookL2']
        self.__thread_lock()
        book = self._orderbook.get_orderbook(BitMEXWebsocket.MAX_ORDERBOOK_LEN)
        self.__thread_unlock()
        return book
    # ===========================================================
    # candle
    #   params:
    #       type: 0, 未確定含まない, 1: 未確定含む
    # ===========================================================
    def candle(self, type=0):
        if type == 0:
            return self._candle[:-1]
        return self._candle

    # ==========================================================
    # ヘルパー関数
    # ==========================================================
    # 注文更新で使用する orderID, price, leavesQtyを注文から取得
    #   param:
    #       order: order
    #   return:
    #       orderID, price, leavesQty
    # ==========================================================
    def get_amend_params(self, order):
        orderID = order['orderID']
        price = order['price']
        leavesQty = order['leavesQty']
        return orderID, price, leavesQty

    # ==========================================================
    # 注文削除で使用する orderID を取得する
    #   param:
    #       orders: order配列
    #   return:
    #       orderID（複数ある場合は 'xxxx,yyyy,zzzz'）
    # ==========================================================
    def get_cancel_params(self, orders):
        orderIDs = ''
        for o in orders:
            if orderIDs != '':
                orderIDs += ','
            orderIDs += o['orderID']
        return orderIDs

    # ==========================================================
    # 注文価格配列を order から取得する
    #   param:
    #       orders: order配列
    #   return:
    #       price list
    # ==========================================================
    def get_price_list(self, orders):
        prices = []
        for o in orders:
            prices.append(o['price'])
        return prices

    # ==========================================================
    # 指定したclOrdIDを含む注文を検索・取得
    #   params:
    #       clOrdID: 'limit_buy', 'limit_sell', 'settle_buy' or 'settle_sell' -> 'settle'だけで決済注文を検索しても良い
    # ==========================================================
    def find_orders(self, open_orders, clOrdID):
        return [order for order in open_orders if 0 < order['clOrdID'].find(clOrdID)]

    # ###########################################################
    # local Methods
    # ###########################################################

    # ===========================================================
    # ローカル変数の初期化
    #   プログラムで変更される可能性のあるデータ
    # ===========================================================
    def __initialize_params(self):
        # メッセージデータ
        self.data = {}
        self.exited = False

        # candle
        self._candle = []
        """
            candleデータの構造
            {
                'timestamp': round(datetime.utcnow().timestamp()),
                'open': 0,
                'high': 0,
                'low': 0,
                'close': 0,
                'volume': 0,
                'buy': 0,
                'sell':0
            }
        """

        # sqlite3 (in memory database)
        self._db = sqlite3.connect(
                database=':memory:',            # in memory
                isolation_level='EXCLUSIVE',    # 開始時にEXCLUSIVEロックを取得する
                check_same_thread=False         # 他のスレッドからの突入を許す
            )

        # orderbook クラス作成
        self._orderbook = OrderBook(self._db, self.logger)
        # order クラス作成
        self._order = Order(self._db, self.logger)

        # 高速化のため、各処理の処理時間を格納するtimemarkを作成
        self.timemark = {}
        self.timemark['partial'] = 0
        self.timemark['insert'] = 0
        self.timemark['update'] = 0
        self.timemark['delete'] = 0
        self.timemark['count'] = 0

        self.__initialize_timemark('execution')
        self.__initialize_timemark('order')
        self.__initialize_timemark('position')
        self.__initialize_timemark('quote')
        self.__initialize_timemark('trade')
        self.__initialize_timemark('margin')
        self.__initialize_timemark('instrument')
        self.__initialize_timemark('orderBookL2')

    # ===========================================================
    # timemarkテーブルの初期化
    # ===========================================================
    def __initialize_timemark(self, table):
        self.timemark[table] = {}
        self.timemark[table]['partial'] = 0
        self.timemark[table]['insert'] = 0
        self.timemark[table]['update'] = 0
        self.timemark[table]['delete'] = 0
        self.timemark[table]['count'] = 0

    # ===========================================================
    # websocket thread終了
    # ===========================================================
    def __wst_thread_exit(self):
        while self.wst.is_alive():
            self.wst.join(timeout=3) # この値が妥当かどうか検討する
            if self.wst.is_alive() == True:
                self.logger.warning('websocket thread {} still alive'.format(self.wst))
            else:
                self.logger.info("websocket thread is ended.")
        """
        self.wst.join(timeout=5) # この値が妥当かどうか検討する
        if self.wst.is_alive() == True:
            self.logger.warning('websocket thread {} still alive'.format(self.wst))
        else:
            self.logger.info("websocket thread is ended.")
        """

    # ===========================================================
    # check candle thread終了
    # ===========================================================
    def __check_candle_thread_exit(self):
        # check candle thread
        while self._check_candle_thread.is_alive():
            self._check_candle_thread.join(timeout=3) # この値が妥当かどうか検討する
            if self._check_candle_thread.is_alive() == True:
                self.logger.warning('check candle thread {} still alive'.format(self._check_candle_thread))
            else:
                self.logger.info("check candle thread is ended.")
        """
        self._check_candle_thread.join(timeout=5)
        if self._check_candle_thread.is_alive() == True:
            self.logger.warning('check candle thread {} still alive'.format(self._check_candle_thread))
        else:
            self.logger.info("check candle thread is ended.")
        """

    # ===========================================================
    # Lock取得
    # ===========================================================
    def __thread_lock(self):
        _count = 0
        while self._lock.acquire(blocking=True, timeout=1) == False :
            _count += 1
            if _count > 3:
                self.logger.error('lock acquire: timeout')
                return False
        return True

    # ===========================================================
    # Lock解放
    # ===========================================================
    def __thread_unlock(self):
        try:
            self._lock.release()
        except Exception as e:
            self.logger.error('lock release: {}'.format(e))
            return False
        return True

    # ===========================================================
    # websocket 接続
    # ===========================================================
    def __connect(self, wsURL, symbol):
        '''Connect to the websocket in a thread.'''
        # -------------------------------------------------------
        # websocket
        # -------------------------------------------------------
        self.ws = websocket.WebSocketApp(wsURL,
                                         on_message=self.__on_message,
                                         on_close=self.__on_close,
                                         on_open=self.__on_open,
                                         on_error=self.__on_error,
                                         header=self.__get_auth())
        self.ws.keep_running = True # 実行中を保持する
        self.logger.debug("Started websocket connection")

        # -------------------------------------------------------
        # websocket スレッド
        # -------------------------------------------------------
        self.wst = threading.Thread(target=lambda: self.ws.run_forever())
        self.wst.daemon = True     # mainスレッドが終わったときにサブスレッドも終了する
        self.wst.start()
        self.logger.debug("Started websocket thread")

        # -------------------------------------------------------
        # ローソク足チェックスレッド
        # -------------------------------------------------------
        self._check_candle_thread = threading.Thread(target=self.__check_candle, args=('check_candle',))
        self._check_candle_thread.daemon = True
        self._check_candle_thread.start()
        self.logger.debug("Started check candle thread")

        # -------------------------------------------------------
        # Wait for connect before continuing
        # -------------------------------------------------------
        conn_timeout = 5
        while not self.ws.sock or not self.ws.sock.connected and conn_timeout:
            time.sleep(1)
            conn_timeout -= 1
        if not conn_timeout:
            self.logger.error("Couldn't connect to WS! Exiting.")
            self.exit()
            raise websocket.WebSocketTimeoutException('Couldn\'t connect to WS! Exiting.')

        # -------------------------------------------------------
        # コネクション確立
        # -------------------------------------------------------
        self.logger.info("Started websocket & threads")

    # ===========================================================
    # nonce作成
    # ===========================================================
    def __generate_nonce(self):
        return int(round(time.time() * 3600))

    # ===========================================================
    # Generates an API signature.
    # A signature is HMAC_SHA256(secret, verb + path + nonce + data), hex encoded.
    # Verb must be uppercased, url is relative, nonce must be an increasing 64-bit integer
    # and the data, if present, must be JSON without whitespace between keys.
    #
    # For example, in psuedocode (and in real code below):
    #
    # verb=POST
    # url=/api/v1/order
    # nonce=1416993995705
    # data={"symbol":"XBTZ14","quantity":1,"price":395.01}
    # signature = HEX(HMAC_SHA256(secret, 'POST/api/v1/order1416993995705{"symbol":"XBTZ14","quantity":1,"price":395.01}'))
    # ===========================================================
    def __generate_signature(self, secret, verb, url, nonce, data):
        """Generate a request signature compatible with BitMEX."""
        # Parse the url so we can remove the base and extract just the path.
        parsedURL = urllib.parse.urlparse(url)
        path = parsedURL.path
        if parsedURL.query:
            path = path + '?' + parsedURL.query

        # print "Computing HMAC: %s" % verb + path + str(nonce) + data
        message = (verb + path + str(nonce) + data).encode('utf-8')

        signature = hmac.new(secret.encode('utf-8'), message, digestmod=hashlib.sha256).hexdigest()
        return signature

    # ===========================================================
    # 認証
    # ===========================================================
    def __get_auth(self):
        '''Return auth headers. Will use API time.time() if present in settings.'''
        if self.api_key:
            self.logger.info("Authenticating with API Key.")
            # To auth to the WS using an API key, we generate a signature of a nonce and
            # the WS API endpoint.
            expires = self.__generate_nonce()
            return [
                'api-expires: ' + str(expires),
                "api-signature: " + self.__generate_signature(self.api_secret, 'GET', '/realtime', expires, ''),
                "api-key:" + self.api_key
            ]
        else:
            self.logger.info("Not authenticating.")
            return []

    # ===========================================================
    # 接続URL取得
    # ===========================================================
    def __get_url(self):
        '''
        Generate a connection URL. We can define subscriptions right in the querystring.
        Most subscription topics are scoped by the symbol we're listening to.
        '''

        # You can sub to orderBookL2 for all levels, or orderBook10 for top 10 levels & save bandwidth
        """
        取得するtable
            execution
            order
            position
            quote
            trade
            margin
            instrument
            orderBookL2
        """
        symbolSubs = ["execution", "instrument", "order", "orderBookL2", "position", "quote", "trade"]
        genericSubs = ["margin"]

        subscriptions = [sub + ':' + self.symbol for sub in symbolSubs]
        subscriptions += genericSubs

        urlParts = list(urllib.parse.urlparse(self.endpoint))
        urlParts[0] = urlParts[0].replace('http', 'ws')
        urlParts[2] = "/realtime?subscribe={}".format(','.join(subscriptions))
        return urllib.parse.urlunparse(urlParts)

    # ===========================================================
    # アカウント待ち
    # ===========================================================
    def __wait_for_account(self):
        '''On subscribe, this data will come down. Wait for it.'''
        # Wait for the time.time() to show up from the ws
        while not {'margin', 'position', 'order', 'execution'} <= set(self.data):
            time.sleep(0.1)

    # ===========================================================
    # シンボル待ち
    # ===========================================================
    def __wait_for_symbol(self, symbol):
        '''On subscribe, this data will come down. Wait for it.'''
        # order, orderBookL2はself.dataを使わなくすると、待ち処理でロックしてしまうので、とりあえずこのまま置いておく。
        while not {'instrument', 'trade', 'quote', 'orderBookL2'} <= set(self.data):
            time.sleep(0.1)

    # ===========================================================
    # コマンド送信（現在未使用）
    # ===========================================================
    def __send_command(self, command, args=None):
        '''Send a raw command.'''
        if args is None:
            args = []
        self.ws.send(json.dumps({"op": command, "args": args}))

    # ===========================================================
    # メッセージ受信部
    # ===========================================================
    def __on_message(self, ws, message):
        '''Handler for parsing WS messages.'''
        message = json.loads(message)
        self.logger.debug(json.dumps(message))

        table = message['table'] if 'table' in message else None
        action = message['action'] if 'action' in message else None
        try:
            # ---------------------------------------------------
            # subscribe
            # ---------------------------------------------------
            if 'subscribe' in message:
                self.logger.debug("Subscribed to %s." % message['subscribe'])
            # ---------------------------------------------------
            # action
            # ---------------------------------------------------
            elif action:

                """
                - この３つはただ追記するのみなので配列 [] で追記
                  - quote　		Partial		Insert								ただ追記するのみ
                  - trade		Partial		Insert								ただ追記するのみ
                  - execution	Partial		Insert								ただ追記するのみ

                - この３つは辞書型 {} で登録・更新
                  - margin　	Partial					Update					一つのデータを更新しつづける→辞書型のUpdateが使える？
                  - position　	Partial					Update					一つのデータを更新しつづける→辞書型のUpdateが使える？
                  - instrument　Partial					Update					一つのデータを更新しつづける→辞書型のUpdateが使える？

                - この２つはDB化が必要
                  - order  		Partial		Insert		Update 					Data部の形が変わる。数が増減する
                  - orderBookL2	Partial		Insert		Update		Delete 		Data部の形が変わる。数が増減する
                """

                # Lock
                self.__thread_lock()

                if table not in self.data:
                    if table in ['orderBookL2']:
                        # DB に 登録(partial)・挿入(insert)・更新(update)・削除(delete)
                        self.data[table] = {}
                    elif table in ['order']:
                        # DB に 登録(partial)・挿入(insert)・更新(update)
                        self.data[table] = {}
                    elif table in ['instrument', 'margin', 'position']:
                        # 辞書型 {} で登録(partial)・更新(update)
                        self.data[table] = {}
                    elif table in ['execution', 'trade', 'quote']:
                        # 配列 [] で登録(partial)・挿入(insert)
                        self.data[table] = []

                # unLock
                self.__thread_unlock()

                # There are four possible actions from the WS:
                # 'partial' - full table image
                # 'insert'  - new row
                # 'update'  - update row
                # 'delete'  - delete row

                # -----------------------------------------------
                # partial
                # -----------------------------------------------
                if action == 'partial':

                    self.logger.debug("%s: partial" % table)

                    #処理時間計測開始
                    start = time.time()

                    # Lock
                    self.__thread_lock()

                    try:
                        # partial
                        if table in ['orderBookL2']:
                            # DB に 登録(partial)・挿入(insert)・更新(update)・削除(delete)
                            # orderbook取得
                            self._orderbook.replace(message['data'])
                        elif table in ['order']:
                            # DB に 登録(partial)・挿入(insert)・更新(update)
                            # order取得
                            orders = [o for o in message['data'] if o['leavesQty'] > 0]
                            self._order.replace(orders)
                        elif table in ['instrument', 'margin', 'position']:
                            # 辞書型 {} で登録(partial)・更新(update)
                            self.data[table].update(message['data'][0])
                        elif table in ['execution', 'trade', 'quote']:
                            # 配列 [] で登録(partial)・挿入(insert)
                            self.data[table] = message['data']
                            #----------------------------------------
                            # candle
                            #----------------------------------------
                            if table == 'trade':
                                self.__init_candle_data(self.data[table])
                    except Exception as e:
                        self.logger.error('Exception {} partial {}'.format(table, e))

                    # unLock
                    self.__thread_unlock()

                    # 処理時間計測終了・登録
                    end = time.time()
                    if self._use_timemark:
                        self.timemark['partial'] += (end - start)
                        self.timemark['count'] += 1
                        self.timemark[table]['partial'] += (end - start)
                        self.timemark[table]['count'] += 1
                    
                # -----------------------------------------------
                # insert
                # -----------------------------------------------
                elif action == 'insert':

                    self.logger.debug('%s: inserting %s' % (table, message['data']))

                    #処理時間計測開始
                    start = time.time()

                    # Lock
                    self.__thread_lock()

                    try:
                        # insert
                        if table in ['orderBookL2']:
                            # DB に 登録(partial)・挿入(insert)・更新(update)・削除(delete)
                            # orderbook取得
                            self._orderbook.replace(message['data'])
                        elif table in ['order']:
                            # DB に 登録(partial)・挿入(insert)・更新(update)
                            # order取得
                            orders = [o for o in message['data'] if o['leavesQty'] > 0]
                            self._order.replace(orders)
                        elif table in ['execution', 'trade', 'quote']:
                            # 配列 [] で登録(partial)・挿入(insert)
                            self.data[table] += message['data']
                            if len(self.data[table]) > (BitMEXWebsocket.MAX_TABLE_LEN * 1.5):
                                self.data[table] = self.data[table][-BitMEXWebsocket.MAX_TABLE_LEN:]
                            #----------------------------------------
                            # candle
                            #----------------------------------------
                            if table == 'trade':
                                for trade in message['data']:
                                    self.__update_candle_data(trade)
                        elif table in ['instrument', 'margin', 'position']:
                            # dataは来ないはず
                            self.logger.error('insert event occured table: {}'.format(table))
                    except Exception as e:
                        self.logger.error('Exception {} insert {}'.format(table, e))

                    # unLock
                    self.__thread_unlock()

                    # 処理時間計測終了・登録
                    end = time.time()
                    if self._use_timemark:
                        self.timemark['insert'] += (end - start)
                        self.timemark['count'] += 1
                        self.timemark[table]['insert'] += (end - start)
                        self.timemark[table]['count'] += 1

                # -----------------------------------------------
                # update
                # -----------------------------------------------
                elif action == 'update':

                    self.logger.debug('%s: updating %s' % (table, message['data']))

                    #処理時間計測開始
                    start = time.time()

                    # Lock
                    self.__thread_lock()

                    try:
                        # update
                        if table in ['orderBookL2']:
                            # DB に 登録(partial)・挿入(insert)・更新(update)・削除(delete)
                            # orderbook取得
                            self._orderbook.update(message['data'])
                        elif table in ['order']:
                            # DB に 登録(partial)・挿入(insert)・更新(update)
                            # order取得
                            update_order = []
                            delete_order = []
                            for order in message['data']:
                                if 'leavesQty' in order:    # leavesQtyを持っているデータ
                                    if order['leavesQty'] <= 0:
                                        # 削除対象
                                        delete_order.append(order)
                                    else:
                                        update_order.append(order)
                                else:
                                    update_order.append(order)
                            # orderを更新
                            for o in update_order:
                                # order情報をUpdate
                                order = self._order.select(o['orderID'])
                                if len(order) != 0:
                                    # orderはdeleteが通知されないかわりに update で leavesQty = 0 の通知をもって delete としているが、
                                    # ごく稀に leavesQty = 0 の通知の後、update が再び通知されることがあるが、
                                    # その後すぐに leavesQty = 0 が再度通知されるので問題ない。DBに存在しない update は無視することとする。
                                    order[0].update(o)
                                    self._order.replace(order)
                                else:
                                    # for DEBUG                                
                                    self.logger.debug('{}, {}, {}, {}'.format(table, action, o['orderID'], 'already deleted'))
                            # キャンセルや約定済みorderを削除
                            if len(delete_order) != 0:
                                self._order.delete(delete_order)
                        elif table in ['instrument', 'margin', 'position']:
                            # 辞書型 {} で登録(partial)・更新(update)
                            self.data[table].update(message['data'][0])
                        elif table in ['execution', 'trade', 'quote']:
                            # dataは来ないはず
                            self.logger.error('update event occured table: {}'.format(table))
                    except Exception as e:
                        self.logger.error('Exception {} update {}'.format(table, e))

                    # unLock
                    self.__thread_unlock()

                    # 処理時間計測終了・登録
                    end = time.time()
                    if self._use_timemark:
                        self.timemark['update'] += (end - start)
                        self.timemark['count'] += 1
                        self.timemark[table]['update'] += (end - start)
                        self.timemark[table]['count'] += 1

                # -----------------------------------------------
                # delete
                # -----------------------------------------------
                elif action == 'delete':

                    self.logger.debug('%s: deleting %s' % (table, message['data']))

                    #処理時間計測開始
                    start = time.time()

                    # Lock
                    self.__thread_lock()

                    try:
                        # delete
                        if table in ['orderBookL2']:
                            # DB に 登録(partial)・挿入(insert)・更新(update)・削除(delete)
                            # orderbook取得
                            self._orderbook.delete(message['data'])
                        elif table in ['execution', 'instrument', 'trade', 'quote', 'margin', 'position', 'order']:
                            # dataは来ないはず
                            self.logger.error('delete event occured table: {}'.format(table))
                    except Exception as e:
                        self.logger.error('Exception {} delete {}'.format(table, e))

                    # unLock
                    self.__thread_unlock()

                    # 処理時間計測終了・登録
                    end = time.time()
                    if self._use_timemark:
                        self.timemark['delete'] += (end - start)
                        self.timemark['count'] += 1
                        self.timemark[table]['delete'] += (end - start)
                        self.timemark[table]['count'] += 1
                    
                # -----------------------------------------------
                # Unknown action は無視する
                # -----------------------------------------------
                else:
                    #raise Exception("Unknown action: %s" % action)
                    self.logger.error('Unknown action {}'.format(action))
        except:
            self.logger.error(traceback.format_exc())

    # ===========================================================
    # エラー受信部
    # ===========================================================
    def __on_error(self, ws, error):
        '''Called on fatal websocket errors. We exit on these.'''
        if not self.exited:
            self.logger.error("__on_error() Error : %s" % error)
            # エラーが発生したらソケットをクロースずる
            self.exit()
            # 例外をスロー
            raise websocket.WebSocketException(error)

    # ===========================================================
    # オープン受信部
    # ===========================================================
    def __on_open(self, ws):
        '''Called when the WS opens.'''
        self.logger.debug("Websocket Opened.")

    # ===========================================================
    # クローズ受信部
    # ===========================================================
    def __on_close(self, ws):
        '''Called on websocket close.'''
        self.logger.info('Websocket Closed')

    # ===========================================================
    # ローソク足の収集開始
    # ===========================================================
    def __init_candle_data(self, trades):
        # ローソク足の最初のタイムスタンプを作成
        ts = round(dateutil.parser.parse(trades[0]['timestamp']).timestamp())
        mark_ts = ts - ts % BitMEXWebsocket.CANDLE_RANGE
        self.logger.debug('ローソク足開始時刻 {}'.format(mark_ts))

        # 最初のデータ
        self._candle.append({
            'timestamp': mark_ts,
            'open': trades[0]['price'],
            'high': trades[0]['price'],
            'low': trades[0]['price'],
            'close': trades[0]['price'],
            'volume': trades[0]['size'],
            'buy': trades[0]['size'] if trades[0]['side'] == 'Buy' else 0,
            'sell': trades[0]['size'] if trades[0]['side'] == 'Sell' else 0
        })

        if len(trades) > 1:
            # data部が複数
            for trade in trades[1:]:
                self.__update_candle_data(trade)

    # ===========================================================
    # ローソク足のデータを更新する
    # ===========================================================
    def __update_candle_data(self, trade):
        ts = round(dateutil.parser.parse(trade['timestamp']).timestamp())
        # 最後のcandle足
        last_candle = self._candle[-1]
        mark_ts = last_candle['timestamp']
        """
        # for DEBUG
        print('■ mark_ts {} ,ts {}, diff {} :判定 {}, {}'.format(
                mark_ts, 
                ts, 
                ts - mark_ts,
                (mark_ts < ts <= (mark_ts + BitMEXWebsocket.CANDLE_RANGE)),
                ((mark_ts + BitMEXWebsocket.CANDLE_RANGE) < ts)
            ))
        """
        # 開始日時からRANGE内に収まっていたら、既存のcandleを更新する
        if mark_ts < ts <= (mark_ts + BitMEXWebsocket.CANDLE_RANGE):
            # timestamp, openは更新しない
            last_candle['high'] = max(last_candle['high'], trade['price'])
            last_candle['low'] = min(last_candle['low'], trade['price'])
            last_candle['close'] = trade['price']
            last_candle['volume'] += trade['size']
            last_candle['buy'] += trade['size'] if trade['side'] == 'Buy' else 0
            last_candle['sell'] += trade['size'] if trade['side'] == 'Sell' else 0
        # 次の時間帯になっていたら、新しいcandleを作る
        elif (mark_ts + BitMEXWebsocket.CANDLE_RANGE) < ts:
            # mark_tsを更新
            mark_ts = mark_ts + BitMEXWebsocket.CANDLE_RANGE
            # 新しいcandleを作成
            self._candle.append({
                'timestamp': mark_ts,
                'open': last_candle['close'],  # 一つ前のcloseデータを今回のopenに設定
                'high': trade['price'],
                'low': trade['price'],
                'close': trade['price'],
                'volume': trade['size'],
                'buy': trade['size'] if trade['side'] == 'Buy' else 0,
                'sell': trade['size'] if trade['side'] == 'Sell' else 0
            })

    # ===========================================================
    # ローソク足の不足分データが無いかどうかをチェックする
    # ===========================================================
    def __check_candle(self, args):
        # エリア設定待ち
        while 'trade' not in self.data:
            time.sleep(1)
        # データの格納待ち
        while len(self.trades()) == 0:
            time.sleep(1)

        UTC = timezone(timedelta(hours=0), name='UTC')

        # メイン処理が生存している間だけ処理する
        while not self.exited:
            # candle生成時間の半分だけ待つ
            time.sleep(BitMEXWebsocket.CANDLE_RANGE / 2)

            # websocketが接続中でなかった場合は待ち
            if not self.ws or not self.ws.sock or not self.ws.sock.connected:
                continue

            # Lock
            self.__thread_lock()

            try:
                # 現在時刻(UTC)のtimestamp
                ts = round(datetime.now(UTC).timestamp())
                # 最後のcandle足
                last_candle = self._candle[-1]
                mark_ts = last_candle['timestamp']
                """
                # for DEBUG
                print('● mark_ts {} ,ts {}, diff {} :判定 {}, {}'.format(
                        mark_ts, 
                        ts, 
                        ts - mark_ts,
                        (mark_ts < ts <= (mark_ts + BitMEXWebsocket.CANDLE_RANGE)),
                        ((mark_ts + BitMEXWebsocket.CANDLE_RANGE) < ts)
                    ))
                """
                # 次の時間帯になっていたら、新しいcandle(空)を作る
                if (mark_ts + BitMEXWebsocket.CANDLE_RANGE) < ts:
                    # mark_tsを更新
                    mark_ts = mark_ts + BitMEXWebsocket.CANDLE_RANGE
                    # 新しいcandleを作成
                    self._candle.append({
                        'timestamp': mark_ts,
                        'open': last_candle['close'],
                        'high': last_candle['close'],
                        'low': last_candle['close'],
                        'close': last_candle['close'],
                        'volume': 0,
                        'buy': 0,
                        'sell': 0
                    })

                # 最大サイズ調整
                if len(self._candle) > (BitMEXWebsocket.MAX_CANDLE_LEN * 1.5):
                    self._candle = self._candle[-BitMEXWebsocket.MAX_CANDLE_LEN:]
            except Exception as e:
                self.logger.error('check candle thread Exception {}'.format(e))
            finally:
                pass

            # unLock
            self.__thread_unlock()

# ###############################################################
# テスト
# ###############################################################
if __name__ == '__main__':

    #-------------------------------------------
    # テストクラス
    #-------------------------------------------
    class Test:

        USE_TESTNET = True
        SYMBOL = 'XBTUSD'
        APIKEY = ''
        SECRET = ''

        def __init__(self, logger):
            # loggerオブジェクトの宣言
            self.logger = logger
            # loggerのログレベル設定(ハンドラに渡すエラーメッセージのレベル)
            self.logger.setLevel(logging.INFO)              # ※ここはConfigで設定可能にする
            # Formatterの生成
            formatter = Formatter(
                    fmt='%(asctime)s, %(levelname)-8s, %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
            # console handlerの生成・追加
            stream_handler = StreamHandler()
            stream_handler.setFormatter(formatter)
            self.logger.addHandler(stream_handler)

            # WebSocket API接続用オブジェクトを生成
            self.ws = BitMEXWebsocket(
                    endpoint='wss://www.bitmex.com/realtime' if Test.USE_TESTNET is False else 'wss://testnet.bitmex.com/realtime', 
                    symbol=Test.SYMBOL, 
                    api_key=Test.APIKEY, 
                    api_secret=Test.SECRET,
                    logger=self.logger,
                    use_timemark=False
                )
            # instrumentメソッドを一度呼び出さないとエラーを吐くので追加(内部的にget_tickerがこの情報を使用するため)
            #self.ws.instrument()

            # 例外発生のカウント
            self.count = 0

        def run(self):
            # websocket start
            while self.ws.ws.sock.connected:
                pass
                """
                # for DEBUG
                book = self.ws.orderbook()
                self.logger.info('orderbook bids[0] {}'.format(book['bids'][0]))
                time.sleep(0.1)
                # ダミーの例外を発生させる
                self.count += 1
                if self.count > 3:
                    raise Exception('Unknown')
                """

        def reconnect(self):
            self.count = 0
            self.ws.reconnect()

        def exit(self):
            self.ws.exit()
            del self.ws

    #-------------------------------------------
    #  空クラス
    #-------------------------------------------
    class T:
        def __init__(self):
            print('init')

        def __del__(self):
            print('del')

        def run(self):
            print('run')
            # for DEBUG
            #raise Exception('exception run')

        def exit(self):
            print('exit')

    #-------------------------------------------
    # 実行
    #-------------------------------------------
    logger = getLogger("test")
    t = Test(logger=logger)
    while True:
        try:
            print('- inmemorydb_bitmex_websocket debug start -')
            t.run()
        except Exception as e:
            print('loop {}, object {}, socket {}'.format(e, t, t.ws))
            t.reconnect()
        finally:
            time.sleep(5)

