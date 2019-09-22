### v1.0.0

- 初版

### v1.0.1

- websocket, bitmexラッパー対応

- websocketサンプル
```
- puppets/
  - sample1/
    - sample1.py
    - sample1.json
```
### v1.0.2

- 5秒ローソク足追加

### v1.0.3

- websocket再接続処理修正

### v1.0.4

- 資産状況通知対応

### v1.0.5

- websocket再接続処理を整理

### v1.0.6

- cancel_order, amend_orderで不正なIDを使用した場合にException。
- orderbook破壊でException。

### v1.0.7

- [Ta-Libのインストール](./docs/04_indicator.md)を追加

### v1.0.8

- ohlcv収集のpartial指定が機能していなかった件を修正
- マルチタイムフレーム対応

### v1.0.9

- doten(ドテン君)のサンプル実装を追加

### v1.0.10

- stop注文メソッドを追加

### v1.0.11

- to_candleDF, change_candleDFメソッドを   
   exchange.ccxt.BitMEX   
   exchange.websocket.BitMEXWebsocket   
   に追加。

### v1.0.12

- positionが長期間存在しない場合にwebsocketのposition:partialが空配列で戻される件を対応
