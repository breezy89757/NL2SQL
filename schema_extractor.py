"""
資料庫 Schema 提取模組

從 SQL Server 提取資料表結構資訊，格式化為 Agent 可用的上下文。
"""

from db_connector import DatabaseConnector
from typing import Optional


class SchemaExtractor:
    """資料庫 Schema 提取器"""

    def __init__(self, db_connector: Optional[DatabaseConnector] = None):
        """
        初始化 Schema 提取器
        
        Args:
            db_connector: 資料庫連線器實例
        """
        self.db = db_connector or DatabaseConnector()

    def get_tables(self) -> list[dict]:
        """
        取得所有資料表資訊
        
        Returns:
            list: 資料表資訊列表
        """
        sql = """
        SELECT 
            TABLE_SCHEMA,
            TABLE_NAME,
            TABLE_TYPE
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
        """
        columns, rows = self.db.execute_query(sql)
        return [
            {
                "schema": row[0],
                "name": row[1],
                "type": row[2]
            }
            for row in rows
        ]

    def get_columns(self, table_schema: str, table_name: str) -> list[dict]:
        """
        取得指定資料表的欄位資訊
        
        Args:
            table_schema: 資料表 Schema
            table_name: 資料表名稱
            
        Returns:
            list: 欄位資訊列表
        """
        sql = f"""
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE,
            COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{table_schema}' AND TABLE_NAME = '{table_name}'
        ORDER BY ORDINAL_POSITION
        """
        columns, rows = self.db.execute_query(sql)
        return [
            {
                "name": row[0],
                "data_type": row[1],
                "max_length": row[2],
                "nullable": row[3],
                "default": row[4]
            }
            for row in rows
        ]

    def get_full_schema(self) -> str:
        """
        取得完整的資料庫 Schema 文字描述
        
        Returns:
            str: 格式化的 Schema 文字
        """
        tables = self.get_tables()
        schema_text = []

        for table in tables:
            full_name = f"[{table['schema']}].[{table['name']}]"
            schema_text.append(f"\n### 資料表: {full_name}")
            
            columns = self.get_columns(table['schema'], table['name'])
            schema_text.append("| 欄位名稱 | 資料類型 | 可為空 |")
            schema_text.append("|---------|---------|--------|")
            
            for col in columns:
                data_type = col['data_type']
                if col['max_length']:
                    data_type += f"({col['max_length']})"
                nullable = "是" if col['nullable'] == "YES" else "否"
                schema_text.append(f"| {col['name']} | {data_type} | {nullable} |")

        return "\n".join(schema_text)

    def format_schema_for_agent(self, schema_text: str = None) -> str:
        """
        將 Schema 格式化為 Agent 提示詞使用的格式
        
        Args:
            schema_text: 自訂的 Schema 文字，若未提供則自動提取
            
        Returns:
            str: 格式化的 Schema 上下文
        """
        if schema_text is None:
            schema_text = self.get_full_schema()
        
        return f"""
以下是資料庫的 Schema 資訊，請根據這些結構來生成 T-SQL：

{schema_text}
"""


# 預設提取器實例
schema_extractor = SchemaExtractor()
