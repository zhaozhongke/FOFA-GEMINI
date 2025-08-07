# FOFA Gemini Key Scraper

This script searches the FOFA search engine for publicly exposed Google Gemini API keys. It then validates the found keys against the Google Gemini API to see if they are active.

## Prerequisites

* Python 3
* The `requests` Python package

## Installation

1. Clone this repository or download the `fofa_scraper.py` script.
2. Install the required Python package:
   ```bash
   pip install requests
   ```

## Configuration

This script requires a FOFA account and API key. You must set the following environment variables:

* `FOFA_EMAIL`: Your FOFA account email address.
* `FOFA_KEY`: Your FOFA API key.

You can set them in your shell like this:

```bash
export FOFA_EMAIL="your_email@example.com"
export FOFA_KEY="your_fofa_api_key"
```

## Usage

To run the script, simply execute it with Python:

```bash
python3 fofa_scraper.py
```

The script will print the potential keys it finds and then try to validate them. At the end, it will print a list of all the valid keys it found.

### Silent Mode

If you want to suppress the verbose output (e.g., the "Found potential key..." and "VALID key found..." messages), you can use the `--silent` or `-s` flag:

```bash
python3 fofa_scraper.py --silent
```

This will only print the final list of valid keys.
