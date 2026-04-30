from flask import Flask, render_template, request, session, redirect
from flask_babel import Babel, get_locale as babel_get_locale
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3


app = Flask(__name__)
app.secret_key = "noe_hemmelig_her"


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return wrapper

#DATABASE
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

#REGISTRERING
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, generate_password_hash(password))
            )
            conn.commit()
        except:
            return render_template("register.html", error="Brukernavn er allerede tatt")


        return redirect("/login")

    return render_template("register.html")



#LOG INN

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect("/dashboard")

        return "Feil brukernavn eller passord"

    return render_template("login.html")



#DASHBOARD
@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()

    # Totalt løste oppgaver
    total = conn.execute(
        "SELECT COUNT(*) as cnt FROM progress WHERE user_id = ?",
        (session["user_id"],)
    ).fetchone()["cnt"]

    # Per nivå
    nivaa1 = conn.execute(
        "SELECT COUNT(*) as cnt FROM progress WHERE user_id = ? AND oppgave_id BETWEEN 1 AND 30",
        (session["user_id"],)
    ).fetchone()["cnt"]

    nivaa2 = conn.execute(
        "SELECT COUNT(*) as cnt FROM progress WHERE user_id = ? AND oppgave_id BETWEEN 2001 AND 2030",
        (session["user_id"],)
    ).fetchone()["cnt"]

    nivaa3 = conn.execute(
        "SELECT COUNT(*) as cnt FROM progress WHERE user_id = ? AND oppgave_id BETWEEN 3001 AND 3030",
        (session["user_id"],)
    ).fetchone()["cnt"]

    return render_template("dashboard.jinja2",
        username=session["username"],
        role=session.get("role", "user"),
        total=total,
        nivaa1=nivaa1,
        nivaa2=nivaa2,
        nivaa3=nivaa3
    )



#ADMINPANNEL
@app.route("/admin")
@login_required
def admin():
    if session.get("role") != "admin":
        return redirect("/dashboard")

    conn = get_db()

    users = conn.execute("""
        SELECT u.id, u.username, u.role,
               COUNT(p.id) as løste
        FROM users u
        LEFT JOIN progress p ON p.user_id = u.id
        GROUP BY u.id
        ORDER BY løste DESC
    """).fetchall()

    totalt_brukere = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()["cnt"]
    totalt_løste = conn.execute("SELECT COUNT(*) as cnt FROM progress").fetchone()["cnt"]

    return render_template("admin.html",
        users=users,
        totalt_brukere=totalt_brukere,
        totalt_løste=totalt_løste,
        current_user_id=session["user_id"]
    )


