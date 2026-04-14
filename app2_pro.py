import streamlit as st
import pandas as pd
import datetime

st.set_page_config(layout="wide")

# ================= LOGIN =================
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 登录系统")

    u = st.text_input("账号")
    p = st.text_input("密码", type="password")

    if st.button("登录"):
        if u == "admin" and p == "123":
            st.session_state.login = True
            st.rerun()
        else:
            st.error("错误")

    st.stop()

# ================= NAV =================
st.markdown("## 🔥 CRM 维护系统")

col1,col2,col3,col4,col5 = st.columns(5)

if col1.button("📊 Dashboard"):
    st.session_state.page="dash"
if col2.button("📥 导入"):
    st.session_state.page="import"
if col3.button("📊 分析"):
    st.session_state.page="analysis"
if col4.button("🎁 维护"):
    st.session_state.page="care"
if col5.button("📜 历史"):
    st.session_state.page="history"

if "page" not in st.session_state:
    st.session_state.page="dash"

# ================= IMPORT =================
if st.session_state.page=="import":

    st.subheader("📥 数据导入")

    nap_file = st.file_uploader("充值", type=["xlsx"])
    rut_file = st.file_uploader("提现", type=["xlsx"])
    login_file = st.file_uploader("登录", type=["xlsx"])

    if st.button("🚀 导入"):
        if nap_file and rut_file and login_file:

            st.session_state.nap = pd.read_excel(nap_file)
            st.session_state.rut = pd.read_excel(rut_file)
            st.session_state.login_df = pd.read_excel(login_file)

            st.session_state.history = "已导入 " + str(datetime.datetime.now())

            st.success("✅ 成功")

# ================= DASHBOARD =================
elif st.session_state.page=="dash":

    st.subheader("📊 总览")

    if "nap" in st.session_state:

        nap = st.session_state.nap
        rut = st.session_state.rut

        total_nap = nap["amount"].sum()
        total_rut = rut["amount"].sum()

        col1,col2,col3 = st.columns(3)

        col1.metric("总充值", total_nap)
        col2.metric("总提现", total_rut)
        col3.metric("净利润", total_nap-total_rut)

# ================= ANALYSIS =================
elif st.session_state.page=="analysis":

    if "nap" not in st.session_state:
        st.warning("无数据")
        st.stop()

    nap = st.session_state.nap
    rut = st.session_state.rut
    login = st.session_state.login_df

    now = datetime.datetime.now()

    nap["date"] = pd.to_datetime(nap["date"])
    rut["date"] = pd.to_datetime(rut["date"])
    login["date"] = pd.to_datetime(login["date"])

    # ===== GROUP =====
    nap_g = nap.groupby("user").agg(
        total_nap=("amount","sum"),
        nap_count=("amount","count"),
        last_nap=("date","max")
    ).reset_index()

    rut_g = rut.groupby("user").agg(
        total_rut=("amount","sum"),
        rut_count=("amount","count")
    ).reset_index()

    login_g = login.groupby("user").agg(
        last_login=("date","max"),
        login_count=("date","count")
    ).reset_index()

    df = nap_g.merge(rut_g, on="user", how="left")
    df = df.merge(login_g, on="user", how="left")
    df.fillna(0, inplace=True)

    df["profit"] = df["total_nap"] - df["total_rut"]
    df["inactive_days"] = (now - df["last_login"]).dt.days

    # ===== TIME WINDOW =====
    def active(df, days):
        return df[df["date"] >= now - datetime.timedelta(days=days)]

    nap_3 = active(nap,3).groupby("user").size()
    nap_7 = active(nap,7).groupby("user").size()

    df["nap_3d"] = df["user"].map(nap_3).fillna(0)
    df["nap_7d"] = df["user"].map(nap_7).fillna(0)

    # ===== CLASSIFY =====
    def classify(r):

        if r["total_nap"] == 0:
            return "❌ 无价值"

        if r["total_nap"] > 10000 and r["nap_7d"]==0:
            return "🔥 VIP流失"

        if r["nap_count"]>5 and r["rut_count"]>5:
            return "⚠️ 高频交易"

        if r["login_count"]>5 and r["nap_7d"]==0:
            return "👀 只登录"

        if r["inactive_days"]>10:
            return "😴 沉睡"

        if r["profit"]>0:
            return "💰 盈利"

        return "普通"

    df["分类"] = df.apply(classify,axis=1)

    # ===== PRIORITY =====
    order = {
        "🔥 VIP流失":1,
        "💰 盈利":2,
        "⚠️ 高频交易":3,
        "😴 沉睡":4,
        "👀 只登录":5
    }

    df["priority"] = df["分类"].map(order)

    df = df.sort_values("priority")

    st.dataframe(df, use_container_width=True)

# ================= CARE =================
elif st.session_state.page=="care":

    st.subheader("🎁 客户维护")

    if "nap" not in st.session_state:
        st.warning("无数据")
        st.stop()

    df = st.session_state.nap.groupby("user")["amount"].sum().reset_index()

    def suggest(x):
        if x>10000:
            return "🎁 5%"
        elif x>3000:
            return "🎁 2%"
        else:
            return "🎁 小奖励"

    df["建议"] = df["amount"].apply(suggest)

    st.dataframe(df)

# ================= HISTORY =================
elif st.session_state.page=="history":

    st.subheader("📜 导入历史")

    if "history" in st.session_state:
        st.info(st.session_state.history)
    else:
        st.warning("暂无记录")
