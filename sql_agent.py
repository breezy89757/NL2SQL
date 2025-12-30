"""
NL2SQL Agent 模組

使用 Microsoft Agent Framework 和 Azure OpenAI 將自然語言轉換為 T-SQL。
Agent 會自動：
1. 取得資料庫 Schema
2. 生成 T-SQL 查詢
3. 測試執行並自動修正錯誤
"""

import asyncio
import os
from typing import Optional

from config import azure_openai_config, openai_provider

# 嘗試導入 Agent Framework (預覽版)
try:
    from agent_framework import ChatAgent
    from agent_framework.azure import AzureOpenAIChatClient
    from agent_framework.openai import OpenAIChatClient
    from openai import AzureOpenAI as OpenAIClient
    AGENT_FRAMEWORK_AVAILABLE = True
except ImportError:
    AGENT_FRAMEWORK_AVAILABLE = False

# 導入自定義工具
from agent_tools import get_database_schema, execute_sql, test_connection

# 導入舊版 OpenAI 客戶端作為備案
from openai import AzureOpenAI



# T-SQL 專家的系統提示詞
SYSTEM_PROMPT = """你是一位 T-SQL 專家助手。你有以下工具可以使用：

1. **get_database_schema()** - 取得資料庫的完整 Schema（資料表和欄位）
2. **execute_sql(sql)** - 執行 SQL 查詢並查看結果或錯誤
3. **test_connection()** - 測試資料庫連線

## 工作流程

當使用者提出查詢需求時，請遵循以下步驟：

1. **先呼叫 get_database_schema()** 了解資料庫結構
2. 根據 Schema 和使用者需求，**生成 T-SQL 語句**
3. **呼叫 execute_sql()** 測試你的查詢
4. 如果有錯誤，**分析錯誤並修正 SQL**，然後重試
5. 成功後，回傳最終的 SQL 語句給使用者

## T-SQL 規則

- 使用方括號 [] 包裹資料表和欄位名稱
- 只生成 T-SQL 語法
- 對於可能回傳大量資料的查詢，加上 TOP 限制
- 對於複雜查詢，加上適當的註解
- **空值檢查**：當使用者要查詢「非空」或「有值」的資料時，除了檢查 IS NOT NULL 之外，也要同時檢查不是空白字串，例如：WHERE [欄位] IS NOT NULL AND [欄位] <> ''

## 回應格式

最終回應請包含：
1. 生成的 SQL 語句（用 ```sql 程式碼區塊包裹）
2. 簡短說明這個查詢做了什麼
"""


