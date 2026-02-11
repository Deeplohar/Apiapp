import requests, time, hmac, hashlib, os, json
import pandas as pd
import pandas_ta as ta
import ccxt 
from datetime import datetime

import requests, time, hmac, hashlib, os, json
import pandas as pd
import pandas_ta as ta
from datetime import datetime

# ================= RENDER IP CHECKER (Ye lines add karein) =================
try:
    current_ip = requests.get('https://api.ipify.org').text
    print("\n" + "="*40)
    print(f"🚀 RENDER SERVER IP: {current_ip}")
    print("Is IP ko copy karke Delta Exchange me whitelist karein!")
    print("="*40 + "\n")
except Exception as e:
    print("IP nikalne me dikkat aayi:", e)
# =========================================================================

# ... (Baki ka settings wala code waisa hi rahega)


# ================= SETTINGS =================
SYMBOL = "XRPUSD"
PRODUCT_ID = 176
BASE_URL = "https://api.india.delta.exchange"

CAPITAL_PER_TRADE = 23   # ~2000 INR ($23 USDT approx)
TIMEFRAME = "5m"

SL_PERCENT = 0.015  # 1.5% Stop Loss
TP_PERCENT = 0.030  # 3.0% Take Profit

# AAPKI API DETAILS
API_KEY = "xjBY5F7HF4IGzC8DuoSCLy6pJWCbgL"
API_SECRET = "LFlr9x4H9xG1iUDsUjddI1JlqLh19wsWTyKhdJjbmc74Od29oCRxYARXiSaw"
# ============================================

# ---------- CORRECTED SIGNING (Payload inclusion is MUST) ----------
def sign(method, path, payload=""):
    ts = str(int(time.time()))
    # Delta POST orders ke liye payload (body) ko sign karna zaruri hai warna order reject hoga
    msg = method + ts + path + payload
    sig = hmac.new(API_SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()
    return ts, sig

def headers(method, path, payload=""):
    ts, sig = sign(method, path, payload)
    return {
        "api-key": API_KEY,
        "timestamp": ts,
        "signature": sig,
        "Content-Type": "application/json"
    }

# ---------- WALLET ----------
def get_wallet():
    path = "/v2/wallet/balances"
    try:
        r = requests.get(BASE_URL + path, headers=headers("GET", path)).json()
        if "result" in r:
            for a in r["result"]:
                if a["asset_symbol"] == "USD":
                    return float(a["available_balance"])
    except: return 0.0
    return 0.0

# ---------- ORDER EXECUTION (Corrected) ----------
def place_order(side, qty):
    path = "/v2/orders"
    body = {
        "product_id": PRODUCT_ID,
        "size": int(qty), # Lots integer hone chahiye (e.g. 10, 15)
        "side": side,
        "order_type": "market"
    }
    # Payload string bina spaces ke honi chahiye signature match karne ke liye
    payload = json.dumps(body, separators=(',', ':'))
    try:
        response = requests.post(BASE_URL + path, data=payload, headers=headers("POST", path, payload)).json()
        # Debugging ke liye agar error aaye
        if "error" in response:
            print(f"\n❌ Order Error: {response['error']['message']}")
        return response
    except Exception as e:
        print(f"\n❌ Request Error: {e}")
        return {}

def calc_qty(price):
    # $23 capital / price = number of contracts (lots)
    return max(1, int(CAPITAL_PER_TRADE / price))

# ---------- DATA ----------
def fetch_data():
    try:
        end = int(time.time())
        start = end - 86400
        url = f"{BASE_URL}/v2/history/candles?symbol={SYMBOL}&resolution={TIMEFRAME}&start={start}&end={end}"
        r = requests.get(url).json()
        df = pd.DataFrame(r["result"])
        df[['close','high','low']] = df[['close','high','low']].apply(pd.to_numeric)
        df["rsi"] = ta.rsi(df["close"], length=14)
        bb = ta.bbands(df["close"], length=20, std=2)
        df["lb"], df["mb"], df["ub"] = bb.iloc[:,0], bb.iloc[:,1], bb.iloc[:,2]
        return df
    except: return None

# ---------- STATS ----------
pos = None
entry = 0
total_trades = 0
wins = 0
start_balance = 0

# ---------- BOT MAIN LOOP ----------
while True:
    try:
        df = fetch_data()
        if df is None:
            time.sleep(5)
            continue

        row = df.iloc[-1]
        ltp, rsi, lb, ub, mb = row.close, row.rsi, row.lb, row.ub, row.mb

        wallet = get_wallet()
        if start_balance == 0: start_balance = wallet

        signal = "NEUTRAL"
        if ltp <= lb and rsi < 35: signal = "BUY SIGNAL"
        elif ltp >= ub and rsi > 65: signal = "SELL SIGNAL"

        # Trading Logic
        if pos is None:
            if signal == "BUY SIGNAL":
                resp = place_order("buy", calc_qty(ltp))
                if "result" in resp: # Sirf success par entry maane
                    pos, entry = "LONG", ltp
            elif signal == "SELL SIGNAL":
                resp = place_order("sell", calc_qty(ltp))
                if "result" in resp:
                    pos, entry = "SHORT", ltp
        else:
            pnl_pct = (ltp - entry) / entry if pos == "LONG" else (entry - ltp) / entry
            exit_reason = None
            if pnl_pct <= -SL_PERCENT: exit_reason = "STOP LOSS"
            elif pnl_pct >= TP_PERCENT: exit_reason = "TAKE PROFIT"

            if exit_reason:
                side = "sell" if pos == "LONG" else "buy"
                resp = place_order(side, calc_qty(ltp))
                if "result" in resp:
                    total_trades += 1
                    if pnl_pct > 0: wins += 1
                    pos = None

        # Dashboard Logic
        winrate = (wins / total_trades * 100) if total_trades > 0 else 0
        netpl = wallet - start_balance

        os.system("clear" if os.name == 'posix' else 'cls')
        print("="*60)
        print("🚀 DELTA REAL AI TRADING BOT (FIXED VERSION)")
        print("="*60)
        print(f"Time        : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Symbol      : {SYMBOL} | TF: {TIMEFRAME}")
        print(f"Wallet      : {wallet:.2f} USDT")
        print(f"Net P/L     : {netpl:.2f} USDT")
        print(f"Trades      : {total_trades} | Win Rate: {winrate:.1f}%")
        print("-"*60)
        print(f"Price (LTP) : {ltp}")
        print(f"RSI (14)    : {rsi:.2f}")
        print(f"BB Bands    : U:{ub:.4f} | M:{mb:.4f} | L:{lb:.4f}")
        print(f"Signal      : {signal}")
        print("-"*60)

        if pos:
            color = "🟢" if pnl_pct >= 0 else "🔴"
            print(f"Position    : {pos}")
            print(f"Entry Price : {entry}")
            print(f"Live PnL    : {color} {pnl_pct*100:.2f}%")
        else:
            print("Position    : STANDBY (Searching...)")

        print("-"*60)
        print("Press Ctrl + C to stop")
        time.sleep(10)

    except Exception as e:
        print("Loop Error:", e)
        time.sleep(5)




