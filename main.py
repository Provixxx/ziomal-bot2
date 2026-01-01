import discord
from discord.ext import tasks
import config
import analyzer
from datetime import datetime
import asyncio
from flask import Flask
from threading import Thread

# --- KOYEB KEEP ALIVE (OSZUSTWO DLA SERWERA) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot zyje i ma sie dobrze!"

def run():
    app.run(host='0.0.0.0', port=8000)

def keep_alive():
    t = Thread(target=run)
    t.start()
# -----------------------------------------------

intents = discord.Intents.default()
intents.message_content = True 
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"--- SYSTEM AKTYWNY: {client.user} ---")
    if not market_loop.is_running():
        market_loop.start()

@tasks.loop(minutes=15)
async def market_loop():
    channel = client.get_channel(config.DISCORD_CHANNEL_ID)
    if not channel: return

    try:
        # POBIERANIE DANYCH
        stocks = await analyzer.get_combined_market_data(config.WATCHLIST_TECH)
        gold = await analyzer.analyze_gold_pro()

        # Budujemy główny Embed (Spółki - zawsze)
        embed = discord.Embed(title="📊 CYKLICZNY RAPORT GIEŁDOWY", color=0x3498db, timestamp=datetime.now())

        # TABELKA USA
        usa = [s for s in stocks if not s['symbol'].endswith('.WA')]
        if usa:
            v_usa = "```ml\nWALOR      | CENA    | ZMIANA\n" + "-"*28 + "\n"
            for s in usa:
                ikona = "🟢" if s['change'] > 0 else "🔴"
                v_usa += f"{s['symbol'].ljust(10)} | {str(s['price']).ljust(7)} | {ikona} {s['change']}%\n"
            v_usa += "```"
            embed.add_field(name="🇺🇸 USA (Tech & AI)", value=v_usa, inline=False)

        # TABELKA GPW
        pl = [s for s in stocks if s['symbol'].endswith('.WA')]
        if pl:
            v_pl = "```ml\nWALOR      | CENA    | ZMIANA\n" + "-"*28 + "\n"
            for s in pl:
                ikona = "🟢" if s['change'] > 0 else "🔴"
                sym = s['symbol'].replace('.WA', '')
                v_pl += f"{sym.ljust(10)} | {str(s['price']).ljust(7)} | {ikona} {s['change']}%\n"
            v_pl += "```"
            embed.add_field(name="🇵🇱 GPW (Polska)", value=v_pl, inline=False)

        # --- SEKCJA ZŁOTA ---
        msg_content = "" 
        
        if gold:
            embed.color = 0xf1c40f if gold['action'] == "BUY" else 0xe74c3c
            embed.title = f"🟡 ALERT ZŁOTA: {gold['action']}!"
            
            sygnal_opis = "🚀 WZROSTY (Kupuj)" if gold['action'] == "BUY" else "🩸 SPADKI (Sprzedaj)"
            
            val_gold = (
                f"Cena: **{gold['price']} USD**\n"
                f"Zmiana: **{gold['change']}%**\n"
                f"Sygnał: **{sygnal_opis}**\n"
                f"Sugerowane TP: {gold['tp']} | SL: {gold['sl']}"
            )
            embed.add_field(name="🏆 SZCZEGÓŁOWA ANALIZA GOLD", value=val_gold, inline=False)
            
            if gold['urgent']:
                msg_content = "⚠️ **UWAGA! DUŻY RUCH NA ZŁOCIE!**"

        await channel.send(content=msg_content, embed=embed)

    except Exception as e:
        print(f"Błąd pętli: {e}")

# Uruchamiamy serwer WWW w tle, a potem bota
keep_alive()
client.run(config.DISCORD_TOKEN)
