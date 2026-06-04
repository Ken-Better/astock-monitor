# A股重大利好监控 v5

Cloud monitor for A-share bullish events. It runs on GitHub Actions, publishes to GitHub Pages, and can push major signals to your phone.

## Live Site

https://ken-better.github.io/astock-monitor/

## What It Does

- Scans public finance/news sources during A-share market hours.
- Scores major bullish events by source weight, keyword strength, authority, specificity, and risk words.
- Maps events to affected sectors and high-attention stocks.
- Generates trade plans with entry logic, position cap, stop loss, take profit, and time stop.
- Publishes `deploy/index.html` and `deploy/data.json` to GitHub Pages.
- Refreshes the web page data every 60 seconds.

## Schedule

- Monday to Friday, China time 09:20-15:05.
- GitHub Actions is scheduled every minute inside that window.
- `run.py` also checks the market window, so accidental outside-hours runs do not create noisy scans.

## Phone Push

Configure any of these in GitHub repository settings:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `SERVERCHAN_KEY`
- `BARK_KEY`
- `BARK_SERVER`
- `PUSHPLUS_KEY`

The notifier deduplicates the same signal fingerprint during the same day.

## Project Structure

```text
.
├── .github/workflows/monitor.yml
├── run.py
├── monitor/
│   ├── config.py
│   ├── scraper.py
│   ├── engine.py
│   ├── dashboard.py
│   ├── notifier.py
│   ├── auto_deploy.py
│   └── market_data.py
├── deploy/
│   ├── index.html
│   └── data.json
└── requirements.txt
```

## Risk Note

This project is an event-monitoring and trading-plan assistant. It is not financial advice. Default single-stock exposure is capped at 12%, and same-sector concentration should be controlled separately.
