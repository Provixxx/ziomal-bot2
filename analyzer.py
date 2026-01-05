import yfinance as yf
import pandas as pd
import config
import requests
import g4f

async def get_market_data_pro(ticker):
    try:
        stock = yf.Ticker(ticker)
        # Pobieramy 50 dni, by mieć dane do SMA50 i RSI
        df = stock.history(period="60d", auto_adjust=True)
        if df.empty or len(df) < 50: 
            print(f"Brak danych historycznych dla: {ticker}")
            return None
            
        current_price = df['Close'].iloc[-1]
        open_price = df['Open'].iloc[-1]
        change = round(((current_price - open_price) / open_price) * 100, 2)
        
        # RSI 14
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = round(100 - (100 / (1 + rs.iloc[-1])), 0)

        # SMA 50
        sma50 = df['Close'].rolling(window=50).mean().iloc[-1]
        trend = "UP 🟢" if current_price > sma50 else "DOWN 🔴"

        # Newsy
        news_headlines = [n['title'] for n in stock.news[:3]]
        news_str = " | ".join(news_headlines) if news_headlines else "Brak newsów"

        status = "NEUTRAL"
        setup = None
        # Strategia: Trend wzrostowy + RSI wyprzedane
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
    prompt = f"Analiza {ticker}. Cena: {price}, RSI: {rsi}, Trend: {trend}. Newsy: {news}. Czy kupować? TAK/NIE + krótko dlaczego."
    try:
        response = await g4f.ChatCompletion.create_async(
            model=g4f.models.gpt_4, 
            messages=[{"role": "user", "content": prompt}]
        )
        return response
    except: 
        return "AI zajęte - analiza techniczna sugeruje okazję."

async def get_combined_market_data(tickers):
    results = []
    for ticker in tickers:
        data = await get_market_data_pro(ticker)
        if data: 
            results.append(data)
    return results

async def analyze_gold_pro():
    url = f'https://finnhub.io/api/v1/quote?symbol=XAU&token={config.FINNHUB_KEY}'
    try:
        r = requests.get(url, timeout=10).json()
        if 'c' not in r or r['c'] == 0: return None
        return {"symbol": "ZŁOTO", "price": r['c'], "change": round(r.get('dp', 0), 2)}
    except: 
        return None
