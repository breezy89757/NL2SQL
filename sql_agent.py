"""
NL2SQL Agent 模組

使用 Microsoft Agent Framework 和 Azure OpenAI 將自然語言轉換為 T-SQL。
"""

import asyncio
from openai import AzureOpenAI
from config import azure_openai_config


# T-SQL 專家的系統提示詞
SYSTEM_PROMPT = """你是一位 T-SQL 專家。你的任務是根據使用者提供的資料庫 Schema 和自然語言描述，生成正確的 T-SQL 查詢語句。

請遵循以下規則：
1. 只生成 T-SQL 語法，不要使用其他 SQL 方言
2. 使用方括號 [] 包裹資料表和欄位名稱
3. 生成的 SQL 必須可以直接執行
4. 如果查詢可能回傳大量資料，請加上 TOP 限制
5. 對於複雜查詢，請加上適當的註解說明
6. 只輸出 SQL 語句，不要額外的解釋文字

如果使用者的需求不清楚或無法從提供的 Schema 中找到對應的資料表/欄位，請說明原因。
"""


class SQLAgent:
    """NL2SQL Agent - 將自然語言轉換為 T-SQL"""

    def __init__(self):
        """初始化 SQL Agent"""
        self.config = azure_openai_config
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """初始化 Azure OpenAI 客戶端"""
        if self.config.is_valid():
            self.client = AzureOpenAI(
                azure_endpoint=self.config.endpoint,
                api_key=self.config.api_key,
                api_version=self.config.api_version,
            )

    def is_ready(self) -> bool:
        """檢查 Agent 是否已準備就緒"""
        return self.client is not None

    def _clean_sql(self, text: str) -> str:
        """清理 SQL 語句，移除 Markdown 標記"""
        # 移除 ```sql 和 ``` 標記
        if "```" in text:
            # 嘗試提取 ```sql ... ``` 中間的內容
            import re
            match = re.search(r"```(sql)?(.*?)```", text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(2).strip()
            # 如果正則匹配失敗但仍有 ```，嘗試簡單分割
            parts = text.split("```")
            return parts[1].strip() if len(parts) > 1 else text.strip()
        return text.strip()

    def generate_sql(self, natural_language: str, schema_context: str) -> str:
        """
        根據自然語言和 Schema 上下文生成 T-SQL
        
        Args:
            natural_language: 使用者的自然語言查詢
            schema_context: 資料庫 Schema 上下文
            
        Returns:
            str: 生成的 T-SQL 語句
        """
        if not self.is_ready():
            return "錯誤：Azure OpenAI 設定不完整，請檢查環境變數。"

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"{schema_context}\n\n使用者需求：{natural_language}"}
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.config.deployment_name,
                messages=messages,
                temperature=0,  # 使用較低溫度以獲得更確定性的輸出
                max_tokens=2000,
            )
            content = response.choices[0].message.content
            return self._clean_sql(content)
        except Exception as e:
            return f"生成 SQL 時發生錯誤：{str(e)}"


    def generate_sql_with_explanation(self, natural_language: str, schema_context: str) -> tuple[str, str]:
        """
        生成 T-SQL 並提供說明
        
        Args:
            natural_language: 使用者的自然語言查詢
            schema_context: 資料庫 Schema 上下文
            
        Returns:
            tuple: (SQL 語句, 說明文字)
        """
        if not self.is_ready():
            return "", "錯誤：Azure OpenAI 設定不完整，請檢查環境變數。"

        explanation_prompt = SYSTEM_PROMPT + """

這次請同時提供：
1. 生成的 T-SQL 語句（放在 ```sql 程式碼區塊中）
2. 簡短的中文說明，解釋這個查詢做了什麼
"""

        messages = [
            {"role": "system", "content": explanation_prompt},
            {"role": "user", "content": f"{schema_context}\n\n使用者需求：{natural_language}"}
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.config.deployment_name,
                messages=messages,
                temperature=0,
                max_tokens=2000,
            )
            content = response.choices[0].message.content
            
            # 嘗試分離 SQL 和說明
            if "```sql" in content:
                parts = content.split("```sql")
                if len(parts) > 1:
                    sql_part = parts[1].split("```")[0].strip()
                    explanation_part = parts[0].strip() + "\n" + "```".join(parts[1].split("```")[1:]).strip()
                    return sql_part, explanation_part
            
            return content, ""
        except Exception as e:
            return "", f"生成 SQL 時發生錯誤：{str(e)}"


# 預設 Agent 實例
sql_agent = SQLAgent()
