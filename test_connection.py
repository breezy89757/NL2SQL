from db_connector import db_connector
import time

print("正在嘗試連接 SQL Server...")
for i in range(5):
    success, message = db_connector.test_connection()
    if success:
        print(f"✅ 連線成功！{message}")
        break
    else:
        print(f"⚠️ 第 {i+1} 次嘗試失敗: {message}")
        if i < 4:
            print("等待 5 秒後重試...")
            time.sleep(5)
