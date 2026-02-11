import requests, time, hmac, hashlib, os, json, threading
import pandas as pd
import pandas_ta as ta
from datetime import datetime
from flask import Flask

# === RENDER FIX: FAKE SERVER ===
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is Running", 200

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_server, daemon=True).start()

# === IP CHECKER ===
try:
    print(f"\n🚀 RENDER IP: {requests.get('https://api.ipify.org').text}\n")
except: pass

# === SETTINGS ===
SYMBOL, PRODUCT_ID = "XRPUSD", 176
BASE_URL = "https://api.india.delta.exchange"
CAPITAL_PER_TRADE, TIMEFRAME = 23, "5m"
SL_PERCENT, TP_PERCENT = 0.015, 0.030
API_KEY = "xjBY5F7HF4IGzC8DuoSCLy6pJWCbgL"
API_SECRET = "LFlr9x4H9xG1iUDsUjddI1JlqLh19wsWTyKhdJjbmc74Od29oCRxYARXiSaw"

def sign(method, path, payload=""):
    ts = str(int(time.time()))
    msg = method + ts + path + payload
    sig = hmac.new(API_SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()
    return ts, sig

def headers(method, path, payload=""):
    ts, sig = sign(method, path, payload)
    return {"api-key": API_KEY, "timestamp": ts, "signature": sig, "Content-Type": "application/json"}

def get_wallet():
    try:
        r = requests.get(BASE_URL + "/v2/wallet/balances", headers=headers("GET", "/v2/wallet/balances")).json()
        for a in r.get("result", []):
            if a["asset_symbol"] == "USD": return float(a["available_balance"])
    except: return 0.0
    return 0.0

def place_order(side, qty):
    path = "/v2/orders"
    body = {"product_id": PRODUCT_ID, "size": int(qty), "side": side, "order_type": "market"}
    payload = json.dumps(body, separators=(',', ':'))
    try: return requests.post(BASE_URL + path, data=payload, headers=headers("POST", path, payload)).json()
    except: return {}

def fetch_data():
    try:
        url = f"{BASE_URL}/v2/history/candles?symbol={SYMBOL}&resolution={TIMEFRAME}&start={int(time.time())-86400}&end={int(time.time())}"
        df = pd.DataFrame(requests.get(url).json()["result"])
        df[['close','high','low']] = df[['close','high','low']].apply(pd.to_numeric)
        df["rsi"] = ta.rsi(df["close"], length=14)
        bb = ta.bbands(df["close"], length=20, std=2)
        df["lb"], df["ub"] = bb.iloc[:,0], bb.iloc[:,2]
        return df
    except: return None

pos, entry, total_trades, wins, start_balance = None, 0, 0, 0, 0

while True:
    try:
        df = fetch_data()
        if df is None: 
            time.sleep(10); continue
        
        row = df.iloc[-1]
        ltp, rsi, lb, ub = row.close, row.rsi, row.lb, row.ub
        wallet = get_wallet()
        if start_balance == 0: start_balance = wallet

        if pos is None:
            if ltp <= lb and rsi < 35:
                if "result" in place_order("buy", int(CAPITAL_PER_TRADE/ltp)): pos, entry = "LONG", ltp
            elif ltp >= ub and rsi > 65:
                if "result" in place_order("sell", int(CAPITAL_PER_TRADE/ltp)): pos, entry = "SHORT", ltp
        else:
            pnl = (ltp - entry)/entry if pos == "LONG" else (entry - ltp)/entry
            if pnl <= -SL_PERCENT or pnl >= TP_PERCENT:
                if "result" in place_order("sell" if pos == "LONG" else "buy", int(CAPITAL_PER_TRADE/ltp)):
                    total_trades += 1
                    if pnl > 0: wins += 1
                    pos = None

        winrate = (wins / total_trades * 100) if total_trades > 0 else 0
        print(f"{datetime.now().strftime('%H:%M:%S')} | LTP: {ltp} | RSI: {rsi:.2f} | Wallet: {wallet} | WinRate: {winrate:.1f}%")
        time.sleep(20)
    except Exception as e:
        print(f"Error: {e}"); time.sleep(10)

