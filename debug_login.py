import pyodbc
import time

conn_str = "Driver={ODBC Driver 18 for SQL Server};Server=localhost,1433;Database=master;UID=sa;PWD=Passw0rd1234;TrustServerCertificate=yes;"

print(f"測試連線字串: {conn_str}")
print("正在連線...")

for i in range(10):
    try:
        conn = pyodbc.connect(conn_str, timeout=5)
        print("✅ 成功連線！密碼正確！")
        conn.close()
        break
    except Exception as e:
        print(f"❌ 嘗試 {i+1}/10 失敗: {e}")
        time.sleep(2)
