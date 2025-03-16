import yfinance as yf

# Escolha um ticker (exemplo: Apple)
ticker = "AAPL"
stock = yf.Ticker(ticker)

# Obter dados fundamentais
market_cap = stock.info.get("marketCap")
market_cap = stock.info.keys()
dividend_yield = stock.info.get("dividendYield")
eps_current_year = stock.info.get("epsCurrentYear")



pe_ratio = stock.info.get("trailingPE")  # Ou "forwardPE" para o futuro

print(f"Market Cap: {market_cap}")
print(f"P/E Ratio: {pe_ratio}")

