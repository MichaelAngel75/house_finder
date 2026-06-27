
# House Finder

Local Python application for searching real estate listings and classifying potential **remate** properties using the OpenAI API.

> **Current status**
>
> This README documents the **first prototype**, which attempted direct crawling of real estate websites. During testing, Propiedades.com returned HTTP/2 protocol errors and request timeouts, so the next version of the project will migrate to a Search API discovery architecture.

---

# Current Architecture

```text
CSV Input
    ↓
Criteria Validation
    ↓
Website Connector
    ↓
Listing Extraction
    ↓
Rule-based Filters
    ↓
OpenAI Classification
    ↓
SQLite Cache
    ↓
CSV Output
```

# Requirements

- macOS
- Python 3.11+
- SQLite
- OpenAI API Key
- Playwright (optional)

## Verify Python

```bash
python3 --version
```

## Verify SQLite

```bash
sqlite3 --version
```

# Create Virtual Environment

```bash
python3 -m venv .houseSearch
source .houseSearch/bin/activate
```

# Install Dependencies

```bash
pip install --upgrade pip

pip install pandas pydantic python-dotenv openai requests beautifulsoup4 typer rich sqlalchemy playwright
```

Install Chromium:

```bash
python3 -m playwright install chromium
```

# Environment Variables

Create `.env`

```text
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4.1-mini

REQUEST_TIMEOUT_SECONDS=8
DELAY_BETWEEN_REQUESTS_SECONDS=1
MAX_PAGES_PER_SITE=1
MAX_RESULTS_PER_SITE=100

DATABASE_URL=sqlite:///house_finder.db
```

# Input File

Filename:

```
input.csv
```

Required columns:

| Column | Description |
|---------|-------------|
| operation | buy or rent |
| min_range | Minimum MXN price |
| max_range | Maximum MXN price |
| bedroom | Minimum bedrooms |
| baths | Minimum bathrooms |
| colonies | Pipe-separated neighborhoods |

Example:

```csv
operation,min_range,max_range,bedrooms,baths,colonies
compra,600000,24200000,2,1,portales|narvarte|roma|campestre churubusco
```

# Output File

```
output.csv
```

Columns:

- portal
- title
- price
- location
- bedrooms
- bathrooms
- description
- url
- is_remate
- remate_stage
- risk_level
- include
- reason

# Running

```bash
source .houseSearch/bin/activate

python3 main.py --input-file input.csv --output-file output.csv
```

# Database

SQLite database created automatically:

```
house_finder.db
```

Inspect it:

```bash
sqlite3 house_finder.db
```

Useful commands:

```sql
.tables
SELECT COUNT(*) FROM listings;
.quit
```

# Known Limitation

The first implementation attempted direct crawling of Propiedades.com and encountered:

- HTTP/2 protocol errors
- Read timeouts
- Browser automation failures
- No reliable listing extraction

Because of this, the project will move to a Search API-based architecture.

# Planned Version 2

```text
CSV Input
    ↓
Query Builder
    ↓
Search API (SerpAPI / Google CSE / Bing)
    ↓
Candidate URLs
    ↓
Page Fetcher
    ↓
Listing Extractor
    ↓
OpenAI Classifier
    ↓
SQLite Cache
    ↓
CSV / Excel Output
```

Planned modules:

```text
search/
fetchers/
extractors/
database/
llm/
exporters/
```

# Safety

- Respect robots.txt when applicable.
- Respect website Terms of Service.
- Rate-limit requests.
- Cache results.
- Do not bypass authentication or access controls.

# Project Status

Completed:

- CSV input
- SQLite support
- OpenAI integration
- Initial connector framework
- Local execution

Next milestone:

Replace direct website crawling with Search API URL discovery.
