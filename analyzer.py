import config 
import requests
import pandas as pd

async def analyze_gold_pro():
    """
    Zwraca dane TYLKO, gdy dzieje się coś ciekawego (zmiana > 0.3% lub < -0.3%).
    W przeciwnym razie zwraca None (cisza).
    """
    symbol = "XAU/USD"
    # Używamy Finnhub (działa stabilnie dla złota)
    url = f'https://finnhub.io/api/v1/quote?symbol=XAU&token={config.FINNHUB_KEY}'
    
    try:
        r = requests.get(url).json()
        if 'c' not in r or r['c'] == 0: 
            return None
            
        current_price = r['c']
        change_pct = r.get('dp', 0)
        
        # Logika sygnałów - ustawiona czułość na 0.3%
        action = "NEUTRAL"
        if change_pct <= -0.3: action = "BUY"
        elif change_pct >= 0.3: action = "SELL"
        
        # Jeśli akcja jest NEUTRALNA, zwracamy None (bot nie wyśle powiadomienia o złocie)
        if action == "NEUTRAL":
            return None

        is_urgent = abs(change_pct) > 0.8  # Powyżej 0.8% to już duży ruch
        
        return {
            "symbol": "ZŁOTO (XAU)", 
            "price": current_price, 
            "action": action,
            "change": round(change_pct, 2), 
            "urgent": is_urgent,
            "sl": round(current_price * 0.99 if action == "BUY" else current_price * 1.01, 2),
            "tp": round(current_price * 1.015 if action == "BUY" else current_price * 0.985, 2)
        }
    except Exception as e:
        print(f"Błąd analizy złota: {e}")
        return None

async def get_stooq_data_safe(ticker):
    # TO JEST KLUCZ: Nagłówek udający przeglądarkę
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        url = f"https://stooq.pl/q/l/?s={ticker}&f=sd2t2ohlcv&h&e=csv"
        # Wysyłamy zapytanie z nagłówkiem
        response = requests.get(url, headers=headers, timeout=10)
        
        from io import StringIO
        import pandas as pd
        
        df = pd.read_csv(StringIO(response.text))
        
        if df.empty or 'Close' not in df.columns or pd.isna(df['Close'].iloc[0]):
            print(f"Brak danych dla {ticker}")
            return None
            
        price = float(df['Close'].iloc[0])
        open_p = float(df['Open'].iloc[0])
        change = round(((price - open_p) / open_p) * 100, 2) if open_p != 0 else 0
        
        return {"symbol": ticker, "price": price, "change": change}
    except Exception as e:
        print(f"Błąd Stooq dla {ticker}: {e}")
        return None

async def get_combined_market_data(tickers):
    results = []
    for ticker in tickers:
        try:
            # Jeśli to polska spółka, idź przez bezpieczny Stooq
            if ticker.endswith('.WA'):
                data = await get_stooq_data_safe(ticker)
                if data:
                    results.append(data)
            else:
                # USA
                url = f'https://finnhub.io/api/v1/quote?symbol={ticker}&token={config.FINNHUB_KEY}'
                r = requests.get(url).json()
                if 'c' in r and r['c'] != 0:
                    results.append({"symbol": ticker, "price": r['c'], "change": r.get('dp', 0)})
        except Exception as e:
            print(f"Błąd przy pobieraniu {ticker}: {e}")
            continue 

    return results



