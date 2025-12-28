"""
SQL Server 資料庫連線模組

提供 SQL Server 的連線管理和查詢執行功能。
"""

import pyodbc
from typing import Optional
from contextlib import contextmanager
from config import sql_server_config


class DatabaseConnector:
    """SQL Server 資料庫連線器"""

    def __init__(self, connection_string: Optional[str] = None):
        """
        初始化資料庫連線器
        
        Args:
            connection_string: 連線字串，若未提供則使用環境變數設定
        """
        self.connection_string = connection_string or sql_server_config.connection_string

    @contextmanager
    def get_connection(self):
        """
        取得資料庫連線的 Context Manager
        
        Yields:
            pyodbc.Connection: 資料庫連線物件
        """
        conn = None
        try:
            conn = pyodbc.connect(self.connection_string)
            yield conn
        finally:
            if conn:
                conn.close()

    def execute_query(self, sql: str) -> tuple[list[str], list[tuple]]:
        """
        執行 SQL 查詢並回傳結果
        
        Args:
            sql: 要執行的 SQL 語句
            
        Returns:
            tuple: (欄位名稱列表, 資料列列表)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            
            # 取得欄位名稱
            columns = [column[0] for column in cursor.description] if cursor.description else []
            
            # 取得所有資料列
            rows = cursor.fetchall()
            
            return columns, [tuple(row) for row in rows]

    def test_connection(self) -> tuple[bool, str]:
        """
        測試資料庫連線
        
        Returns:
            tuple: (是否成功, 訊息)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True, "連線成功！"
        except Exception as e:
            return False, f"連線失敗：{str(e)}"


# 預設連線器實例
db_connector = DatabaseConnector()
