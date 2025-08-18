from fastapi import FastAPI, Request
from pathlib import Path
import json, requests, datetime

app = FastAPI()

# --- Config ---
FILE_PATH = Path("./etfs.json")  # local file path
HARD_LIMIT = 60  # portfolio loss threshold
PER_STOCK_LIMIT = 35  # max loss per stock (EUR)

# --- Default Data ---
DEFAULT_ETFS = [{
    "sy": "AAPL",
    "op": 32.9828,
    "s": "a",
    "p": 2500
}, {
    "sy": "MSFT",
    "op": 102.922,
    "s": "a",
    "p": 5500
}, {
    "sy": "TSLA",
    "op": 56.345,
    "s": "a",
    "p": 2500
}, {
    "sy": "NVDA",
    "op": 104.1299,
    "s": "a",
    "p": 6700
}, {
    "sy": "PLNT",
    "op": 18.71,
    "s": "a",
    "p": 2500
}, {
    "sy": "AMZN",
    "op": 91.66,
    "s": "a",
    "p": 6900
}]


# --- Helpers ---
def load_etfs():
  if not FILE_PATH.exists():
    FILE_PATH.write_text(json.dumps(DEFAULT_ETFS, indent=2))
  return json.loads(FILE_PATH.read_text())


def save_etfs(etfs):
  now = datetime.datetime.now().hour
  if 8 < now <= 22:  # Update file only during market hours
    FILE_PATH.write_text(json.dumps(etfs, indent=2))


def fetch_quote(sy, api_key):
  url = f"https://finnhub.io/api/v1/quote?symbol={sy}&token={api_key}"
  r = requests.get(url, timeout=5)
  r.raise_for_status()
  return r.json()


# --- API Endpoint ---
@app.get("/check")
def check_portfolio(request: Request):
  api_key = request.headers.get("x-api-key")

  if not api_key:
    return {"error": "Missing API key in headers"}

  etfs = load_etfs()
  alerts = []
  total_loss = 0.0

  for etf in etfs:
    if etf["s"] != "a":
      continue

    if etf["p"] > 0 and etf["op"] > 0:

      data = fetch_quote(etf["sy"], api_key)
      current = data.get("c")
      open_price = data.get("o")
      etf_count = int(etf["p"] / etf["op"])
      stop_price = open_price - (PER_STOCK_LIMIT / etf_count)

      if current < stop_price:
        alerts.append(
            f"STOP LOSS for {etf['sy']}: Current {current:.4f} < Limit {stop_price:.4f}"
        )
        # loss = (entry price - current price) * ( position size / etf price)
        loss = (open_price - current) * etf_count
        total_loss += loss

      # update ETF stored open price if API gives one
      etf["op"] = open_price

  # save file once after loop
  save_etfs(etfs)

  if total_loss >= HARD_LIMIT:
    alerts.append(f"⚠️ Total portfolio loss approx €{total_loss:.2f}")

  return {"alerts": alerts}
