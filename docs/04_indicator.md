### インジケータ

- smaやemaのようなインジケータはpandasの機能を使えば実現できるが、高度な機能については Ta-Lib の機能を利用する。

- Ta-Libはインストールで躓くケースが多い。   
以下のサイトを参考にした。

  - https://qiita.com/aisurta/items/34e8cf47c4eb4fdd5d68

- Ta-Lib インストール   
cloud9のターミナルで以下を実行

```
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -zxvf ta-lib-0.4.0-src.tar.gz
cd ta-lib
./configure --prefix=/usr
make
sudo make install

sudo bash -c "echo "/usr/local/lib64" >> /etc/ld.so.conf"
sudo /sbin/ldconfig
sudo pip3 install ta-lib
```