@app.route("/admin/slett/<int:user_id>", methods=["POST"])
@login_required
def admin_slett_bruker(user_id):
    if session.get("role") != "admin":
        return redirect("/dashboard")

    conn = get_db()
    conn.execute("DELETE FROM progress WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    return redirect("/admin")


@app.route("/admin/rolle/<int:user_id>", methods=["POST"])
@login_required
def admin_endre_rolle(user_id):
    if session.get("role") != "admin":
        return redirect("/dashboard")

    ny_rolle = request.form.get("rolle")
    if ny_rolle in ["user", "admin"]:
        conn = get_db()
        conn.execute("UPDATE users SET role = ? WHERE id = ?", (ny_rolle, user_id))
        conn.commit()
    return redirect("/admin")



#LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# SPRÅK


def get_locale():
    return request.args.get("lang", "nb")

babel = Babel(app, locale_selector=get_locale)

@app.context_processor
def inject_locale():
    return {"get_locale": get_locale}


# INDEX

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')



# OPPGAVER – VELG TEMA

@app.route('/oppgaver')
@login_required
def oppgaver():
    return render_template('oppgaver.html')



@app.route('/oppgaver/trinn/<int:trinn>')
@login_required
def oppgaver_trinn(trinn):
    if trinn == 8:
        return render_template("oppgaver_trinn_8.html")
    elif trinn == 9:
        return render_template("oppgaver_trinn_9.html")
    elif trinn == 10:
        return render_template("oppgaver_trinn_10.html")
    else:
        return "Ugyldig trinn", 404


# ALGEBRA – VELG UNDERTEMA

@app.route('/oppgaver/algebra')
def oppgaver_algebra():

    undertemaer = [
        {"navn": "Regnerekkefølge", "link": "/oppgaver/algebra/regnerekkefolge"},
        {"navn": "Likninger", "link": "/oppgaver/algebra/likninger"},
    ]

    return render_template(
        "oppgaver_algebra.html",
        undertemaer=undertemaer
    )


# REGNEREKKEFØLGE – VELG NIVÅ

@app.route('/oppgaver/algebra/regnerekkefolge')
def regnerekkefolge():

    undertemaer = [
        {"navn": "Regnerekkefølge", "link": "/oppgaver/algebra/regnerekkefolge"},
        {"navn": "Likninger", "link": "/oppgaver/algebra/likninger"},
    ]

    return render_template(
        "oppgaver_algebra_regnerekkefolge.html",
        undertemaer=undertemaer
    )


# REGNEREKKEFØLGE NIVÅ 1

@app.route('/oppgaver/Regnerekkefølge/nivaa1', methods=['GET', 'POST'])
@login_required
def regnerekkefolge_nivaa1_route():

    # 1. Oppgaver
    oppgaver = [
        ("2 + 3 ⋅ 2", "8"),
        ("4 + 6 : 2", "7"),
        ("5 ⋅ 2 + 1", "11"),
        ("8 - 3 + 2", "7"),
        ("10 : 2 + 4", "9"),

        ("3 + 4 ⋅ 2", "11"),
        ("6 + 8 : 4", "8"),
        ("7 - 2 + 5", "10"),
        ("9 ⋅ 1 + 3", "12"),
        ("12 : 3 + 2", "6"),

        ("4 ⋅ 2 + 6", "14"),
        ("15 - 6 + 1", "10"),
        ("18 : 3 + 1", "7"),
        ("2 + 5 ⋅ 3", "17"),
        ("20 : 5 + 4", "8"),

        ("3 ⋅ 3 + 2", "11"),
        ("14 - 4 + 3", "13"),
        ("16 : 4 + 6", "10"),
        ("5 + 2 ⋅ 4", "13"),
        ("9 + 12 : 3", "13"),

        ("7 ⋅ 2 - 3", "11"),
        ("8 + 9 : 3", "11"),
        ("6 ⋅ 2 + 5", "17"),
        ("21 : 3 + 2", "9"),
        ("4 + 3 ⋅ 3", "13"),

        ("10 - 2 ⋅ 3", "4"),
        ("18 : 2 - 4", "5"),
        ("3 + 6 ⋅ 2", "15"),
        ("5 ⋅ 3 - 4", "11"),
        ("12 : 4 + 7", "10")
    ]

    # 2. Hvilken oppgave er vi på?
    nummer = int(request.args.get("n", 1))
    total = len(oppgaver)

    # 3. Ferdig?
    if nummer > total:
        return render_template(
            "ferdig.html",
            tittel="Nivå 1 – Regnerekkefølge",
            melding="Du fullførte nivå 1! Bra jobba 🎉"
        )

    oppgave, fasit = oppgaver[nummer - 1]

    resultat = ""
    riktig = None

    conn = get_db()

    # 4. HENT progresjon fra database
    rows = conn.execute(
        "SELECT oppgave_id FROM progress WHERE user_id = ? AND status = 'riktig'",
        (session["user_id"],)
    ).fetchall()

    riktige_oppgaver = {row["oppgave_id"] for row in rows}

    # 5. POST – bruker svarer
    if request.method == "POST":
        svar = request.form["svar"].strip()

        if svar == fasit:
            resultat = "✅ Riktig!"
            riktig = True

            # LAGRE progresjon
            conn.execute(
                "INSERT OR REPLACE INTO progress (user_id, oppgave_id, status) VALUES (?, ?, ?)",
                (session["user_id"], nummer, "riktig")
            )
            conn.commit()

            riktige_oppgaver.add(nummer)

        elif svar == "67":
            resultat = "🤡🤮 Du er ikke morsom 🖕"
            riktig = False

        else:
            resultat = "❌ Feil, prøv igjen!"
            riktig = False

    # 6. Render
    return render_template(
        "regnerekkefolge_nivaa1.html",
        oppgave=oppgave,
        nummer=nummer,
        total=total,
        resultat=resultat,
        riktig=riktig,

        oppgave_nummer=nummer,
        oppgaver=list(range(1, total + 1)),
        riktige_oppgaver=riktige_oppgaver
    )

# REGNEREKKEFØLGE NIVÅ 2


regnerekkefolge_nivaa2 = [
    ("(3 + 2) ⋅ 4", "20"),
    ("6 ⋅ (2 + 1)", "18"),
    ("(8 - 3) ⋅ 2", "10"),
    ("4 + (6 : 2)", "7"),
    ("(10 - 4) + 3", "9"),

    ("2 ⋅ (5 + 3)", "16"),
    ("(12 : 3) + 5", "9"),
    ("7 + (4 ⋅ 2)", "15"),
    ("(9 - 1) : 2", "4"),
    ("3 + (8 - 5)", "6"),

    ("(6 + 2) ⋅ 3", "24"),
    ("(15 - 9) + 4", "10"),
    ("4 ⋅ (3 + 1)", "16"),
    ("(18 : 2) - 4", "5"),
    ("5 + (12 : 3)", "9"),

    ("(7 + 3) ⋅ 2", "20"),
    ("(20 - 8) : 4", "3"),
    ("6 + (9 - 2)", "13"),
    ("(14 : 2) + 6", "13"),
    ("3 ⋅ (4 + 2)", "18"),

    ("(16 - 6) : 2", "5"),
    ("8 + (3 ⋅ 3)", "17"),
    ("(5 + 7) - 4", "8"),
    ("2 + (10 : 2)", "7"),
    ("(9 - 3) ⋅ 3", "18"),

    ("4 + (15 : 3)", "9"),
    ("(8 + 4) : 2", "6"),
    ("6 ⋅ (3 - 1)", "12"),
    ("(10 - 2) + 5", "13"),
    ("3 + (14 : 2)", "10")
]


@app.route('/oppgaver/Regnerekkefølge/nivaa2', methods=['GET', 'POST'])
@login_required
def regnerekkefolge_nivaa2_route():

    oppgaver = regnerekkefolge_nivaa2
    nummer = int(request.args.get("n", 1))
    total = len(oppgaver)

    # egen ID-serie for nivå 2
    oppgave_id = 2000 + nummer

    if nummer > total:
        return render_template(
            "ferdig.html",
            tittel="Nivå 2 – Regnerekkefølge",
            melding="Du fullførte nivå 2! Sterkt jobba 🔥"
        )

    oppgave, fasit = oppgaver[nummer - 1]

    resultat = ""
    riktig = None

    conn = get_db()

    rows = conn.execute(
        "SELECT oppgave_id FROM progress WHERE user_id = ? AND status = 'riktig'",
        (session["user_id"],)
    ).fetchall()

    riktige_oppgaver = {row["oppgave_id"] for row in rows}

    if request.method == "POST":
        svar = request.form["svar"].strip()

        if svar == fasit:
            resultat = "✅ Riktig!"
            riktig = True

            conn.execute(
                "INSERT OR REPLACE INTO progress (user_id, oppgave_id, status) VALUES (?, ?, ?)",
                (session["user_id"], oppgave_id, "riktig")
            )
            conn.commit()

            riktige_oppgaver.add(oppgave_id)

        elif svar == "67":
            resultat = "🤡🤮 Du er ikke morsom 🖕"
            riktig = False
        else:
            resultat = "❌ Feil, prøv igjen!"
            riktig = False

    # venstre meny med unike ID-er
    venstre_meny = []
    for i in range(1, total + 1):
        venstre_meny.append({
            "nummer": i,
            "id": 2000 + i,
            "link": f"/oppgaver/Regnerekkefølge/nivaa2?n={i}"
        })

    return render_template(
        "regnerekkefolge_nivaa2.html",
        oppgave=oppgave,
        nummer=nummer,
        total=total,
        resultat=resultat,
        riktig=riktig,
        oppgave_nummer=nummer,
        oppgaver=venstre_meny,
        riktige_oppgaver=riktige_oppgaver,
        undertemaer=[
            {"navn": "Regnerekkefølge", "link": "/oppgaver/algebra/regnerekkefolge"},
            {"navn": "Likninger", "link": "/oppgaver/algebra/likninger"},
        ]
    )

# REGNEREKKEFØLGE NIVÅ 3

regnerekkefolge_nivaa3 = [
    ("(3 + 2) ⋅ (4 - 1)", "15"),
    ("6 ⋅ (2 + 1) - 4", "14"),
    ("(8 - 3) ⋅ (2 + 2)", "20"),
    ("4 + (6 : 2) ⋅ 3", "13"),
    ("(10 - 4) + (3 ⋅ 2)", "12"),

    ("2 ⋅ (5 + 3) - 6", "10"),
    ("(12 : 3) + (5 ⋅ 2)", "14"),
    ("7 + (4 ⋅ 2) ⋅ 2", "23"),
    ("(9 - 1) : 2 + 7", "11"),
    ("3 + (8 - 5) ⋅ 4", "15"),

    ("(6 + 2) ⋅ 3 - 5", "19"),
    ("(15 - 9) + (4 ⋅ 3)", "18"),
    ("4 ⋅ (3 + 1) ⋅ 2", "32"),
    ("(18 : 2) - 4 + 9", "14"),
    ("5 + (12 : 3) ⋅ 4", "21"),

    ("(7 + 3) ⋅ 2 ⋅ 2", "40"),
    ("(20 - 8) : 4 + 9", "12"),
    ("6 + (9 - 2) ⋅ 3", "27"),
    ("(14 : 2) + 6 ⋅ 2", "20"),
    ("3 ⋅ (4 + 2) ⋅ 2", "36"),

    ("(16 - 6) : 2 ⋅ 5", "25"),
    ("8 + (3 ⋅ 3) ⋅ 2", "26"),
    ("(5 + 7) - 4 ⋅ 3", "0"),
    ("2 + (10 : 2) ⋅ 4", "22"),
    ("(9 - 3) ⋅ 3 ⋅ 2", "36"),

    ("4 + (15 : 3) ⋅ 5", "29"),
    ("(8 + 4) : 2 ⋅ 6", "36"),
    ("6 ⋅ (3 - 1) ⋅ 3", "36"),
    ("(10 - 2) + 5 ⋅ 4", "28"),
    ("3 + (14 : 2) ⋅ 3", "24")
]


@app.route('/oppgaver/Regnerekkefølge/nivaa3', methods=['GET', 'POST'])
@login_required
def regnerekkefolge_nivaa3_route():

    nummer = int(request.args.get("n", 1))
    total = len(regnerekkefolge_nivaa3)

    # ID-serie 3000+ for nivå 3
    oppgave_id = 3000 + nummer

    if nummer > total:
        return render_template(
            "ferdig.html",
            tittel="Nivå 3 – Regnerekkefølge",
            melding="Du fullførte nivå 3! Monstersterkt 💪🔥"
        )

    oppgave, fasit = regnerekkefolge_nivaa3[nummer - 1]

    resultat = ""
    riktig = None

    conn = get_db()

    # Hent progresjon fra database
    rows = conn.execute(
        "SELECT oppgave_id FROM progress WHERE user_id = ? AND status = 'riktig'",
        (session["user_id"],)
    ).fetchall()

    riktige_oppgaver = {row["oppgave_id"] for row in rows}

    if request.method == "POST":
        svar = request.form["svar"].strip()

        if svar == fasit:
            resultat = "✅ Riktig!"
            riktig = True

            conn.execute(
                "INSERT OR REPLACE INTO progress (user_id, oppgave_id, status) VALUES (?, ?, ?)",
                (session["user_id"], oppgave_id, "riktig")
            )
            conn.commit()

            riktige_oppgaver.add(oppgave_id)

        elif svar == "67":
            resultat = "🤡🤮 Du er ikke morsom 🖕"
            riktig = False

        else:
            resultat = "❌ Feil, prøv igjen!"
            riktig = False

    # Venstre meny med unike ID-er
    venstre_meny = []
    for i in range(1, total + 1):
        venstre_meny.append({
            "nummer": i,
            "id": 3000 + i,
            "link": f"/oppgaver/Regnerekkefølge/nivaa3?n={i}"
        })

    return render_template(
        "regnerekkefolge_nivaa3.html",
        oppgave=oppgave,
        nummer=nummer,
        total=total,
        resultat=resultat,
        riktig=riktig,
        oppgave_nummer=nummer,
        oppgaver=venstre_meny,
        riktige_oppgaver=riktige_oppgaver,
        undertemaer=[
            {"navn": "Regnerekkefølge", "link": "/oppgaver/algebra/regnerekkefolge"},
            {"navn": "Likninger", "link": "/oppgaver/algebra/likninger"},
        ]
    )



# START SERVER

if __name__ == '__main__':
    app.run(debug=True)





