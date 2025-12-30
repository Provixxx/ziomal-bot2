import requests
import random
import time
import asyncio

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
]

async def analyze_gold_pro():
    # Zostawiamy Finnhub dla złota (to działało w testach)
    symbol = "XAU/USD"
    url = f'https://finnhub.io/api/v1/quote?symbol={symbol}&token={config.FINNHUB_KEY}'
    try:
        r = requests.get(url).json()
        if 'c' not in r or r['c'] == 0: return None
        current_price = r['c']
        change_pct = r.get('dp', 0)
        is_urgent = abs(change_pct) > 0.3
        action = "NEUTRAL"
        if change_pct < -0.3: action = "BUY"
        elif change_pct > 0.3: action = "SELL"
        if action != "NEUTRAL":
            return {
                "symbol": "ZŁOTO", "price": current_price, "action": action,
                "change": round(change_pct, 2), "urgent": is_urgent,
                "sl": round(current_price * 0.995 if action == "BUY" else current_price * 1.005, 2),
                "tp": round(current_price * 1.015 if action == "BUY" else current_price * 0.985, 2)
            }
    except: return None
    return None


import pandas as pd

async def get_stooq_data_safe(ticker):
    try:
        # Pobieranie CSV ze Stooq
        url = f"https://stooq.pl/q/l/?s={ticker}&f=sd2t2ohlcv&h&e=csv"
        df = pd.read_csv(url)
        
        if df.empty or 'Close' not in df.columns:
            return None
            
        price = float(df['Close'].iloc[0])
        # Obliczanie zmiany (Close vs Open)
        open_p = float(df['Open'].iloc[0])
        change = round(((price - open_p) / open_p) * 100, 2) if open_p != 0 else 0
        
        return {
            "symbol": ticker,
            "price": price,
            "change": change
        }
    except Exception as e:
        print(f"Błąd Stooq dla {ticker}: {e}")
        return None


async def get_combined_market_data(tickers):
    results = []
    for ticker in tickers:
        try:
            # Jeśli to polska spółka, idź przez bezpieczny Stooq
            if ticker.endswith('.WA'):
                data = await get_stooq_data_safe(ticker)
                if data:
                    results.append(data)
            else:
                # USA - Poprawione: ticker zamiast symbol
                url = f'https://finnhub.io/api/v1/quote?symbol={ticker}&token={config.FINNHUB_KEY}'
                r = requests.get(url).json()
                if 'c' in r:
                    results.append({"symbol": ticker, "price": r['c'], "change": r.get('dp', 0)})
        except Exception as e:
            print(f"Błąd przy pobieraniu {ticker}: {e}")
            continue # Przejdź do kolejnego tickera zamiast wywalać bota

    return results



