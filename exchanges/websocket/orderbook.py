# 参考
#  https://www.htmllifehack.xyz/entry/2018/08/03/231351

from datetime import datetime
from sqlite3 import Connection
# for logging
import logging

# ###############################################################
# 板情報クラス
# ###############################################################
class OrderBook:

    """
    // id   : ID（IDエントリは、価格とシンボルを組み合わせたものであり、所定の価格レベルで常に固有の値となります。 
    //            更新 や 削除 のアクションを適用するために使用されます。[bitmex公式より]）
    // price: 価格 実数（0.5刻み）
    // size : サイズ -> ここ整数
    // side : 方向(Buy or Sell) -> TEXT
    // symbol: XBTUSD -> TEXT
    // tm   : 時間(UTC) -> Timestamp型
    """
    __COLUMN_SETS = 'id INTEGER primary key, '\
                    'price REAL NOT NULL, '\
                    'size INTEGER NOT NULL, '\
                    'side TEXT NOT NULL, '\
                    'symbol TEXT NOT NULL, '\
                    'tm TIMESTAMP'

    __TABLE_NAME = 'ORDERBOOK_TBL'    # 板情報

    #==================================
    # 初期化
    #==================================
    def __init__(self, Connection, logger=None):

        self.logger = logger if logger is not None else logging.getLogger(__name__)

        self._con = Connection  # DB connection

        c = self._con.cursor()
        self.beginTrans(c)
        try:
            c.execute('CREATE TABLE IF NOT EXISTS ' + OrderBook.__TABLE_NAME + ' ( ' + OrderBook.__COLUMN_SETS + ' ) ')
        except Exception as e:
            self.logger.error(e)
            self.rollback(c)
        else:
            self.commit(c)
        finally:
            c.close()

    #==================================
    # REPLACE
    #  データが有ればUpdate, なければInsertする。
    #   params: json list [{'symbol': 'XBTUSD', 'id': 15500000100, 'side': 'Sell', 'size': 100001, 'price': 999999}, {...},,,,]
    #==================================
    def replace(self, data):
        c = self._con.cursor()
        self.beginTrans(c)
        try:
            list = []
            for row in data:
                list.append(tuple([
                        row['id'],
                        row['price'],
                        row['size'],
                        row['side'],
                        row['symbol'],
                        int(datetime.utcnow().timestamp())
                    ]))
            #                                                   params: list [(id, price, size, side, symbol, tm), (...)]
            c.executemany('REPLACE INTO ' + OrderBook.__TABLE_NAME + ' VALUES (?,?,?,?,?,?)', list)
        except Exception as e:
            self.logger.error(e)
            self.rollback(c)
        else:
            self.commit(c)
        finally:
            c.close()

    #==================================
    # UPDATE
    #   params: json list [{'symbol': 'XBTUSD', 'id': 15500000100, 'side': 'Sell', 'size': 100001}, {...},,,,]
    #==================================
    def update(self, data):
        c = self._con.cursor()
        self.beginTrans(c)
        try:
            list = []
            for row in data:
                list.append(tuple([
                        row['size'],
                        row['side'],
                        int( datetime.utcnow().timestamp()),
                        row['id']
                    ]))
            #                                                   params: list [(size, side, tm, id), (...)]
            c.executemany('UPDATE ' + OrderBook.__TABLE_NAME + ' SET size = ?, side = ?, tm = ? WHERE id = ?', list)
        except Exception as e:
            self.logger.error(e)
            self.rollback(c)
        else:
            self.commit(c)
        finally:
            c.close()

    #==================================
    # DELETE
    #   params: json list [{'symbol': 'XBTUSD', 'id': 15599452050, 'side': 'Buy'}, {},,,,]
    #==================================
    def delete(self, data):
        c = self._con.cursor()
        self.beginTrans(c)
        try:
            list = []
            for row in data:
                list.append(tuple([
                        0,
                        row['side'],
                        int( datetime.utcnow().timestamp()),
                        row['id']
                    ]))
            #                                                   params: list [(0, side, tm, id), (...)]
            c.executemany('UPDATE ' + OrderBook.__TABLE_NAME + ' SET size = ?, side = ?, tm = ? WHERE id = ?', list)
        except Exception as e:
            self.logger.error(e)
            self.rollback(c)
        else:
            self.commit(c)
        finally:
            c.close()

    #==================================
    # SELECT
    #   param:
    #       side: Buy/Sellの方向 (TEXT)
    #       num: 取得個数 (INTEGER)
    #       direction: 降順(DESC)／昇順(ASC) (TEXT)
    #   return:
    #       json list [{'symbol': 'XBTUSD', 'id': 15500000100, 'side': 'Sell', 'size': 100001, 'price': 999999}, {...},,,,]
    #==================================
    def select(self, side='Buy', num=5, direction='ASC'):
        data = []
        c = self._con.cursor()
        self.beginTrans(c)
        try:
            #                  0,     1,    2,    3,      4,  5
            c.execute('SELECT id, price, size, side, symbol, tm FROM ' + OrderBook.__TABLE_NAME + ' WHERE ( side == "' + side + '" AND size != 0 ) ORDER BY id ' + direction + ' LIMIT ' + str(num) )
            list = c.fetchall()
            for row in list:
                data.append({
                    'symbol': row[4], 
                    'id': row[0], 
                    'side': row[3], 
                    'size': row[2], 
                    'price': row[1]
                })
        except Exception as e:
            self.logger.error(e)
            self.rollback(c)
        else:
            self.commit(c)
        finally:
            c.close()
        return data

    #==================================
    # CLEAR
    #   テーブルのデータでsizeを一括で0に設定し、現在時刻でUpdateする
    #==================================
    def clear(self):
        c = self._con.cursor()
        self.beginTrans(c)
        try:
            c.execute('UPDATE ' + OrderBook.__TABLE_NAME + ' SET size = ? , tm = ?', (0, int(datetime.utcnow().timestamp())))
        except Exception as e:
            self.logger.error(e)
            self.rollback(c)
        else:
            self.commit(c)
        finally:
            c.close()

    #==================================
    # トランザクション開始
    #==================================
    def beginTrans(self, corsor):
        corsor.execute('BEGIN')

    #==================================
    # トランザクション終了(COMMIT)
    #==================================
    def commit(self, corsor):
        corsor.execute("COMMIT")

    #==================================
    # トランザクション終了(ROLLLBACK)
    #==================================
    def rollback(self, corsor):
        corsor.execute("ROLLBACK")

    #==================================
    # 板情報
    #==================================
    def get_orderbook(self, length):
        bids = self.select(side='Buy', num=length, direction='ASC')
        asks = self.select(side='Sell', num=length, direction='DESC')
        return {'bids' : bids, 'asks' : asks}
