"""
NL2SQL 設定管理模組

從環境變數載入所有設定，提供統一的設定存取介面。
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()


@dataclass
class AzureOpenAIConfig:
    """Azure OpenAI 設定"""
    endpoint: str
    api_key: str
    deployment_name: str
    api_version: str

    @classmethod
    def from_env(cls) -> "AzureOpenAIConfig":
        """從環境變數建立設定"""
        return cls(
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        )

    def is_valid(self) -> bool:
        """檢查設定是否完整"""
        return bool(self.endpoint and self.api_key and self.deployment_name)


@dataclass
class SQLServerConfig:
    """SQL Server 設定"""
    connection_string: str

    @classmethod
    def from_env(cls) -> "SQLServerConfig":
        """從環境變數建立設定"""
        return cls(
            connection_string=os.getenv("SQL_SERVER_CONNECTION_STRING", "")
        )

    def is_valid(self) -> bool:
        """檢查設定是否完整"""
        return bool(self.connection_string)


# 全域設定實例
azure_openai_config = AzureOpenAIConfig.from_env()
sql_server_config = SQLServerConfig.from_env()
