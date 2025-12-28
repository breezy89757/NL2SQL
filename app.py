"""
NL2SQL - 自然語言轉 T-SQL Web 應用程式

使用 Streamlit 建立的 Web UI，整合 Azure OpenAI 進行 NL2SQL 轉換。
"""

import streamlit as st
from sql_agent import SQLAgent
from db_connector import DatabaseConnector
from schema_extractor import SchemaExtractor
from config import azure_openai_config, sql_server_config


def init_session_state():
    """初始化 Session State"""
    if "schema_text" not in st.session_state:
        st.session_state.schema_text = ""
    if "generated_sql" not in st.session_state:
        st.session_state.generated_sql = ""
    if "query_results" not in st.session_state:
        st.session_state.query_results = None
    if "connection_string" not in st.session_state:
        st.session_state.connection_string = sql_server_config.connection_string


def render_sidebar():
    """渲染側邊欄"""
    with st.sidebar:
        st.header("⚙️ 設定")
        
        # Azure OpenAI 狀態
        st.subheader("Azure OpenAI")
        if azure_openai_config.is_valid():
            st.success(f"✅ 已連接: {azure_openai_config.deployment_name}")
        else:
            st.error("❌ 未設定，請檢查 .env 檔案")
        
        st.divider()
        
        # 資料庫連線設定
        st.subheader("SQL Server 連線")
        
        connection_string = st.text_area(
            "連線字串",
            value=st.session_state.connection_string,
            height=100,
            help="ODBC 連線字串"
        )
        st.session_state.connection_string = connection_string
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("測試連線", use_container_width=True):
                db = DatabaseConnector(connection_string)
                success, message = db.test_connection()
                if success:
                    st.success(message)
                else:
                    st.error(message)
        
        with col2:
            if st.button("提取 Schema", use_container_width=True):
                try:
                    db = DatabaseConnector(connection_string)
                    extractor = SchemaExtractor(db)
                    st.session_state.schema_text = extractor.get_full_schema()
                    st.success("Schema 提取成功！")
                except Exception as e:
                    st.error(f"提取失敗：{str(e)}")
        
        st.divider()
        
        # Schema 輸入
        st.subheader("📋 資料庫 Schema")
        st.caption("可手動輸入或從資料庫提取")
        
        schema_text = st.text_area(
            "Schema 內容",
            value=st.session_state.schema_text,
            height=300,
            placeholder="""範例格式：
### 資料表: [dbo].[Customers]
| 欄位名稱 | 資料類型 | 可為空 |
|---------|---------|--------|
| CustomerID | int | 否 |
| CustomerName | nvarchar(100) | 否 |
| Email | nvarchar(255) | 是 |
| Phone | nvarchar(20) | 是 |
""",
            label_visibility="collapsed"
        )
        st.session_state.schema_text = schema_text


def render_main_content():
    """渲染主要內容區域"""
    st.title("🔄 NL2SQL")
    st.caption("自然語言轉 T-SQL 查詢工具")
    
    # 自然語言輸入
    st.subheader("💬 輸入您的查詢需求")
    natural_language = st.text_area(
        "自然語言描述",
        placeholder="例如：列出所有客戶的姓名和電話，按姓名排序",
        height=100,
        label_visibility="collapsed"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        generate_btn = st.button("🚀 生成 SQL", type="primary", use_container_width=True)
    
    # 生成 SQL
    if generate_btn:
        if not natural_language:
            st.warning("請輸入查詢需求")
        elif not st.session_state.schema_text:
            st.warning("請先輸入或提取資料庫 Schema")
        else:
            with st.spinner("正在生成 SQL..."):
                agent = SQLAgent()
                if not agent.is_ready():
                    st.error("Azure OpenAI 未正確設定，請檢查 .env 檔案")
                else:
                    schema_context = f"""
以下是資料庫的 Schema 資訊，請根據這些結構來生成 T-SQL：

{st.session_state.schema_text}
"""
                    sql = agent.generate_sql(natural_language, schema_context)
                    st.session_state.generated_sql = sql
                    st.session_state.query_results = None
    
    # 顯示生成的 SQL
    if st.session_state.generated_sql:
        st.divider()
        st.subheader("📝 生成的 T-SQL")
        
        st.code(st.session_state.generated_sql, language="sql")
        
        # 複製按鈕
        st.button("📋 複製 SQL", 
                  on_click=lambda: st.toast("請手動複製上方的 SQL 程式碼"))
        
        st.divider()
        
        # 執行 SQL（可選功能）
        st.subheader("▶️ 執行查詢（可選）")
        st.warning("⚠️ 請確認 SQL 語句正確後再執行，以避免意外的資料變更")
        
        if st.button("執行 SQL", type="secondary"):
            try:
                db = DatabaseConnector(st.session_state.connection_string)
                columns, rows = db.execute_query(st.session_state.generated_sql)
                st.session_state.query_results = {"columns": columns, "rows": rows}
            except Exception as e:
                st.error(f"執行失敗：{str(e)}")
        
        # 顯示查詢結果
        if st.session_state.query_results:
            st.subheader("📊 查詢結果")
            results = st.session_state.query_results
            
            if results["rows"]:
                # 建立資料表顯示
                import pandas as pd
                df = pd.DataFrame(results["rows"], columns=results["columns"])
                st.dataframe(df, use_container_width=True)
                st.caption(f"共 {len(results['rows'])} 筆資料")
            else:
                st.info("查詢成功，但沒有回傳資料")


def main():
    """主程式"""
    st.set_page_config(
        page_title="NL2SQL",
        page_icon="🔄",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 自訂 CSS
    st.markdown("""
    <style>
    .stTextArea textarea {
        font-family: 'Consolas', 'Monaco', monospace;
    }
    </style>
    """, unsafe_allow_html=True)
    
    init_session_state()
    render_sidebar()
    render_main_content()


if __name__ == "__main__":
    main()
