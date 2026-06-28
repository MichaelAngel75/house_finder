# Mexico House Finder v2

## Overview

Mexico House Finder v2 is a Python application that discovers residential property listings across multiple Mexican real estate websites, evaluates whether they appear to be **bank-owned foreclosure opportunities (remates bancarios)**, and filters out high-risk opportunities using OpenAI.

Unlike the original version, this project **does not rely on crawling a single real estate website**. Instead, it uses a pluggable search provider architecture that discovers candidate URLs from search engines before optionally fetching page content.

This makes the application significantly more robust, scalable, and easier to maintain.

---

# Why Version 2?

## Problems with Version 1

The original implementation attempted to scrape websites such as:

* Propiedades.com
* Inmuebles24
* Lamudi

Typical problems encountered:

* HTTP/2 protocol errors
* Timeouts
* Dynamic JavaScript rendering
* Anti-bot protections
* Website HTML changes
* Frequent selector failures

Example:

```
Found raw listings: 0
```

while manually browsing the same website clearly showed many matching properties.

The application was spending most of its effort trying to bypass website protections rather than solving the actual business problem.

---

# Version 2 Solution

Instead of scraping websites directly, Version 2 works like this:

```
Search Criteria
        │
        ▼
Search Provider
(Google / SerpAPI / Mock)
        │
        ▼
Candidate URLs
        │
        ▼
Deduplication
        │
        ▼
(Optional)
Page Fetch
(Requests / Playwright)
        │
        ▼
OpenAI Classifier
        │
        ▼
SQLite Cache
        │
        ▼
CSV Output
```

This architecture separates:

* discovering listings
* reading pages
* evaluating risk

into independent modules.

---

# Architecture

```
searching-houses-v2/

│
├── main.py
├── config.py
├── models.py
├── database.py
├── classifier.py
├── exporter.py
├── query_builder.py
├── dedupe.py
│
├── search_providers/
│     ├── __init__.py
│     ├── base.py
│     ├── mock.py
│     ├── serpapi.py
│     ├── google_custom_search.py
│     └── bing.py
│
├── fetchers/
│     ├── __init__.py
│     ├── base.py
│     ├── requests_fetcher.py
│     └── playwright_fetcher.py
│
├── input.csv
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

# Features

* Modular architecture
* SQLite caching
* Duplicate detection
* Search provider abstraction
* Mock provider for offline development
* Google Custom Search support
* SerpAPI support
* Optional Playwright page fetching
* OpenAI classification
* CSV export
* Easily extensible

---

# Requirements

* Python 3.11+
* SQLite
* macOS / Linux / Windows
* OpenAI API Key

Optional:

* Google Custom Search API
* SerpAPI
* Playwright Chromium

---

# Installation

Clone the repository.

Create a virtual environment:

```bash
python3 -m venv .houseSearch
```

Activate it:

macOS / Linux

```bash
source .houseSearch/bin/activate
```

Windows

```bash
.houseSearch\\Scripts\\activate
```

Install dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Install Playwright browser (optional):

```bash
python3 -m playwright install chromium
```

---

# Environment Variables

Copy the example file.

```bash
cp .env.example .env
```

Example:

```env
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4.1-mini

SEARCH_PROVIDER=mock

SERPAPI_API_KEY=

GOOGLE_API_KEY=
GOOGLE_SEARCH_ENGINE_ID=

DATABASE_URL=sqlite:///house_finder.db

ENABLE_LIVE_FETCH=false
ENABLE_PLAYWRIGHT_FALLBACK=false
```

---

# Search Providers

Currently supported:

| Provider | Purpose                       |
| -------- | ----------------------------- |
| mock     | Local development             |
| google   | Google Programmable Search    |
| serpapi  | Google search through SerpAPI |
| bing     | Legacy only                   |

Switch provider by changing:

```env
SEARCH_PROVIDER=mock
```

or

```env
SEARCH_PROVIDER=google
```

or

```env
SEARCH_PROVIDER=serpapi
```

No application code changes are required.

---

# Input File

The application expects a CSV file.

Example:

```csv
operacion,rango_min,rango_max,recamaras,banios,colonias
compra,600000,24200000,2,1,portales|narvarte|roma|campestre churubusco
```

Columns:

| Column    | Description                  |
| --------- | ---------------------------- |
| operacion | compra / renta               |
| rango_min | Minimum price                |
| rango_max | Maximum price                |
| recamaras | Minimum bedrooms             |
| banios    | Minimum bathrooms            |
| colonias  | Pipe-separated neighborhoods |

---

# Output File

The application produces:

```
output.csv
```

Columns include:

* criteria_id
* title
* snippet
* url
* source_domain
* is_remate
* remate_stage
* risk_level
* include
* confidence
* reason
* red_flags

---

# SQLite Database

The application automatically creates:

```
house_finder.db
```

Tables:

* search_runs
* criteria
* candidate_urls
* classifications

Inspect the database:

```bash
sqlite3 house_finder.db
```

Useful commands:

```sql
.tables

SELECT COUNT(*) FROM candidate_urls;

SELECT COUNT(*) FROM classifications;

.quit
```

---

# Running

Local testing (Mock):

```bash
python3 main.py \
  --input-file input.csv \
  --output-file output.csv
```

Using Google:

```
SEARCH_PROVIDER=google
```

Using SerpAPI:

```
SEARCH_PROVIDER=serpapi
```

---

# How OpenAI Is Used

OpenAI **does not search the web**.

Instead, it evaluates candidate listings.

It determines:

* Is this actually a remate?
* What legal stage appears to be described?
* Does it appear low risk?
* Should it be included?

The model only evaluates candidate URLs discovered by the search provider.

---

# Current Risk Rules

Include:

* Escriturado
* Adjudicado
* Listo para escriturar
* Clear legal status

Reject:

* Cesión de derechos litigiosos
* Juicio pendiente
* Sin posesión
* Ocupado
* No visitable
* Legal stage unclear

---

# Future Improvements

* React dashboard
* FastAPI REST API
* Scheduled searches
* Email notifications
* Historical price tracking
* Duplicate detection across portals
* Excel export
* Property image extraction
* Vector search for semantic matching
* Public registry integration
* AI summarization of listings
* Multi-user authentication

---

# Why This Architecture

Instead of solving:

> "How do I scrape every real estate website?"

the application now solves:

> "Given candidate property URLs, determine whether they represent legitimate, low-risk foreclosure opportunities."

This separation of responsibilities results in:

* easier maintenance
* lower coupling
* simpler testing
* improved scalability
* easier addition of new search providers
* easier migration to cloud infrastructure

---

# License

This project is intended for educational and research purposes.

Always review the Terms of Service of any website before fetching content, respect robots.txt where appropriate, and prefer official APIs whenever they are available.
