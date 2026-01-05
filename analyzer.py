import yfinance as yf
import pandas as pd
import config
import requests
import g4f
import asyncio

# --- WZMOCNIONA SESJA (Zalecane) ---
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache'
})

async def get_market_data_pro(ticker):
    try:
        # Przekazujemy sesję do Ticker
        stock = yf.Ticker(ticker, session=session)
        
        # Zmieniamy na 30d, aby zapytanie było "lżejsze" i bezpieczniejsze
        df = stock.history(period="30d", interval="1d", auto_adjust=True)
        
        if df.empty or len(df) < 15:
            print(f"Błąd: Yahoo zablokowało dane dla {ticker}")
            return None
            
        current_price = df['Close'].iloc[-1]
        prev_close = df['Close'].iloc[-2]
        change = round(((current_price - prev_close) / prev_close) * 100, 2)
        
        # OBLICZANIE RSI (14)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        # Zabezpieczenie przed dzieleniem przez zero
        avg_loss = loss.iloc[-1]
        if avg_loss == 0:
            rsi = 100
        else:
            rs = gain.iloc[-1] / avg_loss
            rsi = round(100 - (100 / (1 + rs)), 0)

        # SMA 20 (Szybszy trend dla technologii i GPW)
        sma20 = df['Close'].rolling(window=20).mean().iloc[-1]
        trend = "UP 🟢" if current_price > sma20 else "DOWN 🔴"

        # Newsy (pobierane tylko jeśli nie ma błędu)
        news_str = "Brak newsów"
        try:
            if stock.news:
                news_headlines = [n['title'] for n in stock.news[:3]]
                news_str = " | ".join(news_headlines)
        except: pass

        status = "NEUTRAL"
        setup = None
        # Strategia: Trend wzrostowy i korekta (RSI <= 38)
        if current_price > sma20 and rsi <= 38:
            status = "MOCNE KUPUJ 🔥"
            setup = {
                "sl": round(current_price * 0.96, 2), 
                "tp": round(current_price * 1.08, 2)
            }
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
            "news": news_str
        }
    except Exception as e:
        print(f"Krytyczny błąd pobierania {ticker}: {e}")
        return None

async def verify_with_ai(ticker, price, rsi, trend, news):
    prompt = f"Analiza {ticker}. Cena: {price}, RSI: {rsi}, Trend: {trend}. Newsy: {news}. Czy to dobry moment na wejście? Krótko: TAK/NIE + powód."
    try:
        # Dodany timeout, by AI nie blokowało bota
        response = await asyncio.wait_for(
            g4f.ChatCompletion.create_async(
                model=g4f.models.gpt_4, 
                messages=[{"role": "user", "content": prompt}]
            ), timeout=15.0)
        return response
    except: 
        return "AI nie odpowiedziało w terminie. Sprawdź RSI i trend samodzielnie."

async def get_combined_market_data(tickers):
    results = []
    for ticker in tickers:
        data = await get_market_data_pro(ticker)
        if data: 
            results.append(data)
        # Krótka pauza między tickerami, by nie prowokować Yahoo
        await asyncio.sleep(1) 
    return results

async def analyze_gold_pro():
    url = f'https://finnhub.io/api/v1/quote?symbol=XAU&token={config.FINNHUB_KEY}'
    try:
        r = requests.get(url, timeout=10).json()
        if 'c' not in r or r['c'] == 0: return None
        return {
            "symbol": "ZŁOTO", 
            "price": r['c'], 
            "change": round(r.get('dp', 0), 2)
        }
    except: 
        return None

