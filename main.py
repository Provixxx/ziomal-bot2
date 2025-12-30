import discord
from discord.ext import tasks
import config
import analyzer
from datetime import datetime

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"--- SYSTEM MONITORINGU START ---")
    if not market_loop.is_running(): market_loop.start()

@tasks.loop(minutes=5)
async def market_loop():
    channel = client.get_channel(config.DISCORD_CHANNEL_ID)
    if not channel: return

    try:
        # POBIERANIE DANYCH
        stocks = await analyzer.get_combined_market_data(config.WATCHLIST_TECH)
        gold = await analyzer.analyze_gold_pro()

        embed = discord.Embed(title="📊 PODSUMOWANIE RYNKU", color=0x3498db, timestamp=datetime.now())

        # SEKCJA USA
        usa = [s for s in stocks if not s['symbol'].endswith('.WA')]
        if usa:
            txt_usa = "WALOR      | CENA    | ZMIANA\n" + "-"*30 + "\n"
            for s in usa:
                ikona = "▲" if s['change'] > 0 else "▼"
                txt_usa += f"{s['symbol'].ljust(10)} | {str(s['price']).ljust(7)} | {ikona} {s['change']}%\n"
            embed.add_field(name="🇺🇸 NASDAQ / NYSE", value=f"```ml\n{txt_usa}```", inline=False)

        # SEKCJA POLSKA (GPW)
        pl = [s for s in stocks if s['symbol'].endswith('.WA')]
        if len(pl) > 0:
            txt_pl = "WALOR      | CENA    | ZMIANA\n" + "-" * 30 + "\n"
            for s in pl:
                ikona = "▲" if s['change'] > 0 else "▼"
                txt_pl += f"{s['symbol'].replace('.WA', '').ljust(10)} | {str(s['price']).ljust(7)} | {ikona} {s['change']}%\n"
            embed.add_field(name="🇵🇱 GPW (WARSZAWA)", value=f"```ml\n{txt_pl}```", inline=False)
        else:
            # To się wyświetla, gdy lista 'pl' jest pusta
            embed.add_field(name="🇵🇱 GPW (WARSZAWA)", value="`Trwa pobieranie danych...`", inline=False)

        await channel.send(embed=embed)

        # ALERT ZŁOTA (Oddzielnie)
        if gold:
            # ... kod alertu złota bez zmian ...
            pass

    except Exception as e:
        print(f"Błąd: {e}")

client.run(config.DISCORD_TOKEN)