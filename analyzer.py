import pandas as pd
import config
import requests
import g4f
import asyncio
import time

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50
    delta = pd.Series(prices).diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    avg_gain = gain.iloc[-1]
    avg_loss = loss.iloc[-1]
    if avg_loss == 0: return 100
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 0)

async def verify_with_ai(ticker, price, rsi, trend):
    # Profesjonalny prompt łączący liczby z interpretacją
    prompt = (f"Jesteś ekspertem giełdowym. Przeanalizuj {ticker}: "
              f"Cena {price}, RSI {rsi}, Trend {trend}. "
              f"W jednej krótkiej linii (max 12 słów) napisz czy to okazja do wejścia.")
    try:
        response = await asyncio.wait_for(
            g4f.ChatCompletion.create_async(
                model=g4f.models.gpt_4,
                messages=[{"role": "user", "content": prompt}]
            ), timeout=15.0)
        return response
    except:
        return f"Analiza techniczna: {trend}. RSI na poziomie {rsi}."

async def get_market_data_pro(ticker):
    # Obsługa polskich spółek (GPW) i USA
    finnhub_ticker = ticker.replace('.WA', '.WAR')
    
    quote_url = f'https://finnhub.io/api/v1/quote?symbol={finnhub_ticker}&token={config.FINNHUB_KEY}'
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
        
        # Obliczanie RSI i Trendu
        rsi = 50
        trend = "SIDE ⚪"
        if r_candles.get('s') == 'ok':
            close_prices = r_candles['c']
            rsi = calculate_rsi(close_prices)
            if len(close_prices) >= 20:
                sma20 = pd.Series(close_prices).rolling(window=20).mean().iloc[-1]
                trend = "UP 🟢" if current_price > sma20 else "DOWN 🔴"

        # Sygnały specjalne
        status = "NEUTRAL"
        setup = None
        if trend == "UP 🟢" and rsi <= 38:
            status = "MOCNE KUPUJ 🔥"
            setup = {"sl": round(current_price * 0.96, 2), "tp": round(current_price * 1.08, 2)}
        elif rsi >= 75:
            status = "⚠️ GRZANE"

        # --- INTEGRACJA Z AI ---
        ai_comment = await verify_with_ai(ticker, current_price, int(rsi), trend)

        return {
            "symbol": ticker,
            "price": round(current_price, 2),
            "change": change,
            "rsi": int(rsi),
            "status": status,
            "trend": trend,
            "setup": setup,
            "news": ai_comment # Tutaj trafia profesjonalna opinia AI
        }
    except Exception as e:
        print(f"Błąd {ticker}: {e}")
        return None

async def get_combined_market_data(tickers):
    results = []
    for ticker in tickers:
        data = await get_market_data_pro(ticker)
        if data: results.append(data)
        await asyncio.sleep(1.0) # Przerwa dla stabilności AI i API
    return results

async def analyze_gold_pro():
    url = f'https://finnhub.io/api/v1/quote?symbol=XAU&token={config.FINNHUB_KEY}'
    try:
        r = requests.get(url, timeout=10).json()
        return {"symbol": "ZŁOTO", "price": r['c'], "change": round(r.get('dp', 0), 2)}
    except: return None
