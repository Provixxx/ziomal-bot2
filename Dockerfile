# Używamy lekkiej wersji Pythona
FROM python:3.10-slim

# Ustawiamy folder roboczy wewnątrz kontenera
WORKDIR /app

# Kopiujemy listę bibliotek i instalujemy je
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiujemy resztę plików (main.py, analyzer.py, config.py)
COPY . .

# Komenda startowa bota

python main.py & python -m http.server 8000
