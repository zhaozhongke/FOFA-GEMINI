import asyncio
import base64
import logging
import logging.config
import re
import sqlite3
from collections import Counter
from datetime import datetime
from typing import List, Dict, Any, Tuple

import httpx
import yaml
import fofa
import backoff

# --- Custom Exceptions for Backoff ---

class ApiRateLimitError(Exception):
    """Custom exception for HTTP 429 Too Many Requests."""
    pass

class ApiServerError(Exception):
    """Custom exception for HTTP 5xx server errors."""
    pass

# --- Configuration and Logging ---

def setup_logging(config_path='config.yaml'):
    """Loads logging configuration from the YAML file."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            if 'logging' in config:
                logging.config.dictConfig(config['logging'])
            else:
                logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
                logging.warning("No 'logging' section in config, using basic config.")
    except FileNotFoundError:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
        logging.error(f"Config file not found at {config_path}, using basic logging.")

def load_config(config_path='config.yaml') -> Dict[str, Any]:
    """Loads the main configuration from the YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logging.error(f"Config file not found at {config_path}. Exiting.")
        exit(1)

# --- FOFA Client ---

class FofaClient:
    """A client to interact with the FOFA API."""
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.email = config.get('email')
        self.key = config.get('key')
        self.query = config.get('query')
        self.page_size = config.get('page_size', 100)

        if not self.email or not self.key:
            self.logger.critical("FOFA email or key not found in config. Exiting.")
            exit(1)

        self.client = fofa.Client(self.email, self.key)

    def search(self, page: int) -> List[Tuple]:
        """Performs a search for a given page."""
        self.logger.info(f"Searching FOFA page {page} for query: {self.query}")
        try:
            data = self.client.search(self.query, page=page, size=self.page_size, fields="host,ip,port,data")
            if "results" in data:
                return data["results"]
            if data.get("error"):
                self.logger.error(f"FOFA API Error: {data.get('errmsg')}")
            return []
        except Exception as e:
            self.logger.error(f"An unexpected error occurred while querying FOFA: {e}", exc_info=True)
            return []

# --- Key Validator ---

def is_fatal_code(e):
    """Determines if an HTTP error is fatal (should not be retried)."""
    if not isinstance(e, httpx.HTTPStatusError):
        return False
    # Do not retry on client errors (4xx) other than 429.
    return 400 <= e.response.status_code < 500 and e.response.status_code != 429

class KeyValidator:
    """Validates Google API keys concurrently with resiliency."""
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.validation_url = "https://generativelanguage.googleapis.com/v1beta/models?key={}"
        self.gemini_key_pattern = re.compile(r"AIzaSy[a-zA-Z0-9_-]{33}")

    def find_potential_keys(self, text: str) -> List[str]:
        """Finds all potential Gemini keys in a given text."""
        return self.gemini_key_pattern.findall(text)

    @backoff.on_exception(backoff.expo,
                          (httpx.RequestError, ApiRateLimitError, ApiServerError),
                          max_tries=5,
                          giveup=is_fatal_code,
                          logger=logging.getLogger(__name__),
                          on_backoff=lambda details: logging.warning(f"Backing off {details['wait']:.1f}s after {details['tries']} tries for key {details['args'][1][:10]}..."))
    async def validate_key(self, client: httpx.AsyncClient, key: str, context: Dict) -> Tuple[str, str, Dict]:
        """
        Validates a single key with backoff for retries.
        Returns a tuple of (status, key, context).
        """
        self.logger.debug(f"Validating key: {key[:10]}... from host {context.get('host')}")
        response = await client.get(self.validation_url.format(key=key), timeout=10)

        if response.status_code == 200:
            self.logger.info(f"VALID key found: {key[:10]}... at {context.get('host')}")
            return "VALID_UNRESTRICTED", key, context
        elif response.status_code == 400 and "API key not valid" in response.text:
            self.logger.debug(f"Invalid key: {key[:10]}...")
            return "INVALID", key, context
        elif response.status_code == 403:
            self.logger.warning(f"RESTRICTED key found: {key[:10]}... at {context.get('host')}")
            return "VALID_RESTRICTED", key, context
        elif response.status_code == 429:
            self.logger.warning(f"Rate limited on key {key[:10]}... Retrying.")
            raise ApiRateLimitError()
        elif response.status_code >= 500:
            self.logger.warning(f"Server error ({response.status_code}) on key {key[:10]}... Retrying.")
            raise ApiServerError()
        else:
            self.logger.debug(f"Unknown status for key {key[:10]}...: {response.status_code}")
            response.raise_for_status() # Raise HTTPStatusError for other 4xx codes to trigger 'giveup'
            return "UNKNOWN", key, context

# --- Main Orchestrator ---

