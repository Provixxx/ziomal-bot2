import requests
import pandas as pd
import config
import io
import yfinance as yf

async def get_stooq_data_safe(ticker):
    try:
        # Yahoo Finance pobierze dane dla CDR.WA, KGH.WA itd.
        stock = yf.Ticker(ticker)
        # Pobieramy historię z ostatniego dnia
        df = stock.history(period="1d")
        
        if df.empty:
            return None
            
        price = df['Close'].iloc[-1]
        open_p = df['Open'].iloc[-1]
        
        change = round(((price - open_p) / open_p) * 100, 2) if open_p != 0 else 0
        
        return {"symbol": ticker, "price": round(price, 2), "change": change}
    except Exception as e:
        print(f"Błąd Yahoo dla {ticker}: {e}")
        return None

async def get_combined_market_data(tickers):
    results = []
    for ticker in tickers:
        try:
            if ticker.endswith('.WA'):
                data = await get_stooq_data_safe(ticker)
                if data: results.append(data)
            else:
                # USA - Finnhub
                url = f'https://finnhub.io/api/v1/quote?symbol={ticker}&token={config.FINNHUB_KEY}'
                r = requests.get(url, timeout=10).json()
                if 'c' in r and r['c'] != 0:
                    results.append({"symbol": ticker, "price": r['c'], "change": r.get('dp', 0)})
        except Exception as e:
            print(f"Błąd przy {ticker}: {e}")
    return results

async def analyze_gold_pro():
    url = f'https://finnhub.io/api/v1/quote?symbol=XAU&token={config.FINNHUB_KEY}'
    try:
        r = requests.get(url, timeout=10).json()
        if 'c' not in r or r['c'] == 0: return None
        price = r['c']
        change = r.get('dp', 0)
        
        action = "NEUTRAL"
        if change <= -0.3: action = "BUY"
        elif change >= 0.3: action = "SELL"
        
        if action == "NEUTRAL": return None

        return {
            "symbol": "ZŁOTO (XAU)", "price": price, "action": action, "change": round(change, 2),
            "urgent": abs(change) > 0.8,
            "sl": round(price * 0.99 if action == "BUY" else price * 1.01, 2),
            "tp": round(price * 1.015 if action == "BUY" else price * 0.985, 2)
        }
    except: return None

