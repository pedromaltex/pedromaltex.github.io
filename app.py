import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from flask import jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import yfinance
import json

from helpers import apology, login_required, lookup, usd, get_data

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Sets the time of the events
current_time = datetime.now()


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    # Deixar predefinido o gráfico de 1 ano
    selected_options = ['1y']
    stock_total = 0

    period = ['1d', '1wk', '1mo', 'YTD', '1y', '5y', '20y']
    interval = ['1m', '1h', '1h', '1h', '1d', '1wk', '1mo']

    # Processar a seleção do período quando o formulário é submetido
    if request.method == "POST":
        selected_options = request.form.getlist('selecao')

        for i in range(len(period)):
            if selected_options[0] == period[i]:
                data = get_data("^GSPC", period[i], interval[i])  # Sempre usar ^GSPC no index

        session['index_labels'] = data[0]
        session['index_values'] = data[1]
        session['index_selected_options'] = selected_options

        return redirect("/")

    # Obter dados do portfólio do utilizador
    portfolio = db.execute("SELECT * FROM portfolio WHERE user_id = ?", session["user_id"])
    cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]['cash']

    # Garantir que as variáveis têm os tipos corretos para cálculos no Jinja
    for stock in portfolio:
        stock["total"] = int(stock["shares"]) * float(stock["price"])
        stock_total += stock["total"]

    # Obter os dados do S&P 500 (por enquanto)
    data = get_data("^GSPC", period[4], interval[4])  # TODO: Substituir ^GSPC por PORTFOLIO quando a função estiver completa
    labels, values = data

    # Buscar os dados da sessão para GET requests
    labels = session.get('index_labels', [])
    values = session.get('index_values', [])
    selected_options = session.get('index_selected_options', [])

    #########################################################################################################################
    # TODO: O gráfico da página principal não está a ser do S&P 500 e sim do quoted, e não sei porque isto está a acontecer #
    #########################################################################################################################

    return render_template(
        "index.html",
        portfolio=portfolio,
        cash=float(cash),
        stock_total=float(stock_total),
        portfolio_json=json.dumps(portfolio),
        labels=labels,
        values=values,
        period=period,
        interval=interval,
        selected_options=selected_options
    )



@app.route("/predict", methods=["GET", "POST"])
@login_required
def predict():
    """Get stock quote."""
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("must provide symbol", 400)

        stock = lookup(request.form.get("symbol"))
        if stock is None:
            return apology("invalid symbol", 400)

        # Redirect to predicted page
        #TODO Falta fazer a predicted page
        return apology("You still have to do the integration with PIC")
        return render_template("predicted.html", stock=stock)
    return render_template("predict.html")

