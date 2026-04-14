
import streamlit as st
import pandas as pd
from datetime import datetime
import io

st.set_page_config(layout="wide")

# ================= UI =================
st.title("🔥 CRM SMART SYSTEM")

menu = st.sidebar.radio("Menu", [
    "📥 Upload",
    "📊 Dashboard",
    "📊 Analysis",
    "🎯 CRM"
])

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

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df

# ================= STATE =================
for k in ["nap","rut","login"]:
    if k not in st.session_state:
        st.session_state[k] = None

# ================= UPLOAD =================
if menu == "📥 Upload":

    nap = st.file_uploader("充值")
    rut = st.file_uploader("提现")
    login = st.file_uploader("登录")

    if nap:
        st.session_state.nap = read_file(nap,"nap")
    if rut:
        st.session_state.rut = read_file(rut,"rut")
    if login:
        st.session_state.login = read_file(login,"login")

    st.success("✅ Done")

# ================= DASHBOARD =================
if menu == "📊 Dashboard":

    if st.session_state.nap is None:
        st.warning("Upload data first")
        st.stop()

    nap = st.session_state.nap
    rut = st.session_state.rut if st.session_state.rut is not None else pd.DataFrame()

    total_nap = nap["amount"].sum()
    total_rut = rut["amount"].sum() if not rut.empty else 0

    c1,c2 = st.columns(2)
    c1.metric("💰 Total Deposit", int(total_nap))
    c2.metric("💸 Total Withdraw", int(total_rut))

# ================= ANALYSIS =================
if menu == "📊 Analysis":

    nap = st.session_state.nap
    rut = st.session_state.rut

    if nap is None or rut is None:
        st.warning("Upload data first")
        st.stop()

    nap_g = nap.groupby("user")["amount"].sum().reset_index()
    rut_g = rut.groupby("user")["amount"].sum().reset_index()

    df = pd.merge(nap_g,rut_g,on="user",how="outer",suffixes=("_nap","_rut")).fillna(0)
    df["profit"] = df["amount_nap"] - df["amount_rut"]

    st.dataframe(df.sort_values("profit",ascending=False), use_container_width=True)

# ================= CRM =================
if menu == "🎯 CRM":

    nap = st.session_state.nap
    login = st.session_state.login
    rut = st.session_state.rut if st.session_state.rut is not None else pd.DataFrame()

    if nap is None or login is None:
        st.warning("Need nap + login data")
        st.stop()

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

    # ===== RULE =====
    df["A1_LOGIN_NO_DEPOSIT"] = (df["nap_total"] == 0) & (df["days_login"] <= 3)
    df["A2_RECENT_DEPOSIT_LOST"] = (df["days_no_nap"] >= 3) & (df["days_no_nap"] <= 7)
    df["A3_DEPOSIT_DROP"] = (df["profit"] < 0)
    df["A4_HIGH_VALUE_COOLING"] = (df["nap_total"] > 10000) & (df["days_no_nap"] >= 5)
    df["B1_LOGIN_OK_NO_REDEPOSIT"] = (df["days_login"] <= 3) & (df["days_no_nap"] >= 2)

    # ===== PRIORITY =====
    def priority(row):
        if row["A1_LOGIN_NO_DEPOSIT"] or row["A2_RECENT_DEPOSIT_LOST"]:
            return "P1"
        elif row["A3_DEPOSIT_DROP"] or row["A4_HIGH_VALUE_COOLING"]:
            return "P2"
        else:
            return "P3"

    df["priority"] = df.apply(priority, axis=1)

    # ===== ACTION =====
    def action(row):
        if row["A1_LOGIN_NO_DEPOSIT"]:
            return "Gửi KM lần đầu"
        if row["A2_RECENT_DEPOSIT_LOST"]:
            return "Call + bonus giữ chân"
        if row["A3_DEPOSIT_DROP"]:
            return "Check trải nghiệm"
        if row["A4_HIGH_VALUE_COOLING"]:
            return "VIP chăm sóc riêng"
        if row["B1_LOGIN_OK_NO_REDEPOSIT"]:
            return "Push nạp lại"
        return "Theo dõi"

    df["action"] = df.apply(action, axis=1)

    # ===== FILTER =====
    st.subheader("🎯 CRM LIST")

    p = st.selectbox("Priority", ["ALL","P1","P2","P3"])

    view = df.copy()
    if p != "ALL":
        view = view[view["priority"] == p]

    view = view.sort_values(["priority","score"], ascending=[True,False])

    st.dataframe(view[[
        "user","nap_total","rut_total",
        "days_no_nap","days_login",
        "priority","action"
    ]], use_container_width=True)

    # ===== EXPORT =====
    def download_excel(df):
        output = io.BytesIO()
        df.to_excel(output, index=False)
        return output

    st.download_button(
        "📥 Export Excel",
        download_excel(view),
        "crm.xlsx"
    )
