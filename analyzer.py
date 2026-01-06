import yfinance as yf
import pandas as pd
import config
import requests
import g4f
import asyncio
import time

# Sesja do newsów (opcjonalnie)
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50
    delta = pd.Series(prices).diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    avg_gain = gain.iloc[-1]
    avg_loss = loss.iloc[-1]
    
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 0)

async def get_market_data_pro(ticker):
    # Obsługa polskich spółek dla Finnhub
    finnhub_ticker = ticker.replace('.WA', '.WAR')
    
    # 1. Pobieranie ceny aktualnej (Quote)
    quote_url = f'https://finnhub.io/api/v1/quote?symbol={finnhub_ticker}&token={config.FINNHUB_KEY}'
    # 2. Pobieranie świec historycznych do RSI i SMA (ostatnie 30 dni)
    end = int(time.time())
    start = end - (30 * 24 * 60 * 60)
    candles_url = f'https://finnhub.io/api/v1/stock/candle?symbol={finnhub_ticker}&resolution=D&from={start}&to={end}&token={config.FINNHUB_KEY}'

    try:
        r_quote = requests.get(quote_url, timeout=10).json()
        r_candles = requests.get(candles_url, timeout=10).json()

        if 'c' not in r_quote or r_quote['c'] == 0:
            return None

        current_price = r_quote['c']
        change = round(r_quote.get('dp', 0), 2)
        
        # Obliczanie wskaźników z historii
        rsi = 50
        trend = "SIDE ⚪"
        if r_candles.get('s') == 'ok':
            close_prices = r_candles['c']
            rsi = calculate_rsi(close_prices)
            sma20 = pd.Series(close_prices).rolling(window=20).mean().iloc[-1]
            trend = "UP 🟢" if current_price > sma20 else "DOWN 🔴"

        # Logika sygnałów
        status = "NEUTRAL"
        setup = None
        if trend == "UP 🟢" and rsi <= 38:
            status = "MOCNE KUPUJ 🔥"
            setup = {"sl": round(current_price * 0.96, 2), "tp": round(current_price * 1.08, 2)}
        elif rsi >= 75:
            status = "⚠️ GRZANE"

        return {
            "symbol": ticker,
            "price": round(current_price, 2),
            "change": change,
            "rsi": int(rsi),
            "status": status,
            "trend": trend,
            "setup": setup,
            "news": "Dane Finnhub Pro"
        }
    except Exception as e:
        print(f"Błąd {ticker}: {e}")
        return None

async def verify_with_ai(ticker, price, rsi, trend, news):
    prompt = f"Analiza {ticker}. Cena: {price}, RSI: {rsi}, Trend: {trend}. Czy to moment na wejście? Krótko: TAK/NIE + powód."
    try:
        response = await asyncio.wait_for(
            g4f.ChatCompletion.create_async(
                model=g4f.models.gpt_4,
                messages=[{"role": "user", "content": prompt}]
            ), timeout=15.0)
        return response
    except:
        return "AI zajęte. Sprawdź RSI."

async def get_combined_market_data(tickers):
    results = []
    for ticker in tickers:
        data = await get_market_data_pro(ticker)
        if data:
            results.append(data)
        await asyncio.sleep(0.5) # Przerwa dla API
    return results

async def analyze_gold_pro():
    url = f'https://finnhub.io/api/v1/quote?symbol=XAU&token={config.FINNHUB_KEY}'
    try:
        r = requests.get(url, timeout=10).json()
        return {"symbol": "ZŁOTO", "price": r['c'], "change": round(r.get('dp', 0), 2)}
    except:
        return None
