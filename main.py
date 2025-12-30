import discord
from discord.ext import tasks
import config
import analyzer
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True 
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"--- SYSTEM AKTYWNY: {client.user} ---")
    if not market_loop.is_running():
        market_loop.start()

@tasks.loop(minutes=5)
async def market_loop():
    channel = client.get_channel(config.DISCORD_CHANNEL_ID)
    if not channel: return

    try:
        # POBIERANIE DANYCH
        stocks = await analyzer.get_combined_market_data(config.WATCHLIST_TECH)
        gold = await analyzer.analyze_gold_pro()

        embed = discord.Embed(title="📊 ANALIZA RYNKOWA", color=0x2ecc71, timestamp=datetime.now())

        # TABELKA USA
        usa = [s for s in stocks if not s['symbol'].endswith('.WA')]
        if usa:
            v_usa = "```ml\nWALOR      | CENA    | ZMIANA\n" + "-"*28 + "\n"
            for s in usa:
                ikona = "▲" if s['change'] > 0 else "▼"
                v_usa += f"{s['symbol'].ljust(10)} | {str(s['price']).ljust(7)} | {ikona} {s['change']}%\n"
            v_usa += "```"
            embed.add_field(name="🇺🇸 NASDAQ / NYSE", value=v_usa, inline=False)

        # TABELKA GPW (Jeśli dane są > 0)
        pl = [s for s in stocks if s['symbol'].endswith('.WA') and s['price'] > 0]
        if pl:
            v_pl = "```ml\nWALOR      | CENA    | ZMIANA\n" + "-"*28 + "\n"
            for s in pl:
                ikona = "▲" if s['change'] > 0 else "▼"
                sym = s['symbol'].replace('.WA', '')
                v_pl += f"{sym.ljust(10)} | {str(s['price']).ljust(7)} | {ikona} {s['change']}%\n"
            v_pl += "```"
            embed.add_field(name="🇵🇱 GPW (WARSZAWA)", value=v_pl, inline=False)
        else:
            embed.add_field(name="🇵🇱 GPW (WARSZAWA)", value="`⚠️ Brak świeżych danych ze Stooq...`", inline=False)

        # SEKCJA SYGNAŁÓW ZŁOTA
        if gold:
            zmiana = gold.get('change', 0)
            sygnal = "⚪ CZEKAJ"
            if zmiana > 0.5: sygnal = "🟢 KUPUJ (Trend wzrostowy)"
            elif zmiana < -0.5: sygnal = "🔴 SPRZEDAWAJ (Trend spadkowy)"
            
            val_gold = f"Cena: **{gold['price']} USD** ({zmiana}%)\nSygnał: **{sygnal}**"
            embed.add_field(name="🟡 ANALIZA ZŁOTA", value=val_gold, inline=False)

        await channel.send(embed=embed)

    except Exception as e:
        print(f"Błąd pętli: {e}")

client.run(config.DISCORD_TOKEN)
