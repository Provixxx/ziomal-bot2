import discord
from discord.ext import tasks
import config
import analyzer
import asyncio
from datetime import datetime
from flask import Flask
from threading import Thread

# --- SERWER KEEP ALIVE ---
app = Flask('')
@app.route('/')
def home(): return "SYSTEM ONLINE"
def run(): app.run(host='0.0.0.0', port=8000)
Thread(target=run, daemon=True).start()

# --- BOT DISCORD ---
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# Funkcja tworząca TABELĘ ANSI (Kolory + Wyrównanie)
def create_ansi_table(data_list):
    # Nagłówek: Biały tekst, wyrównany
    table = "```ansi\n"
    table += "[1;37mWALOR   |   CENA   |   ZM%   | RSI[0m\n"
    table += "------------------------------------\n"
    
    for d in data_list:
        # Kolor ZMIANY (Zielony / Czerwony)
        if d['change'] >= 0:
            color = "[0;32m" # Green
            sign = "+"
        else:
            color = "[0;31m" # Red
            sign = ""
        
        # Kolor RSI (Niebieski/Cyjan)
        rsi_color = "[0;36m"
        
        # Formatowanie wiersza
        # :<7 (do lewej), :>8 (do prawej)
        row = f"[1;37m{d['symbol']:<7}[0m | [1;37m{d['price']:>8.2f}[0m | {color}{d['change']:>+6.2f}%[0m | {rsi_color}{d['rsi']:>3}[0m"
        table += row + "\n"
        
    table += "```"
    return table

@tasks.loop(minutes=15)
async def market_loop():
    channel = client.get_channel(config.DISCORD_CHANNEL_ID)
    if not channel:
        print("Błąd: Brak kanału ID")
        return

    try:
        # 1. Pobieranie danych
        print("Pobieram dane giełdowe...")
        stocks = await analyzer.get_combined_market_data(config.WATCHLIST_TECH)
        gold = await analyzer.analyze_gold_pro()
        
        # 2. Podział na rynki
        usa_stocks = [s for s in stocks if '.WA' not in s['orig_symbol']]
        pl_stocks = [s for s in stocks if '.WA' in s['orig_symbol']]

        # 3. Tworzenie Raportu
        embed = discord.Embed(title="📊 RAPORT GIEŁDOWY PRO", color=0x2b2d31, timestamp=datetime.now())
        
        # Tabela USA
        if usa_stocks:
            embed.add_field(name="🇺🇸 USA Tech", value=create_ansi_table(usa_stocks), inline=False)
        
        # Tabela PL
        if pl_stocks:
            embed.add_field(name="🇵🇱 GPW Polska", value=create_ansi_table(pl_stocks), inline=False)
            
        # 4. Sekcja SYGNAŁÓW (Tylko jeśli są okazje)
        signals_text = ""
        for s in stocks:
            # Warunek: RSI ekstremalne LUB wykryta formacja
            if s['rsi'] <= 35 or s['rsi'] >= 75 or s['pattern'] != "➖":
                
                # Ikona statusu
                if s['rsi'] <= 35: icon = "🟢 OKAZJA"
                elif s['rsi'] >= 75: icon = "🔴 GRZANE"
                else: icon = "⚠️ OBSERWUJ"
                
                signals_text += f"**{s['symbol']}** {icon} (RSI: {s['rsi']})\n"
                signals_text += f"├ 🕯️ Formacja: **{s['pattern']}**\n"
                signals_text += f"├ 🎯 TP: {s['tp']} | 🛑 SL: {s['sl']}\n"
                if s['ai']:
                    signals_text += f"└ 🤖 AI: *{s['ai']}*\n"
                signals_text += "\n"
        
        if signals_text:
            embed.add_field(name="⚡ SYGNAŁY I SETUPY", value=signals_text, inline=False)

        # 5. Złoto Footer
        if gold:
            g_arrow = "⬆️" if gold['change'] >= 0 else "⬇️"
            embed.set_footer(text=f"🟡 ZŁOTO: {gold['price']} USD ({gold['change']:+.2f}%) {g_arrow}")

        await channel.send(embed=embed)
        print("Raport wysłany.")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

@client.event
async def on_ready():
    print(f"Zalogowano jako {client.user}")
    if not market_loop.is_running():
        market_loop.start()

client.run(config.DISCORD_TOKEN)
