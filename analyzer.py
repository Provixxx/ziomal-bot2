import yfinance as yf
import pandas as pd
import config
import requests
import g4f # Darmowe AI

async def get_market_data_pro(ticker):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="200d", auto_adjust=True)
        if df.empty or len(df) < 50: return None
            
        current_price = df['Close'].iloc[-1]
        open_price = df['Open'].iloc[-1]
        change = round(((current_price - open_price) / open_price) * 100, 2)
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = round((100 - (100 / (1 + gain / loss))).iloc[-1], 0)

        # SMA 50 - Filtr Trendu
        sma50 = df['Close'].rolling(window=50).mean().iloc[-1]
        trend = "UP 🟢" if current_price > sma50 else "DOWN 🔴"

        # Newsy
        news_headlines = [n['title'] for n in stock.news[:3]]
        news_str = " | ".join(news_headlines) if news_headlines else "Brak newsów"

        status = "NEUTRAL"
        setup = None
        # OKAZJA: Trend wzrostowy + niskie RSI (Korekta do wsparcia)
        if current_price > sma50 and rsi <= 35:
            status = "MOCNE KUPUJ 🔥"
            setup = {"sl": round(current_price * 0.97, 2), "tp": round(current_price * 1.10, 2)}
        elif rsi >= 75: 
            status = "⚠️ GRZANE"

        return {
            "symbol": ticker, "price": round(current_price, 2), "change": change,
            "rsi": int(rsi), "status": status, "trend": trend, "setup": setup, "news": news_str
        }
    except Exception as e:
        print(f"Błąd analizy {ticker}: {e}")
        return None

async def verify_with_ai(ticker, price, rsi, trend, news):
    """Sztuczna Inteligencja analizuje Newsy + Technikę"""
    prompt = f"Analiza {ticker}. Cena: {price}, RSI: {rsi}, Trend: {trend}. Najnowsze newsy: {news}. Czy to bezpieczny moment na zakup? Odpowiedz: TAK/NIE + krótkie uzasadnienie."
    try:
        response = await g4f.ChatCompletion.create_async(model=g4f.models.gpt_4, messages=[{"role": "user", "content": prompt}])
        return response
    except: return "AI niedostępne - sprawdź newsy sam."

async def get_combined_market_data(tickers):
    results = []
    for ticker in tickers:
        data = await get_market_data_pro(ticker)
        if data: results.append(data)
    return results

async def analyze_gold_pro():
    url = f'https://finnhub.io/api/v1/quote?symbol=XAU&token={config.FINNHUB_KEY}'
    try:
        r = requests.get(url, timeout=10).json()
        if 'c' not in r or r['c'] == 0: return None
        return {"symbol": "ZŁOTO", "price": r['c'], "change": round(r.get('dp', 0), 2), "urgent": abs(r.get('dp', 0)) > 0.7}
    except: return None
