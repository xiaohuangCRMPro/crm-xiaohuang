import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

# ================= UI =================
st.title("🔥 CRM维护系统（赚钱版）")

menu = st.sidebar.radio(
    "📊 功能菜单",
    ["📊 总览", "📥 数据导入", "📊 分析", "🎯 客户维护"]
)

# ================= LOAD DATA =================
def safe_read(file):
    df = pd.read_excel(file)
    df.columns = df.columns.str.strip()

    col_map = {
        "会员ID": "user",
        "支付金额": "amount",
        "提现金额": "amount",
        "完成时间": "date",
        "日期": "date"
    }

    df.rename(columns=col_map, inplace=True)

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    return df

# ================= STATE =================
if "nap" not in st.session_state:
    st.session_state.nap = None
if "rut" not in st.session_state:
    st.session_state.rut = None
if "login" not in st.session_state:
    st.session_state.login = None

# ================= IMPORT =================
if menu == "📥 数据导入":

    st.subheader("📥 上传数据")

    nap_file = st.file_uploader("充值数据", type=["xlsx"])
    rut_file = st.file_uploader("提现数据", type=["xlsx"])
    login_file = st.file_uploader("登录数据", type=["xlsx"])

    if nap_file:
        st.session_state.nap = safe_read(nap_file)

    if rut_file:
        st.session_state.rut = safe_read(rut_file)

    if login_file:
        st.session_state.login = safe_read(login_file)

    st.success("数据已加载")

# ================= DASHBOARD =================
if menu == "📊 总览":

    if st.session_state.nap is not None and st.session_state.rut is not None:

        total_nap = st.session_state.nap["amount"].sum()
        total_rut = st.session_state.rut["amount"].sum()

        col1, col2 = st.columns(2)

        col1.metric("💰 总充值", int(total_nap))
        col2.metric("💸 总提现", int(total_rut))

    else:
        st.warning("请先上传数据")

# ================= ANALYSIS =================
if menu == "📊 分析":

    if st.session_state.nap is not None and st.session_state.rut is not None:

        nap = st.session_state.nap
        rut = st.session_state.rut

        nap_group = nap.groupby("user")["amount"].sum().reset_index()
        rut_group = rut.groupby("user")["amount"].sum().reset_index()

        df = pd.merge(nap_group, rut_group, on="user", how="outer", suffixes=("_nap", "_rut")).fillna(0)
        df["profit"] = df["amount_nap"] - df["amount_rut"]

        st.dataframe(df.sort_values("profit", ascending=False), use_container_width=True)

    else:
        st.warning("请先上传数据")

# ================= CRM CORE =================
if menu == "🎯 客户维护":

    if st.session_state.nap is None or st.session_state.login is None:
        st.warning("需要充值 + 登录数据")
        st.stop()

    nap = st.session_state.nap
    login = st.session_state.login

    now = datetime.now()

    # ===== 最近时间 =====
    nap_recent = nap.groupby("user")["date"].max().reset_index()
    login_recent = login.groupby("user")["date"].max().reset_index()

    df = pd.merge(nap_recent, login_recent, on="user", how="outer", suffixes=("_nap", "_login"))

    df["days_no_nap"] = (now - df["date_nap"]).dt.days
    df["days_login"] = (now - df["date_login"]).dt.days

    # ===== 分类 =====
    def classify(row):
        if pd.isna(row["date_nap"]):
            return "🔥 活跃未充值"

        if row["days_no_nap"] <= 3:
            return "✅ 正常用户"

        if row["days_no_nap"] <= 7:
            return "⚠️ 流失风险"

        return "❄️ 沉睡用户"

    df["type"] = df.apply(classify, axis=1)

    # ===== VIP =====
    total_nap = nap.groupby("user")["amount"].sum().reset_index()
    total_nap.rename(columns={"amount": "total"}, inplace=True)

    df = pd.merge(df, total_nap, on="user", how="left")

    df["vip"] = df["total"].apply(lambda x: "💎 VIP" if x > 10000 else "")

    # ===== 建议 =====
    def suggest(row):
        if row["type"] == "🔥 活跃未充值":
            return "🎁 送彩金"
        if row["type"] == "⚠️ 流失风险":
            return "📞 联系客户"
        if row["type"] == "❄️ 沉睡用户":
            return "🔥 唤醒活动"
        if row["vip"] == "💎 VIP":
            return "💎 专属客服"
        return "保持"

    df["建议"] = df.apply(suggest, axis=1)

    # ===== 排序 =====
    priority = {
        "🔥 活跃未充值": 1,
        "⚠️ 流失风险": 2,
        "❄️ 沉睡用户": 3,
        "✅ 正常用户": 4
    }

    df["priority"] = df["type"].map(priority)

    df = df.sort_values(["priority", "total"], ascending=[True, False])

    st.subheader("🎯 重点客户")

    st.dataframe(
        df[["user", "type", "vip", "days_no_nap", "days_login", "total", "建议"]],
        use_container_width=True
    )
