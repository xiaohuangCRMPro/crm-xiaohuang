import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide")

# ================= UI STYLE =================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #020617, #0f172a);
    color: white;
}

section[data-testid="stSidebar"] {
    background-color: #020617;
}

h1, h2, h3 {
    color: #f97316;
}

.card {
    background: #111827;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #374151;
    text-align: center;
}

.money {
    background: linear-gradient(90deg,#065f46,#064e3b);
    padding: 15px;
    border-radius: 12px;
}

.vip {
    background: linear-gradient(90deg,#78350f,#451a03);
    padding: 15px;
    border-radius: 12px;
}

.sleep {
    background: #1f2937;
    padding: 15px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

st.title("🔥 CRM赚钱系统 PRO MAX")

# ================= MENU =================
menu = st.sidebar.radio("功能菜单",
    ["📊 总览","📥 数据上传","📊 分析","🎯 客户管理"]
)

# ================= READ =================
def read_file(file, t):
    df = pd.read_excel(file)
    df.columns = df.columns.str.strip()

    if t == "nap":
        df.rename(columns={"会员ID":"user","支付金额":"amount","完成时间":"date"}, inplace=True)

    if t == "rut":
        df.rename(columns={"会员ID":"user","提现金额":"amount","完成时间":"date"}, inplace=True)

    if t == "login":
        df.rename(columns={"会员ID":"user","日期":"date"}, inplace=True)

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    return df

# ================= STATE =================
for k in ["nap","rut","login"]:
    if k not in st.session_state:
        st.session_state[k] = None

# ================= UPLOAD =================
if menu == "📥 数据上传":

    nap = st.file_uploader("充值")
    rut = st.file_uploader("提现")
    login = st.file_uploader("登录")

    if nap:
        st.session_state.nap = read_file(nap,"nap")
    if rut:
        st.session_state.rut = read_file(rut,"rut")
    if login:
        st.session_state.login = read_file(login,"login")

    st.success("数据加载完成")

# ================= DASHBOARD =================
if menu == "📊 总览":

    if st.session_state.nap is None or st.session_state.rut is None:
        st.warning("先上传数据")
        st.stop()

    total_nap = st.session_state.nap["amount"].sum()
    total_rut = st.session_state.rut["amount"].sum()

    c1,c2 = st.columns(2)

    c1.markdown(f'<div class="card"><h2>总充值</h2><h1>{int(total_nap)}</h1></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="card"><h2>总提现</h2><h1>{int(total_rut)}</h1></div>', unsafe_allow_html=True)

# ================= ANALYSIS =================
if menu == "📊 分析":

    if st.session_state.nap is None or st.session_state.rut is None:
        st.warning("先上传数据")
        st.stop()

    nap = st.session_state.nap
    rut = st.session_state.rut

    nap_g = nap.groupby("user")["amount"].sum().reset_index()
    rut_g = rut.groupby("user")["amount"].sum().reset_index()

    df = pd.merge(nap_g,rut_g,on="user",how="outer",suffixes=("_nap","_rut")).fillna(0)
    df["profit"] = df["amount_nap"] - df["amount_rut"]

    st.dataframe(df.sort_values("profit",ascending=False), use_container_width=True)

# ================= CRM =================
if menu == "🎯 客户管理":

    if st.session_state.nap is None or st.session_state.login is None:
        st.warning("需要充值+登录")
        st.stop()

    nap = st.session_state.nap
    login = st.session_state.login
    rut = st.session_state.rut if st.session_state.rut is not None else pd.DataFrame()

    now = datetime.now()

    # ===== TOTAL =====
    nap_total = nap.groupby("user")["amount"].sum().reset_index()
    nap_total.rename(columns={"amount":"nap_total"}, inplace=True)

    if not rut.empty:
        rut_total = rut.groupby("user")["amount"].sum().reset_index()
        rut_total.rename(columns={"amount":"rut_total"}, inplace=True)
    else:
        rut_total = pd.DataFrame(columns=["user","rut_total"])

    df = pd.merge(nap_total,rut_total,on="user",how="outer").fillna(0)

    # ===== DATE =====
    nap_last = nap.groupby("user")["date"].max().reset_index()
    login_last = login.groupby("user")["date"].max().reset_index()

    df = df.merge(nap_last,on="user",how="left")
    df = df.merge(login_last,on="user",how="left",suffixes=("_nap","_login"))

    df["days_no_nap"] = (now - df["date_nap"]).dt.days
    df["days_login"] = (now - df["date_login"]).dt.days

    df["profit"] = df["nap_total"] - df["rut_total"]

    # ===== SCORE =====
    df["score"] = (
        df["nap_total"]*0.4 +
        (30 - df["days_no_nap"].clip(0,30))*20 +
        (30 - df["days_login"].clip(0,30))*10
    )

    # ===== 分类 =====
    def classify(r):
        if r["nap_total"] == 0 and r["days_login"] <= 3:
            return "🎯 可转化"
        if r["days_no_nap"] <= 3:
            return "✅ 正常"
        if r["days_no_nap"] <= 7:
            return "⚠️ 风险"
        return "❄️ 流失"

    df["type"] = df.apply(classify,axis=1)

    # ===== 赚钱客户 =====
    money = df[(df["days_login"]<=3) & (df["days_no_nap"]>=2)]

    st.markdown("### 💰 赚钱客户")
    st.markdown('<div class="money">优先处理</div>', unsafe_allow_html=True)
    st.dataframe(money.sort_values("score",ascending=False).head(20), use_container_width=True)

    # ===== VIP =====
    vip = df[df["nap_total"]>10000]

    st.markdown("### 💎 VIP")
    st.markdown('<div class="vip">高价值用户</div>', unsafe_allow_html=True)
    st.dataframe(vip.sort_values("nap_total",ascending=False), use_container_width=True)

    # ===== 流失 =====
    sleep = df[df["days_no_nap"]>7]

    st.markdown("### ❄️ 流失用户")
    st.markdown('<div class="sleep">需要唤醒</div>', unsafe_allow_html=True)
    st.dataframe(sleep, use_container_width=True)
