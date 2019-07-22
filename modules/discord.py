# -*- coding: utf-8 -*-
# ==========================================
# Discord
# ==========================================
import requests


# ==========================================
# Discord クラス
#   param:
#       URL: discord webhook url
# ==========================================
class Discord:

    # ======================================
    # 初期化
    #   param:
    #       URL: discord webhook url
    # ======================================
    def __init__(self, discord_webhook_url=""):
        # ----------------------------------
        # discord webhook url設定
        # ----------------------------------
        self._discord_webhook_url = discord_webhook_url  # discord通知用URL

    # ======================================
    # 通知
    #   param:
    #       message: 通知メッセージ
    #       fileName: 画像ファイル
    # ======================================
    def send(self, message, fileName=None):
        if "" != self._discord_webhook_url:
            data = {"content": " " + message + " "}
            if fileName == None:
                r = requests.post(self._discord_webhook_url, data=data)
            else:
                try:
                    file = {"imageFile": open(fileName, "rb")}
                    r = requests.post(self._discord_webhook_url, data=data, files=file)
                except:
                    r = requests.post(self._discord_webhook_url, data=data)
            if r.status_code == 404:
                raise RuntimeError("指定URL[{}]は存在しません".format(self._discord_webhook_url))


"""
例：
message += 'BTC\r'
message += '10 BTC'

send(message)

"""
