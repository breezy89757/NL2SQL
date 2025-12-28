from db_connector import db_connector
import random
from datetime import datetime, timedelta

def init_db():
    print("🚀 開始初始化資料庫...")
    
    with db_connector.get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. 如果資料表存在先刪除
        print("🧹 清理舊資料...")
        cursor.execute("IF OBJECT_ID('Orders', 'U') IS NOT NULL DROP TABLE Orders")
        cursor.execute("IF OBJECT_ID('Customers', 'U') IS NOT NULL DROP TABLE Customers")
        
        # 2. 建立 Customers 表
        print("📦 建立 Customers 資料表...")
        cursor.execute("""
            CREATE TABLE Customers (
                CustomerID INT PRIMARY KEY IDENTITY(1,1),
                Name NVARCHAR(100) NOT NULL,
                Email NVARCHAR(100),
                Phone NVARCHAR(20),
                City NVARCHAR(50),
                JoinDate DATE DEFAULT GETDATE()
            )
        """)
        
        # 3. 建立 Orders 表
        print("📦 建立 Orders 資料表...")
        cursor.execute("""
            CREATE TABLE Orders (
                OrderID INT PRIMARY KEY IDENTITY(1,1),
                CustomerID INT FOREIGN KEY REFERENCES Customers(CustomerID),
                OrderDate DATE DEFAULT GETDATE(),
                TotalAmount DECIMAL(10, 2),
                Status NVARCHAR(20) -- Pending, Shipped, Delivered, Cancelled
            )
        """)
        
        # 4. 插入假資料
        print("📝 插入測試資料...")
        
        # 假客戶
        names = ["大衛", "愛麗絲", "包伯", "查理", "伊娃", "法蘭克", "葛瑞斯", "漢克"]
        cities = ["台北", "台中", "高雄", "新竹", "台南"]
        
        customer_ids = []
        for name in names:
            city = random.choice(cities)
            email = f"{name.lower()}@example.com" # 這裡不轉英文了，簡單示意
            cursor.execute(
                "INSERT INTO Customers (Name, Email, Phone, City) VALUES (?, ?, ?, ?)",
                (name, f"user_{random.randint(100,999)}@test.com", f"0912-{random.randint(100,999)}-{random.randint(100,999)}", city)
            )
            # 取得剛插入的 ID
            cursor.execute("SELECT @@IDENTITY")
            customer_ids.append(cursor.fetchone()[0])
            
        # 假訂單
        statuses = ["Pending", "Shipped", "Delivered", "Cancelled"]
        
        for _ in range(20): # 建立 20 筆訂單
            cid = random.choice(customer_ids)
            amount = random.randint(100, 5000)
            status = random.choice(statuses)
            
            # 隨機日期 (最近 30 天)
            days_ago = random.randint(0, 30)
            order_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            
            cursor.execute(
                "INSERT INTO Orders (CustomerID, TotalAmount, Status, OrderDate) VALUES (?, ?, ?, ?)",
                (cid, amount, status, order_date)
            )
            
        conn.commit()
        print("✅ 資料初始化完成！")

if __name__ == "__main__":
    try:
        init_db()
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
