"""
Agent Tools 模組

定義 Microsoft Agent Framework 可呼叫的函數工具。
這些工具讓 AI Agent 能夠：
1. 取得資料庫 Schema
2. 執行 SQL 查詢並回傳結果或錯誤
"""

from typing import Annotated
from pydantic import Field
from agent_framework import ai_function

from db_connector import DatabaseConnector
from schema_extractor import SchemaExtractor
from config import sql_server_config


@ai_function(
    name="get_database_schema",
    description="取得資料庫的完整 Schema，包含所有資料表和欄位資訊。在生成 SQL 之前請先呼叫此工具。"
)
def get_database_schema() -> str:
    """
    取得連接的 SQL Server 資料庫的完整 Schema。
    
    Returns:
        str: 格式化的 Schema 文字，包含所有資料表和欄位
    """
    try:
        db = DatabaseConnector(sql_server_config.connection_string)
        extractor = SchemaExtractor(db)
        schema = extractor.get_full_schema()
        if not schema.strip():
            return "資料庫中沒有找到任何資料表。"
        return schema
    except Exception as e:
        return f"無法取得 Schema：{str(e)}"


@ai_function(
    name="execute_sql",
    description="執行 T-SQL 查詢並回傳結果。如果查詢失敗，會回傳錯誤訊息，你可以根據錯誤修正 SQL 後重試。"
)
def execute_sql(
    sql: Annotated[str, Field(description="要執行的 T-SQL 查詢語句")]
) -> str:
    """
    執行 SQL 查詢並回傳結果。
    
    Args:
        sql: 要執行的 T-SQL 查詢語句
        
    Returns:
        str: 查詢結果（格式化為表格）或錯誤訊息
    """
    try:
        db = DatabaseConnector(sql_server_config.connection_string)
        columns, rows = db.execute_query(sql)
        
        if not rows:
            return "查詢執行成功，但沒有回傳任何資料。"
        
        # 格式化為表格
        result_lines = []
        
        # 標題列
        header = " | ".join(str(col) for col in columns)
        result_lines.append(header)
        result_lines.append("-" * len(header))
        
        # 資料列 (限制最多 50 筆)
        for row in rows[:50]:
            row_str = " | ".join(str(val) if val is not None else "NULL" for val in row)
            result_lines.append(row_str)
        
        if len(rows) > 50:
            result_lines.append(f"... (共 {len(rows)} 筆資料，僅顯示前 50 筆)")
        else:
            result_lines.append(f"(共 {len(rows)} 筆資料)")
        
        return "\n".join(result_lines)
        
    except Exception as e:
        error_msg = str(e)
        # 提供更有幫助的錯誤訊息
        if "Invalid column name" in error_msg:
            return f"SQL 錯誤：欄位名稱無效。{error_msg}\n請檢查 Schema 確認正確的欄位名稱。"
        elif "Invalid object name" in error_msg:
            return f"SQL 錯誤：資料表名稱無效。{error_msg}\n請檢查 Schema 確認正確的資料表名稱。"
        else:
            return f"SQL 執行錯誤：{error_msg}\n請根據錯誤訊息修正 SQL 後重試。"


@ai_function(
    name="test_connection",
    description="測試資料庫連線是否正常"
)
def test_connection() -> str:
    """
    測試資料庫連線。
    
    Returns:
        str: 連線狀態訊息
    """
    try:
        db = DatabaseConnector(sql_server_config.connection_string)
        success, message = db.test_connection()
        return message
    except Exception as e:
        return f"連線測試失敗：{str(e)}"
