import streamlit as st
import pandas as pd
from datetime import datetime

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
for key in ["nap", "rut", "login"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ================= MASTER TABLE =================
def build_master():
    nap = st.session_state.nap
    rut = st.session_state.rut
    login = st.session_state.login

    nap_sum = nap.groupby("user")["amount"].sum().reset_index().rename(columns={"amount": "total_nap"})
    rut_sum = rut.groupby("user")["amount"].sum().reset_index().rename(columns={"amount": "total_rut"})

    nap_last = nap.groupby("user")["date"].max().reset_index().rename(columns={"date": "last_nap"})
    login_last = login.groupby("user")["date"].max().reset_index().rename(columns={"date": "last_login"})

    df = nap_sum.merge(rut_sum, on="user", how="outer")
    df = df.merge(nap_last, on="user", how="left")
    df = df.merge(login_last, on="user", how="left")

    df.fillna(0, inplace=True)

    df["profit"] = df["total_nap"] - df["total_rut"]

    now = datetime.now()

    df["days_no_nap"] = (now - pd.to_datetime(df["last_nap"], errors="coerce")).dt.days
    df["days_login"] = (now - pd.to_datetime(df["last_login"], errors="coerce")).dt.days

    return df

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

        master = build_master()

        col1, col2, col3 = st.columns(3)

        col1.metric("💰 总充值", int(master["total_nap"].sum()))
        col2.metric("💸 总提现", int(master["total_rut"].sum()))
        col3.metric("📈 总利润", int(master["profit"].sum()))

    else:
        st.warning("请先上传数据")

# ================= ANALYSIS =================
if menu == "📊 分析":

    if st.session_state.nap is None or st.session_state.rut is None:
        st.warning("请先上传数据")
    else:
        master = build_master()

        st.subheader("📊 用户总数据")

        st.dataframe(
            master.sort_values("profit", ascending=False),
            use_container_width=True
        )

# ================= CRM =================
if menu == "🎯 客户维护":

    if st.session_state.nap is None or st.session_state.login is None:
        st.warning("需要充值 + 登录数据")
        st.stop()

    df = build_master()

    # ===== 分类 =====
    def classify(row):
        if row["total_nap"] == 0 and row["days_login"] <= 3:
            return "🔥 活跃未充值"

        if row["days_no_nap"] <= 3:
            return "✅ 正常用户"

        if row["days_no_nap"] <= 7:
            return "⚠️ 流失风险"

        return "❄️ 沉睡用户"

    df["type"] = df.apply(classify, axis=1)

    # ===== VIP =====
    df["vip"] = df["total_nap"].apply(lambda x: "💎 VIP" if x > 10000 else "")

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

    df = df.sort_values(["priority", "total_nap"], ascending=[True, False])

    st.subheader("🎯 客户维护核心")

    st.dataframe(
        df[[
            "user",
            "total_nap",
            "total_rut",
            "profit",
            "days_no_nap",
            "days_login",
            "type",
            "vip",
            "建议"
        ]],
        use_container_width=True
    )
