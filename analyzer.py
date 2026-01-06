import pandas as pd
import config
import requests
import g4f
import asyncio
import time

# --- MATEMATYKA (RSI) ---
def calculate_rsi(prices, period=14):
    if len(prices) < period + 1: return 50
    delta = pd.Series(prices).diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    # Zabezpieczenie przed dzieleniem przez zero
    if loss.iloc[-1] == 0: return 100
    
    rs = gain.iloc[-1] / loss.iloc[-1]
    return int(round(100 - (100 / (1 + rs)), 0))

# --- AI (OPINIA) ---
async def get_ai_opinion(ticker, price, rsi, trend):
    # Krótki prompt dla szybkiej i konkretnej odpowiedzi do tabeli
    prompt = (f"Spółka {ticker}. Cena {price}, RSI {rsi}, Trend {trend}. "
              f"Napisz w MAX 3 słowach ocenę (np. 'Mocne kupuj', 'Czekaj', 'Sprzedaj').")
    try:
        response = await asyncio.wait_for(
            g4f.ChatCompletion.create_async(
                model=g4f.models.gpt_4,
                messages=[{"role": "user", "content": prompt}]
            ), timeout=8.0) # Krótki timeout, żeby nie blokować bota
        return response.strip()
    except:
        return "Brak opinii"

# --- GŁÓWNA FUNKCJA POBIERANIA ---
async def get_market_data_pro(ticker):
    # Finnhub wymaga '.WAR' dla Polski, ale my w configu mamy '.WA'
    finnhub_ticker = ticker.replace('.WA', '.WAR')
    
    # Pobieramy 35 dni historii (dla RSI i SMA20) + aktualną cenę
    end = int(time.time())
    start = end - (35 * 24 * 60 * 60)
    
    quote_url = f'https://finnhub.io/api/v1/quote?symbol={finnhub_ticker}&token={config.FINNHUB_KEY}'
    candles_url = f'https://finnhub.io/api/v1/stock/candle?symbol={finnhub_ticker}&resolution=D&from={start}&to={end}&token={config.FINNHUB_KEY}'

    try:
        r_quote = requests.get(quote_url, timeout=5).json()
        r_candles = requests.get(candles_url, timeout=5).json()

        # Sprawdzenie czy są dane
        if 'c' not in r_quote or r_quote['c'] == 0:
            return None
        if r_candles.get('s') != 'ok':
            # Jeśli brak świec, zwracamy podstawowe dane bez RSI
            return {
                "symbol": ticker, "price": r_quote['c'], "change": r_quote.get('dp', 0),
                "rsi": 50, "trend": "SIDE", "ai": "Brak danych hist."
            }

        # --- OBLICZENIA ---
        current_price = r_quote['c']
        change = round(r_quote.get('dp', 0), 2)
        close_prices = r_candles['c']
        
        # 1. RSI
        rsi = calculate_rsi(close_prices)
        
        # 2. Trend (SMA 20)
        sma20 = pd.Series(close_prices).rolling(window=20).mean().iloc[-1]
        trend = "UP 🟢" if current_price > sma20 else "DOWN 🔴"

        # 3. Zapytanie do AI (opcjonalne - można wyłączyć dla szybkości)
        ai_verdict = await get_ai_opinion(ticker, current_price, rsi, trend)

        return {
            "symbol": ticker.replace('.WA', ''), # Usuwamy .WA dla czystej tabeli
            "original_symbol": ticker, # Zachowujemy oryginał do logiki
            "price": current_price,
            "change": change,
            "rsi": rsi,
            "trend": trend,
            "ai": ai_verdict
        }
    except Exception as e:
        print(f"Błąd dla {ticker}: {e}")
        return None

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
