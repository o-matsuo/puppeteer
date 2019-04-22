### 参考

- candle取得時のpartialフラグが機能シない件を修正   
参考にした[サイト](https://note.mu/nagi7692/n/n5a52e0fa8c28)

- ログをファイルにも出力   
参考にした[サイト](https://codeday.me/jp/qa/20181223/28667.html)

- ロギング機能を追加。（まだコンソール出力のみ）   
参考にした[サイト](https://qiita.com/mimitaro/items/9fa7e054d60290d13bfc)
### private_get_position()

- 戻り値
```
[{
    'account': 188487, 
    'symbol': 'XBTUSD', 
    'currency': 'XBt', 
    'underlying': 'XBT', 
    'quoteCurrency': 'USD', 
    'commission': 0.00075, 
    'initMarginReq': 0.01, 
    'maintMarginReq': 0.005, 
    'riskLimit': 20000000000, 
    'leverage': 100, 
    'crossMargin': True, 
    'deleveragePercentile': 1, 
    'rebalancedPnl': -2607484, 
    'prevRealisedPnl': 9986, 
    'prevUnrealisedPnl': 0, 
    'prevClosePrice': 5101, 
    'openingTimestamp': '2019-04-07T08:00:00.000Z', 
    'openingQty': -693, 
    'openingCost': 11440187, 
    'openingComm': -685612, 
    'openOrderBuyQty': 0, 
    'openOrderBuyCost': 0, 
    'openOrderBuyPremium': 0, 
    'openOrderSellQty': 0, 
    'openOrderSellCost': 0, 
    'openOrderSellPremium': 0, 
    'execBuyQty': 0, 
    'execBuyCost': 0, 
    'execSellQty': 0, 
    'execSellCost': 0, 
    'execQty': 0, 
    'execCost': 0, 
    'execComm': 0, 
    'currentTimestamp': '2019-04-07T08:00:00.313Z', 
    'currentQty': -693, 
    'currentCost': 11440187, 
    'currentComm': -685612, 
    'realisedCost': -1925209, 
    'unrealisedCost': 13365396, 
    'grossOpenCost': 0, 
    'grossOpenPremium': 0, 
    'grossExecCost': 0, 
    'isOpen': True, 
    'markPrice': 5101, 
    'markValue': 13585572, 
    'riskValue': 13585572, 
    'homeNotional': -0.13585572, 
    'foreignNotional': 693, 
    'posState': '', 
    'posCost': 13365396, 
    'posCost2': 13365396, 
    'posCross': 0, 
    'posInit': 133654, 
    'posComm': 10125, 
    'posLoss': 0, 
    'posMargin': 143779, 
    'posMaint': 76952, 
    'posAllowance': 0, 
    'taxableMargin': 0, 
    'initMargin': 0, 
    'maintMargin': 363955, 
    'sessionMargin': 0, 
    'targetExcessMargin': 0, 
    'varMargin': 0, 
    'realisedGrossPnl': 1925209, 
    'realisedTax': 0, 
    'realisedPnl': 2610821, 
    'unrealisedGrossPnl': 220176, 
    'longBankrupt': 0, 
    'shortBankrupt': 0, 
    'taxBase': 2145385, 
    'indicativeTaxRate': 0, 
    'indicativeTax': 0, 
    'unrealisedTax': 0, 
    'unrealisedPnl': 220176, 
    'unrealisedPnlPcnt': 0.0165, 
    'unrealisedRoePcnt': 1.6474, 
    'simpleQty': None, 
    'simpleCost': None, 
    'simpleValue': None, 
    'simplePnl': None, 
    'simplePnlPcnt': None, 
    'avgCostPrice': 5184.8395, 
    'avgEntryPrice': 5184.8395, 
    'breakEvenPrice': 5186, 
    'marginCallPrice': 100000000, 
    'liquidationPrice': 100000000, 
    'bankruptPrice': 100000000, 
    'timestamp': '2019-04-07T08:00:00.313Z', 
    'lastPrice': 5101, 
    'lastValue': 13585572
}]
```

### fetch_balance()

- 戻り値
```
{
    'info': 
        [{
            'account': 188487, 
            'currency': 'XBt', 
            'riskLimit': 1000000000000, 
            'prevState': '', 
            'state': '', 
            'action': '', 
            'amount': 35665179, 
            'pendingCredit': 0, 
            'pendingDebit': 0, 
            'confirmedDebit': 0, 
            'prevRealisedPnl': 9986, 
            'prevUnrealisedPnl': 0, 
            'grossComm': -685612, 
            'grossOpenCost': 0, 
            'grossOpenPremium': 0, 
            'grossExecCost': 0, 
            'grossMarkValue': 13585572, 
            'riskValue': 13585572, 
            'taxableMargin': 0, 
            'initMargin': 0, 
            'maintMargin': 363955, 
            'sessionMargin': 0, 
            'targetExcessMargin': 0, 
            'varMargin': 0, 
            'realisedPnl': 2610821, 
            'unrealisedPnl': 220176, 
            'indicativeTax': 0, 
            'unrealisedProfit': 0, 
            'syntheticMargin': None, 
            'walletBalance': 38276000, 
            'marginBalance': 38496176, 
            'marginBalancePcnt': 1, 
            'marginLeverage': 0.35290705237839726, 
            'marginUsedPcnt': 0.0095, 
            'excessMargin': 38132221, 
            'excessMarginPcnt': 1, 
            'availableMargin': 38132221, 
            'withdrawableMargin': 38132221, 
            'timestamp': '2019-04-07T08:00:00.492Z', 
            'grossLastValue': 13585572, 
            'commission': None
        }], 
    'BTC': {
        'free': 0.38132221, 
        'used': 0.0036395499999999914, 
        'total': 0.38496176
    }, 
    'free': {
        'BTC': 0.38132221
    }, 
    'used': {
        'BTC': 0.0036395499999999914
    }, 
    'total': {
        'BTC': 0.38496176
    }
}
```

### fetch_open_orders(SYMBOL)

- 戻り値
```
[{
    'info': 
        {
            'orderID': '2e6678df-76b0-224e-f084-01aa775b7c76', 
            'clOrdID': '', 
            'clOrdLinkID': '', 
            'account': 188487, 
            'symbol': 'XBTUSD', 
            'side': 'Buy', 
            'simpleOrderQty': None, 
            'orderQty': 30, 
            'price': 5166, 
            'displayQty': None, 
            'stopPx': None, 
            'pegOffsetValue': None, 
            'pegPriceType': '', 
            'currency': 'USD', 
            'settlCurrency': 'XBt', 
            'ordType': 'Limit', 
            'timeInForce': 'GoodTillCancel', 
            'execInst': '', 
            'contingencyType': '', 
            'exDestination': 'XBME', 
            'ordStatus': 'New', 
            'triggered': '', 
            'workingIndicator': True, 
            'ordRejReason': '', 
            'simpleLeavesQty': None, 
            'leavesQty': 30, 
            'simpleCumQty': None, 
            'cumQty': 0, 
            'avgPx': None, 
            'multiLegReportingType': 'SingleSecurity', 
            'text': 'Submission from testnet.bitmex.com', 
            'transactTime': '2019-04-07T09:31:14.270Z', 
            'timestamp': '2019-04-07T09:31:14.270Z'
        }, 
    'id': '2e6678df-76b0-224e-f084-01aa775b7c76', 
    'timestamp': 1554629474270, 
    'datetime': '2019-04-07T09:31:14.270Z', 
    'lastTradeTimestamp': 1554629474270, 
    'symbol': 'BTC/USD', 
    'type': 'limit', 
    'side': 'buy', 
    'price': 5166.0, 
    'amount': 30.0, 
    'cost': 0.0, 
    'filled': 0.0, 
    'remaining': 30.0, 
    'status': 'open', 
    'fee': None
}]
```

### funding rateを取得するには、Instrument にあるデータを使う？

```
[
  {
    "symbol": "string",
    "rootSymbol": "string",
    "state": "string",
    "typ": "string",
    "listing": "2019-04-14T04:31:33.822Z",
    "front": "2019-04-14T04:31:33.822Z",
    "expiry": "2019-04-14T04:31:33.822Z",
    "settle": "2019-04-14T04:31:33.822Z",
    "relistInterval": "2019-04-14T04:31:33.822Z",
    "inverseLeg": "string",
    "sellLeg": "string",
    "buyLeg": "string",
    "optionStrikePcnt": 0,
    "optionStrikeRound": 0,
    "optionStrikePrice": 0,
    "optionMultiplier": 0,
    "positionCurrency": "string",
    "underlying": "string",
    "quoteCurrency": "string",
    "underlyingSymbol": "string",
    "reference": "string",
    "referenceSymbol": "string",
    "calcInterval": "2019-04-14T04:31:33.825Z",
    "publishInterval": "2019-04-14T04:31:33.825Z",
    "publishTime": "2019-04-14T04:31:33.825Z",
    "maxOrderQty": 0,
    "maxPrice": 0,
    "lotSize": 0,
    "tickSize": 0,
    "multiplier": 0,
    "settlCurrency": "string",
    "underlyingToPositionMultiplier": 0,
    "underlyingToSettleMultiplier": 0,
    "quoteToSettleMultiplier": 0,
    "isQuanto": true,
    "isInverse": true,
    "initMargin": 0,
    "maintMargin": 0,
    "riskLimit": 0,
    "riskStep": 0,
    "limit": 0,
    "capped": true,
    "taxed": true,
    "deleverage": true,
    "makerFee": 0,
    "takerFee": 0,
    "settlementFee": 0,
    "insuranceFee": 0,
    "fundingBaseSymbol": "string",
    "fundingQuoteSymbol": "string",
    "fundingPremiumSymbol": "string",
    "fundingTimestamp": "2019-04-14T04:31:33.826Z",
    "fundingInterval": "2019-04-14T04:31:33.826Z",
    "fundingRate": 0,                                       ###### これか？
    "indicativeFundingRate": 0,
    "rebalanceTimestamp": "2019-04-14T04:31:33.827Z",
    "rebalanceInterval": "2019-04-14T04:31:33.827Z",
    "openingTimestamp": "2019-04-14T04:31:33.827Z",
    "closingTimestamp": "2019-04-14T04:31:33.827Z",
    "sessionInterval": "2019-04-14T04:31:33.827Z",
    "prevClosePrice": 0,
    "limitDownPrice": 0,
    "limitUpPrice": 0,
    "bankruptLimitDownPrice": 0,
    "bankruptLimitUpPrice": 0,
    "prevTotalVolume": 0,
    "totalVolume": 0,
    "volume": 0,
    "volume24h": 0,
    "prevTotalTurnover": 0,
    "totalTurnover": 0,
    "turnover": 0,
    "turnover24h": 0,
    "homeNotional24h": 0,
    "foreignNotional24h": 0,
    "prevPrice24h": 0,
    "vwap": 0,
    "highPrice": 0,
    "lowPrice": 0,
    "lastPrice": 0,
    "lastPriceProtected": 0,
    "lastTickDirection": "string",
    "lastChangePcnt": 0,
    "bidPrice": 0,
    "midPrice": 0,
    "askPrice": 0,
    "impactBidPrice": 0,
    "impactMidPrice": 0,
    "impactAskPrice": 0,
    "hasLiquidity": true,
    "openInterest": 0,
    "openValue": 0,
    "fairMethod": "string",
    "fairBasisRate": 0,
    "fairBasis": 0,
    "fairPrice": 0,
    "markMethod": "string",
    "markPrice": 0,
    "indicativeTaxRate": 0,
    "indicativeSettlePrice": 0,
    "optionUnderlyingPrice": 0,
    "settledPrice": 0,
    "timestamp": "2019-04-14T04:31:33.829Z"
  }
]
```

### 0.5刻みでpriceを丸める方法

```
#!/usr/bin/python3

# 参考にしたサイト
#  https://qiita.com/sak_2/items/b2dd8bd1c4e4b0788e9a
#  https://note.nkmk.me/python-round-decimal-quantize/

import math

UNIT = 0.5

# python2系と同じroundとするとこうなる。
__round=lambda x:(x*2+1)//2

# =============================
# 一番近い0.5刻みの値でUPする
# =============================
def fix_up_unit(price):
    _diff = price - math.floor(price)
    # 小数点以下が0 または、0.5
    if _diff == 0 or _diff == UNIT:
        return price
    # 小数点以下が0.5より大きい
    elif _diff > UNIT:
        return math.floor(price) + UNIT * 2
    # 小数点以下が0.5より小さい
    elif _diff < UNIT:
        return math.floor(price) + UNIT

# =============================
# 一番近い0.5刻みの値でDOWNする
# =============================
def fix_down_unit(price):
    _diff = price - math.floor(price)
    # 小数点以下が0 または、0.5
    if _diff == 0 or _diff == UNIT:
        return price
    # 小数点以下が0.5より大きい
    elif _diff > UNIT:
        return math.floor(price) + UNIT
    # 小数点以下が0.5より小さい
    elif _diff < UNIT:
        return math.floor(price)

#------------------------------
print(fix_up_unit(1.2))
print(fix_up_unit(1.5))
print(fix_up_unit(1.51))
print(fix_up_unit(1.7))
print(fix_up_unit(2.0))
print(fix_up_unit(2.01))

#------------------------------
print(fix_down_unit(1.2))
print(fix_down_unit(1.5))
print(fix_down_unit(1.49))
print(fix_down_unit(1.7))
print(fix_down_unit(2.0))
print(fix_down_unit(1.99))
```

### もっと簡単な0.5切り上げ・切り下げ

参考にしたサイト
　https://teratail.com/questions/176744

```
import math

# 0.5刻みで切り捨て
def _floor(x):
    return math.floor(x*2)/2

# 0.5刻みで切り上げ
def _ceil(x):
    return math.ceil(x*2)/2

# 切り下げ
print('----------')
print(_floor(1.0))
print(_floor(1.1))
print(_floor(1.5))
print(_floor(1.7))
print(_floor(2.0))
print(_floor(2.2))
print(_floor(2.5))
print(_floor(2.7))
print(_floor(3.0))

# 切り上げ
print('----------')
print(_ceil(1.0))
print(_ceil(1.1))
print(_ceil(1.5))
print(_ceil(1.7))
print(_ceil(2.0))
print(_ceil(2.2))
print(_ceil(2.5))
print(_ceil(2.7))
print(_ceil(3.0))
```
