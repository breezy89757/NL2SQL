# NL2SQL

> 自然語言轉 T-SQL 查詢工具 — 整合 Microsoft Agent Framework 與 Azure OpenAI

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.40-FF4B4B?logo=streamlit)
![Azure OpenAI](https://img.shields.io/badge/Azure-OpenAI-0078D4?logo=microsoft-azure)

將自然語言轉換為 T-SQL 查詢的 Web 應用程式，具備自動 Schema 載入、SQL 自我修正等功能。

![NL2SQL Demo](docs/images/demo-main.png)

## Features

- **Agentic Mode** — 使用 Microsoft Agent Framework，自動取得 Schema、生成 SQL、測試執行
- **一鍵查詢** — 輸入問題 → 直接顯示結果表格
- **自動 Schema 載入** — 首次查詢時自動從資料庫提取 Schema
- **自我修正** — 遇到 SQL 錯誤時自動分析並修正

## Tech Stack

| Category | Technology |
|----------|------------|
| Web UI | Streamlit |
| AI Agent | Microsoft Agent Framework (Preview) |
| LLM | Azure OpenAI (GPT-4o) |
| Database | SQL Server (T-SQL) |
| Package Manager | uv |

## Quick Start

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure Environment

```bash
cp .env.template .env
```

Edit `.env`:

```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
SQL_SERVER_CONNECTION_STRING=Driver={ODBC Driver 18 for SQL Server};Server=localhost,1433;Database=master;UID=sa;PWD=YourPassword;TrustServerCertificate=yes;
```

### 3. Start Database (Docker)

```bash
docker compose up -d
```

### 4. Run

```bash
uv run streamlit run app.py
```

Open http://localhost:8501

## Usage Examples

- `列出所有資料表`
- `顯示所有客戶的姓名和 Email`
- `顯示每個客戶的訂單總金額`
- `找出金額超過 1000 的訂單`

## Project Structure

```
NL2SQL/
├── app.py              # Streamlit main app
├── sql_agent.py        # NL2SQL Agent
├── agent_tools.py      # Custom tools (Schema/SQL execution)
├── db_connector.py     # SQL Server connector
├── schema_extractor.py # Schema extraction
├── config.py           # Configuration
├── docker-compose.yml  # SQL Server container
└── .env.template       # Environment template
```

## Prerequisites

> [!IMPORTANT]
> 1. Install **ODBC Driver 18 for SQL Server** — [Download (Windows)](https://go.microsoft.com/fwlink/?linkid=2280795)
> 2. Ensure Azure OpenAI resource is deployed
> 3. Start SQL Server: `docker compose up -d`

## License

MIT
