import yfinance as yf
import pandas as pd
from datetime import datetime, timezone

# Empresa alvo
target_ticker = "AAPL"

# Índice de mercado (exemplos: ^GSPC = S&P 500, ^IXIC = Nasdaq, ^BVSP = IBOV)
market_ticker = "^GSPC"

# Baixar os dados históricos
day, month, year = datetime.now().day, datetime.now().month, datetime.now().year
data = yf.download([target_ticker, market_ticker], start=f"{year-1}-{month}-{day}", end=f"{year}-{month}-{day}")#["Adj Close"]

# Calcular retornos diários
returns = data.pct_change().dropna()

# Calcular a correlação
correlation = returns.corr().iloc[0, 1]

print(f"Correlação de {target_ticker} com {market_ticker}: {correlation:.4f}")
