import discord
from discord.ext import tasks
import config
import analyzer
from datetime import datetime
import asyncio

# --- KONFIGURACJA KLIENTA ---
# Włączamy uprawnienia do pisania wiadomości
intents = discord.Intents.default()
intents.message_content = True 
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"--- ZALOGOWANO JAKO: {client.user} ---")
    print(f"--- SYSTEM WE FRANKFURCIE STABILNY ---")
    
    channel = client.get_channel(config.DISCORD_CHANNEL_ID)
    if channel:
        await channel.send("🚀 **Ziomal-bot2** gotowy! Moduł analizy złota (bez pozycji) aktywny.")
    
    if not market_loop.is_running():
        market_loop.start()

@tasks.loop(minutes=5)
async def market_loop():
    channel = client.get_channel(config.DISCORD_CHANNEL_ID)
    if not channel:
        print(f"BŁĄD: Nie znaleziono kanału o ID: {config.DISCORD_CHANNEL_ID}")
        return

    try:
        print("Pobieranie danych rynkowych...")
        # 1. POBIERANIE DANYCH
        stocks = await analyzer.get_combined_market_data(config.WATCHLIST_TECH)
        gold = await analyzer.analyze_gold_pro()

        # 2. BUDOWANIE RAPORTU
        embed = discord.Embed(title="📊 RAPORT GIEŁDOWY & SYGNAŁY", color=0x2ecc71, timestamp=datetime.now())

        # --- SEKCJA USA (NASDAQ/NYSE) ---
        usa = [s for s in stocks if not s['symbol'].endswith('.WA')]
        if usa:
            txt_usa = ""
            for s in usa:
                ikona = "🟢" if s['change'] > 0 else "🔴"
                txt_usa += f"**{s['symbol']}**: ${s['price']} ({ikona} {s['change']}%)\n"
            embed.add_field(name="🇺🇸 USA (Tech)", value=txt_usa, inline=True)

        # --- SEKCJA POLSKA (GPW) ---
        pl = [s for s in stocks if s['symbol'].endswith('.WA')]
        if pl:
            txt_pl = ""
            for s in pl:
                ikona = "🟢" if s['change'] > 0 else "🔴"
                clean_symbol = s['symbol'].replace('.WA', '')
                txt_pl += f"**{clean_symbol}**: {s['price']} PLN ({ikona} {s['change']}%)\n"
            embed.add_field(name="🇵🇱 GPW (Warszawa)", value=txt_pl, inline=True)
        
        # --- SEKCJA ZŁOTA (KONKRETNA ANALIZA I SYGNAŁ) ---
        if gold:
            cena = gold.get('price', 0)
            zmiana = gold.get('change', 0)
            
            # Logika sygnałów
            sygnal = "⚪ NEUTRALNY (Konsolidacja)"
            kolor_sygnalu = "⚪"
            alert_dodatkowy = ""

            if zmiana >= 1.0:
                sygnal = "🚀 RAKIETA (Bardzo silny trend wzrostowy)"
                alert_dodatkowy = "\n⚠️ **UWAGA: DUŻA ZMIENNOŚĆ!**"
            elif zmiana > 0.5:
                sygnal = "🟢 KUPUJ (Silny trend wzrostowy)"
            elif zmiana > 0:
                sygnal = "📈 LEKKI WZROST (Pozytywnie)"
            elif zmiana <= -1.0:
                sygnal = "🩸 KRWAWIENIE (Bardzo silny spadek)"
                alert_dodatkowy = "\n⚠️ **UWAGA: DUŻA ZMIENNOŚĆ!**"
            elif zmiana < -0.5:
                sygnal = "🔴 SPRZEDAWAJ (Silny trend spadkowy)"
            elif zmiana < 0:
                sygnal = "📉 LEKKI SPADEK (Negatywnie)"

            wartosc_pola = (
                f"Cena rynkowa: **{cena} USD**\n"
                f"Zmiana 24h: **{zmiana}%**\n"
                f"-----------------------------\n"
                f"Sygnał AI: **{sygnal}**"
                f"{alert_dodatkowy}"
            )
            
            embed.add_field(name="🟡 ANALIZA ZŁOTA (XAU/USD)", value=wartosc_pola, inline=False)

        embed.set_footer(text="System monitorowania Ziomal-bot2 | Server: Frankfurt")
        
        await channel.send(embed=embed)
        print("Raport z sygnałami wysłany.")

    except Exception as e:
        print(f"CRITICAL ERROR w pętli market_loop: {e}")

client.run(config.DISCORD_TOKEN)
