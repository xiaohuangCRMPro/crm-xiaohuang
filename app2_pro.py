import streamlit as st
import pandas as pd

st.set_page_config(page_title="CRM维护系统", layout="wide")

st.title("🔥 CRM 维护系统")

# ======================
# LOAD FUNCTIONS
# ======================

def convert_date(df, col):
    df[col] = df[col].astype(str)
    df[col] = df[col].str.replace("年","-").str.replace("月","-").str.replace("日","")
    df[col] = pd.to_datetime(df[col], errors="coerce")
    return df

def load_nap(file):
    df = pd.read_excel(file)
    df = df.rename(columns={
        "会员ID": "user",
        "支付金额": "amount",
        "完成时间": "date"
    })
    df = convert_date(df, "date")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    return df

def load_rut(file):
    df = pd.read_excel(file)
    df = df.rename(columns={
        "会员ID": "user",
        "提现金额": "amount",
        "完成时间": "date"
    })
    df = convert_date(df, "date")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    return df

def load_login(file):
    df = pd.read_excel(file)
    df = df.rename(columns={
        "会员ID": "user",
        "日期": "date"
    })
    df = convert_date(df, "date")
    return df

# ======================
# MENU
# ======================

menu = st.sidebar.selectbox("📂 菜单", [
    "Dashboard",
    "导入数据",
    "分析",
    "客户维护",
])

# ======================
# IMPORT DATA
# ======================

if menu == "导入数据":

    st.header("📥 上传数据")

    nap_file = st.file_uploader("上传充值数据", type=["xlsx"])
    rut_file = st.file_uploader("上传提现数据", type=["xlsx"])
    login_file = st.file_uploader("上传登录数据", type=["xlsx"])

    if nap_file:
        st.session_state.nap = load_nap(nap_file)
        st.success("充值数据已加载")

    if rut_file:
        st.session_state.rut = load_rut(rut_file)
        st.success("提现数据已加载")

    if login_file:
        st.session_state.login = load_login(login_file)
        st.success("登录数据已加载")

# ======================
# DASHBOARD
# ======================

if menu == "Dashboard":

    st.header("📊 总览")

    if "nap" in st.session_state:
        total_nap = st.session_state.nap["amount"].sum()
        st.metric("总充值", total_nap)

    if "rut" in st.session_state:
        total_rut = st.session_state.rut["amount"].sum()
        st.metric("总提现", total_rut)

# ======================
# ANALYSIS
# ======================

if menu == "分析":

    st.header("📊 数据分析")

    if "nap" in st.session_state and "rut" in st.session_state:

        df_nap = st.session_state.nap.groupby("user")["amount"].sum()
        df_rut = st.session_state.rut.groupby("user")["amount"].sum()

        df = pd.concat([df_nap, df_rut], axis=1).fillna(0)
        df.columns = ["充值", "提现"]

        df["利润"] = df["充值"] - df["提现"]

        st.dataframe(df.sort_values("利润", ascending=False))

# ======================
# CRM MAINTENANCE
# ======================

if menu == "客户维护":

    st.header("🎁 客户维护")

    if "login" in st.session_state and "nap" in st.session_state:

        now = pd.Timestamp.now()

        login_df = st.session_state.login
        nap_df = st.session_state.nap

        # 最近3天登录
        recent_login = login_df[
            login_df["date"] >= now - pd.Timedelta(days=3)
        ]

        active_users = set(recent_login["user"])
        nap_users = set(nap_df["user"])

        # 登录但没充值
        no_deposit = list(active_users - nap_users)

        st.subheader("🔥 活跃但未充值用户")
        st.write(no_deposit)

        # 沉睡用户
        last_login = login_df.groupby("user")["date"].max().reset_index()

        sleep_users = last_login[
            last_login["date"] < now - pd.Timedelta(days=7)
        ]

        st.subheader("❄️ 沉睡用户")
        st.dataframe(sleep_users)

        # VIP
        vip = nap_df.groupby("user")["amount"].sum().reset_index()
        vip = vip[vip["amount"] > 1000]

        st.subheader("💎 VIP用户")
        st.dataframe(vip)

# ======================
# DEBUG
# ======================

st.sidebar.write("📌 状态:")
st.sidebar.write(st.session_state.keys())
