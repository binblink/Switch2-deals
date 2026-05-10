from asyncio.log import logger

from flask import Flask, jsonify, flash, redirect, request
from db.connection import get_connection, release_connection
from db.queries import get_games_from_db, upsert_product
from amazon.sync import refresh_product
from flask import render_template
import os
from playwright.sync_api import sync_playwright
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

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
        upsert_product(conn, game_id, asin)
        success = refresh_product(conn, asin)
        flash("ASIN mis à jour !" if success else "Produit indisponible sur Amazon", 
              "success" if success else "error")
    except Exception as e:
        flash(f"Erreur : {e}", "error")
    finally:
        release_connection(conn)
    return redirect("/admin")

@app.route("/admin/game/<int:game_id>/exclude", methods=["POST"])
def toggle_exclude(game_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE games SET is_excluded = NOT is_excluded WHERE id = %s RETURNING is_excluded
            """, (game_id,))
            new_status = cur.fetchone()[0]
        conn.commit()
        flash("Jeu exclu des résultats." if new_status else "Jeu réintégré aux résultats.", 
              "info")
    except Exception as e:
        flash(f"Erreur : {e}", "error")
        conn.rollback()
    finally:
        release_connection(conn)
    return redirect("/admin")

@app.route("/admin/bulk-exclude", methods=["POST"])
def bulk_exclude():
    game_ids = request.form.getlist("game_ids")
    if not game_ids:
        flash("Aucun jeu sélectionné.", "error")
        return redirect("/admin")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE games SET is_excluded = TRUE 
                WHERE id = ANY(%s::integer[])
            """, (game_ids,))
        conn.commit()
        flash(f"{len(game_ids)} jeux exclus.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Erreur : {e}", "error")
    finally:
        release_connection(conn)
    return redirect("/admin")

@app.route("/api/game/<int:game_id>/prices")
def get_game_prices(game_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT pr.price, pr.scraped_at
                FROM prices pr
                JOIN products p ON p.id = pr.product_id
                WHERE p.game_id = %s
                ORDER BY pr.scraped_at ASC
            """, (game_id,))
            rows = cur.fetchall()
            return jsonify([
                {
                    "price": float(row[0]),
                    "scraped_at": row[1].isoformat()
                }
                for row in rows
            ])
    finally:
        release_connection(conn)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)