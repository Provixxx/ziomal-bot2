import yfinance as yf
import pandas as pd
import config
import requests

async def get_stooq_data_safe(ticker):
    """Pobiera dane dla GPW i USA korzystając z biblioteki yfinance"""
    try:
        stock = yf.Ticker(ticker)
        # Pobieramy historię z ostatniego dnia, aby mieć pewność danych
        df = stock.history(period="1d")
        
        if df.empty:
            print(f"DEBUG: Brak danych dla {ticker}")
            return None
            
        price = df['Close'].iloc[-1]
        open_p = df['Open'].iloc[-1]
        
        # Obliczanie procentowej zmiany
        change = round(((price - open_p) / open_p) * 100, 2) if open_p != 0 else 0
        
        return {
            "symbol": ticker, 
            "price": round(price, 2), 
            "change": change
        }
    except Exception as e:
        print(f"Błąd Yahoo dla {ticker}: {e}")
        return None

async def get_combined_market_data(tickers):
    """Zbiera dane dla wszystkich tickerów z Twojej listy"""
    results = []
    for ticker in tickers:
        data = await get_stooq_data_safe(ticker)
        if data:
            results.append(data)
    return results

async def analyze_gold_pro():
    """Analiza złota - Finnhub działa dobrze dla metali, zostawiamy go"""
    url = f'https://finnhub.io/api/v1/quote?symbol=XAU&token={config.FINNHUB_KEY}'
    try:
        r = requests.get(url, timeout=10).json()
        if 'c' not in r or r['c'] == 0:
            return None
            
        current_price = r['c']
        change_pct = r.get('dp', 0)
        
        # Logika alertów złota
        action = "NEUTRAL"
        if change_pct <= -0.3: action = "BUY"
        elif change_pct >= 0.3: action = "SELL"
        
        if action == "NEUTRAL":
            return None

        return {
            "symbol": "ZŁOTO (XAU)", 
            "price": current_price, 
            "action": action,
            "change": round(change_pct, 2), 
            "urgent": abs(change_pct) > 0.8,
            "sl": round(current_price * 0.99 if action == "BUY" else current_price * 1.01, 2),
            "tp": round(current_price * 1.015 if action == "BUY" else current_price * 0.985, 2)
        }
    except:
        return None
