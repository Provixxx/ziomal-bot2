import pandas as pd
import config
import requests
import g4f
import asyncio
import time

# --- MATEMATYKA ---
def calculate_rsi(prices, period=14):
    if len(prices) < period + 1: return 50
    delta = pd.Series(prices).diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    if loss.iloc[-1] == 0: return 100
    rs = gain.iloc[-1] / loss.iloc[-1]
    return int(round(100 - (100 / (1 + rs)), 0))

def detect_pattern(opens, highs, lows, closes):
    # Prosta detekcja formacji na ostatniej świecy
    o, h, l, c = opens[-1], highs[-1], lows[-1], closes[-1]
    o_prev, c_prev = opens[-2], closes[-2]
    
    body = abs(c - o)
    wick_upper = h - max(c, o)
    wick_lower = min(c, o) - l
    
    # 1. Młot (Hammer) - Potencjalne odwrócenie na wzrosty
    if wick_lower > 2 * body and wick_upper < body:
        return "🔨 MŁOT"
    
    # 2. Objęcie Hossy (Bullish Engulfing)
    if c > o and c_prev < o_prev and c > o_prev and o < c_prev:
        return "⏫ OBJĘCIE"
        
    return "➖"

def calculate_setup(price, atr_proxy):
    # Wyliczanie TP i SL na podstawie zmienności (proste podejście)
    sl = round(price - (atr_proxy * 1.5), 2)
    tp = round(price + (atr_proxy * 3.0), 2)
    return sl, tp

# --- AI ---
async def get_ai_verdict(ticker, rsi, pattern):
    prompt = f"Spółka {ticker}. RSI: {rsi}. Formacja: {pattern}. Krótki werdykt traderski (max 1 zdanie)."
    try:
        response = await asyncio.wait_for(g4f.ChatCompletion.create_async(
            model=g4f.models.gpt_4,
            messages=[{"role": "user", "content": prompt}]
        ), timeout=6.0)
        return response.strip()
    except: return "Obserwuj poziom wsparcia."

# --- GŁÓWNA FUNKCJA ---
async def get_market_data_pro(ticker):
    finnhub_ticker = ticker.replace('.WA', '.WAR') # Fix dla Polski
    end = int(time.time())
    start = end - (40 * 24 * 60 * 60) # 40 dni historii
    
    try:
        # Pobieranie danych
        q = requests.get(f'https://finnhub.io/api/v1/quote?symbol={finnhub_ticker}&token={config.FINNHUB_KEY}', timeout=5).json()
        c = requests.get(f'https://finnhub.io/api/v1/stock/candle?symbol={finnhub_ticker}&resolution=D&from={start}&to={end}&token={config.FINNHUB_KEY}', timeout=5).json()

        if 'c' not in q or c.get('s') != 'ok': return None

        # Zmienne
        price = q['c']
        change = q.get('dp', 0)
        closes = c['c']
        opens = c['o']
        highs = c['h']
        lows = c['l']
        
        # Analiza
        rsi = calculate_rsi(closes)
        pattern = detect_pattern(opens, highs, lows, closes)
        
        # SL/TP (używamy różnicy High-Low jako prostego ATR)
        volatility = sum([h-l for h, l in zip(highs[-5:], lows[-5:])]) / 5
        sl, tp = calculate_setup(price, volatility)

        # AI (tylko dla ciekawych sytuacji, żeby nie spamować API)
        ai_msg = ""
        if rsi < 35 or rsi > 75 or pattern != "➖":
            ai_msg = await get_ai_verdict(ticker, rsi, pattern)

        return {
            "symbol": ticker.replace('.WA', ''),
            "orig_symbol": ticker,
            "price": price,
            "change": change,
            "rsi": rsi,
            "pattern": pattern,
            "sl": sl,
            "tp": tp,
            "ai": ai_msg
        }
    except Exception as e:
        print(f"Err {ticker}: {e}")
        return None

async def get_combined_market_data(tickers):
    tasks = [get_market_data_pro(t) for t in tickers]
    return [r for r in await asyncio.gather(*tasks) if r]

async def analyze_gold_pro():
    try:
        r = requests.get(f'https://finnhub.io/api/v1/quote?symbol=XAU&token={config.FINNHUB_KEY}', timeout=5).json()
        return {"price": r['c'], "change": r.get('dp', 0)}
    except: return None
