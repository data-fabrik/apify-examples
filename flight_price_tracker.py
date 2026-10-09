"""Track the cheapest price of one route and date; alert on a drop of more than 10 %.

Usage:
    python flight_price_tracker.py CDG JFK 2027-03-15 --currency EUR
    python flight_price_tracker.py --self-test

Run it once a day (cron, Windows Task Scheduler). Each run is one Actor search
($0.01 on the free plan, all flights of the search included) and appends one line
to flight_history.csv. The alert compares with the previous line of the same
route and date.

Token: environment variable APIFY_TOKEN, nothing else.
"""
import argparse
import csv
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ACTOR = "datafabrik/google-flights-scraper"
HISTORY = Path("flight_history.csv")
FIELDS = ["checkedAt", "origin", "destination", "departureDate", "currency", "cheapestPrice", "flightNumbers", "priceLevel"]
ALERT_DROP_PERCENT = 10


def drop_percent(previous, current):
    """Positive when the price went down. None when there is nothing to compare with."""
    if previous is None or previous <= 0:
        return None
    return (previous - current) / previous * 100


def last_price(origin, destination, departure_date):
    if not HISTORY.exists():
        return None
    with HISTORY.open(newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f)
                if (r["origin"], r["destination"], r["departureDate"]) == (origin, destination, departure_date)]
    return float(rows[-1]["cheapestPrice"]) if rows else None


def search(origin, destination, departure_date, currency):
    from apify_client import ApifyClient  # imported here so --self-test needs no network or package

    token = os.environ.get("APIFY_TOKEN")
    if not token:
        sys.exit("APIFY_TOKEN is not set (Apify Console -> Settings -> API & Integrations)")
    client = ApifyClient(token)
    run = client.actor(ACTOR).call(run_input={
        "origins": [origin],
        "destinations": [destination],
        "departureDates": [departure_date],
        "currency": currency,
        "maxFlightsPerSearch": 20,  # cheapest flights come first in Google's order; fewer rows, same price
    })
    items = list(client.dataset(run.default_dataset_id).iterate_items())
    flights = [i for i in items if i.get("type") == "flight" and i.get("price")]
    if not flights:
        statuses = {i.get("status") for i in items if i.get("type") != "flight"}
        sys.exit(f"no priced flight returned (search status: {statuses or 'unknown'}); nothing charged")
    cheapest = min(flights, key=lambda f: f["price"])
    return cheapest


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("origin", nargs="?", help="IATA airport or city code, e.g. CDG or PAR")
    p.add_argument("destination", nargs="?", help="e.g. JFK or NYC")
    p.add_argument("departure_date", nargs="?", help="YYYY-MM-DD")
    p.add_argument("--currency", default="USD")
    p.add_argument("--self-test", action="store_true", help="check the alert arithmetic without calling the API")
    args = p.parse_args()

    if args.self_test:
        assert drop_percent(None, 100) is None
        assert drop_percent(200, 170) == 15
        assert drop_percent(200, 210) == -5
        assert drop_percent(200, 170) > ALERT_DROP_PERCENT and not drop_percent(200, 185) > ALERT_DROP_PERCENT
        print("self-test ok")
        return
    if not (args.origin and args.destination and args.departure_date):
        p.error("origin, destination and departure_date are required (or --self-test)")

    previous = last_price(args.origin, args.destination, args.departure_date)
    cheapest = search(args.origin, args.destination, args.departure_date, args.currency)
    price = float(cheapest["price"])

    new_file = not HISTORY.exists()
    with HISTORY.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            w.writeheader()
        w.writerow({
            "checkedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "origin": args.origin, "destination": args.destination, "departureDate": args.departure_date,
            "currency": cheapest.get("currency", args.currency), "cheapestPrice": price,
            "flightNumbers": " ".join(cheapest.get("flightNumbers") or []),
            "priceLevel": cheapest.get("searchPriceLevel") or "",
        })

    drop = drop_percent(previous, price)
    line = f"{args.origin}->{args.destination} {args.departure_date}: {price:.0f} {cheapest.get('currency', args.currency)}"
    if drop is None:
        print(f"{line} (first record)")
    elif drop > ALERT_DROP_PERCENT:
        print(f"ALERT {line}, down {drop:.0f} % from {previous:.0f}")
    else:
        print(f"{line} ({drop:+.0f} % vs {previous:.0f})")


if __name__ == "__main__":
    main()
