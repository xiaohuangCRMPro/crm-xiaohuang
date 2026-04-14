import streamlit as st
import pandas as pd
import time

# ================= CONFIG =================
st.set_page_config(
    page_title="XiaoHuang CRM",
    page_icon="🐉",
    layout="wide"
)

# ================= STYLE =================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.9)),
    url("https://images.unsplash.com/photo-1503264116251-35a269479413");
    background-size: cover;
    background-attachment: fixed;
}

/* LOGIN BOX */
.login-box {
    max-width: 400px;
    margin: auto;
    margin-top: 120px;
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(10px);
    padding: 30px;
    border-radius: 20px;
    color: white;
    box-shadow: 0 0 30px rgba(255,75,75,0.5);
}

/* TITLE */
.title {
    text-align:center;
    font-size:42px;
    font-weight:bold;
    color:#ff4b4b;
}

/* BUTTON */
.stButton>button {
    width:100%;
    border-radius:10px;
    background:#ff4b4b;
    color:white;
    font-size:16px;
}
</style>
""", unsafe_allow_html=True)

# ================= LOGIN =================
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.markdown('<div class="title">🐉 XiaoHuang CRM 🐉</div>', unsafe_allow_html=True)

    st.markdown('<div class="login-box">', unsafe_allow_html=True)

    username = st.text_input("👤 Username")
    password = st.text_input("🔒 Password", type="password")

    if st.button("🚀 Đăng nhập"):
        if username == "admin" and password == "123":
            st.session_state.login = True
            st.rerun()
        else:
            st.error("❌ Sai tài khoản")

    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ================= MAIN =================

st.title("🔥 XiaoHuang CRM Dashboard")

menu = st.sidebar.selectbox("📌 Menu", [
    "Dashboard",
    "Upload Data",
    "Preview",
    "功能说明"
])

# ================= DASHBOARD =================
if menu == "Dashboard":
    st.subheader("📊 Tổng quan hệ thống")
    st.info("Upload dữ liệu để bắt đầu phân tích")

# ================= UPLOAD =================
elif menu == "Upload Data":

    st.subheader("📂 Upload dữ liệu Excel")

    nap_file = st.file_uploader("📥 File nạp", type=["xlsx"])
    rut_file = st.file_uploader("📤 File rút", type=["xlsx"])
    login_file = st.file_uploader("🔑 File login", type=["xlsx"])

    if nap_file and rut_file and login_file:

        progress = st.progress(0)
        status = st.empty()

        status.text("🚀 Đang xử lý dữ liệu...")

        progress.progress(20)
        time.sleep(0.5)
        nap = pd.read_excel(nap_file)

        progress.progress(50)
        time.sleep(0.5)
        rut = pd.read_excel(rut_file)

        progress.progress(80)
        time.sleep(0.5)
        login_df = pd.read_excel(login_file)

        progress.progress(100)
        time.sleep(0.3)

        st.session_state.nap = nap
        st.session_state.rut = rut
        st.session_state.login_df = login_df

        status.text("✅ Hoàn thành!")
        st.success("Upload thành công!")

# ================= PREVIEW =================
elif menu == "Preview":

    if "nap" in st.session_state:

        st.subheader("📊 Dữ liệu")

        col1, col2, col3 = st.columns(3)

        col1.metric("Tổng nạp", st.session_state.nap.shape[0])
        col2.metric("Tổng rút", st.session_state.rut.shape[0])
        col3.metric("User login", st.session_state.login_df.shape[0])

        st.dataframe(st.session_state.nap.head(), use_container_width=True)

    else:
        st.warning("⚠️ Chưa upload dữ liệu")

# ================= 功能说明 =================
elif menu == "功能说明":

    st.title("📘 功能说明 / Mô tả chức năng")

    st.markdown("""
    ## 🐉 XiaoHuang CRM 系统 / Hệ thống CRM XiaoHuang

    一个轻量级数据分析工具  
    Công cụ phân tích dữ liệu nhẹ, chạy trực tiếp trên web  

    ---

    ### 🔐 登录系统 / Đăng nhập
    用户账号密码登录  
    Người dùng đăng nhập bằng tài khoản  

    ---

    ### 📂 数据上传 / Tải dữ liệu
    支持上传3个Excel文件  
    Hỗ trợ 3 file Excel  

    • 充值数据 / Nạp  
    • 提现数据 / Rút  
    • 登录数据 / Login  

    ---

    ### 📊 数据统计 / Thống kê
    自动统计关键数据  
    Tự động thống kê  

    ---

    ### 📈 数据预览 / Xem dữ liệu
    显示上传数据  
    Hiển thị dữ liệu  

    ---

    ### 🎨 界面设计 / Giao diện
    云背景 + 深色主题  
    Nền mây + giao diện tối  

    ---

    ### 🚀 系统特点 / Điểm mạnh
    无需安装软件  
    Không cần cài đặt  

    支持多用户  
    Hỗ trợ nhiều người dùng  

    ---

    ### 🔮 后续扩展 / Nâng cấp
    VIP分类  
    AI推荐  
    数据导出  
    """)

    st.success("🔥 系统持续升级中 / Hệ thống đang nâng cấp...")
