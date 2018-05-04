ytce
====

指定したYouTube Liveのチャット欄から、指定したチャンネルによる書き込みを抽出するCLIスクリプト。

## 必要なもの

- Python 3.6.x
- httplib2
- oauth2client
- Google Cloud Platformのアカウント

## 準備
[ここ](https://blog.sky-net.pw/article/86)を参考にさせて頂きました。

### Pythonの環境を整える
Python 3.6.xをインストールし、
```
pip install httplib2 oauth2client
```
で`httplib2`と`oauth2client`をインストールする。

### Google Cloud PlatformでAPIを設定する
[Google Cloud Platform](https://console.cloud.google.com/getting-started)にアクセスし、アカウントを作る。半年の無料トライアルが可能だが、クレジットカードの情報は必須な模様。

[この辺](https://www.apps-gcp.com/gcp-startup/)を参考に新しいプロジェクトを作り、**YouTube Data API v3**を有効にしておく。

**Credentials**から、Create credentials -> OAuth client IDと辿ると、OAuth client IDの作成ウィザードになる。Application typeはOtherを選び、Create。すると下の方にclient IDができているので、右にあるダウンロードボタンでjson形式のファイルとしてダウンロードする。

### 必要なファイルをコピーする
このリポジトリをまるごとダウンロードして、どこか好きな所に置く。OAuth client IDファイルも同じディレクトリに入れておくと都合がよい。

### Configファイルを設定する
このリポジトリについているconfig.txtを開き、
```
"api_key_file": "",
```
の`""`の間にOAuth client IDの.jsonファイルのパスを入れて、保存する。

他のパラメータの意味は以下の通り。

```
"live_channel_ids": {"<key>": "<value>", }
```
は、チャットを抽出したいYouTube Liveが行われているチャンネルのID（チャンネルページのURLの後ろについている英数字）の辞書。`<key>`は単なる識別用のキーで特に意味はない。

```
"author_channel_ids": {"<key>": "<value>", }
```
は、書き込みを取得したい人のチャンネルのIDの辞書（ここで指定されたチャンネルによる書き込みのみが抽出される）。`<key>`は単なる識別用のキーで特に意味はない。

```
"log_file": <path>
```
は、取得した書き込みの出力先ファイルのパス。

## 使い方

ターミナル or コマンドプロンプトでytce.pyがあるディレクトリに移動しておく。configファイルが`config.txt`だとすると、
```
python ytce.py config.txt
```
でプログラムが起動する。プロセスが生きている限り、取得した書き込みが`log_file`で指定したログファイルに延々と追記されていく。
初回のみ、実行時にブラウザでOAuth認証画面に飛ばされるので、適当なアカウントを選んで認証する。
これによりconfigファイル内の`credential_file`で指定したパスに認証用の.jsonファイルが生成され、次回からはOAuthの認証は必要なくなる。

## 既知の限界・問題・リスク
- 起動時にliveが行われていないチャンネルのチャットは取得できない。ただし、動作中にliveが終了した場合、その後のチャットも拾えるようだ。
- `ytce.py`を実行中にLiveが開始した場合、一度`ytce.py`を再起動しないと反映されない。あくまで`ytce.py`が起動した際に"Connected"と表示されたliveしか見ない。
- 長時間動作させ続けたときにメモリリーク等の問題が起きる恐れがある。

## ライセンス

TBA

## 改良案
- 定期的に新しいliveが開始していないか確認する

## 作者

p-h-d