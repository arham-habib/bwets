import logging, os, uuid
from flask import Flask, render_template, request, redirect, url_for, flash, session
from dotenv import load_dotenv
from sqlalchemy import select, func
from .models import SessionLocal, Player, PropUniverse, AdvanceBet, WinBet, PropBet, User
from .api import api as fastapi_app
from .odds import pool_odds, prop_odds
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

def create_app():

    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET", "dev")

    # Authentication decorator
    def login_required(f):
        def decorated_function(*args, **kwargs):
            if 'user_email' not in session:
                flash("Please log in to access this page", "error")
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form["email"].strip().lower()
            password = request.form["password"]
            
            if not email.endswith("@bwater.com"):
                flash("Only @bwater.com addresses are allowed", "error")
                return render_template("login.html")
            
            with SessionLocal() as db:
                user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
                
                if user and check_password_hash(user.password_hash, password):
                    session['user_email'] = user.email
                    session['user_id'] = user.id
                    flash("Login successful!", "success")
                    return redirect(url_for('index'))
                else:
                    flash("Invalid email or password", "error")
                    return render_template("login.html")
        
        return render_template("login.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            email = request.form["email"].strip().lower()
            password = request.form["password"]
            confirm_password = request.form["confirm_password"]
            
            if not email.endswith("@bwater.com"):
                flash("Only @bwater.com addresses are allowed", "error")
                return render_template("register.html")
            
            if password != confirm_password:
                flash("Passwords do not match", "error")
                return render_template("register.html")
            
            if len(password) < 6:
                flash("Password must be at least 6 characters long", "error")
                return render_template("register.html")
            
            with SessionLocal() as db:
                existing_user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
                if existing_user:
                    flash("User with this email already exists", "error")
                    return render_template("register.html")
                
                password_hash = generate_password_hash(password)
                new_user = User(email=email, password_hash=password_hash)
                db.add(new_user)
                db.commit()
                
                flash("Registration successful! Please log in.", "success")
                return redirect(url_for('login'))
        
        return render_template("register.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("You have been logged out", "success")
        return redirect(url_for('index'))

    @app.route("/")
    def index():
        with SessionLocal() as db:
            total = (
                (db.scalar(select(func.sum(AdvanceBet.amount))) or 0) +
                (db.scalar(select(func.sum(WinBet.amount)))     or 0) +
                (db.scalar(select(func.sum(PropBet.amount)))    or 0)
            )

        buttons = [
            {"href": url_for("advance"), "title": "Advance",
            "desc": "Bet on who advances in the heat"},
            {"href": url_for("win"),     "title": "Win",
            "desc": "Bet on who wins the whole event"},
            {"href": url_for("props"),   "title": "Props",
            "desc": "Yes / No side‑bets"},
        ]
        return render_template("index.html", cum=total, buttons=buttons)

    @app.route("/advance")
    @login_required
    def advance():
        with SessionLocal() as db:
            runners = (
                db.execute(
                    select(Player)
                    .order_by(Player.division, Player.heat, Player.player_name)
                )
                .scalars()
                .all()
            )

            # --- nest by division → heat ----------------------------------
            divisions = {}
            for p in runners:
                d = divisions.setdefault(p.division, {})
                d.setdefault(p.heat, []).append(p)

            odds = pool_odds(db, AdvanceBet, AdvanceBet.player_id)

            div_totals = {d: sum(odds.get(pl.id, {}).get("stake", 0)
                     for heats in h.values() for pl in heats)
              for d, h in divisions.items()}
            heat_totals = { (d,h): sum(odds.get(pl.id, {}).get("stake", 0)
                                    for pl in players)
                            for d, heats in divisions.items()
                            for h, players in heats.items()}

            total_pool = db.scalar(select(func.sum(AdvanceBet.amount))) or 0.0

        return render_template("advance.html",
                            divisions=divisions,
                            odds=odds,
                            pool_total=total_pool,
                            div_totals=div_totals,
                            heat_totals=heat_totals)
    

    @app.route("/bet", methods=["POST"])
    @login_required
    def bet():
        email = session.get('user_email')
        if not email or not email.endswith("@bwater.com"):
            flash("Authentication required", "error")
            return redirect(url_for("login"))
        
        market = request.form["market"]
        target = request.form["target_id"]
        amt = float(request.form["amount"])

        with SessionLocal() as db:
            if market == "advance":
                db.add(AdvanceBet(player_id=target, amount=amt, bettor_email=email))
            elif market == "win":
                db.add(WinBet(player_id=target, amount=amt, bettor_email=email))
            elif market == "prop":
                side_yes = request.form.get("side_yes") == "true"
                db.add(PropBet(prop_id=target, amount=amt, side_yes=side_yes, bettor_email=email))
            db.commit()
        flash(f"Bet placed: {email} → {market} ${amt}")
        return redirect(request.referrer or url_for("index"))
    
    @app.route("/win")
    @login_required
    def win():
        with SessionLocal() as db:
            players = (
                db.execute(
                    select(Player)
                    .where(Player.active == True)
                    .order_by(Player.division, Player.player_name)
                )
                .scalars()
                .all()
            )

            # nest players by division
            divisions = {}
            for p in players:
                divisions.setdefault(p.division, []).append(p)

            odds = pool_odds(db, WinBet, WinBet.player_id)

            # total $ per division
            div_totals = {d: sum(odds.get(pl.id, {}).get("stake", 0)
                                for pl in plist)
                        for d, plist in divisions.items()}

        return render_template("win.html",
                            divisions=divisions,
                            odds=odds,
                            div_totals=div_totals)

    @app.route("/props")
    @login_required
    def props():
        with SessionLocal() as db:
            props = db.execute(select(PropUniverse)
                            .where(PropUniverse.active==True)).scalars().all()
            odds = prop_odds(db)
            pool_total = db.scalar(select(func.sum(PropBet.amount))) or 0.0
        return render_template("props.html", props=props,
                            odds=odds, pool_total=pool_total)

    @app.route("/rules")
    def rules():
        return render_template("rules.html")

    
    return app



# --- run both apps behind one server -----------------------
def main():
    flask_app = create_app()
    application = DispatcherMiddleware(flask_app, {"/api": fastapi_app})
    run_simple("0.0.0.0", 8080, application, use_reloader=False)

if __name__ == "__main__":
    main()
