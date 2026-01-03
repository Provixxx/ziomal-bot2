import discord
from discord.ext import tasks
import config
import analyzer
from datetime import datetime, time
import pytz 
from flask import Flask
from threading import Thread
import asyncio

# --- KEEP ALIVE (Web Server) ---
app = Flask('')

@app.route('/')
def home():
    return f"System operacyjny: ONLINE. Czas: {datetime.now().strftime('%H:%M:%S')}"

def run():
    app.run(host='0.0.0.0', port=8000)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
# -------------------------------

intents = discord.Intents.default()
intents.message_content = True 
client = discord.Client(intents=intents)

def is_market_hours():
    """Zwraca True, jeśli giełda w PL lub USA pracuje"""
    tz_pl = pytz.timezone('Europe/Warsaw')
    now_dt = datetime.now(tz_pl)
    now = now_dt.time()
    weekday = now_dt.weekday() # 0=Pon, 6=Niedz

    if weekday >= 5: return False # Weekend

    # GPW: 09:00 - 17:05
    market_pl = time(9, 0) <= now <= time(17, 5)
    # USA: 15:30 - 22:05
    market_usa = time(15, 30) <= now <= time(22, 5)

    return market_pl or market_usa

@client.event
async def on_ready():
    print(f"--- ZALOGOWANO JAKO: {client.user} ---")
    if not market_loop.is_running():
        market_loop.start()

@tasks.loop(minutes=15)
async def market_loop():
    # 1. Sprawdzamy godziny pracy
    if not is_market_hours():
        print(f"[{datetime.now().strftime('%H:%M')}] Giełda zamknięta. Czuwanie...")
        return

    channel = client.get_channel(config.DISCORD_CHANNEL_ID)
    if not channel:
        print("Błąd: Nie znaleziono kanału ID")
        return

    try:
        print("Pobieranie danych giełdowych...")
        stocks = await analyzer.get_combined_market_data(config.WATCHLIST_TECH)
        gold = await analyzer.analyze_gold_pro()

        if not stocks and not gold: 
            return

        embed = discord.Embed(title="📊 RAPORT GIEŁDOWY (LIVE)", color=0x3498db, timestamp=datetime.now())

        # SEKCJA USA
        usa = [s for s in stocks if not s['symbol'].endswith('.WA')]
        if usa:
            v_usa = "```ml\nWALOR   | CENA    | ZM    | RSI\n" + "-"*31 + "\n"
            for s in usa:
                ikona = "+" if s['change'] > 0 else "-"
                v_usa += f"{s['symbol'].ljust(7)} | {str(s['price']).ljust(7)} | {ikona}{str(abs(s['change'])).ljust(4)}% | {s['rsi']}\n"
            v_usa += "```"
            embed.add_field(name="🇺🇸 USA Tech", value=v_usa, inline=False)

        # SEKCJA GPW
        pl = [s for s in stocks if s['symbol'].endswith('.WA')]
        if pl:
            v_pl = "```ml\nWALOR   | CENA    | ZM    | RSI\n" + "-"*31 + "\n"
            for s in pl:
                ikona = "+" if s['change'] > 0 else "-"
                sym = s['symbol'].replace('.WA', '')
                v_pl += f"{sym.ljust(7)} | {str(s['price']).ljust(7)} | {ikona}{str(abs(s['change'])).ljust(4)}% | {s['rsi']}\n"
            v_pl += "```"
            embed.add_field(name="🇵🇱 GPW Polska", value=v_pl, inline=False)

        # ALERTY
        alert_msg = ""
        if gold:
            val_gold = f"Cena: **{gold['price']}** | Zmiana: **{gold['change']}%** | {gold['action']}"
            embed.add_field(name="🟡 GOLD ALERT", value=val_gold, inline=False)
            if gold['urgent']: alert_msg += "⚠️ **RUCH NA ZŁOCIE!** "

        opportunities = [s for s in stocks if s['status'] != "NEUTRAL"]
        if opportunities:
            op_text = ""
            for s in opportunities:
                op_text += f"• **{s['symbol']}**: {s['status']} (RSI: {s['rsi']})\n"
            embed.add_field(name="⚡ SYGNAŁY TECHNICZNE", value=op_text, inline=False)
            alert_msg += " | ⚡ **OKAZJA**"

        await channel.send(content=alert_msg, embed=embed)

    except Exception as e:
        print(f"CRITICAL ERROR w pętli: {e}")

@market_loop.before_loop
async def before_market_loop():
    await client.wait_until_ready()

# Start serwera WWW w osobnym wątku
keep_alive()
# Start bota
client.run(config.DISCORD_TOKEN)
