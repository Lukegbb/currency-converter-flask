"""Currency converter - Flask app using live exchange rates."""
import os
import time

import requests
from flask import Flask, jsonify, render_template, request

RATES_URL = "https://api.exchangerate-api.com/v4/latest/{base}"
CACHE_SECONDS = 60 * 60
SUPPORTED = ["EUR", "USD", "GBP", "BRL", "CAD", "AUD", "JPY", "CHF", "CNY", "INR", "PLN", "SEK"]


class RateProvider:
    """Fetches exchange rates and keeps them in memory for an hour,
    so we don't call the external API on every conversion."""

    def __init__(self, ttl=CACHE_SECONDS, clock=time.monotonic):
        self.ttl = ttl
        self.clock = clock
        self._cache = {}

    def get_rates(self, base):
        cached = self._cache.get(base)
        if cached and self.clock() - cached[0] < self.ttl:
            return cached[1]
        response = requests.get(RATES_URL.format(base=base), timeout=5)
        response.raise_for_status()
        rates = response.json()["rates"]
        self._cache[base] = (self.clock(), rates)
        return rates


def error(message, status=400):
    return jsonify({"error": message}), status


def create_app(provider=None):
    app = Flask(__name__)
    rates = provider or RateProvider()

    @app.get("/")
    def index():
        return render_template("index.html", currencies=SUPPORTED)

    @app.get("/api/currencies")
    def currencies():
        return jsonify(SUPPORTED)

    @app.post("/convert")
    def convert():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return error("Request body must be JSON.")

        base = str(data.get("base", "")).upper()
        target = str(data.get("target", "")).upper()
        if base not in SUPPORTED or target not in SUPPORTED:
            return error("Unsupported currency.")

        try:
            amount = float(data.get("amount"))
        except (TypeError, ValueError):
            return error("Amount must be a number.")
        if amount <= 0:
            return error("Amount must be greater than 0.")

        if base == target:
            rate = 1.0
        else:
            try:
                rate = rates.get_rates(base)[target]
            except (requests.RequestException, KeyError, ValueError):
                return error("Exchange rates are unavailable right now. Please try again.", 503)

        return jsonify({
            "base": base,
            "target": target,
            "amount": amount,
            "rate": rate,
            "converted_amount": round(amount * rate, 2),
        })

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
