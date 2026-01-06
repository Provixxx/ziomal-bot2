import discord
from discord.ext import tasks
import config, analyzer, asyncio
from datetime import datetime
from flask import Flask
from threading import Thread

# --- SERVER ---
app = Flask('')
@app.route('/')
def home(): return "SYSTEM OPERATIONAL"
def run(): app.run(host='0.0.0.0', port=8000)
Thread(target=run, daemon=True).start()

# --- BOT ---
intents = discord.Intents.default()
client = discord.Client(intents=intents)

def create_ansi_table(data_list):
    # Nagłówek w kolorze białym/bold
    table = "```ansi\n"
    table += "[1;37mWALOR   |   CENA   |   ZM%   | RSI[0m\n"
    table += "------------------------------------\n"
    
    for d in data_list:
        # Logika kolorów ANSI
        # 32m = Zielony, 31m = Czerwony
        color_code = "[0;32m" if d['change'] >= 0 else "[0;31m"
        change_fmt = f"{d['change']:>+6.2f}%"
        
        # Wiersz tabeli
        # Symbol na biało, Cena na biało, Zmiana w kolorze, RSI na cyjanowo
        row = f"[0;37m{d['symbol']:<7}[0m | [0;37m{d['price']:>8.2f}[0m | {color_code}{change_fmt}[0m | [0;36m{d['rsi']:>3}[0m"
        table += row + "\n"
        
    table += "```"
    return table

@tasks.loop(minutes=15)
async def market_loop():
    channel = client.get_channel(config.DISCORD_CHANNEL_ID)
    if not channel: return

    try:
        # Pobieranie danych
        stocks = await analyzer.get_combined_market_data(config.WATCHLIST_TECH)
        gold = await analyzer.analyze_gold_pro()
        
        # Segregacja
        usa = [s for s in stocks if '.WA' not in s['orig_symbol']]
        pl = [s for s in stocks if '.WA' in s['orig_symbol']]

        embed = discord.Embed(title="📊 RAPORT GIEŁDOWY PRO", color=0x2b2d31, timestamp=datetime.now())

        # 1. TABELE
        if usa: embed.add_field(name="🇺🇸 USA Tech", value=create_ansi_table(usa), inline=False)
        if pl: embed.add_field(name="🇵🇱 GPW Polska", value=create_ansi_table(pl), inline=False)

        # 2. SYGNAŁY (Formacje + SL/TP)
        signals_txt = ""
        for s in stocks:
            # Warunek sygnału: RSI skrajne LUB wykryta formacja
            if s['rsi'] <= 35 or s['rsi'] >= 80 or s['pattern'] != "➖":
                icon = "🔥" if s['rsi'] <= 35 else "⚠️"
                if s['pattern'] != "➖": icon = "🕯️"
                
                signals_txt += f"**{s['symbol']}** {icon}\n"
                signals_txt += f"├ Formacja: {s['pattern']}\n"
                signals_txt += f"├ RSI: {s['rsi']}\n"
                signals_txt += f"└ 🎯 TP: {s['tp']} | 🛑 SL: {s['sl']}\n"
                if s['ai']: signals_txt += f"🤖 AI: *{s['ai']}*\n"
                signals_txt += "\n"
        
        if signals_txt:
            embed.add_field(name="⚡ SYGNAŁY I SETUPY", value=signals_txt, inline=False)

        # 3. ZŁOTO
        if gold:
            g_change = f"{gold['change']:+.2f}%"
            embed.set_footer(text=f"🟡 GOLD (XAU/USD): {gold['price']} $ ({g_change})")

        await channel.send(embed=embed)

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

@client.event
async def on_ready():
    if not market_loop.is_running(): market_loop.start()

client.run(config.DISCORD_TOKEN)
