import requests, time, hmac, hashlib, os, json, threading
import pandas as pd
import pandas_ta as ta
from datetime import datetime
from flask import Flask

# === RENDER FIX: IP DISPLAY VERSION ===
app = Flask(__name__)

@app.route('/')
def home():
    try:
        # Ye line aapki asli Render IP nikaal legi aur screen par dikhayegi
        current_ip = requests.get('https://api.ipify.org').text
        return f"<h1>Bot is Running</h1><p>Your Delta IP: <b style='color:blue; font-size:20px;'>{current_ip}</b></p><p>Copy this IP and paste it in Delta Exchange Whitelist.</p>", 200
    except:
        return "Bot is Running (IP Fetch Error)", 200

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# Server ko background thread mein chalayein
threading.Thread(target=run_server, daemon=True).start()

# === SETTINGS ===
SYMBOL, PRODUCT_ID = "XRPUSD", 176
BASE_URL = "https://api.india.delta.exchange"
CAPITAL_PER_TRADE, TIMEFRAME = 23, "5m"
SL_PERCENT, TP_PERCENT = 0.015, 0.030

# Aapki API Keys
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
        path = "/v2/wallet/balances"
        r = requests.get(BASE_URL + path, headers=headers("GET", path)).json()
        for a in r.get("result", []):
            if a["asset_symbol"] == "USD": return float(a["available_balance"])
    except: return 0.0
    return 0.0

def place_order(side, qty):
    path = "/v2/orders"
    body = {"product_id": PRODUCT_ID, "size": int(qty), "side": side, "order_type": "market"}
    payload = json.dumps(body, separators=(',', ':'))
    try: 
        return requests.post(BASE_URL + path, data=payload, headers=headers("POST", path, payload)).json()
    except: return {}

def fetch_data():
    try:
        url = f"{BASE_URL}/v2/history/candles?symbol={SYMBOL}&resolution={TIMEFRAME}&start={int(time.time())-86400}&end={int(time.time())}"
        r = requests.get(url).json()
        df = pd.DataFrame(r["result"])
        df[['close','high','low']] = df[['close','high','low']].apply(pd.to_numeric)
        df["rsi"] = ta.rsi(df["close"], length=14)
        bb = ta.bbands(df["close"], length=20, std=2)
        df["lb"], df["ub"] = bb.iloc[:,0], bb.iloc[:,2]
        return df
    except: return None

# Initialize Variables
pos, entry, total_trades, wins, start_balance = None, 0, 0, 0, 0

print("🚀 Bot starting... Check your Render URL for IP Whitelisting.")

while True:
    try:
        df = fetch_data()
        if df is None: 
            time.sleep(10); continue
        
        row = df.iloc[-1]
        ltp, rsi, lb, ub = row.close, row.rsi, row.lb, row.ub
        wallet = get_wallet()
        if start_balance == 0: start_balance = wallet

        # Trading Logic
        if pos is None:
            if ltp <= lb and rsi < 35:
                qty = int(CAPITAL_PER_TRADE/ltp)
                if "result" in place_order("buy", qty): 
                    pos, entry = "LONG", ltp
                    print(f"✅ LONG Order Placed at {entry}")
            elif ltp >= ub and rsi > 65:
                qty = int(CAPITAL_PER_TRADE/ltp)
                if "result" in place_order("sell", qty): 
                    pos, entry = "SHORT", ltp
                    print(f"✅ SHORT Order Placed at {entry}")
        else:
            pnl = (ltp - entry)/entry if pos == "LONG" else (entry - ltp)/entry
            if pnl <= -SL_PERCENT or pnl >= TP_PERCENT:
                side = "sell" if pos == "LONG" else "buy"
                if "result" in place_order(side, int(CAPITAL_PER_TRADE/ltp)):
                    total_trades += 1
                    if pnl > 0: wins += 1
                    print(f"❌ Position Closed. PNL: {pnl*100:.2f}%")
                    pos = None

        winrate = (wins / total_trades * 100) if total_trades > 0 else 0
        print(f"{datetime.now().strftime('%H:%M:%S')} | LTP: {ltp} | RSI: {rsi:.2f} | Wallet: {wallet:.2f} | WinRate: {winrate:.1f}%")
        
        time.sleep(20) # 20 seconds wait
    except Exception as e:
        print(f"Error in Loop: {e}"); time.sleep(10)
