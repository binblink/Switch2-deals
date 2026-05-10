from flask import Flask, jsonify, flash, redirect, request
from db.connection import get_connection, release_connection
from db.queries import get_games_from_db
from flask import render_template
import os

app = Flask(__name__, 
    template_folder='../templates',
    static_folder='../static'
)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")

@app.route("/")
def home():
    conn = get_connection()
    try:
        games = get_games_from_db(conn)
        return render_template("index.html", games=games)
    finally:
        release_connection(conn)

@app.route("/health")
def health():
    return {"status": "ok"}

@app.route("/admin")
def admin():
    conn = get_connection()
    try:
        games = get_games_from_db(conn)
        return render_template("admin.html", games=games)
    finally:
        release_connection(conn)

@app.route("/admin/game/<int:game_id>", methods=["POST"])
def update_asin(game_id):
    asin = request.form.get("asin")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Désactive l'ancien produit
            cur.execute("""
                UPDATE products SET is_available = FALSE 
                WHERE game_id = %s AND asin != %s
            """, (game_id, asin))

            # Upsert le nouveau
            cur.execute("""
                INSERT INTO products (game_id, asin, is_manual, is_available)
                VALUES (%s, %s, TRUE, TRUE)
                ON CONFLICT (asin) DO UPDATE SET
                    game_id = EXCLUDED.game_id,
                    is_manual = TRUE,
                    is_available = TRUE
            """, (game_id, asin))

        conn.commit()
        flash("ASIN mis à jour !", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Erreur : {e}", "error")
    finally:
        release_connection(conn)

    return redirect("/admin")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)