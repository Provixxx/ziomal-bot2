import discord
from discord.ext import tasks
import config
import analyzer
from datetime import datetime, time
import pytz 
from flask import Flask
from threading import Thread
import asyncio

# --- KEEP ALIVE ---
app = Flask('')

@app.route('/')
def home():
    return f"System ONLINE. Czas: {datetime.now().strftime('%H:%M:%S')}"

def run():
    app.run(host='0.0.0.0', port=8000)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- KONFIGURACJA BOTA ---
intents = discord.Intents.default()
intents.message_content = True 
client = discord.Client(intents=intents)

def is_market_hours():
    # Sprawdza czy giełda działa (9-17 PL, 15:30-22 USA) + weekendy OFF
    tz_pl = pytz.timezone('Europe/Warsaw')
    now_dt = datetime.now(tz_pl)
    if now_dt.weekday() >= 5: return False # Weekend
    now = now_dt.time()
    market_pl = time(9, 0) <= now <= time(17, 15)
    market_usa = time(15, 30) <= now <= time(22, 15)
    return market_pl or market_usa

def create_pro_table(data_list):
    # Tworzy tabelę ASCII idealnie wyrównaną
    # Używamy bloku codeblock dla czcionki o stałej szerokości
    if not data_list: return "Brak danych."
    
    # Nagłówek
    table = "```text\n"
    table += f"{'WALOR':<7} | {'CENA':>8} | {'ZM':>7} | {'RSI':>3}\n"
    table += "-" * 35 + "\n"
    
    # Wiersze
    for item in data_list:
        # Formatowanie ceny i zmiany
        price_str = f"{item['price']:.2f}"
        change_str = f"{item['change']:+.2f}%"
        
        table += f"{item['symbol']:<7} | {price_str:>8} | {change_str:>7} | {item['rsi']:>3}\n"
    
    table += "```"
    return table

@client.event
async def on_ready():
    print(f"--- ZALOGOWANO: {client.user} ---")
    if not market_loop.is_running():
        market_loop.start()

@tasks.loop(minutes=15)
async def market_loop():
    # if not is_market_hours(): return  <-- ODKOMENTUJ TO W PRODUKCJI, TERAZ TESTUJEMY

    channel = client.get_channel(config.DISCORD_CHANNEL_ID)
    if not channel: 
        print("Błąd: Nie znaleziono kanału ID w configu.")
        return

    try:
        # 1. Pobieranie danych
        print("Pobieram dane...")
        all_data = await analyzer.get_combined_market_data(config.WATCHLIST_TECH)
        gold = await analyzer.analyze_gold_pro()

        # 2. Sortowanie (USA vs PL)
        # Rozpoznajemy PL po tym, że w configu (original_symbol) było '.WA'
        usa_stocks = [s for s in all_data if '.WA' not in s['original_symbol']]
        pl_stocks = [s for s in all_data if '.WA' in s['original_symbol']]

        # 3. Budowanie Raportu (Embed)
        embed = discord.Embed(title="📊 RAPORT GIEŁDOWY (PRO + AI)", color=0x2b2d31, timestamp=datetime.now())
        
        if usa_stocks:
            embed.add_field(name="🇺🇸 USA Tech", value=create_pro_table(usa_stocks), inline=False)
        
        if pl_stocks:
            embed.add_field(name="🇵🇱 GPW Polska", value=create_pro_table(pl_stocks), inline=False)
            
        # 4. Sekcja AI / Sygnały
        signals_text = ""
        for s in all_data:
            # Warunki na sygnał
            if s['rsi'] <= 35:
                signals_text += f"🟢 **{s['symbol']}**: OKAZJA (RSI {s['rsi']}) - AI: *{s['ai']}*\n"
            elif s['rsi'] >= 80:
                signals_text += f"⚠️ **{s['symbol']}**: GRZANE (RSI {s['rsi']}) - AI: *{s['ai']}*\n"
        
        if signals_text:
            embed.add_field(name="⚡ SYGNAŁY TECHNICZNE", value=signals_text, inline=False)

        # 5. Złoto
        if gold:
            footer_text = f"🟡 ZŁOTO: {gold['price']} USD ({gold['change']}%)"
            embed.set_footer(text=footer_text)

        await channel.send(embed=embed)
        print("Raport wysłany.")

    except Exception as e:
        print(f"Błąd krytyczny w pętli: {e}")

@market_loop.before_loop
async def before_market_loop():
    await client.wait_until_ready()

keep_alive()
client.run(config.DISCORD_TOKEN)