class SQLAgent:
    """NL2SQL Agent - 將自然語言轉換為 T-SQL"""

    def __init__(self):
        """初始化 SQL Agent"""
        self.config = azure_openai_config
        self.legacy_client = None
        self.chat_client = None
        self.tools = None
        
        # 先初始化 legacy_client 作為備案
        if self.config.is_valid():
            self.legacy_client = AzureOpenAI(
                azure_endpoint=self.config.endpoint,
                api_key=self.config.api_key,
                api_version=self.config.api_version,
            )
        
        # 嘗試使用 Agent Framework
        self._use_agent_framework = AGENT_FRAMEWORK_AVAILABLE and self.config.is_valid()
        if self._use_agent_framework:
            self._init_agent_framework()

    def _init_agent_framework(self):
        """初始化 Agent Framework 客戶端"""
        try:
            # 設定環境變數供 Agent Framework 使用
            os.environ.setdefault("AZURE_OPENAI_ENDPOINT", self.config.endpoint)
            os.environ.setdefault("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", self.config.deployment_name)
            
            # 根據 Provider 選擇客戶端類型
            provider = openai_provider.lower()
            if provider == "openai" or provider == "litellm":
                # 使用 OpenAI 兼容客戶端 (適用於 LiteLLM 或原生 OpenAI)
                self.chat_client = OpenAIChatClient(
                    api_key=self.config.api_key,
                    openai_base=self.config.endpoint,
                    model=self.config.deployment_name
                )
            else:
                # 使用 Azure OpenAI ChatCompletions 客戶端 (預設)
                self.chat_client = AzureOpenAIChatClient(
                    api_key=self.config.api_key,
                    azure_endpoint=self.config.endpoint,
                    model=self.config.deployment_name
                )
            self.tools = [get_database_schema, execute_sql, test_connection]
        except Exception as e:
            print(f"Agent Framework 初始化失敗: {e}")
            self._use_agent_framework = False
            self._init_legacy_client()

    def _init_legacy_client(self):
        """初始化舊版 OpenAI 客戶端（備案）"""
        self.chat_client = None
        self.tools = None
        if self.config.is_valid():
            self.legacy_client = AzureOpenAI(
                azure_endpoint=self.config.endpoint,
                api_key=self.config.api_key,
                api_version=self.config.api_version,
            )
        else:
            self.legacy_client = None

    def is_ready(self) -> bool:
        """檢查 Agent 是否已準備就緒"""
        if self._use_agent_framework:
            return self.chat_client is not None
        return self.legacy_client is not None

    def get_mode(self) -> str:
        """取得目前使用的模式"""
        if self._use_agent_framework:
            return "Agent Framework (Agentic Mode)"
        return "Legacy OpenAI (Basic Mode)"

    async def generate_sql_async(self, user_query: str) -> str:
        """
        使用 Agent Framework 非同步生成 SQL
        
        Args:
            user_query: 使用者的自然語言查詢
            
        Returns:
            str: Agent 的回應（包含 SQL 和說明）
        """
        if not self._use_agent_framework:
            raise RuntimeError("Agent Framework 未啟用")

        async with ChatAgent(
            chat_client=self.chat_client,
            instructions=SYSTEM_PROMPT,
            tools=self.tools
        ) as agent:
            result = await agent.run(user_query)
            return result.text

    def generate_sql(self, natural_language: str, schema_context: str = "") -> str:
        """
        根據自然語言生成 T-SQL
        
        Args:
            natural_language: 使用者的自然語言查詢
            schema_context: 資料庫 Schema 上下文（舊版模式使用）
            
        Returns:
            str: 生成的 T-SQL 語句或 Agent 回應
        """
        if not self.is_ready():
            return "錯誤：Azure OpenAI 設定不完整，請檢查環境變數。"

        # 使用 Agent Framework
        if self._use_agent_framework:
            return asyncio.run(self.generate_sql_async(natural_language))
        
        # 僅在未啟用 Agent Framework 時使用舊版模式
        return self._generate_sql_legacy(natural_language, schema_context)

    def _generate_sql_legacy(self, natural_language: str, schema_context: str) -> str:
        """舊版 SQL 生成方法（無 Agentic 功能）"""
        legacy_prompt = """你是一位 T-SQL 專家。根據使用者提供的資料庫 Schema 和自然語言描述，生成正確的 T-SQL 查詢語句。

請遵循以下規則：
1. 只生成 T-SQL 語法
2. 使用方括號 [] 包裹資料表和欄位名稱
3. 生成的 SQL 必須可以直接執行
4. 如果查詢可能回傳大量資料，請加上 TOP 限制
5. 只輸出 SQL 語句，不要額外的解釋文字
"""
        
        messages = [
            {"role": "system", "content": legacy_prompt},
            {"role": "user", "content": f"{schema_context}\n\n使用者需求：{natural_language}"}
        ]

        try:
            response = self.legacy_client.chat.completions.create(
                model=self.config.deployment_name,
                messages=messages,
                temperature=0,
                max_tokens=2000,
            )
            content = response.choices[0].message.content
            return self._clean_sql(content)
        except Exception as e:
            return f"生成 SQL 時發生錯誤：{str(e)}"

    def _clean_sql(self, text: str) -> str:
        """清理 SQL 語句，移除 Markdown 標記"""
        if "```" in text:
            import re
            match = re.search(r"```(sql)?(.*?)```", text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(2).strip()
            parts = text.split("```")
            return parts[1].strip() if len(parts) > 1 else text.strip()
        return text.strip()


# 預設 Agent 實例
sql_agent = SQLAgent()
