# オープンソース 仮想通貨自動取引bot開発フレームワーク
##  〜〜〜　Puppeteer (傀儡師)　〜〜〜

![docs/image/puppeteer_main.png](docs/image/puppeteer_main.png)

## Puppeteer(傀儡師)とは

- 名称の意味：傀儡師、人形使い、puppeteer、puppet player
- イメージ：　戦略を裏で操る 傀儡師 をイメージしました。
- 機能：
  - 対応している取引所は[bitmex](https://www.bitmex.com/?lang=ja-JP)です。
  - [TestNet](https://testnet.bitmex.com/?lang=ja-JP)にも対応していますので、実運用前に十分に試験が可能です。
  - 仮想通貨自動売買botを、テンプレートを使うことにより素早く作成することができます。
  - websocketでデータを収集させることも可能です。それにより取引所のREST APIを高速に発行しつづける必要がなくなります。
  - 内臓した5秒ローソク足収集機能を使って売買の意思決定を行うことが容易になります。
  - 資産状況をdiscordに定期的に通知することができます。
  - 一般的に使用するであろう取引所のAPIのラッパー関数を用意していますので、簡単に取引所に対して売買指示を出せます。

## 独自のストラテジ(Puppet(傀儡))の作成

- 自分のストラテジ(Puppet(傀儡))を作成し、本フレームワークに組み込むことで自分だけのPuppetを作成することができます。
- Puppetを作成するには「プログラム言語python」や「[ccxt](https://github.com/ccxt/ccxt)」の知識が必要ですが、   
そういった煩わしい部分を極力隠蔽していく方針です。

## ドキュメント

- 01.[インストール](./docs/01_install.md)
- 02.[設定](./docs/02_setting.md)
- 03.[試行](./docs/03_test_run.md)
- 04.[インジケータ](./docs/04_indicator.md)

## 注意事項

- 取引所[bitmex](https://www.bitmex.com/?lang=ja-JP)のアカウントを取得した直後や、長期間(一週間程度)ポジションを保持していない状態で   
websocketを有効にしてPuppeteer起動すると「ポジションのPartial情報が取得できない」エラーが発生し、処理が継続できないことがあります。   
その場合は、1ドルでも良いので一回売り買いを行った後でpuppeteerを実行してください。   
REST APIしか使わない(websocketを有効にしない)場合には問題ありません。

## ライセンス

- [MIT](./LICENSE.txt)
