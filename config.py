import os

MODE = "PROD"
TEST_MODE = False
TEST_GOLD_ALERT = False
FORCE_TEST_ALERT = False

DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1451632628842365013/FkOAiiIesLb18Ox_Fs9JaLj2Z_LZ-TLnayjS7Kkc0z1SW00s7WWlweHAATZdN2EgJ_8T"
BINANCE_BASE_URL = "https://api.binance.com"
DISCORD_TOKEN = "MTQ1NDA3NjQyMTY4MDE0MDQyMA.GexajH.SsqRYZ_f7NrQXajkVPd4QmkjJlzjjVknK0kgdc"
GOLD_ALERT_CHANNEL_ID = 1451632561230184529
ALERT_WEBHOOK_URL = "https://discord.com/api/webhooks/1451632628842365013/FkOAiiIesLb18Ox_Fs9JaLj2Z_LZ-TLnayjS7Kkc0z1SW00s7WWlweHAATZdN2EgJ_8T"
FINNHUB_API_KEY = "d57vh69r01qptoapb3ggd57vh69r01qptoapb3h0"
ALPHA_API_KEY = "G89VGTZWN74X87B6"
BINANCE_SYMBOL = "BTCUSDT"

# =========================
# STOCKS – USA (PRO)
# =========================
STOCKS_US = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA",
    "AMD", "NFLX", "PLTR", "MSTR", "COIN",

    # DODANE
    "SAP", "OKLO", "ASML", "AXP", "TSM", "BE", "PLD", "URA"
]
STOCKS_PL = [
    "CBF.WA", "MBR.WA", "CRS.WA", "MRB.WA", "SNT.WA",
    "KGH.WA", "PKN.WA", "XTB.WA", "DNT.WA", "PKP.WA", "SCW.WA"
]

# =========================
# TIMEFRAMES
# =========================
CANDLE_LIMIT = 100

