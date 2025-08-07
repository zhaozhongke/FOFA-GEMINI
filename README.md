# Production-Grade FOFA Gemini Key Scanner

This script searches the FOFA search engine for publicly exposed Google Gemini API keys. It uses a modern, asynchronous architecture to validate found keys concurrently and efficiently.

This tool is based on the principles outlined in the "Automated Reconnaissance and Defense of Gemini API Key Leakage" report, focusing on performance, resiliency, and maintainability.

## Features

- **Asynchronous**: Uses `asyncio` and `httpx` for high-performance, non-blocking network I/O.
- **Resilient**: Implements exponential backoff with the `backoff` library to handle API rate limits and transient network errors gracefully.
- **Configurable**: All settings are managed in a `config.yaml` file, separating configuration from code.
- **Structured Logging**: Outputs JSON-formatted logs for easy parsing and monitoring in a production environment.
- **Producer-Consumer Model**: Efficiently fetches data from FOFA and validates keys in parallel using an `asyncio.Queue`.

## Prerequisites

* Python 3.7+
* A FOFA account with API credentials.

## Installation

1.  Clone this repository.
2.  Install the required Python packages using `pip`:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  Rename `config.yaml.example` to `config.yaml` (or create a new `config.yaml`).
2.  Open `config.yaml` and enter your FOFA email and API key:
    ```yaml
    fofa:
      email: "your_fofa_email@example.com"
      key: "your_fofa_api_key"
      # You can also customize the query and other parameters here.
      query: 'body="AIzaSy"'
    ```
    *Note: The placeholder credentials in `config.yaml` should be replaced before running the script.*

## Usage

### Running the Scanner

To run the scanner, simply execute the `main.py` script:

```bash
python3 main.py
```

The script will output structured logs to the console. At the end of the scan, it will save any found valid keys to `valid_keys.txt` and record the overall statistics in the `scans.db` database.

### Viewing the Dashboard

To view the history of scan results on a web interface:

1.  Make sure you have installed all the dependencies: `pip install -r requirements.txt`
2.  Run the Flask web server:
    ```bash
    python3 dashboard.py
    ```
3.  Open your web browser and navigate to `http://127.0.0.1:8080`.

You will see a dashboard with a table of all previous scan results.

### Logging

The logging level and format can be customized in the `logging` section of the `config.yaml` file. By default, it logs `INFO` level messages and above in JSON format.
