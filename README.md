# apify-examples


Background and the direct-to-Google alternative: [pytrends is dead: 3 ways to get Google Trends data in 2026 (with code)](https://dev.to/datafabrik/pytrends-is-dead-3-ways-to-get-google-trends-data-in-2026-with-code-1i5i) on dev.to.
Three small, runnable scripts that call the Data Fabrik Actors on the Apify platform and do something useful with the result: a CSV of Google Trends data, a flight price history with a drop alert, and a 7-night rate-shopping table for one hotel.

| Script | Actor | What it does | Approximate cost per run |
|---|---|---|---|
| `google_trends_to_csv.py` | [Google Trends Scraper & API](https://apify.com/datafabrik/google-trends-scraper) | One call, one report per search line, flat rows written to `trends.csv` with pandas | $0.0025 per report on the free plan ($0.0010 on Gold); empty or failed searches are free |
| `flight_price_tracker.py` | [Google Flights Scraper & API](https://apify.com/datafabrik/google-flights-scraper) | Searches one route and date, appends the cheapest price to `flight_history.csv`, prints an alert when the price dropped by more than 10 % since the last run | $0.01 per search (all flights of the search included) |
| `hotel_rate_shopping.js` | [Google Hotels Scraper & API](https://apify.com/datafabrik/google-hotels-scraper) | One hotel, 7 consecutive nights, every booking site's offer, printed as a table | about $0.05 on the free plan (7 × ($0.0025 per hotel with a price + $0.004 per hotel with offers)) |

All prices are those listed on the Actor pages at the time of writing (October 2026); the Actor page is the reference.

## Prerequisites

- An Apify account (there is a free plan) and its API token: **Apify Console → Settings → API & Integrations**.
- Python 3.9+ for the two Python scripts: `pip install "apify-client>=3" pandas` (the scripts use the typed `Run` object of client 3.x)
- Node.js 18+ for the JavaScript script: `npm install apify-client`

## The token

The scripts read the token from the `APIFY_TOKEN` environment variable. They never ask for it as an argument and it is never written to a file in this repository.

```bash
# macOS / Linux
export APIFY_TOKEN=...
# Windows (PowerShell)
$env:APIFY_TOKEN = "..."
```

If the variable is missing, every script stops with a clear message before calling anything.

## Usage

```bash
# Google Trends: one report per argument; "a, b" compares up to 5 terms on the same scale
python google_trends_to_csv.py "bitcoin, ethereum" "solar panels" --geo US --range "today 12-m"

# Google Flights: one route, one date; run it daily (cron, Task Scheduler) to build the history
python flight_price_tracker.py CDG JFK 2027-03-15 --currency EUR
python flight_price_tracker.py --self-test        # checks the alert arithmetic, no API call

# Google Hotels: one hotel by name or Google Hotels link, 7 nights from the check-in date
node hotel_rate_shopping.js "Ritz Paris" 2027-03-01 EUR
```

## What the Actors return

- Google Trends values are Google's relative interest (0–100 for the terms, place and period of the report), not absolute search volumes.
- Flight prices are the total for all passengers at the time of the run, for the point of sale and currency you choose.
- Hotel prices are for the whole room for the number of adults you set; hotels without a price for the dates are returned free, with empty price fields.

The field names used in the scripts (`searchTerms`, `outputLayout`, `origins`, `departureDates`, `hotels`, `consecutiveDays`, `includeOffers`, `pricePerNight`, `cheapestOffer`…) are documented on each Actor page.

## License

MIT, see `LICENSE`.
