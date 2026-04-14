import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(layout="wide")

# ========================
# DB
# ========================
def get_conn():
    return sqlite3.connect("crm.db", check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS deposit (
        uid TEXT,
        amount REAL,
        time TEXT,
        UNIQUE(uid, time)
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS login (
        uid TEXT,
        date TEXT,
        UNIQUE(uid, date)
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ========================
# UI
# ========================
st.title("🔥 CRM 系统（云版本）")

col1, col2 = st.columns(2)

with col1:
    dep_file = st.file_uploader("充值数据", type=["xlsx"])

with col2:
    log_file = st.file_uploader("登录数据", type=["xlsx"])

# ========================
# BUTTON TRIGGER (VIP🔥)
# ========================
if st.button("🚀 更新数据"):

    conn = get_conn()

    if dep_file:
        df = pd.read_excel(dep_file)
        df.columns = ["uid", "amount", "time"]

        df.to_sql("temp_dep", conn, if_exists="replace", index=False)

        conn.execute("""
        INSERT OR IGNORE INTO deposit
        SELECT * FROM temp_dep
        """)

    if log_file:
        df = pd.read_excel(log_file)
        df.columns = ["uid", "date"]

        df.to_sql("temp_log", conn, if_exists="replace", index=False)

        conn.execute("""
        INSERT OR IGNORE INTO login
        SELECT * FROM temp_log
        """)

    conn.close()

    st.success("✅ 数据已更新（自动去重）")

# ========================
# LOAD DATA
# ========================
conn = get_conn()

deposit = pd.read_sql("SELECT * FROM deposit", conn)
login = pd.read_sql("SELECT * FROM login", conn)

conn.close()

# ========================
# ANALYSIS
# ========================
if len(deposit) > 0:

    deposit["time"] = pd.to_datetime(deposit["time"])
    login["date"] = pd.to_datetime(login["date"])

    today = deposit["time"].max()
    last7 = today - pd.Timedelta(days=7)

    dep7 = deposit[deposit["time"] >= last7]
    dep7 = dep7.groupby("uid")["amount"].sum().reset_index()
    dep7.columns = ["uid", "7天充值"]

    hist = deposit.groupby("uid")["amount"].sum().reset_index()
    hist.columns = ["uid", "历史充值"]

    login7 = login[login["date"] >= last7]
    login7 = login7.groupby("uid")["date"].nunique().reset_index()
    login7.columns = ["uid", "7天登录"]

    df = hist.merge(dep7, on="uid", how="left")
    df = df.merge(login7, on="uid", how="left")

    df.fillna(0, inplace=True)

    df["流失评分"] = (
        df["7天充值"].apply(lambda x: 3 if x == 0 else 0) +
        df["7天登录"].apply(lambda x: 2 if x < 2 else 0)
    )

    df["优先级"] = df["流失评分"].apply(lambda x: "P1" if x > 3 else "P2")

    st.dataframe(df, use_container_width=True)

    st.bar_chart(df["流失评分"])
