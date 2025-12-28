# NL2SQL - 自然語言轉 T-SQL 工具

將自然語言轉換為 T-SQL 查詢的 Web 應用程式，使用 Azure OpenAI 和 Streamlit 建構。

## 功能特色

- 🔄 **自然語言轉 SQL**：輸入中文或英文描述，自動生成 T-SQL 查詢
- 📋 **Schema 輸入**：手動輸入或自動從資料庫提取 Schema
- 📝 **SQL 預覽**：顯示生成的 T-SQL 語句
- ▶️ **執行查詢**：可選功能，直接執行 SQL 並顯示結果

## 技術棧

- **Web UI**: Streamlit
- **AI**: Azure OpenAI (GPT-4o)
- **資料庫**: SQL Server (T-SQL)
- **虛擬環境**: uv

## 快速開始

### 1. 安裝依賴

```bash
# 使用 uv 建立虛擬環境並安裝依賴
uv sync
```

### 2. 設定環境變數

複製 `.env.template` 為 `.env` 並填入您的設定：

```bash
cp .env.template .env
```

編輯 `.env` 檔案：

```env
# Azure OpenAI 設定
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o

# SQL Server 連線字串
SQL_SERVER_CONNECTION_STRING=Driver={ODBC Driver 18 for SQL Server};Server=localhost;Database=YourDB;Trusted_Connection=yes;TrustServerCertificate=yes;
```

### 3. 啟動應用程式

```bash
uv run streamlit run app.py
```

瀏覽器會自動開啟 http://localhost:8501

## 使用說明

1. **設定連線**：在側邊欄輸入 SQL Server 連線字串
2. **提取 Schema**：點擊「提取 Schema」自動取得資料庫結構，或手動輸入
3. **輸入需求**：在主區域輸入自然語言查詢需求
4. **生成 SQL**：點擊「生成 SQL」按鈕
5. **執行查詢**（可選）：確認 SQL 正確後，點擊「執行 SQL」查看結果

## 專案結構

```
NL2SQL/
├── app.py                 # Streamlit 主程式
├── config.py              # 設定管理
├── sql_agent.py           # NL2SQL Agent 邏輯
├── db_connector.py        # SQL Server 連線工具
├── schema_extractor.py    # Schema 提取工具
├── pyproject.toml         # 專案設定 (uv)
├── requirements.txt       # 套件依賴 (備用)
├── .env.template          # 環境變數範本
└── README.md              # 專案說明
```

## 注意事項

> [!IMPORTANT]
> **必要安裝步驟：**
> 1. 您必須安裝 **ODBC Driver 18 for SQL Server** 才能讓程式連線資料庫。
>    - [👉 點此下載官方安裝檔 (Windows)](https://go.microsoft.com/fwlink/?linkid=2280795)
>    - 下載後請執行安裝檔，並選取預設選項安裝即可。
> 
> 2. 確保 Azure OpenAI 資源已建立並部署模型。
> 3. 確保 SQL Server 已啟動。如果是使用 Docker：
>    ```bash
>    # 啟動資料庫
>    docker compose up -d
>    ```

