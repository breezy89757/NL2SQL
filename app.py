"""
NL2SQL - 自然語言轉 T-SQL Web 應用程式

使用 Streamlit 建立的 Web UI，整合 Microsoft Agent Framework 進行 NL2SQL 轉換。
一鍵查詢：輸入問題 → 生成 SQL → 執行 → 顯示結果
"""

import streamlit as st
import re
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
    if "agent_response" not in st.session_state:
        st.session_state.agent_response = ""
    if "query_results" not in st.session_state:
        st.session_state.query_results = None
    if "error_message" not in st.session_state:
        st.session_state.error_message = ""
    if "connection_string" not in st.session_state:
        st.session_state.connection_string = sql_server_config.connection_string


def extract_sql_from_response(response: str) -> str:
    """從 Agent 回應中提取 SQL"""
    if "```sql" in response:
        match = re.search(r"```sql(.*?)```", response, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
    # 嘗試找任何程式碼區塊
    if "```" in response:
        match = re.search(r"```(.*?)```", response, re.DOTALL)
        if match:
            return match.group(1).strip()
    return response.strip()


def render_sidebar():
    """渲染側邊欄"""
    with st.sidebar:
        st.header("⚙️ 設定")
        
        # Agent 模式狀態
        agent = SQLAgent()
        mode = agent.get_mode()
        if "Agentic" in mode:
            st.success(f"🤖 Agentic Mode")
        else:
            st.warning(f"📝 Legacy Mode")
        
        st.divider()
        
        # 連線狀態
        st.subheader("資料庫連線")
        
        connection_string = st.text_area(
            "連線字串",
            value=st.session_state.connection_string,
            height=80,
            label_visibility="collapsed"
        )
        st.session_state.connection_string = connection_string
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("測試連線", use_container_width=True):
                db = DatabaseConnector(connection_string)
                success, message = db.test_connection()
                if success:
                    st.success("✅ 連線成功")
                else:
                    st.error(f"❌ {message}")
        
        with col2:
            if st.button("載入 Schema", use_container_width=True):
                try:
                    db = DatabaseConnector(connection_string)
                    extractor = SchemaExtractor(db)
                    st.session_state.schema_text = extractor.get_full_schema()
                    st.success("✅ Schema 已載入")
                except Exception as e:
                    st.error(f"❌ {str(e)}")
        
        # 顯示已載入的資料表數量
        if st.session_state.schema_text:
            table_count = st.session_state.schema_text.count("### 資料表:")
            st.caption(f"📋 已載入 {table_count} 個資料表")


def run_query(natural_language: str) -> dict:
    """執行完整查詢流程：自動載入 Schema → 生成 SQL → 執行 → 回傳結果"""
    result = {
        "success": False,
        "sql": "",
        "explanation": "",
        "columns": [],
        "rows": [],
        "error": ""
    }
    
    agent = SQLAgent()
    if not agent.is_ready():
        result["error"] = "Azure OpenAI 未設定"
        return result
    
    # Step 0: 自動載入 Schema (如果尚未載入)
    if not st.session_state.schema_text:
        try:
            db = DatabaseConnector(st.session_state.connection_string)
            extractor = SchemaExtractor(db)
            st.session_state.schema_text = extractor.get_full_schema()
        except Exception as e:
            result["error"] = f"無法載入資料庫 Schema: {str(e)}"
            return result
    
    # Step 1: 生成 SQL
    schema_context = f"資料庫 Schema：\n{st.session_state.schema_text}"
    response = agent.generate_sql(natural_language, schema_context)
    
    result["explanation"] = response
    result["sql"] = extract_sql_from_response(response)
    
    if not result["sql"] or "錯誤" in result["sql"]:
        result["error"] = response
        return result
    
    # Step 2: 執行 SQL
    try:
        db = DatabaseConnector(st.session_state.connection_string)
        columns, rows = db.execute_query(result["sql"])
        result["columns"] = columns
        result["rows"] = rows
        result["success"] = True
    except Exception as e:
        result["error"] = str(e)
    
    return result


def render_main_content():
    """渲染主要內容區域"""
    st.title("🔄 NL2SQL")
    st.caption("用自然語言查詢資料庫")
    
    # 查詢輸入區
    query = st.text_input(
        "輸入您的問題",
        placeholder="例如：列出所有客戶的姓名和電話",
        label_visibility="collapsed"
    )
    
    if st.button("🔍 查詢", type="primary", use_container_width=True):
        if not query:
            st.warning("請輸入查詢問題")
            return
        
        # 執行查詢
        with st.spinner("🤖 AI 正在分析並查詢資料庫..."):
            result = run_query(query)
        
        # 儲存結果
        st.session_state.generated_sql = result["sql"]
        st.session_state.agent_response = result["explanation"]
        
        if result["success"]:
            st.session_state.query_results = {
                "columns": result["columns"],
                "rows": result["rows"]
            }
            st.session_state.error_message = ""
        else:
            st.session_state.query_results = None
            st.session_state.error_message = result["error"]
    
    # 顯示結果
    if st.session_state.query_results:
        results = st.session_state.query_results
        
        # 結果表格
        st.subheader("📊 查詢結果")
        if results["rows"]:
            import pandas as pd
            df = pd.DataFrame(results["rows"], columns=results["columns"])
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"共 {len(results['rows'])} 筆資料")
        else:
            st.info("查詢成功，但沒有資料")
        
        # 可展開的 SQL 詳情
        with st.expander("📝 查看生成的 SQL"):
            st.code(st.session_state.generated_sql, language="sql")
    
    elif st.session_state.error_message:
        st.error(f"❌ {st.session_state.error_message}")
        if st.session_state.generated_sql:
            with st.expander("📝 查看生成的 SQL (可能有誤)"):
                st.code(st.session_state.generated_sql, language="sql")


def main():
    """主程式"""
    st.set_page_config(
        page_title="NL2SQL",
        page_icon="🔄",
        layout="wide",
        initial_sidebar_state="collapsed"  # 預設收合側邊欄
    )
    
    # 簡潔 CSS
    st.markdown("""
    <style>
    .stTextInput input { font-size: 1.1rem; }
    .stButton button { font-size: 1.1rem; }
    </style>
    """, unsafe_allow_html=True)
    
    init_session_state()
    render_sidebar()
    render_main_content()


if __name__ == "__main__":
    main()
