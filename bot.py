import requests, time, hmac, hashlib, os, json, threading
import pandas as pd
import pandas_ta as ta
from datetime import datetime
from flask import Flask

# ================= RENDER FREE TIER FIX (FLASK) =================
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is Running 24/7"

def run_server():
    # Render default port 10000 use karta hai
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# Server ko alag thread mein start karein
threading.Thread(target=run_server, daemon=True).start()
# ================================================================

# ================= RENDER IP CHECKER ============================
try:
    current_ip = requests.get('https://api.ipify.org').text
    print("\n" + "="*40)
    print(f"🚀 RENDER SERVER IP: {current_ip}")
    print("Is IP ko copy karke Delta Exchange me whitelist karein!")
    print("="*40 + "\n")
except Exception as e:
    print("IP nikalne me dikkat aayi:", e)
# ================================================================

# ================= SETTINGS =================
SYMBOL = "XRPUSD"
PRODUCT_ID = 176
BASE_URL = "https://api.india.delta.exchange"

CAPITAL_PER_TRADE = 23   
TIMEFRAME = "5m"

SL_PERCENT = 0.015  
TP_PERCENT = 0.030  

API_KEY = "xjBY5F7HF4IGzC8DuoSCLy6pJWCbgL"
API_SECRET = "LFlr9x4H9xG1iUDsUjddI1JlqLh19wsWTyKhdJjbmc74Od29oCRxYARXiSaw"
# ============================================

def sign(method, path, payload=""):
    ts = str(int(time.time()))
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

def place_order(side, qty):
    path = "/v2/orders"
    body = {
        "product_id": PRODUCT_ID,
        "size": int(qty), 
        "side": side,
        "order_type": "market"
    }
    payload = json.dumps(body, separators=(',', ':'))
    try:
        response = requests.post(BASE_URL + path, data=payload, headers=headers("POST", path, payload)).json()
        if "error" in response:
            print(f"\n❌ Order Error: {response['error']['message']}")
        return response
    except Exception as e:
        print(f"\n❌ Request Error: {e}")
        return {}

def calc_qty(price):
    return max(1, int(CAPITAL_PER_TRADE / price))

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

pos = None
entry = 0
total_trades = 0
wins = 0
start_balance = 0

print("🚀 Bot initialized. Waiting for first data fetch...")

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

        if pos is None:
            if signal == "BUY SIGNAL":
                resp = place_order("buy", calc_qty(ltp))
                if "result" in resp:
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

        winrate = (

