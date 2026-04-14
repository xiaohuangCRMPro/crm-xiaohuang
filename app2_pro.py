import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# ===== CONFIG =====
st.set_page_config(layout="wide")

# ===== STYLE =====
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg,#020617,#0f172a);
    color: white;
}

/* HEADER */
.title {
    text-align:center;
    padding:15px;
    font-size:32px;
    font-weight:bold;
    color:#f97316;
}

/* MENU */
.menu-btn button {
    width: 100%;
    height: 45px;
    border-radius: 10px;
    background: #111827;
    color: #9ca3af;
    border: 1px solid #1f2937;
    font-weight: 600;
}

.active-btn button {
    background: linear-gradient(90deg,#f97316,#fb7185);
    color: white !important;
    border: none;
}

/* CARD */
.card {
    padding:20px;
    border-radius:15px;
    background:#111827;
    text-align:center;
    font-size:20px;
}

/* BUTTON */
.stButton>button {
    background: linear-gradient(90deg,#f97316,#fb7185);
    border-radius:10px;
    color:white;
    font-weight:bold;
}

/* TABLE */
[data-testid="stDataFrame"] {
    border-radius:10px;
}
</style>
""", unsafe_allow_html=True)

# ===== LOGIN =====
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.markdown("<h2 style='text-align:center'>🔐 登录系统</h2>", unsafe_allow_html=True)
    user = st.text_input("账号")
    pw = st.text_input("密码", type="password")

    if st.button("登录"):
        if user == "xiaohuang" and pw == "aa123456":
            st.session_state.login = True
            st.rerun()
        else:
            st.error("Sai tài khoản")

    st.stop()

# ===== HEADER =====
st.markdown("<div class='title'>🔥 XiaoHuang CRM Pro 🔥</div>", unsafe_allow_html=True)

# ===== MENU =====
if "menu" not in st.session_state:
    st.session_state.menu = "Dashboard"

def set_menu(x):
    st.session_state.menu = x

menus = ["Dashboard","Import","Analysis","P1","History"]
icons = ["📊","📥","🧠","🔥","📅"]

cols = st.columns(5)
for i,m in enumerate(menus):
    with cols[i]:
        cls = "active-btn" if st.session_state.menu==m else "menu-btn"
        st.markdown(f"<div class='{cls}'>", unsafe_allow_html=True)
        if st.button(f"{icons[i]} {m}"):
            set_menu(m)
        st.markdown("</div>", unsafe_allow_html=True)

menu = st.session_state.menu

# ===== DB =====
conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    uid TEXT,
    nap REAL,
    rut REAL,
    login TEXT,
    days_no_login REAL,
    标签 TEXT,
    priority TEXT,
    AI建议 TEXT,
    date TEXT
)
""")
conn.commit()

# ===== IMPORT =====
if menu == "Import":
    st.title("📥 导入数据")

    nap_file = st.file_uploader("充值")
    rut_file = st.file_uploader("提现")
    login_file = st.file_uploader("登录")

    if st.button("🚀 运行分析"):
        with st.spinner("Đang xử lý siêu cấp..."):
            nap = pd.read_excel(nap_file)
            rut = pd.read_excel(rut_file)
            login = pd.read_excel(login_file)

            nap.columns = ["uid","nap","date"]
            rut.columns = ["uid","rut","date"]
            login.columns = ["uid","login"]

            df = nap.merge(rut, on="uid", how="outer")
            df = df.merge(login, on="uid", how="outer")

            df.fillna(0, inplace=True)

            df["login"] = pd.to_datetime(df["login"], errors="coerce")
            df["days_no_login"] = (pd.Timestamp.now() - df["login"]).dt.days

            df["标签"] = "正常"
            df.loc[df["days_no_login"] > 3, "标签"] = "流失风险"
            df.loc[(df["nap"]>1000)&(df["rut"]>0),"标签"]="VIP流失"

            df["priority"] = "P3"
            df.loc[df["标签"]!="正常","priority"]="P1"

            df["AI建议"]="维护"
            df.loc[df["标签"]=="流失风险","AI建议"]="发奖励拉回"
            df.loc[df["标签"]=="VIP流失","AI建议"]="人工联系+优惠"

            df["date"]=str(datetime.now())

            df.to_sql("history", conn, if_exists="append", index=False)

        st.success("🔥 完成")

# ===== LOAD =====
df = pd.read_sql("SELECT * FROM history", conn)

# ===== DASHBOARD =====
if menu == "Dashboard":
    st.title("📊 Dashboard")

    c1,c2,c3,c4 = st.columns(4)

    c1.markdown(f"<div class='card'>👤 用户<br>{df['uid'].nunique()}</div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='card'>🔥 P1<br>{(df['priority']=='P1').sum()}</div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='card'>💰 VIP<br>{(df['标签']=='VIP流失').sum()}</div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='card'>⚠️ 风险<br>{(df['标签']=='流失风险').sum()}</div>", unsafe_allow_html=True)

# ===== ANALYSIS =====
if menu == "Analysis":
    st.title("🧠 分析")
    st.dataframe(df, use_container_width=True)

# ===== P1 =====
if menu == "P1":
    st.title("🔥 高优先级")
    st.dataframe(df[df["priority"]=="P1"], use_container_width=True)

# ===== HISTORY =====
if menu == "History":
    st.title("📅 历史")
    st.dataframe(df, use_container_width=True)