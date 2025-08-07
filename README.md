# FOFA Gemini Key Scanner & Dashboard

This project provides a suite of tools to find and validate publicly exposed Google Gemini API keys using the FOFA API. It is designed with production-readiness in mind, featuring a resilient, asynchronous scanner and a web dashboard for viewing historical results. The entire application is containerized and managed with Docker and Docker Compose for easy, one-click deployment.

---

### [English](#english-documentation) | [中文文档](#chinese-documentation-中文文档)

---

## English Documentation

### Overview

This application consists of two main components, managed by `docker-compose`:
1.  **Scanner**: A Python script that runs on a schedule (or manually), scans for keys, validates them, and saves the statistics to a shared database.
2.  **Dashboard**: A Flask web application that displays the historical scan data from the database.

### Prerequisites

*   [Docker](https://www.docker.com/get-started)
*   [Docker Compose](https://docs.docker.com/compose/install/)
*   A FOFA account with API credentials.

### 🚀 One-Click Deployment

**1. Clone the Repository**
```bash
git clone <repository_url>
cd <repository_name>
```

**2. Configure Your Credentials**

Copy the example environment file to a new `.env` file:
```bash
cp .env.example .env
```
Now, open the `.env` file with a text editor and enter your FOFA email and API key:
```
# .env
FOFA_EMAIL=your_fofa_email@example.com
FOFA_KEY=your_fofa_api_key
```
This file is used by `docker-compose` to securely pass your secrets to the application containers.

**3. Launch the Application**

Run the following command from the project root directory:
```bash
docker-compose up -d
```
This command will:
-   Build the Docker image for the application.
-   Start the `dashboard` web server in the background.
-   Make the dashboard available at `http://localhost:8080`.

### Usage

*   **View the Dashboard**: Open your web browser and navigate to `http://localhost:8080`.
*   **Run a Manual Scan**: To trigger a scan immediately, run the `scanner` service:
    ```bash
    docker-compose run --rm scanner
    ```
    After the scan completes, refresh the dashboard to see the new results.
*   **View Logs**: To see the logs for the web dashboard:
    ```bash
    docker-compose logs -f dashboard
    ```
*   **Stop the Application**: To stop and remove the containers:
    ```bash
    docker-compose down
    ```

### Automated Scanning

For fully automated 24/7 operation, you should schedule the scanner to run periodically. You can do this on the host machine using `cron`.

1.  Open your crontab for editing: `crontab -e`
2.  Add a line to run the `docker-compose run` command on a schedule. For example, to run a scan every day at 2:00 AM:
    ```crontab
    0 2 * * * cd /path/to/your/project && docker-compose run --rm scanner
    ```
    **Important**: Replace `/path/to/your/project` with the absolute path to the project directory where your `docker-compose.yml` file is located.

---

## Chinese Documentation (中文文档)

### 概述

本应用包含两个由 `docker-compose` 管理的核心组件：
1.  **扫描器 (Scanner)**：一个Python脚本，可以被定时（或手动）执行。它负责扫描、验证API密钥，并将统计结果保存到一个共享的数据库中。
2.  **仪表盘 (Dashboard)**：一个Flask网站应用，用于从数据库中读取并展示历史扫描数据。

### 先决条件

*   [Docker](https://www.docker.com/get-started)
*   [Docker Compose](https://docs.docker.com/compose/install/)
*   一个拥有API凭证的FOFA账户。

### 🚀 一键部署

**1. 克隆代码仓库**
```bash
git clone <repository_url>
cd <repository_name>
```

**2. 配置您的凭证**

将环境文件示例复制为一个新的 `.env` 文件：
```bash
cp .env.example .env
```
然后，用文本编辑器打开 `.env` 文件，并填入您的FOFA邮箱和API密钥：
```
# .env
FOFA_EMAIL=your_fofa_email@example.com
FOFA_KEY=your_fofa_api_key
```
`docker-compose` 会使用此文件来安全地将您的密钥传递给应用容器。

**3. 启动应用**

在项目根目录下，运行以下命令：
```bash
docker-compose up -d
```
这个命令将会：
-   为本应用构建Docker镜像。
-   在后台启动 `dashboard` 网站服务器。
-   现在，你可以通过 `http://localhost:8080` 访问仪表盘。

### 使用方法

*   **查看仪表盘**: 打开您的浏览器并访问 `http://localhost:8080`。
*   **手动执行扫描**: 如果想立即触发一次扫描，可以运行 `scanner` 服务：
    ```bash
    docker-compose run --rm scanner
    ```
    扫描结束后，刷新仪表盘页面即可看到最新的结果。
*   **查看日志**: 查看网站服务器的日志：
    ```bash
    docker-compose logs -f dashboard
    ```
*   **停止应用**: 停止并移除所有容器：
    ```bash
    docker-compose down
    ```

### 自动化扫描

为了实现全天候24小时自动化运行，您应该在宿主机上使用 `cron` 等工具来周期性地运行扫描器。

1.  编辑您的 crontab 文件: `crontab -e`
2.  添加一行来定时执行 `docker-compose run` 命令。例如，设置在每天凌晨2点执行一次扫描：
    ```crontab
    0 2 * * * cd /path/to/your/project && docker-compose run --rm scanner
    ```
    **重要提示**: 请务必将 `/path/to/your/project` 替换成存放 `docker-compose.yml` 文件的项目目录的绝对路径。
