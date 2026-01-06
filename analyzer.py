import pandas as pd
import config
import requests
import g4f
import asyncio
import time

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1: return 50
    delta = pd.Series(prices).diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    if loss.iloc[-1] == 0: return 100
    rs = gain.iloc[-1] / loss.iloc[-1]
    return int(round(100 - (100 / (1 + rs)), 0))

async def get_ai_opinion(ticker, price, rsi, trend):
    # Prompt ustawiony pod profesjonalny, giełdowy język
    prompt = (f"Jako analityk oceń {ticker}: Cena {price}, RSI {rsi}, Trend {trend}. "
              f"Napisz werdykt w 3-5 słowach (np. 'Silna akumulacja', 'Ryzyko korekty').")
    try:
        response = await asyncio.wait_for(
            g4f.ChatCompletion.create_async(
                model=g4f.models.gpt_4,
                messages=[{"role": "user", "content": prompt}]
            ), timeout=8.0)
        return response.strip()
    except:
        return "Neutralny sentyment"

async def get_market_data_pro(ticker):
    # Konwersja dla Finnhub (CDR.WA -> CDR.WAR)
    finnhub_ticker = ticker.replace('.WA', '.WAR')
    end = int(time.time())
    start = end - (35 * 24 * 60 * 60)
    
    q_url = f'https://finnhub.io/api/v1/quote?symbol={finnhub_ticker}&token={config.FINNHUB_KEY}'
    c_url = f'https://finnhub.io/api/v1/stock/candle?symbol={finnhub_ticker}&resolution=D&from={start}&to={end}&token={config.FINNHUB_KEY}'

    try:
        r_q = requests.get(q_url, timeout=5).json()
        r_c = requests.get(c_url, timeout=5).json()

        if 'c' not in r_q or r_q['c'] == 0: return None

        price = r_q['c']
        change = round(r_q.get('dp', 0), 2)
        rsi = 50
        trend = "SIDE ⚪"

        if r_c.get('s') == 'ok':
            close_prices = r_c['c']
            rsi = calculate_rsi(close_prices)
            sma20 = pd.Series(close_prices).rolling(window=20).mean().iloc[-1]
            trend = "UP 🟢" if price > sma20 else "DOWN 🔴"

        ai_verdict = await get_ai_opinion(ticker, price, rsi, trend)

        return {
            "symbol": ticker.replace('.WA', ''),
            "orig_symbol": ticker,
            "price": price,
            "change": change,
            "rsi": rsi,
            "trend": trend,
            "ai": ai_verdict
        }
    except: return None

async def get_combined_market_data(tickers):
    tasks = [get_market_data_pro(t) for t in tickers]
    results = await asyncio.gather(*tasks)
    return [r for r in results if r is not None]

async def analyze_gold_pro():
    try:
        url = f'https://finnhub.io/api/v1/quote?symbol=XAU&token={config.FINNHUB_KEY}'
        r = requests.get(url, timeout=5).json()
        return {"price": r['c'], "change": round(r.get('dp', 0), 2)}
    except: return None
