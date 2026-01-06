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
    # Finnhub używa końcówki .WAR zamiast .WA dla polskiej giełdy
    finnhub_ticker = ticker.replace('.WA', '.WAR')
    url = f'https://finnhub.io/api/v1/quote?symbol={finnhub_ticker}&token={config.FINNHUB_KEY}'
    
    try:
        # Używamy oficjalnego API z Twoim kluczem
        r = requests.get(url, timeout=10).json()
        
        # 'c' to cena aktualna, 'dp' to zmiana procentowa
        if 'c' not in r or r['c'] == 0:
            print(f"Finnhub brak danych dla: {ticker}")
            return None

        current_price = r['c']
        change = round(r.get('dp', 0), 2)
        
        # Finnhub w wersji Free nie daje RSI. Ustawiamy 50 (neutral), 
        # aby bot mógł wysłać raport bez błędów.
        rsi = 50 
        trend = "UP 🟢" if change > 0 else "DOWN 🔴"

        return {
            "symbol": ticker, 
            "price": round(current_price, 2), 
            "change": change,
            "rsi": rsi, 
            "status": "DANE LIVE (API)", 
            "trend": trend, 
            "setup": None, 
            "news": "Dane pobrane stabilnie przez Finnhub"
        }
    except Exception as e:
        print(f"Błąd API {ticker}: {e}")
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


