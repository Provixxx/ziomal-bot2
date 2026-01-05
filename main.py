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
    if not is_market_hours(): return

    channel = client.get_channel(config.DISCORD_CHANNEL_ID)
    if not channel: return

    try:
        stocks = await analyzer.get_combined_market_data(config.WATCHLIST_TECH)
        gold = await analyzer.analyze_gold_pro()

        # 1. TABELA (Standard)
        embed = discord.Embed(title="📊 RAPORT GIEŁDOWY (PRO + AI)", color=0x3498db, timestamp=datetime.now())
        for region, name in [("usa", "🇺🇸 USA Tech"), ("pl", "🇵🇱 GPW Polska")]:
            filtered = [s for s in stocks if (s['symbol'].endswith('.WA') if region == "pl" else not s['symbol'].endswith('.WA'))]
            if filtered:
                v = "```ml\nWALOR   | CENA    | TRND | RSI\n" + "-"*30 + "\n"
                for s in filtered:
                    sym = s['symbol'].replace('.WA', '')
                    v += f"{sym.ljust(7)} | {str(s['price']).ljust(7)} | {s['trend']} | {s['rsi']}\n"
                v += "```"
                embed.add_field(name=name, value=v, inline=False)
        await channel.send(embed=embed)

        # 2. ALERTY TOP PICK (Potwierdzone przez AI)
        for s in stocks:
            if s['status'] == "MOCNE KUPUJ 🔥":
                ai_verdict = await analyzer.verify_with_ai(s['symbol'], s['price'], s['rsi'], s['trend'], s['news'])
                
                alert = discord.Embed(title=f"🚀 AI TOP PICK: {s['symbol']}", color=0x00ff00)
                alert.add_field(name="🤖 WERDYKT AI", value=f"**{ai_verdict}**", inline=False)
                alert.add_field(name="🎯 WEJŚCIE", value=f"**{s['price']}**", inline=True)
                alert.add_field(name="🛑 STOP LOSS", value=f"**{s['setup']['sl']}**", inline=True)
                alert.add_field(name="💰 TAKE PROFIT", value=f"**{s['setup']['tp']}**", inline=True)
                await channel.send(content="@everyone ⚡ **Sygnał potwierdzony przez AI i Newsy!**", embed=alert)
         if gold:
            await channel.send(f"🟡 **ZŁOTO (XAU/USD)**: {gold['price']} USD ({gold['change']}%)")
             
    except Exception as e:
        print(f"Error: {e}")

@market_loop.before_loop
async def before_market_loop():
    await client.wait_until_ready()

# Start serwera WWW w osobnym wątku
keep_alive()
# Start bota
client.run(config.DISCORD_TOKEN)


