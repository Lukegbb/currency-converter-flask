# Currency Converter

![CI](https://github.com/Lukegbb/currency-converter-flask/actions/workflows/ci.yml/badge.svg)

A small web app for converting between currencies using live exchange rates. The backend is **Flask** and the page uses **Bootstrap** and plain JavaScript.

## Features

- Converts between 12 currencies (EUR, USD, GBP, BRL, CAD, AUD, JPY and others)
- Live rates from [ExchangeRate-API](https://www.exchangerate-api.com/), cached in memory for one hour to avoid unnecessary API calls
- Shows the rate used, e.g. `1 EUR = 1.0850 USD`
- Swap button and amounts formatted per currency (`€100.00 = $108.50`)
- History of the last 10 conversions, saved in the browser
- Input validation with clear JSON errors (`400`), and a `503` if the rates API is down
- Unit tests with a fake rate provider, so they run offline, on GitHub Actions

## Running locally

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py                  # http://127.0.0.1:5000
```

Set `FLASK_DEBUG=1` to run in debug mode.

## API

`POST /convert`

```json
{ "base": "EUR", "target": "USD", "amount": 100 }
```

Response:

```json
{ "base": "EUR", "target": "USD", "amount": 100.0, "rate": 1.085, "converted_amount": 108.5 }
```

`GET /api/currencies` returns the list of supported currencies.

## Tests

```bash
python -m unittest discover -s tests -t . -v
```

## Project structure

```
├── app.py              # Flask app, validation and rate caching
├── templates/index.html
├── static/style.css
└── tests/test_app.py
```
