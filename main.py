import discord
from discord.ext import tasks
import config, analyzer, asyncio, pytz
from datetime import datetime, time
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "ONLINE"

def run(): app.run(host='0.0.0.0', port=8000)
Thread(target=run, daemon=True).start()

intents = discord.Intents.default()
client = discord.Client(intents=intents)

def create_table(data):
    # Formatowanie tabeli ASCII (czcionka monospaced)
    t = "```text\n"
    t += f"{'WALOR':<7} | {'CENA':>8} | {'ZM':>7} | {'RSI':>3}\n"
    t += "-" * 35 + "\n"
    for d in data:
        t += f"{d['symbol']:<7} | {d['price']:>8.2f} | {d['change']:>6.2f}% | {d['rsi']:>3}\n"
    return t + "```"

@tasks.loop(minutes=15)
async def market_loop():
    channel = client.get_channel(config.DISCORD_CHANNEL_ID)
    if not channel: return

    try:
        all_data = await analyzer.get_combined_market_data(config.WATCHLIST_TECH)
        gold = await analyzer.analyze_gold_pro()

        usa = [s for s in all_data if '.WA' not in s['orig_symbol']]
        pl = [s for s in all_data if '.WA' in s['orig_symbol']]

        embed = discord.Embed(title="📊 RAPORT GIEŁDOWY (PRO + AI)", color=0x2b2d31, timestamp=datetime.now())
        
        if usa: embed.add_field(name="🇺🇸 USA Tech", value=create_table(usa), inline=False)
        if pl: embed.add_field(name="🇵🇱 GPW Polska", value=create_table(pl), inline=False)
        
        # Sekcja AI i Sygnałów
        signals = ""
        for s in all_data:
            if s['rsi'] <= 35 or s['rsi'] >= 80:
                emoji = "🟢" if s['rsi'] <= 35 else "⚠️"
                status = "OKAZJA" if s['rsi'] <= 35 else "GRZANE"
                signals += f"{emoji} **{s['symbol']}**: {status} (RSI: {s['rsi']}) - AI: *{s['ai']}*\n"
        
        if signals: embed.add_field(name="⚡ SYGNAŁY I AI", value=signals, inline=False)
        if gold: embed.set_footer(text=f"🟡 ZŁOTO: {gold['price']} USD ({gold['change']}%)")

        await channel.send(embed=embed)
    except Exception as e: print(f"Error: {e}")

@client.event
async def on_ready(): 
    print("Bot gotowy.")
    if not market_loop.is_running(): market_loop.start()

client.run(config.DISCORD_TOKEN)