async def worker(name: str, queue: asyncio.Queue, validator: KeyValidator, http_client: httpx.AsyncClient, valid_keys: list, stats_counter: Counter):
    """A worker task that consumes from the queue and validates keys."""
    logger = logging.getLogger(name)
    while True:
        key, context = await queue.get()
        status = "ERROR" # Default status
        try:
            status, validated_key, ctx = await validator.validate_key(http_client, key, context)
            if status.startswith("VALID"):
                valid_keys.append((status, validated_key, ctx))
        except Exception as e:
            logger.error(f"Failed to validate key from host {context.get('host')} after all retries: {e}")
        finally:
            stats_counter[status] += 1
            queue.task_done()


async def main():
    """Main function to orchestrate the scanning process."""
    setup_logging()
    config = load_config()
    logger = logging.getLogger(__name__)

    fofa_config = config.get('fofa', {})
    validator_config = config.get('validator', {})

    fofa_client = FofaClient(fofa_config)
    validator = KeyValidator(validator_config)

    key_queue = asyncio.Queue()
    valid_keys_found = []
    stats_counter = Counter()
    total_potential_keys = 0

    concurrency = validator_config.get('concurrency', 10)
    async with httpx.AsyncClient() as http_client:
        workers = [
            asyncio.create_task(worker(f"worker-{i}", key_queue, validator, http_client, valid_keys_found, stats_counter))
            for i in range(concurrency)
        ]

        logger.info(f"Starting scan with {concurrency} workers.")
        for page_num in range(1, 6): # Limiting to 5 pages for this example
            results = fofa_client.search(page=page_num)
            if not results:
                logger.info("No more results from FOFA. Stopping producer.")
                break

            for host, ip, port, data_blob in results:
                context = {"host": host, "ip": ip, "port": port}
                potential_keys = set(validator.find_potential_keys(str(data_blob)))
                total_potential_keys += len(potential_keys)
                for key in potential_keys:
                    logger.debug(f"Queueing key from {host}")
                    await key_queue.put((key, context))

        await key_queue.join()
        logger.info("Key queue is empty. Cancelling workers.")

        for w in workers:
            w.cancel()
        await asyncio.gather(*workers, return_exceptions=True)

    logger.info(f"Scan complete. Found {len(valid_keys_found)} valid keys.")

    # --- Display Statistics ---
    print("\n--- Scan Statistics ---")
    print(f"Total potential keys found: {total_potential_keys}")
    print(f"Validation attempts: {sum(stats_counter.values())}")
    for status, count in stats_counter.items():
        print(f"  - {status}: {count}")
    print("-----------------------")

    if valid_keys_found:
        print("\n--- Found Valid Gemini Keys ---")
        with open("valid_keys.txt", "w") as f:
            for status, key, context in valid_keys_found:
                line = f"Status: {status}, Key: {key}, Host: {context.get('host')}, IP: {context.get('ip')}\n"
                print(line.strip())
                f.write(line)
        print("\nResults saved to valid_keys.txt")
    else:
        print("\nNo valid Gemini keys found.")

    save_stats_to_db(total_potential_keys, stats_counter)


def save_stats_to_db(total_keys: int, stats: Counter):
    """Saves the scan statistics to an SQLite database."""
    logger = logging.getLogger(__name__)
    db_file = "scans.db"
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_time TEXT NOT NULL,
                total_potential_keys INTEGER NOT NULL,
                valid_unrestricted INTEGER DEFAULT 0,
                valid_restricted INTEGER DEFAULT 0,
                invalid INTEGER DEFAULT 0,
                unknown INTEGER DEFAULT 0,
                error INTEGER DEFAULT 0
            )
        """)

        # Prepare data for insertion
        scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data_to_insert = {
            "scan_time": scan_time,
            "total_potential_keys": total_keys,
            "valid_unrestricted": stats.get("VALID_UNRESTRICTED", 0),
            "valid_restricted": stats.get("VALID_RESTRICTED", 0),
            "invalid": stats.get("INVALID", 0),
            "unknown": stats.get("UNKNOWN", 0),
            "error": stats.get("ERROR", 0)
        }

        # Insert a new record
        cursor.execute("""
            INSERT INTO scan_history (scan_time, total_potential_keys, valid_unrestricted, valid_restricted, invalid, unknown, error)
            VALUES (:scan_time, :total_potential_keys, :valid_unrestricted, :valid_restricted, :invalid, :unknown, :error)
        """, data_to_insert)

        conn.commit()
        logger.info(f"Successfully saved scan statistics to {db_file}")

    except sqlite3.Error as e:
        logger.error(f"Database error: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Scan interrupted by user.")
    except Exception as e:
        logging.getLogger(__name__).critical(f"A critical error occurred in main: {e}", exc_info=True)
