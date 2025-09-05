# 未登録のMetaMapをMintする

 * MetaMapはオンチェーン上でNFTをMINTした後、オフチェーンで国名を紐づけるが、これはオンチェーン上のNFT発行処理のみを行う

# セットアップ

```
$ pyenv local 3.9.5
$ python -m venv .venv
$ source .venv/bin/activate
$ pip install dotenv web3
```

# ランダム実行

 * 最大8時間20分稼働する

```
for i in {1..100}; do
    delay=$(( RANDOM % 300 ))   # 0〜299秒のランダム遅延
    echo "Run $i: waiting $delay sec..."
    sleep "$delay"
    python3 UnregMetaMint.py
    sleep $((300 - delay))
done
```

