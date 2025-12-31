import requests
import pandas as pd
import config
import io

async def get_stooq_data_safe(ticker):
    # Udajemy przeglądarkę Chrome na Windowsie
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        # Pobieramy CSV jako surowy tekst
        url = f"https://stooq.pl/q/l/?s={ticker}&f=sd2t2ohlcv&h&e=csv"
        response = requests.get(url, headers=headers, timeout=15)
        pprint(f"DEBUG {ticker}: Status {response.status_code}")
if response.status_code != 200:
    print(f"DEBUG {ticker}: Treść błędu: {response.text[:100]}")
        
        if response.status_code != 200:
            print(f"Błąd Stooq {ticker}: {response.status_code}")
            return None

        # Zamiana tekstu na DataFrame (tabelkę)
        df = pd.read_csv(io.StringIO(response.text))
        
        if df.empty or 'Close' not in df.columns:
            return None
            
        price = float(df['Close'].iloc[0])
        open_p = float(df['Open'].iloc[0])
        
        if pd.isna(price) or price <= 0:
            return None

        change = round(((price - open_p) / open_p) * 100, 2) if open_p != 0 else 0
        
        return {"symbol": ticker, "price": price, "change": change}
    except Exception as e:
        print(f"Wyjątek dla {ticker}: {e}")
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

