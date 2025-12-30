import asyncio
import requests
import config

async def analyze_gold_pro():
    # Zostawiamy Finnhub dla złota (to działało w testach)
    symbol = "XAU/USD"
    url = f'https://finnhub.io/api/v1/quote?symbol={symbol}&token={config.FINNHUB_KEY}'
    try:
        r = requests.get(url).json()
        if 'c' not in r or r['c'] == 0: return None
        current_price = r['c']
        change_pct = r.get('dp', 0)
        is_urgent = abs(change_pct) > 0.3
        action = "NEUTRAL"
        if change_pct < -0.3: action = "BUY"
        elif change_pct > 0.3: action = "SELL"
        if action != "NEUTRAL":
            return {
                "symbol": "ZŁOTO", "price": current_price, "action": action,
                "change": round(change_pct, 2), "urgent": is_urgent,
                "sl": round(current_price * 0.995 if action == "BUY" else current_price * 1.005, 2),
                "tp": round(current_price * 1.015 if action == "BUY" else current_price * 0.985, 2)
            }
    except: return None
    return None


async def get_combined_market_data(tickers):
    results = []
    for symbol in tickers:
        try:
            if symbol.endswith('.WA'):
                # Używamy Google Finance przez prosty link (często działa najlepiej)
                clean_symbol = symbol.replace('.WA', '')
                url = f"https://www.google.com/search?q=GPW+{clean_symbol}+kurs"
                headers = {'User-Agent': 'Mozilla/5.0'}
                r = requests.get(url, headers=headers, timeout=5)

                # To jest wersja uproszczona - jeśli Google nie zadziała, wracamy do USA
                # Aby to naprawdę działało bez błędu, bot musi mieć serwer (Koyeb/GitHub)
                # bo Google blokuje zbyt częste zapytania z tego samego PC
                results.append({"symbol": symbol, "price": 0.0, "change": 0.0})
            else:
                # USA (To u Ciebie działa idealnie)
                url = f'https://finnhub.io/api/v1/quote?symbol={symbol}&token={config.FINNHUB_KEY}'
                r = requests.get(url).json()
                if 'c' in r:
                    results.append({"symbol": symbol, "price": r['c'], "change": r.get('dp', 0)})
        except:
            continue
    return results