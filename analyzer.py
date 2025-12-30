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


async def get_stooq_data_safe(ticker):
    """Pobiera dane ze Stooq z zabezpieczeniem przed banem"""
    # Usuwamy .WA jeśli występuje, Stooq w CSV tego nie lubi
    symbol = ticker.replace('.WA', '').lower()
    url = f"https://stooq.pl/q/l/?s={symbol}&f=sd2t2ohlcv&h&e=csv"

    headers = {'User-Agent': random.choice(USER_AGENTS)}

    try:
        # Losowe opóźnienie 1-3 sekundy, żeby nie bombardować serwera
        await asyncio.sleep(random.uniform(1, 3))

        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            if len(lines) > 1:
                data = lines[1].split(',')
                # Format Stooq CSV: Symbol,Date,Time,Open,High,Low,Close,Volume
                price = float(data[6])
                # Obliczamy przybliżoną zmianę (uproszczone)
                return {"symbol": ticker, "price": price, "change": 0.0}
    except Exception as e:
        print(f"Błąd Stooq dla {ticker}: {e}")
    return None


async def get_combined_market_data(tickers):
    results = []
    for ticker in tickers:
        # Jeśli to polska spółka, idź przez bezpieczny Stooq
        if ticker.endswith('.WA'):
            data = await get_stooq_data_safe(ticker)
            if data:
                results.append(data)
        else:
                # USA (To u Ciebie działa idealnie)
                url = f'https://finnhub.io/api/v1/quote?symbol={symbol}&token={config.FINNHUB_KEY}'
                r = requests.get(url).json()
                if 'c' in r:
                    results.append({"symbol": symbol, "price": r['c'], "change": r.get('dp', 0)})
        except:
            pass

    return results
