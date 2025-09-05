
from dotenv import load_dotenv
from web3 import Web3
import os, json
from decimal import Decimal

load_dotenv()

# ==== 必要情報（環境変数 or 直書き）====
RPC_URL = os.environ["RPC_URL"]
PRIVATE_KEY = os.environ["PRIVATE_KEY"]
CONTRACT_ADDRESS = '0xc09286a6F0687C769579ac38dD682390A48d0092'
CHAIN_ID = 1868
QTY = 1
ISO = 'JP'

# ABI を別ファイルからロード
with open("abi.json", "r", encoding="utf-8") as f:
    ABI = json.load(f)

# ==== 接続・アカウント ====
w3 = Web3(Web3.HTTPProvider(RPC_URL))
acct = w3.eth.account.from_key(PRIVATE_KEY)
contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=ABI)

def get_fee_per_mint():
    try:
        return int(contract.functions.fee().call())
    except Exception as e:
        print("fee() 取得に失敗:", e)
        return 0

def build_gas_price_fields():
    latest = w3.eth.get_block("latest")
    base = latest.get("baseFeePerGas")
    if base is not None:
        # 直近の priority 分布（10/50/90%）を参照
        hist = w3.eth.fee_history(5, "latest", [10, 50, 90])
        suggested_tip = int(min([b for b in hist["reward"][-1]]))  # 最小を採用
        tip = max(100, suggested_tip)  # 下限100 wei
        buffer = base // 20  # +5%
        return {
            "maxPriorityFeePerGas": tip,
            "maxFeePerGas": base + tip + buffer
        }
    else:
        return {"gasPrice": w3.eth.gas_price}

def main():
    fee_per = get_fee_per_mint()
    total_value = fee_per * QTY
    print(f"fee per mint: {fee_per} wei, quantity: {QTY}, total value: {total_value} wei")

    # 事前に totalSupply 表示（任意）
    try:
        ts_before = contract.functions.totalSupply().call()
        print("totalSupply(before):", ts_before)
    except:
        pass

    tx_func = contract.functions.mint(QTY, ISO)

    # nonce は pending を含めて取得（連投に強い）
    nonce = w3.eth.get_transaction_count(acct.address, "pending")

    gas_fields = build_gas_price_fields()

    # ガス見積
    gas_est = tx_func.estimate_gas({"from": acct.address, "value": total_value})
    gas_limit = int(gas_est * Decimal("1.20"))  # 2割マージン

    tx = tx_func.build_transaction({
        "from": acct.address,
        "chainId": CHAIN_ID,
        "nonce": nonce,
        "gas": gas_limit,
        "value": total_value,
        **gas_fields
    })

    signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    # v5/v6 どちらでも動くように両対応
    raw_tx = getattr(signed, "rawTransaction", None) or getattr(signed, "raw_transaction", None)

    tx_hash = w3.eth.send_raw_transaction(raw_tx)
    print("submitted tx:", tx_hash.hex())

    rcpt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print("status:", rcpt.status, "block:", rcpt.blockNumber)

    # 事後確認（任意）
    try:
        ts_after = contract.functions.totalSupply().call()
        print("totalSupply(after):", ts_after)
    except:
        pass

if __name__ == "__main__":
    main()
