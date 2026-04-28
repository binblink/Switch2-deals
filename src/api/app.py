from flask import Flask, jsonify
from src.db.connection import get_connection

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"message": "SwitchDeals API running yaaayyyy"})

@app.route("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)