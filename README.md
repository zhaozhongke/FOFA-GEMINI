# Production-Grade FOFA Gemini Key Scanner

This project provides a suite of tools to find and validate publicly exposed Google Gemini API keys using the FOFA API. It is designed with production-readiness in mind, featuring a resilient, asynchronous scanner and a web dashboard for viewing historical results. The entire application is containerized with Docker for easy deployment and management.

## Features

- **Asynchronous Scanner**: Uses `asyncio` and `httpx` for high-performance, non-blocking network I/O.
- **Resilient**: Implements exponential backoff to handle API rate limits and transient network errors gracefully.
- **Web Dashboard**: A Flask-based web interface to view the history of all scan results.
- **Production Ready**:
    - Runs the web app via a Gunicorn WSGI server.
    - Containerized with Docker for consistent and portable deployments.
    - Prioritizes environment variables for secure secret management.
    - Includes a wrapper script for easy automation with `cron`.
- **Configurable**: Non-sensitive settings are managed in a `config.yaml` file.
- **Structured Logging**: Outputs JSON-formatted logs for easy parsing and monitoring.

## Prerequisites

*   Python 3.7+
*   Docker
*   A FOFA account with API credentials.

## Project Structure

```
.
├── Dockerfile              # Instructions to build the Docker image
├── config.yaml             # Configuration for the scanner
├── dashboard.py            # The Flask web dashboard application
├── main.py                 # The main asynchronous scanner script
├── requirements.txt        # Python dependencies
├── run_scanner.sh          # Wrapper script for automated scanning
├── templates/
│   └── index.html          # HTML template for the web dashboard
└── wsgi.py                 # WSGI entry point for Gunicorn
```

## Local Development & Usage

### 1. Installation

Clone the repository and install the required Python packages:
```bash
git clone <repository_url>
cd <repository_name>
pip install -r requirements.txt
```

### 2. Configuration

Secrets (FOFA credentials) are managed via environment variables. Non-sensitive parameters are in `config.yaml`.

Set your credentials as environment variables:
```bash
export FOFA_EMAIL="your_fofa_email@example.com"
export FOFA_KEY="your_fofa_api_key"
```
Alternatively, you can edit `config.yaml`, but this is not recommended for production.

### 3. Running the Scanner Manually

You can run a one-off scan using the wrapper script:
```bash
./run_scanner.sh
```
This will run the scan and save the results to the `scans.db` SQLite database.

### 4. Running the Web Dashboard Locally

To run the dashboard with the Flask development server:
```bash
python3 dashboard.py
```
Then open your browser to `http://127.0.0.1:8080`.

---

## Production Deployment with Docker

The recommended way to run this application in production is using the provided Dockerfile.

### 1. Build the Docker Image

From the project root directory, run the build command:
```bash
docker build -t fofa-scanner-dashboard .
```

### 2. Run the Web Dashboard Container

Run the web dashboard as a daemonized container. You must pass your FOFA secrets as environment variables.

```bash
docker run -d \
  --name fofa-dashboard \
  -p 8080:8080 \
  -e FOFA_EMAIL="your_fofa_email@example.com" \
  -e FOFA_KEY="your_fofa_api_key" \
  -v $(pwd)/scans.db:/app/scans.db \
  fofa-scanner-dashboard
```
**Explanation:**
*   `-d`: Runs the container in detached mode.
*   `--name fofa-dashboard`: Assigns a name to the container.
*   `-p 8080:8080`: Maps port 8080 on your host to port 8080 in the container.
*   `-e FOFA_EMAIL=...`: Sets the FOFA_EMAIL environment variable inside the container.
*   `-e FOFA_KEY=...`: Sets the FOFA_KEY environment variable inside the container.
*   `-v $(pwd)/scans.db:/app/scans.db`: **(Important)** Mounts the `scans.db` file from your host into the container. This ensures the database persists even if the container is removed and allows the scanner (running outside the container) to write to it.

You can now access the dashboard at `http://<your_server_ip>:8080`.

### 3. Automated Scanning with Cron

The scanner script should be run periodically from the host machine using a scheduler like `cron`. The scanner will write to the `scans.db` file, and the running Docker container will read from it.

1.  Make sure `run_scanner.sh` is executable: `chmod +x run_scanner.sh`.
2.  Edit your crontab: `crontab -e`.
3.  Add a line to schedule the job. For example, to run the scan every day at 3 AM:
    ```crontab
    0 3 * * * /path/to/your/project/run_scanner.sh >> /path/to/your/project/scanner.log 2>&1
    ```
    **Remember to replace `/path/to/your/project/` with the actual absolute path to the `run_scanner.sh` script.**
