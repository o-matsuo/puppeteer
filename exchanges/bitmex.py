# -*- coding: utf-8 -*-
"""
現状は使用していない。将来的な複数取引所サポートに向けて準備
"""

import ccxt

# bitmex
bitmex = ccxt.bitmex({
    'apiKey': '',
    'secret': ''
})
# for TESTNET
bitmex.urls['api'] = bitmex.urls['test'] 

