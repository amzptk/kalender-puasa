from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

# ================= DB =================
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT, password TEXT, wa TEXT)''')
    conn.commit()
    conn.close()

init_db()

# ================= LOGIN =================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pw = request.form["password"]

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (user, pw))
        result = c.fetchone()
        conn.close()

        if result:
            session["user"] = user
            return redirect("/dashboard")
        else:
            return "Login gagal"

    return render_template("login.html")

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    return render_template("dashboard.html", user=session["user"])

# ================= TAMBAH USER =================
@app.route("/add", methods=["POST"])
def add_user():
    user = request.form["username"]
    pw = request.form["password"]
    wa = request.form["wa"]

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT INTO users VALUES (?, ?, ?)", (user, pw, wa))
    conn.commit()
    conn.close()

    return "User ditambahkan!"

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
