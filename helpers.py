import requests

import pandas as pd

from flask import redirect, render_template, session
from functools import wraps
import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
import datetime


def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def lookup(symbol):
    """Look up quote for symbol using yfinance."""

    # Validar o símbolo de entrada
    if not isinstance(symbol, str) or len(symbol) == 0:
        print("Erro: O símbolo deve ser uma string não vazia.")
        return None

    try:
        # Buscar dados de ações usando yfinance
        ticker = yf.Ticker(symbol.upper())
        stock_info = ticker.info

        # Tentar diferentes campos para obter o preço
        if 'regularMarketPrice' in stock_info:
            price = stock_info['regularMarketPrice']
        elif 'last_price' in stock_info:
            price = stock_info['last_price']
        elif 'previousClose' in stock_info:
            price = stock_info['previousClose']
        else:
            print(f"Erro: Não foi possível encontrar o preço de {symbol}.")
            return None

        # Verificar se a empresa foi encontrada
        if 'longName' in stock_info:
            return {
                "name": stock_info["longName"],
                "price": price,
                "symbol": symbol.upper()
            }
        else:
            print(f"Erro: Não foi possível encontrar o nome da empresa para {symbol}.")
            return None

    except ValueError as e:
        print(f"Erro de análise de dados: {e}")
    except KeyError as e:
        print(f"Erro de chave: Dados esperados ausentes para {symbol}.")
    except Exception as e:
        print(f"Erro: Problema ao buscar dados para {symbol}. {e}")

    return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"


def get_data(symbol, period='1y', interval='1d'):

    if symbol == "PORTFOLIO":
        #TODO Colocar aqui o gráfico da evolução da carteira ao longo do tempo
        return None
    data = yf.download(tickers=symbol, period=period, interval=interval)

    data.reset_index(inplace=True)

    #Caso o DataFrame tenha um MultiIndex, remover os níveis extras
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.droplevel(1)  # Remove o primeiro nível do índice

    if interval in ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h']:
        data = data[["Datetime", "Open", "Close"]]

        # Convertendo datas para string no formato ISO para facilitar a serialização
        data['Datetime'] = data['Datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')

        # Convertendo para listas compatíveis com JSON
        labels = data['Datetime'].tolist()

        #values = data['Close'].tolist() é a versão simplificada, mas como só queria 2 casas decimais, tive de por esta versão manhosa em baixo
        values = [round(v, 2) for v in data['Close'].tolist()]

    elif interval in ['1d', '5d', '1wk', '1mo', '3mo']:
        data = data[["Date", "Open", "Close"]]

        # Convertendo datas para string no formato ISO para facilitar a serialização
        data['Date'] = data['Date'].dt.strftime('%Y-%m-%d')

        # Convertendo para listas compatíveis com JSON
        labels = data['Date'].tolist()

        #values = data['Close'].tolist() é a versão simplificada, mas como só queria 2 casas decimais, tive de por esta versão manhosa em baixo
        values = [round(v, 2) for v in data['Close'].tolist()]
    else:
        raise ValueError("Meteste um valor errado no interval, estes são os válidos: \
                         1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo")



    return labels, values


get_data('^GSPC', '50y', '1d')


'''
    today=datetime.datetime.now()

    data = yf.download(symbol, start=f"{today.year-5}-{today.month}-{today.day}", end=f"{today.year}-{today.month}-{today.day}")

    data.reset_index(inplace=True)

    # Se houver MultiIndex, remover os níveis extras
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.droplevel(1)

    data = data[['Date', 'Close']]

    # Convertendo datas para string no formato ISO para facilitar a serialização
    data['Date'] = data['Date'].dt.strftime('%Y-%m-%d')

    # Convertendo para listas compatíveis com JSON
    labels = data['Date'].tolist()

    #values = data['Close'].tolist() é a versão simplificada, mas como só queria 2 casas decimais, tive de por esta versão manhosa em baixo
    values = [round(v, 2) for v in data['Close'].tolist()]
    return labels, values'''




import requests
from datetime import datetime, timezone

# Defina sua chave API do Finnhub
API_KEY = "cv3qp99r01ql2eusvo70cv3qp99r01ql2eusvo7g" 

def get_news(symbol, max_news=100):
    """Obtém notícias financeiras para um símbolo específico usando Finnhub"""
    try:
        url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from=2024-01-01&to={datetime.today().strftime("%Y-%m-%d")}&token={API_KEY}"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"[ERROR] Falha ao buscar notícias do Finnhub para {symbol}")
            return []

        data = response.json()

        news_list = []
        for article in data[:max_news]:  # Pega até 'max_news' notícias
            date_parsed = datetime.fromtimestamp(article["datetime"], tz=timezone.utc) if "datetime" in article else None

            news_list.append({
                "title": article.get("headline", "Sem título"),
                "link": article.get("url", "#"),
                "content": article.get("summary", "Sem descrição disponível"),
                "date": date_parsed,
                "publisher": article.get("source", "Desconhecido"),
                "image": article.get("image", None)  # Obtém a imagem da notícia
            })

        return news_list

    except Exception as e:
        print(f"[ERROR] Erro ao buscar notícias para {symbol}: {str(e)}")
        return []
