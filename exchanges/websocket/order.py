# 参考
#  https://www.htmllifehack.xyz/entry/2018/08/03/231351

from datetime import datetime
from sqlite3 import Connection
import json
# for logging
import logging

# ###############################################################
# 注文クラス
# ###############################################################
class Order:

    """
    // orderID  : 注文ID　TEXT primary key
    // obj      : 注文オブジェクト（中身はJSON） TEXT
    // tm       : 時間(UTC) -> Timestamp型
    """
    __COLUMN_SETS = 'orderID TEXT primary key, '\
                    'obj TEXT NOT NULL, '\
                    'tm TIMESTAMP'

    __TABLE_NAME = 'ORDER_TBL'      # 注文情報

    #==================================
    # 初期化
    #==================================
    def __init__(self, Connection, logger=None):

        self.logger = logger if logger is not None else logging.getLogger(__name__)

        self._con = Connection  # DB connection

        c = self._con.cursor()
        self.beginTrans(c)
        try:
            c.execute('CREATE TABLE IF NOT EXISTS ' + Order.__TABLE_NAME + ' ( ' + Order.__COLUMN_SETS + ' ) ')
        except Exception as e:
            self.logger.error(e)
            self.rollback(c)
        else:
            self.commit(c)
        finally:
            c.close()
            
        self.logger.info('class Order initialized')

    # ===========================================================
    # デストラクタ
    # ===========================================================
    def __del__(self):
        self.logger.info('class Order deleted')

    #==================================
    # REPLACE
    #  データが有ればUpdate, なければInsertする。
    #   params: order list [{'orderID': '447904dc-34b5-e390-8ef9-379924024a19',,,,注文情報,,,,}, {...},,,,]
    #==================================
    def replace(self, data):
        c = self._con.cursor()
        self.beginTrans(c)
        try:
            list = []
            for row in data:
                list.append(tuple([
                        row['orderID'],
                        json.dumps(row),    # 一度TEXTに変換して入れる。sqlite3はver3.9以降でJSONデータをカラムに持てるが、AWS Cloud9のsqlite3はver3.7
                        int(datetime.utcnow().timestamp())
                    ]))
            #                                                   params: list [(orderID, obj, tm), (...)]
            c.executemany('REPLACE INTO ' + Order.__TABLE_NAME + ' VALUES (?,?,?)', list)
        except Exception as e:
            self.logger.error(e)
            self.rollback(c)
        else:
            self.commit(c)
        finally:
            c.close()

    #==================================
    # DELETE
    #   params: order list [{'orderID': '447904dc-34b5-e390-8ef9-379924024a19',,,,注文情報,,,,}, {...},,,,]
    #==================================
    def delete(self, data):
        c = self._con.cursor()
        self.beginTrans(c)
        try:
            list = []
            for row in data:
                list.append(tuple([
                        row['orderID']
                    ]))
            #                                                   params: list [(orderID), (...)]
            c.executemany('DELETE FROM ' + Order.__TABLE_NAME + ' WHERE orderID = ?', list)
        except Exception as e:
            self.logger.error(e)
            self.rollback(c)
        else:
            self.commit(c)
        finally:
            c.close()

    #==================================
    # SELECT
    #   params: 
    #       orderID
    #   return:
    #       json list [{'orderID': '447904dc-34b5-e390-8ef9-379924024a19',,,,注文情報,,,,}, {...},,,,]
    #==================================
    def select(self, orderID):
        data = []
        c = self._con.cursor()
        self.beginTrans(c)
        try:
            #                  0,     1,    2
            c.execute('SELECT orderID, obj, tm FROM ' + Order.__TABLE_NAME + ' WHERE orderID = ?', (orderID,) )
            list = c.fetchall()
            for row in list:
                data.append(
                        json.loads(row[1])  # TEXTをJSONに変換
                    )
        except Exception as e:
            self.logger.error(e)
            self.rollback(c)
        else:
            self.commit(c)
        finally:
            c.close()
        return data

    #==================================
    # SELECTALL
    #   return:
    #       json list [{'orderID': '447904dc-34b5-e390-8ef9-379924024a19', 'obj' : {注文情報}}, {...},,,,]
    #==================================
    def selectAll(self):
        data = []
        c = self._con.cursor()
        self.beginTrans(c)
        try:
            #                  0,     1,    2
            c.execute('SELECT orderID, obj, tm FROM ' + Order.__TABLE_NAME)
            list = c.fetchall()
            for row in list:
                data.append(
                        json.loads(row[1])  # TEXTをJSONに変換
                    )
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
    #   テーブルのデータを一括削除する
    #==================================
    def clear(self):
        c = self._con.cursor()
        self.beginTrans(c)
        try:
            c.execute('DELETE FROM ' + Order.__TABLE_NAME)
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
    # 注文情報
    #==================================
    def get_orders(self):
        orders = self.selectAll()
        return orders
