import yfinance as yf
import pandas as pd
import config
import requests

async def get_market_data_pro(ticker):
    """Pobiera dane PRO: Cena, Zmiana, RSI, Trend"""
    try:
        stock = yf.Ticker(ticker)
        # Pobieramy 200 dni, żeby policzyć średnią (Trend) i RSI
        df = stock.history(period="200d")
        
        if df.empty or len(df) < 15:
            return None
            
        current_price = df['Close'].iloc[-1]
        open_price = df['Open'].iloc[-1]
        
        # 1. Obliczanie Zmiany % (Intraday)
        change = round(((current_price - open_price) / open_price) * 100, 2) if open_price != 0 else 0
        
        # 2. Obliczanie RSI (14 dni) - Czy jest tanio?
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi_raw = 100 - (100 / (1 + rs))
        rsi = round(rsi_raw.iloc[-1], 0)

        # 3. Status RSI
        status = "NEUTRAL"
        if rsi >= 70: status = "⚠️ GRZANE"
        elif rsi <= 30: status = "💎 OKAZJA"

        return {
            "symbol": ticker, 
            "price": round(current_price, 2), 
            "change": change,
            "rsi": int(rsi),
            "status": status
        }
    except Exception as e:
        print(f"Błąd analizy {ticker}: {e}")
        return None

async def get_combined_market_data(tickers):
    results = []
    for ticker in tickers:
        data = await get_market_data_pro(ticker)
        if data:
            results.append(data)
    return results

async def analyze_gold_pro():
    """Złoto z Finnhub - bez zmian logicznych, tylko obsługa błędów"""
    url = f'https://finnhub.io/api/v1/quote?symbol=XAU&token={config.FINNHUB_KEY}'
    try:
        r = requests.get(url, timeout=10).json()
        if 'c' not in r or r['c'] == 0: return None
        
        current_price = r['c']
        change_pct = r.get('dp', 0)
        
        action = "NEUTRAL"
        if change_pct <= -0.5: action = "BUY" # Zwiększyłem lekko próg, żeby nie spamował
        elif change_pct >= 0.5: action = "SELL"
        
        if action == "NEUTRAL": return None

        return {
            "symbol": "ZŁOTO (XAU)", 
            "price": current_price, 
            "action": action,
            "change": round(change_pct, 2), 
            "urgent": abs(change_pct) > 1.0,
            "sl": round(current_price * 0.99 if action == "BUY" else current_price * 1.01, 2),
            "tp": round(current_price * 1.015 if action == "BUY" else current_price * 0.985, 2)
        }
    except:
        return None
