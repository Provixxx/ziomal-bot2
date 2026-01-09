import pandas as pd
import config
import requests
import g4f
import asyncio
import time

# --- 1. MATEMATYKA (RSI) ---
def calculate_rsi(prices, period=14):
    if len(prices) < period + 1: return 50
    delta = pd.Series(prices).diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    if loss.iloc[-1] == 0: return 100
    rs = gain.iloc[-1] / loss.iloc[-1]
    return int(round(100 - (100 / (1 + rs)), 0))

# --- 2. FORMACJE ŚWIECOWE ---
def detect_pattern(opens, highs, lows, closes):
    # Pobieramy ostatnią świecę
    o, h, l, c = opens[-1], highs[-1], lows[-1], closes[-1]
    o_prev, c_prev = opens[-2], closes[-2] # Poprzednia świeca
    
    body = abs(c - o)
    wick_upper = h - max(c, o)
    wick_lower = min(c, o) - l
    
    # MŁOT (Hammer) - Potencjał wzrostu
    if wick_lower > 2 * body and wick_upper < (body * 0.5) and body > 0:
        return "🔨 MŁOT"
    
    # SPADAJĄCA GWIAZDA (Shooting Star) - Potencjał spadku
    if wick_upper > 2 * body and wick_lower < (body * 0.5) and body > 0:
        return "🌠 SPAD. GWIAZDA"
    
    # OBJĘCIE HOSSY (Bullish Engulfing) - Wzrosty
    if c > o and c_prev < o_prev and c > o_prev and o < c_prev:
        return "⏫ OBJ. HOSSY"
        
    # OBJĘCIE BESSY (Bearish Engulfing) - Spadki
    if c < o and c_prev > o_prev and c < o_prev and o > c_prev:
        return "⏬ OBJ. BESSY"
        
    return "➖"

# --- 3. AI (GPT-4) ---
async def get_ai_opinion(ticker, price, rsi, pattern):
    prompt = (f"Spółka {ticker}. Cena {price}. RSI {rsi}. Formacja techniczna: {pattern}. "
              f"Jako profesjonalny trader napisz JEDNO zdanie werdyktu (np. 'Kupuj pod odbicie', 'Ryzyko spadku').")
    try:
        response = await asyncio.wait_for(
            g4f.ChatCompletion.create_async(
                model=g4f.models.gpt_4,
                messages=[{"role": "user", "content": prompt}]
            ), timeout=8.0)
        return response.strip()
    except:
        return "Analiza niedostępna"

# --- 4. GŁÓWNA FUNKCJA POBIERANIA ---
async def get_market_data_pro(ticker):
    # Konwersja symboli dla Finnhub (PL wymaga .WAR)
    finnhub_ticker = ticker.replace('.WA', '.WAR')
    
    # Pobieramy 40 dni historii (dla RSI i SMA)
    end = int(time.time())
    start = end - (40 * 24 * 60 * 60)
    
    try:
        # Requesty
        q_url = f'https://finnhub.io/api/v1/quote?symbol={finnhub_ticker}&token={config.FINNHUB_KEY}'
        c_url = f'https://finnhub.io/api/v1/stock/candle?symbol={finnhub_ticker}&resolution=D&from={start}&to={end}&token={config.FINNHUB_KEY}'
        
        r_q = requests.get(q_url, timeout=5).json()
        r_c = requests.get(c_url, timeout=5).json()

        if 'c' not in r_q or r_c.get('s') != 'ok':
            return None

        # Dane
        price = r_q['c']
        change = r_q.get('dp', 0)
        closes = r_c['c']
        
        # Obliczenia
        rsi = calculate_rsi(closes)
        pattern = detect_pattern(r_c['o'], r_c['h'], r_c['l'], closes)
        
        # SL / TP (na podstawie zmienności - ATR uproszczony)
        # Średnia zmienność z 5 dni
        volatility = sum([h-l for h, l in zip(r_c['h'][-5:], r_c['l'][-5:])]) / 5
        sl = round(price - (volatility * 1.5), 2)
        tp = round(price + (volatility * 3.0), 2)

        # AI pytamy tylko gdy coś się dzieje (oszczędność czasu)
        ai_msg = ""
        if rsi <= 35 or rsi >= 75 or pattern != "➖":
            ai_msg = await get_ai_opinion(ticker, price, rsi, pattern)

        return {
            "symbol": ticker.replace('.WA', ''), # Wyświetlana nazwa
            "orig_symbol": ticker,               # Oryginał do sortowania
            "price": price,
            "change": change,
            "rsi": rsi,
            "pattern": pattern,
            "sl": sl,
            "tp": tp,
            "ai": ai_msg
        }
    except Exception as e:
        print(f"Błąd {ticker}: {e}")
        return None

async def get_combined_market_data(tickers):
    tasks = [get_market_data_pro(t) for t in tickers]
    results = await asyncio.gather(*tasks)
    return [r for r in results if r is not None]

async def analyze_gold_pro():
    try:
        url = f'https://finnhub.io/api/v1/quote?symbol=XAU&token={config.FINNHUB_KEY}'
        r = requests.get(url, timeout=5).json()
        return {"price": r['c'], "change": r.get('dp', 0)}
    except: return None

