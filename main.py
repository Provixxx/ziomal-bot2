import discord
from discord.ext import tasks
import config
import analyzer
from datetime import datetime, time
import pytz # Do obsługi czasu polskiego
from flask import Flask
from threading import Thread
import asyncio

# --- KEEP ALIVE ---
app = Flask('')
@app.route('/')
def home(): return "Bot czuwa! Uzyj UptimeRobot, aby mnie nie uspic."
def run(): app.run(host='0.0.0.0', port=8000)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
# ------------------

intents = discord.Intents.default()
intents.message_content = True 
client = discord.Client(intents=intents)

def is_market_hours():
    """Sprawdza, czy giełda w USA lub Polsce działa"""
    tz_pl = pytz.timezone('Europe/Warsaw')
    now = datetime.now(tz_pl).time()
    weekday = datetime.now(tz_pl).weekday() # 0=Pon, 6=Niedz

    if weekday >= 5: return False # Weekend - cisza

    # GPW: 09:00 - 17:10
    market_pl = time(9, 0) <= now <= time(17, 10)
    # USA: 15:30 - 22:15
    market_usa = time(15, 30) <= now <= time(22, 15)

    return market_pl or market_usa

@client.event
async def on_ready():
    print(f"--- SYSTEM AKTYWNY: {client.user} ---")
    if not market_loop.is_running():
        market_loop.start()

@tasks.loop(minutes=15)
async def market_loop():
    channel = client.get_channel(config.DISCORD_CHANNEL_ID)
    if not channel: return

    # 1. Sprawdzamy czy giełda działa. Jeśli nie - przerywamy pętlę w tym obiegu.
    if not is_market_hours():
        print("Giełda zamknięta - tryb czuwania (nie wysyłam raportu).")
        return

    try:
        stocks = await analyzer.get_combined_market_data(config.WATCHLIST_TECH)
        gold = await analyzer.analyze_gold_pro()

        # Jeśli brak danych (np. święto), nie wysyłaj pustego
        if not stocks and not gold: return

        embed = discord.Embed(title="📊 RAPORT GIEŁDOWY (LIVE)", color=0x3498db, timestamp=datetime.now())

        # TABELKA USA
        usa = [s for s in stocks if not s['symbol'].endswith('.WA')]
        if usa:
            v_usa = "```ml\nWALOR   | CENA    | ZM    | RSI\n" + "-"*31 + "\n"
            for s in usa:
                ikona = "+" if s['change'] > 0 else "-"
                v_usa += f"{s['symbol'].ljust(7)} | {str(s['price']).ljust(7)} | {ikona}{str(abs(s['change'])).ljust(4)}% | {s['rsi']}\n"
            v_usa += "```"
            embed.add_field(name="🇺🇸 USA Tech", value=v_usa, inline=False)

        # TABELKA GPW
        pl = [s for s in stocks if s['symbol'].endswith('.WA')]
        if pl:
            v_pl = "```ml\nWALOR   | CENA    | ZM    | RSI\n" + "-"*31 + "\n"
            for s in pl:
                ikona = "+" if s['change'] > 0 else "-"
                sym = s['symbol'].replace('.WA', '')
                v_pl += f"{sym.ljust(7)} | {str(s['price']).ljust(7)} | {ikona}{str(abs(s['change'])).ljust(4)}% | {s['rsi']}\n"
            v_pl += "```"
            embed.add_field(name="🇵🇱 GPW Polska", value=v_pl, inline=False)

        # ALERTY (Gold + RSI Stocks)
        alert_msg = ""
        
        # Alert Złota
        if gold:
            val_gold = f"Cena: **{gold['price']}** | Zmiana: **{gold['change']}%** | {gold['action']}"
            embed.add_field(name="🟡 GOLD ALERT", value=val_gold, inline=False)
            if gold['urgent']: alert_msg += "⚠️ **RUCH NA ZŁOCIE!** "

        # Alerty RSI (Dla akcji)
        opportunities = [s for s in stocks if s['status'] != "NEUTRAL"]
        if opportunities:
            op_text = ""
            for s in opportunities:
                op_text += f"• **{s['symbol']}**: {s['status']} (RSI: {s['rsi']})\n"
            embed.add_field(name="⚡ SYGNAŁY TECHNICZNE", value=op_text, inline=False)
            alert_msg += " | ⚡ **OKAZJA NA RYNKU!**"

        await channel.send(content=alert_msg, embed=embed)

    except Exception as e:
        print(f"CRITICAL ERROR w pętli: {e}")

keep_alive()
client.run(config.DISCORD_TOKEN)