@app.route("/news", methods=["GET", "POST"])
@login_required
def news():
    return apology("You still have to do this code")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":

        # Ensure symbol was submitted
        symbol = request.form.get("symbol")
        if not symbol:
            apology("must provide symbol", 400)
        symbol = symbol.upper()
        if not lookup(symbol):
            apology("must provide a valid symbol", 400)

        # Require user's input of shares
        shares = request.form.get("shares")
        try:
            shares = int(shares)
            if shares <= 0:
                return apology("must provide a valid number of shares", 400)
        except ValueError:
            return apology("must provide a valid number of shares", 400)

        # Store stock price and total value of wallet in variables
        stock = lookup(symbol)
        if stock is None:
            return apology("invalid symbol", 400)

        # See current price of the selected stock
        current_price = float(stock["price"])
        print(current_price)

        # see the total cash in wallet
        total_cash_wallet = db.execute(
            "SELECT cash FROM users WHERE id = ?", session["user_id"]
        )
        total_cash_wallet = total_cash_wallet[0]["cash"]

        # conta quantas vezes há operações com aquele stock
        how_many_buys_stock = db.execute(
            "SELECT COUNT (*) FROM portfolio WHERE symbol = ? AND user_id = ?", symbol, session["user_id"])[0]['COUNT (*)']

        # STORE DATA TO KEEP TRACK OF PURCHASE. TABLES SQL
        if total_cash_wallet > current_price * int(shares):
            if how_many_buys_stock == 0:
                # Registra a compra na tabela portfolio da base de dados pela primeira vez
                db.execute(
                    "INSERT INTO portfolio (user_id, symbol, shares, price) VALUES (?,?,?,?)",
                    session["user_id"], symbol, shares, current_price
                )
            else:
                # Faz update no número de ações detidas pelo usuário
                db.execute(
                    "UPDATE portfolio SET shares = shares + ?, price = ? WHERE user_id = ? AND symbol = ?",
                    int(shares), current_price, session["user_id"], symbol)

            # Guardar no histórico de compras #TODO

            # Update no cash total da carteira
            cost = current_price * float(shares)
            db.execute("UPDATE users SET cash = cash - ? WHERE id = ?",
                       cost, session["user_id"]
                       )
            # Sets the time of the events formated already
            current_time = datetime.now()
            current_time_formatted = current_time.strftime("%Y-%m-%d %H:%M:%S")
            # Update in history
            db.execute(
                "INSERT INTO history (user_id, symbol, buysell, shares, price, time) VALUES (?, ?, 1, ?, ?, ?)",
                session["user_id"], symbol, shares, current_price, current_time_formatted
            )

            # Redirect to home page
            return redirect("/")
        # Render an apology
        return apology("Cash in wallet inferior to desired purchase. Cannot afford the number of shares.")
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    portfolio = db.execute("SELECT * FROM portfolio WHERE user_id = ?",
                           session["user_id"])
    history = db.execute("SELECT * FROM history WHERE user_id = ? ORDER BY time DESC",
                         session["user_id"])

    return render_template("history.html", portfolio=portfolio, history=history)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        if not session['via_button']:
            if not request.form.get("symbol"):
                return apology("must provide symbol", 400)

            stock = lookup(request.form.get("symbol"))
            if stock is None:
                return apology("invalid symbol", 400)
            symbol = stock['symbol']

        try:
            stock = lookup(symbol)
        except UnboundLocalError:
            stock = lookup(session['symbol'])
        symbol = stock['symbol']


        selected_options = ['1y'] #Deixar predefinido o gráfico de 1 ano
        period =   ['1d', '1wk', '1mo', 'YTD', '1y', '5y', '20y', '99y']
        interval = ['1m', '1h',  '1h',  '1h',  '1d', '1wk','1mo', '3mo', '3mo']

        selected_options = request.form.getlist('selecao')
        if selected_options == []:
            selected_options = ['1y']

        for i in range(len(period)):
            if selected_options[0] == period[i]:
                data = get_data(symbol, period[i], interval[i])

        labels = data[0]
        values = data[1]

        # Store data in the session
        session['labels'] = labels
        session['values'] = values
        session['selected_options'] = selected_options
        session['symbol'] = symbol
        session['stock'] = stock

        # Redirect to quoted page
        session['via_button'] = True
        return render_template("quoted.html", stock=stock, labels=labels, values=values, \
                        selected_options=selected_options)

    session['via_button'] = False
    return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)
        # Ensure password was submitted
        elif not request.form.get("password") or not request.form.get("confirmation"):
            return apology("must provide password", 400)
        # Ensure confirmation password was submitted
        elif request.form.get("confirmation") != request.form.get("password"):
            return apology("password mismatched", 400)

        else:
            try:
                # Query database for username
                db.execute(
                    "INSERT INTO users (username, hash) VALUES (?, ?)", request.form.get(
                        "username"), generate_password_hash(request.form.get("password"))
                )
            except ValueError:
                return apology("user already exists", 400)

        # Redirect to login page
        return redirect("/login")

    # Redirect user to register page
    return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    portfolio = db.execute("SELECT * FROM portfolio WHERE user_id = ?",
                           session["user_id"])
    if request.method == "POST":
        symbol = request.form.get("symbol")
        if not symbol:
            return apology("must provide symbol", 400)
        symbol = symbol.upper()
        how_many_buys_stock = db.execute(
            "SELECT COUNT (*) FROM portfolio WHERE symbol = ? AND user_id = ?", symbol, session["user_id"])[0]['COUNT (*)']
        if not lookup(symbol) or how_many_buys_stock == 0:
            return apology("must provide a valid symbol that you own", 400)

        # See the current price of the selected stock (IMPORTANTE PARA O HISTÓRICO)
        current_price = float(lookup(symbol)["price"])

        # Check how many shares the user wants to sell
        shares = int(request.form.get("shares"))

        # Check how many shares the user owns
        shares_owned = db.execute(
            "SELECT shares FROM portfolio WHERE symbol = ? AND user_id = ?", symbol, session["user_id"])[0]['shares']

        if type(shares) != int or shares <= 0 or shares > shares_owned:
            return apology("The number of shares is not supported. Remember, put a positive integer or don't try to sell stocks you don't have.")

        # Sets the time of the events formated already
        current_time = datetime.now()
        current_time_formatted = current_time.strftime("%Y-%m-%d %H:%M:%S")

        # Updates shares owned and adds the transaction to the history
        db.execute(
            "UPDATE portfolio SET shares = ? WHERE user_id = ? AND symbol = ?",
            (int(shares_owned) - int(shares)), session["user_id"], symbol)

        # Elimina da carteira caso se venda tudo
        if (int(shares_owned) - int(shares)) == 0:
            db.execute(
                "DELETE FROM portfolio WHERE user_id = ? AND symbol = ?",
                session["user_id"], symbol)

        db.execute(
            "INSERT INTO history (user_id, symbol, buysell, shares, price, time) VALUES (?, ?, -1, ?, ?, ?)",
            session["user_id"], symbol, shares, current_price, current_time_formatted)
        db.execute(
            "UPDATE users SET cash = cash + ? WHERE id = ?",
            shares * current_price, session["user_id"]
        )

        return redirect("/")
    return render_template("sell.html", portfolio=portfolio)


@app.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():
    if request.method == "POST":
        deposit = request.form.get("deposit")
        try:
            deposit = int(deposit)
            if deposit <= 0:
                return apology("must provide a valid deposit", 400)
        except ValueError:
            return apology("must provide a valid number of dollars", 400)
        db.execute("UPDATE users SET cash = cash + ? WHERE id = ?",
                   deposit, session["user_id"])
        render_template("deposit.html")

        # Redirect to home page
        return redirect("/")

    return render_template("deposit.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
